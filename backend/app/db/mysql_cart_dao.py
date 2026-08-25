"""
MySQL DAO for sj_carts (+ sj_cart_items).
"""

import secrets
from typing import Dict, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.oracle_utils import now_utc


class MySQLCartDAO:
    @property
    def TABLE(self):
        suffix = getattr(settings, "table_suffix", "")
        return f"sj_carts{suffix}"

    @property
    def ITEMS_TABLE(self):
        suffix = getattr(settings, "table_suffix", "")
        return f"sj_cart_items{suffix}"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_doc(self, r, items: List[Dict]) -> Dict:
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
                    params["id"] = int(v) if str(v).isdigit() else 0
                elif k in ("user", "user_id"):
                    where_clauses.append("user_id = :user_id")
                    params["user_id"] = int(v) if str(v).isdigit() else 0
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
                        SELECT cart_id, product_id, quantity, sell_as_case
                        FROM {self.ITEMS_TABLE}
                        WHERE cart_id IN ({placeholders})
                        ORDER BY id ASC
                        """
                    ),
                    chunk_params,
                )
                for ir in items_result.fetchall():
                    items_map[ir.cart_id].append(
                        {
                            "product": str(ir.product_id),
                            "quantity": int(ir.quantity),
                            "sellAsCase": bool(ir.sell_as_case),
                        }
                    )

        return [self._row_to_doc(r, items_map[r.external_id]) for r in rows]

    async def findOne(self, query: Dict) -> Optional[Dict]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        return await self.findOne({"_id": id})

    async def _replace_items(self, session, cart_external_id: str, items: List[Dict]) -> None:
        await session.execute(
            text(f"DELETE FROM {self.ITEMS_TABLE} WHERE cart_id = :cart_id"),
            {"cart_id": cart_external_id},
        )
        for it in items or []:
            pid_raw = it.get("product")
            if not pid_raw:
                continue
            qty = it.get("quantity", 0) or 0
            sell_as_case = 1 if it.get("sellAsCase") else 0

            await session.execute(
                text(
                    f"""
                    INSERT INTO {self.ITEMS_TABLE} (cart_id, product_id, quantity, sell_as_case)
                    VALUES (:cart_id, :product_id, :quantity, :sell_as_case)
                    """
                ),
                {
                    "cart_id": cart_external_id,
                    "product_id": str(pid_raw),
                    "quantity": qty,
                    "sell_as_case": sell_as_case,
                },
            )

    async def create(self, data: Dict) -> Dict:
        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        now = now_utc()
        external_id = secrets.token_hex(16)

        user_id_raw = data.get("user")
        uid = int(user_id_raw) if user_id_raw and str(user_id_raw).isdigit() else 0

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

            await self._replace_items(session, external_id, data.get("items") or [])
            await session.commit()

        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: Dict) -> Optional[Dict]:
        existing = await self.findById(id)
        if not existing:
            return None

        factory = self._factory()
        if not factory:
            return None
        now = now_utc()
        pid = int(id) if str(id).isdigit() else 0

        # We only really update items for carts
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET updated_at = :updated_at WHERE id = :id"),
                {"id": pid, "updated_at": now},
            )

            # Fetch external_id
            r = await session.execute(text(f"SELECT external_id FROM {self.TABLE} WHERE id = :id"), {"id": pid})
            eid = r.scalar()

            if "items" in update_data:
                await self._replace_items(session, eid, update_data.get("items") or [])

            await session.commit()

        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        pid = int(id) if str(id).isdigit() else 0
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
            if await self.delete(d.get("_id")):
                deleted += 1
        return {"deletedCount": deleted}

    async def count(self, query: Optional[Dict] = None) -> int:
        docs = await self.findAll(query)
        return len(docs)
