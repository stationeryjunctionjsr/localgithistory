"""
MySQL DAO for sj_wishlists. Fully relational.
"""

from typing import List, Optional
from app.models.daos import WishlistInternalCreate, WishlistInternalUpdate, WishlistItemInternal
from app.models.wishlist import Wishlist

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc


class MySQLWishlistDAO:
    @property
    def TABLE(self):
        return "sj_wishlists"

    def _factory(self):
        return get_async_session_factory()

    def _map_to_schema(self, r, items_rows=None) -> Wishlist:
        w = Wishlist.model_validate(r)
        w.user = str(r.user_id) if r.user_id is not None else None
        if items_rows:
            w.items = [
                WishlistItemInternal(product=str(ir.product_id))
                for ir in items_rows
                if ir.wishlist_id == r.id
            ]
        else:
            w.items = []
        return w

    async def _fetch_items(self, session, ids: List[int]):
        if not ids:
            return []
        items_rows = []
        chunks = [ids[i : i + 999] for i in range(0, len(ids), 999)]
        for chunk in chunks:
            chunk_params = {f"id_{i}": cid for i, cid in enumerate(chunk)}
            placeholders = ", ".join([f":{k}" for k in chunk_params.keys()])
            res = await session.execute(
                text(f"SELECT wishlist_id, product_id FROM sj_wishlist_items WHERE wishlist_id IN ({placeholders})"),
                chunk_params,
            )
            items_rows.extend(res.fetchall())
        return items_rows

    async def _replace_items(self, session, wid: int, items: List[WishlistItemInternal]):
        await session.execute(text("DELETE FROM sj_wishlist_items WHERE wishlist_id = :wid"), {"wid": wid})
        for item in items:
            if not item.product:
                continue
            await session.execute(
                text("INSERT INTO sj_wishlist_items (wishlist_id, product_id) VALUES (:wid, :pid)"),
                {"wid": wid, "pid": str(item.product)},
            )

    async def findAll(
        self,
        id: Optional[int] = None,
        user: Optional[str] = None,
    ) -> List[Wishlist]:
        factory = self._factory()
        if not factory:
            return []

        where_clauses = []
        params = {}
        if id is not None:
            where_clauses.append("id = :id")
            params["id"] = id
        if user is not None:
            where_clauses.append("user_id = :user_id")
            params["user_id"] = int(user) if str(user).isdigit() else None

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        async with factory() as session:
            result = await session.execute(
                text(f"SELECT * FROM {self.TABLE} {where_sql} ORDER BY id ASC"), params
            )
            rows = result.fetchall()
            items_rows = await self._fetch_items(session, [r.id for r in rows])
        return [self._map_to_schema(r, items_rows) for r in rows]

    async def findOne(
        self,
        id: Optional[int] = None,
        user: Optional[str] = None,
    ) -> Optional[Wishlist]:
        records = await self.findAll(id=id, user=user)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[Wishlist]:
        return await self.findOne(id=id)

    async def create(self, data: 'WishlistInternalCreate') -> Optional[Wishlist]:
        factory = self._factory()
        now = now_utc()
        user_id = int((data.user if data.user is not None else 0)) if str((data.user if data.user is not None else "0")).isdigit() else None
        items = (data.items if data.items is not None else [])

        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    INSERT INTO {self.TABLE} (user_id, created_at, updated_at)
                    VALUES (:user_id, :created_at, :updated_at)
                    """
                ),
                {
                    "user_id": user_id,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            new_id = result.lastrowid
            await self._replace_items(session, new_id, items)
            await session.commit()

        return await self.findById(new_id)

    async def update(self, id: int, update_data: 'WishlistInternalUpdate') -> Optional[Wishlist]:
        if not id:
            return None
        existing = await self.findById(id)
        if not existing:
            return None

        factory = self._factory()
        now = now_utc()

        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET updated_at = :u WHERE id = :id"), {"id": id, "u": now}
            )
            if update_data.items is not None:
                await self._replace_items(session, id, update_data.items)
            await session.commit()

        return await self.findById(id)

    async def delete(self, id: int) -> bool:
        factory = self._factory()
        if not factory or not id:
            return False
        async with factory() as session:
            await session.execute(text("DELETE FROM sj_wishlist_items WHERE wishlist_id = :wid"), {"wid": id})
            result = await session.execute(text(f"DELETE FROM {self.TABLE} WHERE id = :id"), {"id": id})
            await session.commit()
            return result.rowcount > 0

    async def deleteMany(self, user: Optional[str] = None) -> int:
        factory = self._factory()
        if not factory:
            return 0
        where_clauses = []
        params = {}
        if user is not None:
            where_clauses.append("user_id = :user_id")
            params["user_id"] = int(user) if str(user).isdigit() else None
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        async with factory() as session:
            await session.execute(
                text(f"DELETE FROM sj_wishlist_items WHERE wishlist_id IN (SELECT id FROM {self.TABLE} WHERE {where_sql})"),
                params,
            )
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE {where_sql}"),
                params,
            )
            await session.commit()
            return result.rowcount or 0


