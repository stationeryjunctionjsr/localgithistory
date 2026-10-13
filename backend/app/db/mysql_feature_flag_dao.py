"""
MySQL DAO for sj_feature_flags. Implements FileStorage-like interface for 'featureFlags'.

This table uses `flag_id` (business key).
We still expose `_id` as numeric PK string for consistency with other DAOs in this codebase.
"""

from typing import List, Optional
from app.models.feature_flag import FeatureFlag, FeatureFlagUpdate

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc


class MySQLFeatureFlagDAO:
    @property
    def TABLE(self):
        return "sj_feature_flags"

    def _map_to_schema(self, r) -> FeatureFlag:
        return FeatureFlag.model_validate(r)

    async def findAll(
        self,
        flag_id: Optional[str] = None,
        name: Optional[str] = None,
        enabled: Optional[bool] = None,
        category: Optional[str] = None,
        id: Optional[int] = None,
    ) -> List[FeatureFlag]:
        async_session = get_async_session_factory()
            
        where_clauses = []
        params = {}
        if id is not None:
            where_clauses.append("id = :id")
            params["id"] = id
        if flag_id is not None:
            where_clauses.append("flag_id = :flag_id")
            params["flag_id"] = flag_id
        if name is not None:
            where_clauses.append("name = :name")
            params["name"] = name
        if enabled is not None:
            where_clauses.append("enabled = :enabled")
            params["enabled"] = 1 if enabled else 0
        if category is not None:
            where_clauses.append("category = :category")
            params["category"] = category

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        async with async_session() as session:
            result = await session.execute(
                text(f"SELECT id, flag_id, name, description, enabled, category, created_at, updated_at FROM {self.TABLE} WHERE {where_sql}"),
                params
            )
            rows = result.fetchall()
            
        return [self._map_to_schema(r) for r in rows]

    async def findOne(
        self,
        id: Optional[int] = None,
        flag_id: Optional[str] = None,
        name: Optional[str] = None,
        enabled: Optional[bool] = None,
        category: Optional[str] = None,
    ) -> Optional[FeatureFlag]:
        records = await self.findAll(id=id, flag_id=flag_id, name=name, enabled=enabled, category=category)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[FeatureFlag]:
        return await self.findOne(id=id)

    async def create(self, data: FeatureFlag) -> FeatureFlag:
        async_session = get_async_session_factory()
        now = now_utc()
        flag_id = data.flag_id or data.id
        if not flag_id:
            raise ValueError("featureFlags requires `id` (flag_id)")
        async with async_session() as session:
            result = await session.execute(
                text(
                    f"""
                    INSERT INTO {self.TABLE} (flag_id, name, description, enabled, category, created_at, updated_at)
                    VALUES (:flag_id, :name, :description, :enabled, :category, :created_at, :updated_at)
                    """
                ),
                {
                    "flag_id": flag_id,
                    "name": data.name,
                    "description": data.description,
                    "enabled": 1 if (data.enabled if data.enabled is not None else True) else 0,
                    "category": data.category,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            new_id = result.lastrowid
            await session.commit()
        return await self.findById(new_id)

    async def update(self, id: int, update_data: FeatureFlagUpdate) -> Optional[FeatureFlag]:
        if not id:
            return None
        async_session = get_async_session_factory()
        now = now_utc()
        updates = ["updated_at = :updated_at"]
        params = {"id": id, "updated_at": now}

        if "flag_id" in update_data.model_fields_set:
            updates.append("flag_id = :flag_id")
            params["flag_id"] = update_data.flag_id

        if "name" in update_data.model_fields_set:
            updates.append("name = :name")
            params["name"] = update_data.name

        if "description" in update_data.model_fields_set:
            updates.append("description = :description")
            params["description"] = update_data.description

        if "enabled" in update_data.model_fields_set:
            updates.append("enabled = :enabled")
            params["enabled"] = 1 if update_data.enabled else 0

        if "category" in update_data.model_fields_set:
            updates.append("category = :category")
            params["category"] = update_data.category

        set_sql = ", ".join(updates)

        async with async_session() as session:
            result = await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
            if result.rowcount == 0:
                existing = await self.findById(id)
                if not existing:
                    return None
        return await self.findById(id)

    async def delete(self, id: int) -> bool:
        if not id:
            return False
        async_session = get_async_session_factory()
        async with async_session() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": id},
            )
            await session.commit()
            return result.rowcount > 0

    async def count(
        self,
        enabled: Optional[bool] = None,
        category: Optional[str] = None,
    ) -> int:
        records = await self.findAll(enabled=enabled, category=category)
        return len(records)

    find_all = findAll
    find_by_id = findById
    find_one = findOne

