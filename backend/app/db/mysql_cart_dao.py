"""
MySQL DAO for sj_carts (+ sj_cart_items).
"""

import secrets
from typing import Dict, List, Optional, Any
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

    def _factory(self):
        return get_async_session_factory()

    def __map_to_schema(self, r, items: List[Dict]) -> Dict:
        return {
            "_id": str(r.id),
            "user": str(r.user_id),
            "items": items,
            "createdAt": r.created_at.isoformat() if r.created_at else None,
            "updatedAt": r.updated_at.isoformat() if r.updated_at else None,
        }

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        factory = self._factory()
        if not factory:
            return []

        where_clauses = []
        params = {}
        if query:
            for k, v in query.items():
                if k in ("_id", "id"):
                    where_clauses.append("id = :id")
                    params["id"] = int(v) if str(v).isdigit() else None
                elif k in ("user", "user_id"):
                    where_clauses.append("user_id = :user_id")
                    params["user_id"] = int(v) if str(v).isdigit() else None
                elif k == "external_id":
                    where_clauses.append("external_id = :external_id")
                    params["external_id"] = str(v)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        async with factory() as session:
            result = await session.execute(
                text(
                    f"SELECT id, external_id, user_id, created_at, updated_at FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"
                ),
                params,
            )
            rows = result.fetchall()

            if not rows:
                return []

            # Bulk fetch items
            cart_ids = [str(r.external_id) for r in rows]
            items_map = {cid: [] for cid in cart_ids}
            chunks = [cart_ids[i : i + 999] for i in range(0, len(cart_ids), 999)]

            for chunk in chunks:
                chunk_params = {f"cid_{i}": cid for i, cid in enumerate(chunk)}
                placeholders = ", ".join([f":{k}" for k in chunk_params.keys()])
                items_result = await session.execute(
                    text(
                        f"""
                        SELECT cart_id, product_id, quantity, sell_as_case, bundle_id, bundle_name, variant_attributes
                        FROM {self.ITEMS_TABLE}
                        WHERE cart_id IN ({placeholders})
                        ORDER BY id ASC
                        """
                    ),
                    chunk_params,
                )
                for ir in items_result.fetchall():
                    variant_attrs = None
                    if ir.variant_attributes:
                        try:
                            import json
                            parsed = json.loads(ir.variant_attributes)
                            from app.models.schemas import VariantAttributes
                            if parsed:
                                variant_attrs = VariantAttributes(**parsed)
                        except (json.JSONDecodeError, TypeError, ValueError):
                            pass
                    items_map[ir.cart_id].append(
                        {
                            "product": str(ir.product_id),
                            "quantity": int(ir.quantity),
                            "sellAsCase": bool(ir.sell_as_case),
                            "bundleId": str(ir.bundle_id) if ir.bundle_id else None,
                            "bundleName": str(ir.bundle_name) if ir.bundle_name else None,
                            "variantAttributes": variant_attrs
                        }
                    )

        return [Cart.model_validate(self.__map_to_schema(r, items_map[r.external_id])) for r in rows]

    async def findOne(self, query: Dict) -> Optional[Dict]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        return await self.findOne({"_id": id})

    async def _replace_items(self, session, cart_external_id: str, items: List[CartItemInternal]) -> None:
        await session.execute(
            text(f"DELETE FROM {self.ITEMS_TABLE} WHERE cart_id = :cart_id"),
            {"cart_id": cart_external_id},
        )
        for it in items or []:
            pid_raw = it.product
            if not pid_raw:
                continue
            qty = (it.quantity if it.quantity is not None else 0) or 0
            sell_as_case = 1 if it.sell_as_case else 0
            bundle_id = it.bundle_id
            bundle_name = it.bundle_name
            import json
            var_attrs = None
            if it.variant_attributes:
                var_attrs = json.dumps({
                    "size": it.variant_attributes.size,
                    "color": it.variant_attributes.color,
                    "material": it.variant_attributes.material,
                    "style": it.variant_attributes.style,
                    "weight": it.variant_attributes.weight,
                    "flavor": it.variant_attributes.flavor
                })

            await session.execute(
                text(
                    f"""
                    INSERT INTO {self.ITEMS_TABLE} (cart_id, product_id, quantity, sell_as_case, bundle_id, bundle_name, variant_attributes)
                    VALUES (:cart_id, :product_id, :quantity, :sell_as_case, :bundle_id, :bundle_name, :variant_attributes)
                    """
                ),
                {
                    "cart_id": cart_external_id,
                    "product_id": str(pid_raw),
                    "quantity": qty,
                    "sell_as_case": sell_as_case,
                    "bundle_id": bundle_id,
                    "bundle_name": bundle_name,
                    "variant_attributes": var_attrs,
                },
            )

    async def create(self, data: CartInternalCreate) -> Dict:
        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        now = now_utc()
        external_id = secrets.token_hex(16)

        user_id_raw = data.user
        uid = int(user_id_raw) if user_id_raw and str(user_id_raw).isdigit() else None

        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    INSERT INTO {self.TABLE} (
                        external_id, user_id, created_at, updated_at
                    ) VALUES (
                        :external_id, :user_id, :created_at, :updated_at
                    )
                    """
                ),
                {
                    "external_id": external_id,
                    "user_id": uid,
                    "created_at": now,
                    "updated_at": now,
                },
            )

            r = await session.execute(
                text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"),
                {"eid": external_id},
            )
            new_id = r.scalar()

            await self._replace_items(session, external_id, data.items or [])
            await session.commit()

        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: CartInternalUpdate) -> Optional[Dict]:
        existing = await self.findById(id)
        if not existing:
            return None

        factory = self._factory()
        if not factory:
            return None
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None

        # We only really update items for carts
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET updated_at = :updated_at WHERE id = :id"),
                {"id": pid, "updated_at": now},
            )

            # Fetch external_id
            r = await session.execute(text(f"SELECT external_id FROM {self.TABLE} WHERE id = :id"), {"id": pid})
            eid = r.scalar()

            if update_data.items is not None:
                await self._replace_items(session, eid, update_data.items)

            await session.commit()

        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            r = await session.execute(text(f"SELECT external_id FROM {self.TABLE} WHERE id = :id"), {"id": pid})
            eid = r.scalar()
            if eid:
                await session.execute(
                    text(f"DELETE FROM {self.ITEMS_TABLE} WHERE cart_id = :cart_id"),
                    {"cart_id": eid},
                )

            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pid},
            )
            await session.commit()
            return result.rowcount > 0

    async def deleteMany(self, query: Dict) -> Dict:
        docs = await self.findAll(query)
        deleted = 0
        for d in docs:
            if await self.delete(d._id):
                deleted += 1
        return {"deletedCount": deleted}

    async def count(self, query: Optional[Dict] = None) -> int:
        docs = await self.findAll(query)
        return len(docs)
