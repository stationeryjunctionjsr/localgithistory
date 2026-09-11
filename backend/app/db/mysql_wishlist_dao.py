"""
MySQL DAO for sj_wishlists. Fully relational.
"""

import secrets
from typing import Dict
from app.models.wishlist import Wishlist, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc


class MySQLWishlistDAO:
    @property
    def TABLE(self):
        suffix = getattr(settings, "table_suffix", "")
        return f"sj_wishlists{suffix}"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_dict(self, r, items: List[str]) -> Dict:
        return {
            "_id": str(r.id),
            "user": str(r.user_id),
            "items": items,
            "createdAt": r.created_at.isoformat() if r.created_at else None,
            "updatedAt": r.updated_at.isoformat() if r.updated_at else None,
        }

    async def _fetch_items(self, session, ids: List[int]) -> Dict[int, List[str]]:
        c_map = {rid: [] for rid in ids}
        if not ids:
            return c_map
        chunks = [ids[i : i + 999] for i in range(0, len(ids), 999)]
        for chunk in chunks:
            chunk_params = {f"id_{i}": cid for i, cid in enumerate(chunk)}
            placeholders = ", ".join([f":{k}" for k in chunk_params.keys()])
            res = await session.execute(
                text(f"SELECT wishlist_id, product_id FROM sj_wishlist_items WHERE wishlist_id IN ({placeholders})"),
                chunk_params,
            )
            for r in res.fetchall():
                c_map[r.wishlist_id].append(r.product_id)
        return c_map

    async def _replace_items(self, session, wid: int, items: List):
        await session.execute(text("DELETE FROM sj_wishlist_items WHERE wishlist_id = :wid"), {"wid": wid})
        for item in items:
            pid = item.get("product") if isinstance(item, dict) else item
            if pid:
                await session.execute(
                    text("INSERT INTO sj_wishlist_items (wishlist_id, product_id) VALUES (:wid, :pid)"),
                    {"wid": wid, "pid": str(pid)},
                )

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
                text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"), params
            )
            rows = result.fetchall()
            items_map = await self._fetch_items(session, [r.id for r in rows])
        return [Wishlist.model_validate(self._row_to_dict(r, items_map[r.id]) ) for r in rows]

    async def findOne(self, query: Dict) -> Optional[Dict]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        return await self.findOne({"_id": id})

    async def create(self, data: Dict) -> Dict:
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        user_id = int(data.get("user", 0)) if str(data.get("user", "0")).isdigit() else None
        items = data.get("items", [])

        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    INSERT INTO {self.TABLE} (external_id, user_id, created_at, updated_at)
                    VALUES (:external_id, :user_id, :created_at, :updated_at)
                    """
                ),
                {
                    "external_id": external_id,
                    "user_id": user_id,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            await session.commit()

            result = await session.execute(
                text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": external_id}
            )
            new_id = result.scalar()
            await self._replace_items(session, new_id, items)
            await session.commit()

        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: Dict) -> Optional[Dict]:
        existing = await self.findById(id)
        if not existing:
            return None

        factory = self._factory()
        now = now_utc()
        wid = int(id) if str(id).isdigit() else None

        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET updated_at = :u WHERE id = :id"), {"id": wid, "u": now}
            )
            if "items" in update_data:
                await self._replace_items(session, wid, update_data["items"])
            await session.commit()

        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        wid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            await session.execute(text("DELETE FROM sj_wishlist_items WHERE wishlist_id = :wid"), {"wid": wid})
            result = await session.execute(text(f"DELETE FROM {self.TABLE} WHERE id = :id"), {"id": wid})
            await session.commit()
            return result.rowcount > 0

    async def deleteMany(self, query: Dict) -> int:
        factory = self._factory()
        docs = await self.findAll(query)
        if not docs:
            return 0
        wids = [int(d["_id"]) for d in docs if str(d.get("_id", "")).isdigit()]
        if not wids:
            return 0
        async with factory() as session:
            for wid in wids:
                await session.execute(text("DELETE FROM sj_wishlist_items WHERE wishlist_id = :wid"), {"wid": wid})
                await session.execute(text(f"DELETE FROM {self.TABLE} WHERE id = :wid"), {"wid": wid})
            await session.commit()
        return len(wids)
