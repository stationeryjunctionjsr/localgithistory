import logging
"""
MySQL DAO for saved-for-later: one row per (user_id, product_id).
Maps to SavedForLater(id: int, user: int, items=[SavedForLaterItem]).
"""

from datetime import datetime, timezone
from typing import List, Optional
from app.models.saved_for_later import SavedForLater, SavedForLaterItem

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc

logger = logging.getLogger(__name__)


class MySQLSavedForLaterDAO:
    @property
    def TABLE(self) -> str:
        return "sj_saved_for_later"

    async def _get_items_for_user(self, user_id: int) -> List[SavedForLaterItem]:
        async_session = get_async_session_factory()
        if not async_session or not user_id:
            return []
        async with async_session() as session:
            result = await session.execute(
                text(f"SELECT product_id, saved_at, created_at FROM {self.TABLE} WHERE user_id = :uid ORDER BY saved_at ASC"),
                {"uid": user_id},
            )
            rows = result.fetchall()
        return [
            SavedForLaterItem(
                user=user_id,
                product=r.product_id,
                product_id=r.product_id,
                created_at=r.created_at or r.saved_at,
                saved_at=r.saved_at,
            )
            for r in rows
        ]

    def _map_to_schema(self, user_id: int, items: List[SavedForLaterItem]) -> SavedForLater:
        return SavedForLater(id=user_id, user=user_id, items=items)

    async def findAll(self, user: Optional[int] = None) -> List[SavedForLater]:
        if user is not None:
            items = await self._get_items_for_user(user)
            return [self._map_to_schema(user, items)]

        async_session = get_async_session_factory()
        if not async_session:
            return []

        async with async_session() as session:
            user_rows = (await session.execute(
                text(f"SELECT DISTINCT user_id FROM {self.TABLE} ORDER BY user_id ASC")
            )).fetchall()
            user_ids = [r.user_id for r in user_rows if r.user_id is not None]

        return [
            self._map_to_schema(uid, await self._get_items_for_user(uid))
            for uid in user_ids
        ]

    async def findOne(self, user: Optional[int] = None, id: Optional[int] = None) -> Optional[SavedForLater]:
        target_uid = user if user is not None else id
        if target_uid is None:
            return None
        items = await self._get_items_for_user(target_uid)
        return self._map_to_schema(target_uid, items)

    async def findById(self, id: int) -> Optional[SavedForLater]:
        return await self.findOne(user=id)

    async def add_item(self, user_id: int, product_id: int) -> bool:
        """Atomically save an item for a user via targeted single-row SQL."""
        if not user_id or not product_id:
            return False
        async_session = get_async_session_factory()
        if not async_session:
            return False
        now = now_utc()
        async with async_session() as session:
            chk = await session.execute(
                text(f"SELECT 1 FROM {self.TABLE} WHERE user_id = :uid AND product_id = :pid LIMIT 1"),
                {"uid": user_id, "pid": product_id},
            )
            if chk.scalar() is not None:
                return True

            await session.execute(
                text(
                    f"""
                    INSERT INTO {self.TABLE} (user_id, product_id, saved_at, created_at, updated_at)
                    VALUES (:user_id, :product_id, :saved_at, :created_at, :updated_at)
                    """
                ),
                {
                    "user_id": user_id,
                    "product_id": product_id,
                    "saved_at": now,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            await session.commit()
            return True

    async def remove_item(self, user_id: int, product_id: int) -> bool:
        """Atomically remove a saved item for a user via targeted single-row DELETE."""
        if not user_id or not product_id:
            return False
        async_session = get_async_session_factory()
        if not async_session:
            return False
        async with async_session() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE user_id = :uid AND product_id = :pid"),
                {"uid": user_id, "pid": product_id},
            )
            await session.commit()
            return result.rowcount > 0

    async def create(self, data: SavedForLater) -> SavedForLater:
        async_session = get_async_session_factory()
        if not async_session:
            raise RuntimeError("MySQL not configured")
        user_id = data.user if data.user is not None else data.id
        items = data.items or []
        if not user_id:
            raise ValueError("user is required")
        now = now_utc()
        async with async_session() as session:
            for item in items:
                pid = item.product if item.product is not None else item.product_id
                if not pid:
                    continue
                saved_at = item.saved_at or item.created_at or now
                created_at = item.created_at or now
                chk = await session.execute(
                    text(f"SELECT 1 FROM {self.TABLE} WHERE user_id = :uid AND product_id = :pid LIMIT 1"),
                    {"uid": user_id, "pid": pid},
                )
                if chk.scalar() is None:
                    await session.execute(
                        text(
                            f"""
                            INSERT INTO {self.TABLE} (user_id, product_id, saved_at, created_at, updated_at)
                            VALUES (:user_id, :product_id, :saved_at, :created_at, :updated_at)
                            """
                        ),
                        {
                            "user_id": user_id,
                            "product_id": pid,
                            "saved_at": saved_at,
                            "created_at": created_at,
                            "updated_at": now,
                        },
                    )
            await session.commit()
        return await self.findOne(user=user_id)

    async def update(self, id: int, update_data: SavedForLater) -> Optional[SavedForLater]:
        """Granular relational update: synchronizes items via set diffing.
        Preserves existing items and their original saved_at timestamps.
        """
        async_session = get_async_session_factory()
        if not async_session or not id:
            return None
        user_id = id
        if update_data.items is None:
            return await self.findOne(user=user_id)

        now = now_utc()
        new_items_list = [
            (item.product if item.product is not None else item.product_id, item)
            for item in update_data.items
            if (item.product is not None or item.product_id is not None)
        ]
        new_pids = {pid for pid, _ in new_items_list}

        async with async_session() as session:
            res = await session.execute(
                text(f"SELECT product_id FROM {self.TABLE} WHERE user_id = :uid"),
                {"uid": user_id},
            )
            existing_pids = {r.product_id for r in res.fetchall() if r.product_id is not None}

            pids_to_delete = existing_pids - new_pids
            pids_to_insert = new_pids - existing_pids

            if pids_to_delete:
                for del_pid in pids_to_delete:
                    await session.execute(
                        text(f"DELETE FROM {self.TABLE} WHERE user_id = :uid AND product_id = :pid"),
                        {"uid": user_id, "pid": del_pid},
                    )

            if pids_to_insert:
                for ins_pid in pids_to_insert:
                    matching_items = [it for pid, it in new_items_list if pid == ins_pid]
                    item_obj = matching_items[0]
                    saved_at = item_obj.saved_at or item_obj.created_at or now
                    created_at = item_obj.created_at or now
                    await session.execute(
                        text(
                            f"""
                            INSERT INTO {self.TABLE} (user_id, product_id, saved_at, created_at, updated_at)
                            VALUES (:user_id, :product_id, :saved_at, :created_at, :updated_at)
                            """
                        ),
                        {
                            "user_id": user_id,
                            "product_id": ins_pid,
                            "saved_at": saved_at,
                            "created_at": created_at,
                            "updated_at": now,
                        },
                    )

            await session.commit()

        return await self.findOne(user=user_id)

    async def delete(self, id: int) -> bool:
        async_session = get_async_session_factory()
        if not async_session or not id:
            return False
        async with async_session() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE user_id = :uid"),
                {"uid": id},
            )
            await session.commit()
            return result.rowcount > 0

    async def count(self, user: Optional[int] = None) -> int:
        async_session = get_async_session_factory()
        if not async_session:
            return 0
        async with async_session() as session:
            if user is not None:
                result = await session.execute(
                    text(f"SELECT COUNT(DISTINCT user_id) FROM {self.TABLE} WHERE user_id = :uid"),
                    {"uid": user},
                )
            else:
                result = await session.execute(text(f"SELECT COUNT(DISTINCT user_id) FROM {self.TABLE}"))
            return int(result.scalar() or 0)

    find_all = findAll
    find_by_id = findById
    find_one = findOne
