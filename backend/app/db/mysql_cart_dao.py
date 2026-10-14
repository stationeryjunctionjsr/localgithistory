"""
MySQL DAO for sj_carts (+ sj_cart_items).
"""

from typing import List, Optional, Any
from app.models.cart import Cart
from app.models.daos import CartInternalCreate, CartInternalUpdate, CartItemInternal

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc


class MySQLCartDAO:
    @property
    def TABLE(self):
        return "sj_carts"

    @property
    def ITEMS_TABLE(self):
        return "sj_cart_items"

    async def findAll(
        self,
        id: Optional[int] = None,
        user: Optional[int] = None,
    ) -> List[Cart]:
        where_clauses = []
        params = {}
        if id is not None:
            where_clauses.append("id = :id")
            params["id"] = id
        if user is not None:
            where_clauses.append("user_id = :user_id")
            params["user_id"] = user

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        async_session = get_async_session_factory()
        async with async_session() as session:
            result = await session.execute(
                text(
                    f"SELECT id, user_id, created_at, updated_at FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"
                ),
                params,
            )
            rows = result.fetchall()

            if not rows:
                return []

            cart_ids = [r.id for r in rows]
            items_rows = await self._fetch_items(session, cart_ids)

        return [self._map_to_schema(r, items_rows) for r in rows]

    def _row_to_item(self, ir) -> CartItemInternal:
        variant_attrs = None
        if ir.variant_attributes:
            try:
                from app.models.schemas import VariantAttributes
                variant_attrs = VariantAttributes.model_validate_json(ir.variant_attributes)
            except (TypeError, ValueError):
                pass
        return CartItemInternal(
            id=str(ir.id),
            product=str(ir.product_id),
            quantity=int(ir.quantity),
            sell_as_case=bool(ir.sell_as_case),
            bundle_id=str(ir.bundle_id) if ir.bundle_id else None,
            bundle_name=str(ir.bundle_name) if ir.bundle_name else None,
            variant_attributes=variant_attrs,
        )

    def _map_to_schema(self, r, items_rows=None) -> Cart:
        cart = Cart.model_validate(r)
        if items_rows:
            cart.items = [
                self._row_to_item(ir)
                for ir in items_rows
                if ir.cart_id == r.id
            ]
        else:
            cart.items = []
        return cart

    async def _fetch_items(self, session, cart_ids: List[int]):
        if not cart_ids:
            return []
        items_rows = []
        chunks = [cart_ids[i : i + 999] for i in range(0, len(cart_ids), 999)]
        for chunk in chunks:
            chunk_params = {f"cid_{i}": cid for i, cid in enumerate(chunk)}
            placeholders = ", ".join([f":{k}" for k in chunk_params.keys()])
            items_result = await session.execute(
                text(
                    f"""
                    SELECT id, cart_id, product_id, quantity, sell_as_case, bundle_id, bundle_name, variant_attributes
                    FROM {self.ITEMS_TABLE}
                    WHERE cart_id IN ({placeholders})
                    ORDER BY id ASC
                    """
                ),
                chunk_params,
            )
            items_rows.extend(items_result.fetchall())
        return items_rows

    async def findOne(
        self,
        id: Optional[int] = None,
        user: Optional[int] = None,
    ) -> Optional[Cart]:
        records = await self.findAll(id=id, user=user)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[Cart]:
        return await self.findOne(id=id)

    async def _replace_items(self, session, cart_id: int, items: List[CartItemInternal]) -> None:
        await session.execute(
            text(f"DELETE FROM {self.ITEMS_TABLE} WHERE cart_id = :cart_id"),
            {"cart_id": cart_id},
        )
        for it in items or []:
            pid_raw = it.product
            if not pid_raw:
                continue
            qty = (it.quantity if it.quantity is not None else 0) or 0
            sell_as_case = 1 if it.sell_as_case else 0
            bundle_id = it.bundle_id
            bundle_name = it.bundle_name
            var_attrs = it.variant_attributes.model_dump_json() if it.variant_attributes else None

            await session.execute(
                text(
                    f"""
                    INSERT INTO {self.ITEMS_TABLE} (cart_id, product_id, quantity, sell_as_case, bundle_id, bundle_name, variant_attributes)
                    VALUES (:cart_id, :product_id, :quantity, :sell_as_case, :bundle_id, :bundle_name, :variant_attributes)
                    """
                ),
                {
                    "cart_id": cart_id,
                    "product_id": str(pid_raw),
                    "quantity": qty,
                    "sell_as_case": sell_as_case,
                    "bundle_id": bundle_id,
                    "bundle_name": bundle_name,
                    "variant_attributes": var_attrs,
                },
            )

    async def create(self, data: CartInternalCreate) -> Optional[Cart]:
        now = now_utc()

        uid = data.user

        cols = ["created_at", "updated_at"]
        vals = [":created_at", ":updated_at"]
        params = {"created_at": now, "updated_at": now}
        if uid is not None:
            cols.append("user_id")
            vals.append(":user_id")
            params["user_id"] = uid

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)

        async_session = get_async_session_factory()
        async with async_session() as session:
            result = await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = result.lastrowid

            await self._replace_items(session, new_id, data.items or [])
            await session.commit()

        return await self.findById(new_id)

    async def update(self, id: int, update_data: CartInternalUpdate) -> Optional['Cart']:
        if not id:
            return None
        now = now_utc()
        updates = ["updated_at = :updated_at"]
        params = {"id": id, "updated_at": now}

        if "user" in update_data.model_fields_set:
            updates.append("user_id = :user_id")
            params["user_id"] = update_data.user

        set_sql = ", ".join(updates)
        async_session = get_async_session_factory()
        async with async_session() as session:
            res = await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            if res.rowcount == 0:
                chk = await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE id = :id"), {"id": id})
                if not chk.fetchone():
                    return None

            if "items" in update_data.model_fields_set and update_data.items is not None:
                await self._replace_items(session, id, update_data.items)

            await session.commit()

        return await self.findById(id)

    async def update_items_atomic(
        self,
        user_id: int,
        merge_fn,
    ) -> Optional['Cart']:
        """Read-lock the user's cart row, apply merge_fn to the current items,
        and write the result — all inside one transaction.

        merge_fn(current_items: List[CartItemInternal]) -> List[CartItemInternal]

        This eliminates the lost-update race that occurs when two concurrent
        requests each read the cart state and the second write overwrites the first.

        Returns the updated Cart, or None when user_id is invalid.
        """
        if not user_id:
            return None
        numeric_uid = user_id
        now = now_utc()

        async_session = get_async_session_factory()
        async with async_session() as session:
            # Lock the cart row so no other worker can read-modify-write concurrently.
            cart_res = await session.execute(
                text(
                    f"SELECT id FROM {self.TABLE} "
                    f"WHERE user_id = :uid FOR UPDATE"
                ),
                {"uid": numeric_uid},
            )
            cart_row = cart_res.fetchone()

            if not cart_row:
                # No cart yet — create one inside the same transaction.
                res = await session.execute(
                    text(
                        f"INSERT INTO {self.TABLE} (user_id, created_at, updated_at) "
                        f"VALUES (:uid, :now, :now)"
                    ),
                    {"uid": numeric_uid, "now": now},
                )
                cart_pk = res.lastrowid
                current_items: List[CartItemInternal] = []
            else:
                cart_pk = cart_row.id

                # Fetch current items while holding the lock
                items_res = await session.execute(
                    text(
                        f"SELECT id, product_id, quantity, sell_as_case, bundle_id, bundle_name, variant_attributes "
                        f"FROM {self.ITEMS_TABLE} WHERE cart_id = :cart_id ORDER BY id ASC"
                    ),
                    {"cart_id": cart_pk},
                )
                current_items = [self._row_to_item(ir) for ir in items_res.fetchall()]

            # Let the caller decide what the new item list should be
            new_items = merge_fn(current_items)

            # Write the result
            await session.execute(
                text(f"UPDATE {self.TABLE} SET updated_at = :now WHERE id = :id"),
                {"now": now, "id": cart_pk},
            )
            await self._replace_items(session, cart_pk, new_items)
            await session.commit()

        return await self.findById(cart_pk)

    async def delete(self, id: int) -> bool:
        if not id:
            return False
        async_session = get_async_session_factory()
        async with async_session() as session:
            await session.execute(
                text(f"DELETE FROM {self.ITEMS_TABLE} WHERE cart_id = :cart_id"),
                {"cart_id": id},
            )

            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": id},
            )
            await session.commit()
            return result.rowcount > 0

    async def deleteMany(self, user: Optional[int] = None) -> int:
        where_clauses = []
        params = {}
        if user is not None:
            where_clauses.append("user_id = :user_id")
            params["user_id"] = user
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        async_session = get_async_session_factory()
        async with async_session() as session:
            await session.execute(
                text(f"DELETE FROM {self.ITEMS_TABLE} WHERE cart_id IN (SELECT id FROM {self.TABLE} WHERE {where_sql})"),
                params,
            )
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE {where_sql}"),
                params,
            )
            await session.commit()
            return result.rowcount or 0

    async def count(self, id: Optional[int] = None, user: Optional[int] = None) -> int:
        where_clauses = []
        params = {}
        if id is not None:
            where_clauses.append("id = :id")
            params["id"] = id
        if user is not None:
            where_clauses.append("user_id = :uid")
            params["uid"] = user
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        async_session = get_async_session_factory()
        async with async_session() as session:
            result = await session.execute(text(f"SELECT COUNT(*) FROM {self.TABLE} WHERE {where_sql}"), params)
            return result.scalar() or 0

