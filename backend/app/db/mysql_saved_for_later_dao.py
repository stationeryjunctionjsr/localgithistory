import logging
"""
MySQL DAO for saved-for-later: one row per (user_id, product_id).
Maps to SavedForLater(id, user, items=[SavedForLaterItem]).
"""

import secrets
from datetime import datetime
from typing import List, Optional, Union
from app.models.saved_for_later import SavedForLater, SavedForLaterItem

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc


def _to_ts(val):
    if val is None:
        return None
    if not isinstance(val, str):
        return val
    try:
        return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
    except Exception as e:
        logging.warning("mysql_saved_for_later_dao._to_ts: could not parse timestamp %r: %s", val, e, exc_info=e)
        return None


class MySQLSavedForLaterDAO:
    @property
    def TABLE(self) -> str:
        return "sj_saved_for_later"

    def _factory(self):
        return get_async_session_factory()

    async def _get_items_for_user(self, user_id: str) -> List[SavedForLaterItem]:
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
            SavedForLaterItem(
                product=str(r[0]),
                product_id=str(r[0]),
                created_at=r[1],
                saved_at=r[1],
            )
            for r in rows
        ]

    def _map_to_schema(self, user_id: str, items: List[SavedForLaterItem]) -> SavedForLater:
        return SavedForLater(id=user_id, user=user_id, items=items)

    async def findAll(self, user: Optional[str] = None) -> List[SavedForLater]:
        factory = self._factory()
        if not factory:
            return []

        if user:
            items = await self._get_items_for_user(str(user))
            return [self._map_to_schema(str(user), items)]

        async with factory() as session:
            result = await session.execute(
                text(f"SELECT user_id, product_id, saved_at FROM {self.TABLE} ORDER BY user_id, saved_at")
            )
            rows = result.fetchall()

        user_items: dict[str, list[SavedForLaterItem]] = {}
        for r in rows:
            uid = str(r[0])
            if uid not in user_items:
                user_items[uid] = []
            user_items[uid].append(
                SavedForLaterItem(
                    product=str(r[1]),
                    product_id=str(r[1]),
                    created_at=r[2],
                    saved_at=r[2],
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
        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        user_id = str((data.user if data.user is not None else ""))
        items = data.items or []
        if not user_id:
            raise ValueError("user is required")
        now = now_utc()
        async with factory() as session:
            for item in items:
                product_id = item.product
                if not product_id:
                    continue
                saved_at = _to_ts(item.created_at) or now
                await session.execute(
                    text(
                        f"""
                        INSERT INTO {self.TABLE} (external_id, user_id, product_id, saved_at, created_at, updated_at)
                        VALUES (REPLACE(UUID(), '-', ''), :user_id, :product_id, :saved_at, :created_at, :updated_at)
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
        factory = self._factory()
        if not factory:
            return None
        user_id = str(id)
        items = update_data.items
        if items is None:
            return await self.findOne(user=user_id)
        now = now_utc()
        async with factory() as session:
            await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE user_id = :uid"),
                {"uid": user_id},
            )
            await session.commit()
            for item in items:
                product_id = item.product or item.product_id
                if not product_id:
                    continue
                saved_at = _to_ts(item.created_at or item.saved_at) or now
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
        return await self.findOne(user=user_id)

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

    async def count(self, user: Optional[str] = None) -> int:
        factory = self._factory()
        if not factory:
            return 0
        async with factory() as session:
            if user:
                result = await session.execute(
                    text(f"SELECT COUNT(DISTINCT user_id) FROM {self.TABLE} WHERE user_id = :uid"),
                    {"uid": str(user)},
                )
            else:
                result = await session.execute(text(f"SELECT COUNT(DISTINCT user_id) FROM {self.TABLE}"))
            return int(result.scalar() or 0)
