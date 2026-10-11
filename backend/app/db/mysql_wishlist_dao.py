"""
MySQL DAO for sj_wishlists. Fully relational.
"""

import secrets
from typing import List, Optional, Union
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
        id: Optional[Union[int, str]] = None,
        user: Optional[Union[int, str]] = None,
        external_id: Optional[str] = None,
    ) -> List[Wishlist]:
        factory = self._factory()
        if not factory:
            return []

        where_clauses = []
        params = {}
        if id is not None:
            where_clauses.append("id = :id")
            params["id"] = int(id) if str(id).isdigit() else None
        if user is not None:
            where_clauses.append("user_id = :user_id")
            params["user_id"] = int(user) if str(user).isdigit() else None
        if external_id is not None:
            where_clauses.append("external_id = :external_id")
            params["external_id"] = str(external_id)

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
        id: Optional[Union[int, str]] = None,
        user: Optional[Union[int, str]] = None,
        external_id: Optional[str] = None,
    ) -> Optional[Wishlist]:
        docs = await self.findAll(id=id, user=user, external_id=external_id)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Wishlist]:
        return await self.findOne(id=id)

    async def create(self, data: 'WishlistInternalCreate') -> Optional[Wishlist]:
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        user_id = int((data.user if data.user is not None else 0)) if str((data.user if data.user is not None else "0")).isdigit() else None
        items = (data.items if data.items is not None else [])

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

    async def update(self, id: str, update_data: 'WishlistInternalUpdate') -> Optional[Wishlist]:
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
            if update_data.items is not None:
                await self._replace_items(session, wid, update_data.items)
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

    async def deleteMany(self, user: Optional[Union[int, str]] = None) -> int:
        factory = self._factory()
        docs = await self.findAll(user=user)
        if not docs:
            return 0
        wids = [int(d.id) for d in docs if str(d.id or "").isdigit()]
        if not wids:
            return 0
        async with factory() as session:
            for wid in wids:
                await session.execute(text("DELETE FROM sj_wishlist_items WHERE wishlist_id = :wid"), {"wid": wid})
                await session.execute(text(f"DELETE FROM {self.TABLE} WHERE id = :wid"), {"wid": wid})
            await session.commit()
        return len(wids)


