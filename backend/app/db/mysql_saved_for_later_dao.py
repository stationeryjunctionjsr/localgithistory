"""
MySQL DAO for saved-for-later: one row per (user_id, product_id).
Exposes virtual doc per user: { _id: user_id, user: user_id, items: [ { productId, savedAt }, ... ] }.
"""

import secrets
from datetime import datetime
from typing import Dict
from app.models.saved_for_later import SavedForLater, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc


def _to_ts(val):
    if val is None:
        return None
    if hasattr(val, "isoformat"):
        return val
    try:
        return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
    except Exception:
        return None


class MySQLSavedForLaterDAO:
    @property
    def TABLE(self) -> str:
        suffix = getattr(settings, "table_suffix", "")
        return f"sj_saved_for_later{suffix}"

    def _factory(self):
        return get_async_session_factory()

    async def _get_items_for_user(self, user_id: str) -> List[Dict]:
        factory = self._factory()
        if not factory:
            return []
        async with factory() as session:
            result = await session.execute(
                text(f"SELECT product_id, saved_at FROM {self.TABLE} WHERE user_id = :uid ORDER BY saved_at"),
                {"uid": user_id},
            )
            rows = result.fetchall()
        return [
            {
                "productId": r[0],
                "savedAt": r[1].isoformat() if hasattr(r[1], "isoformat") and r[1] else None,
            }
            for r in rows
        ]

    def _doc(self, user_id: str, items: List[Dict]) -> Any:
        return SavedForLater.model_validate({
            "_id": user_id, "user": user_id, "items": items})

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        factory = self._factory()
        if not factory:
            return []

        user_id = query.get("user") if query else None
        if user_id:
            items = await self._get_items_for_user(str(user_id))
            return [self._doc(str(user_id), items)]

        async with factory() as session:
            result = await session.execute(text(f"SELECT DISTINCT user_id FROM {self.TABLE}"))
            user_ids = [r[0] for r in result.fetchall()]
        docs = []
        for uid in user_ids:
            items = await self._get_items_for_user(uid)
            docs.append(self._doc(uid, items))
        return docs

    async def findOne(self, query: Dict) -> Optional[Dict]:
        user_id = query.get("user")
        if not user_id:
            return None
        items = await self._get_items_for_user(str(user_id))
        return self._doc(str(user_id), items)

    async def findById(self, id: str) -> Optional[Dict]:
        return await self.findOne({"user": id})

    async def create(self, data: Dict) -> Dict:
        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        user_id = str((data.user if getattr(data, 'user', None) is not None else ""))
        items = data.items or []
        if not user_id:
            raise ValueError("user is required")
        now = now_utc()
        async with factory() as session:
            for item in items:
                product_id = item.productId or item.product_id
                if not product_id:
                    continue
                saved_at = _to_ts(item.savedAt or item.saved_at) or now
                await session.execute(
                    text(
                        f"""
                        INSERT INTO {self.TABLE} (external_id, user_id, product_id, saved_at, created_at, updated_at)
                        VALUES (UUID(), :user_id, :product_id, :saved_at, :created_at, :updated_at)
                        """
                    ),
                    {
                        "user_id": user_id,
                        "product_id": str(product_id),
                        "saved_at": saved_at,
                        "created_at": now,
                        "updated_at": now,
                    },
                )
            await session.commit()
        return await self.findOne({"user": user_id})

    async def update(self, id: str, update_data: Dict) -> Optional[Dict]:
        factory = self._factory()
        if not factory:
            return None
        user_id = str(id)
        items = update_data.items
        if items is None:
            return await self.findOne({"user": user_id})
        now = now_utc()
        async with factory() as session:
            await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE user_id = :uid"),
                {"uid": user_id},
            )
            await session.commit()
            for item in items:
                product_id = item.productId or item.product_id
                if not product_id:
                    continue
                saved_at = _to_ts(item.savedAt or item.saved_at) or now
                await session.execute(
                    text(
                        f"""
                        INSERT INTO {self.TABLE} (external_id, user_id, product_id, saved_at, created_at, updated_at)
                        VALUES (:external_id, :user_id, :product_id, :saved_at, :created_at, :updated_at)
                        """
                    ),
                    {
                        "external_id": secrets.token_hex(16),
                        "user_id": user_id,
                        "product_id": str(product_id),
                        "saved_at": saved_at,
                        "created_at": now,
                        "updated_at": now,
                    },
                )
            await session.commit()
        return await self.findOne({"user": user_id})

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE user_id = :uid"),
                {"uid": str(id)},
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
        return len(await self.findAll(query))

    find_all = findAll
    find_by_id = findById
    find_one = findOne
