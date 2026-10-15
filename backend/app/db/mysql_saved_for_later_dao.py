import logging
"""
MySQL DAO for saved-for-later: one row per (user_id, product_id).
Maps to SavedForLater(id, user, items=[SavedForLaterItem]).
"""

from datetime import datetime, timezone
from typing import List, Optional, Union, Set
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

    async def _get_items_for_user(self, user_id: Union[int, str]) -> List[SavedForLaterItem]:
        async_session = get_async_session_factory()
        if not async_session:
            return []
        uid_str = str(user_id)
        async with async_session() as session:
            result = await session.execute(
                text(f"SELECT product_id, saved_at, created_at FROM {self.TABLE} WHERE user_id = :uid ORDER BY saved_at ASC"),
                {"uid": uid_str},
            )
            rows = result.fetchall()
        return [
            SavedForLaterItem(
                user=uid_str,
                product=str(r.product_id),
                product_id=str(r.product_id),
                created_at=r.created_at or r.saved_at,
                saved_at=r.saved_at,
            )
            for r in rows
        ]

    def _map_to_schema(self, user_id: Union[int, str], items: List[SavedForLaterItem]) -> SavedForLater:
        uid_str = str(user_id)
        return SavedForLater(id=uid_str, user=uid_str, items=items)

    async def findAll(self, user: Optional[Union[int, str]] = None) -> List[SavedForLater]:
        if user is not None:
            items = await self._get_items_for_user(user)
            return [self._map_to_schema(user, items)]

        async_session = get_async_session_factory()
        if not async_session:
            return []

        async with async_session() as session:
            result = await session.execute(
                text(f"SELECT user_id, product_id, saved_at, created_at FROM {self.TABLE} ORDER BY user_id, saved_at ASC")
            )
            rows = result.fetchall()

        user_items: dict[str, list[SavedForLaterItem]] = {}
        for r in rows:
            uid = str(r.user_id)
            if uid not in user_items:
                user_items[uid] = []
            user_items[uid].append(
                SavedForLaterItem(
                    user=uid,
                    product=str(r.product_id),
                    product_id=str(r.product_id),
                    created_at=r.created_at or r.saved_at,
                    saved_at=r.saved_at,
                )
            )
        return [self._map_to_schema(uid, items) for uid, items in user_items.items()]

    async def findOne(self, user: Optional[Union[int, str]] = None, id: Optional[Union[int, str]] = None) -> Optional[SavedForLater]:
        target_uid = user if user is not None else id
        if target_uid is None:
            return None
        items = await self._get_items_for_user(target_uid)
        return self._map_to_schema(target_uid, items)

    async def findById(self, id: Union[int, str]) -> Optional[SavedForLater]:
        return await self.findOne(user=id)

    async def add_item(self, user_id: Union[int, str], product_id: Union[int, str]) -> bool:
        """Atomically save an item for a user via targeted single-row SQL."""
        if not user_id or not product_id:
            return False
        async_session = get_async_session_factory()
        if not async_session:
            return False
        uid_str = str(user_id)
        pid_str = str(product_id)
        now = now_utc()
        async with async_session() as session:
            chk = await session.execute(
                text(f"SELECT 1 FROM {self.TABLE} WHERE user_id = :uid AND product_id = :pid LIMIT 1"),
                {"uid": uid_str, "pid": pid_str},
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
                    "user_id": uid_str,
                    "product_id": pid_str,
                    "saved_at": now,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            await session.commit()
            return True

    async def remove_item(self, user_id: Union[int, str], product_id: Union[int, str]) -> bool:
        """Atomically remove a saved item for a user via targeted single-row DELETE."""
        if not user_id or not product_id:
            return False
        async_session = get_async_session_factory()
        if not async_session:
            return False
        async with async_session() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE user_id = :uid AND product_id = :pid"),
                {"uid": str(user_id), "pid": str(product_id)},
            )
            await session.commit()
            return result.rowcount > 0

    async def create(self, data: SavedForLater) -> SavedForLater:
        async_session = get_async_session_factory()
        if not async_session:
            raise RuntimeError("MySQL not configured")
        user_id = str(data.user or data.id or "")
        items = data.items or []
        if not user_id:
            raise ValueError("user is required")
        now = now_utc()
        async with async_session() as session:
            for item in items:
                product_id = str(item.product or item.product_id or "").strip()
                if not product_id:
                    continue
                saved_at = item.saved_at or item.created_at or now
                created_at = item.created_at or now
                chk = await session.execute(
                    text(f"SELECT 1 FROM {self.TABLE} WHERE user_id = :uid AND product_id = :pid LIMIT 1"),
                    {"uid": user_id, "pid": product_id},
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
                            "product_id": product_id,
                            "saved_at": saved_at,
                            "created_at": created_at,
                            "updated_at": now,
                        },
                    )
            await session.commit()
        return await self.findOne(user=user_id)

    async def update(self, id: Union[int, str], update_data: SavedForLater) -> Optional[SavedForLater]:
        """Granular relational update: synchronizes items via diffing rather than full table deletion.
        Preserves existing items and their original saved_at timestamps.
        """
        async_session = get_async_session_factory()
        if not async_session or id is None:
            return None
        user_id = str(id)
        if update_data.items is None:
            return await self.findOne(user=user_id)

        now = now_utc()
        new_items_map = {}
        for item in update_data.items:
            pid = str(item.product or item.product_id or "").strip()
            if pid:
                new_items_map[pid] = item

        async with async_session() as session:
            res = await session.execute(
                text(f"SELECT product_id FROM {self.TABLE} WHERE user_id = :uid"),
                {"uid": user_id},
            )
            existing_pids = {str(r.product_id) for r in res.fetchall() if r.product_id}
            new_pids = set(new_items_map.keys())

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
                    item_obj = new_items_map[ins_pid]
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

    async def delete(self, id: Union[int, str]) -> bool:
        async_session = get_async_session_factory()
        if not async_session or id is None:
            return False
        async with async_session() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE user_id = :uid"),
                {"uid": str(id)},
            )
            await session.commit()
            return result.rowcount > 0

    async def count(self, user: Optional[Union[int, str]] = None) -> int:
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

    find_all = findAll
    find_by_id = findById
    find_one = findOne
