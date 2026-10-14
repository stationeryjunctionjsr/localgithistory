import logging
"""
MySQL DAO for saved-for-later: one row per (user_id, product_id).
Maps to SavedForLater(id, user, items=[SavedForLaterItem]).
"""

from datetime import datetime
from typing import List, Optional, Union
from app.models.saved_for_later import SavedForLater, SavedForLaterItem

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc


class MySQLSavedForLaterDAO:
    @property
    def TABLE(self) -> str:
        return "sj_saved_for_later"

    async def _get_items_for_user(self, user_id: str) -> List[SavedForLaterItem]:
        async_session = get_async_session_factory()
        if not async_session:
            return []
        async with async_session() as session:
            result = await session.execute(
                text(f"SELECT product_id, saved_at FROM {self.TABLE} WHERE user_id = :uid ORDER BY saved_at"),
                {"uid": user_id},
            )
            rows = result.fetchall()
        return [
            SavedForLaterItem(
                product=str(r.product_id),
                product_id=str(r.product_id),
                created_at=r.saved_at,
                saved_at=r.saved_at,
            )
            for r in rows
        ]

    def _map_to_schema(self, user_id: str, items: List[SavedForLaterItem]) -> SavedForLater:
        return SavedForLater(id=user_id, user=user_id, items=items)

    async def findAll(self, user: Optional[str] = None) -> List[SavedForLater]:
        async_session = get_async_session_factory()
        if not async_session:
            return []

        if user:
            items = await self._get_items_for_user(str(user))
            return [self._map_to_schema(str(user), items)]

        async with async_session() as session:
            result = await session.execute(
                text(f"SELECT user_id, product_id, saved_at FROM {self.TABLE} ORDER BY user_id, saved_at")
            )
            rows = result.fetchall()

        user_items = {}
        for r in rows:
            uid = str(r.user_id)
            if uid not in user_items:
                user_items[uid] = []
            user_items[uid].append(
                SavedForLaterItem(
                    product=str(r.product_id),
                    product_id=str(r.product_id),
                    created_at=r.saved_at,
                    saved_at=r.saved_at,
                )
            )
        return [self._map_to_schema(uid, items) for uid, items in user_items.items()]

    async def findOne(self, user: Optional[str] = None, id: Optional[str] = None) -> Optional[SavedForLater]:
        target_uid = user or id
        if not target_uid:
            return None
        items = await self._get_items_for_user(str(target_uid))
        return self._map_to_schema(str(target_uid), items)

    async def findById(self, id: str) -> Optional[SavedForLater]:
        return await self.findOne(user=id)

    async def create(self, data: SavedForLater) -> SavedForLater:
        async_session = get_async_session_factory()
        if not async_session:
            raise RuntimeError("MySQL not configured")
        user_id = str((data.user if data.user is not None else ""))
        items = data.items or []
        if not user_id:
            raise ValueError("user is required")
        now = now_utc()
        async with async_session() as session:
            for item in items:
                product_id = item.product
                if not product_id:
                    continue
                saved_at = item.created_at or now
                await session.execute(
                    text(
                        f"""
                        INSERT INTO {self.TABLE} (user_id, product_id, saved_at, created_at, updated_at)
                        VALUES (:user_id, :product_id, :saved_at, :created_at, :updated_at)
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
        return await self.findOne(user=user_id)

    async def update(self, id: str, update_data: SavedForLater) -> Optional[SavedForLater]:
        async_session = get_async_session_factory()
        if not async_session:
            return None
        user_id = str(id)
        items = update_data.items
        if items is None:
            return await self.findOne(user=user_id)
        now = now_utc()
        async with async_session() as session:
            await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE user_id = :uid"),
                {"uid": user_id},
            )
            for item in items:
                product_id = item.product or item.product_id
                if not product_id:
                    continue
                saved_at = item.created_at or item.saved_at or now
                await session.execute(
                    text(
                        f"""
                        INSERT INTO {self.TABLE} (user_id, product_id, saved_at, created_at, updated_at)
                        VALUES (:user_id, :product_id, :saved_at, :created_at, :updated_at)
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
        return await self.findOne(user=user_id)

    async def delete(self, id: str) -> bool:
        async_session = get_async_session_factory()
        if not async_session:
            return False
        async with async_session() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE user_id = :uid"),
                {"uid": str(id)},
            )
            await session.commit()
            return result.rowcount > 0

    async def count(self, user: Optional[str] = None) -> int:
        async_session = get_async_session_factory()
        if not async_session:
            return 0
        async with async_session() as session:
            if user:
                result = await session.execute(
                    text(f"SELECT COUNT(DISTINCT user_id) FROM {self.TABLE} WHERE user_id = :uid"),
                    {"uid": str(user)},
                )
            else:
                result = await session.execute(text(f"SELECT COUNT(DISTINCT user_id) FROM {self.TABLE}"))
            return int(result.scalar() or 0)
