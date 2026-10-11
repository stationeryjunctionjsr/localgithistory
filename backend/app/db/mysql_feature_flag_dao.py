"""
MySQL DAO for sj_feature_flags. Implements FileStorage-like interface for 'featureFlags'.

This table uses `flag_id` (business key) instead of `external_id`.
We still expose `_id` as numeric PK string for consistency with other DAOs in this codebase.
"""

from typing import List, Optional, Union
from app.models.feature_flag import FeatureFlag

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc


class MySQLFeatureFlagDAO:
    @property
    def TABLE(self):
        return "sj_feature_flags"

    def _factory(self):
        return get_async_session_factory()

    def _map_to_schema(self, r) -> FeatureFlag:
        return FeatureFlag.model_validate(r)

    async def findAll(
        self,
        flag_id: Optional[str] = None,
        name: Optional[str] = None,
        enabled: Optional[bool] = None,
        category: Optional[str] = None,
        id: Optional[Union[int, str]] = None,
    ) -> List[FeatureFlag]:
        factory = self._factory()
        if not factory:
            return []
            
        where_clauses = []
        params = {}
        if id is not None:
            where_clauses.append("id = :id")
            params["id"] = int(id) if str(id).isdigit() else None
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
        
        async with factory() as session:
            result = await session.execute(
                text(f"SELECT id, flag_id, name, description, enabled, category, created_at, updated_at FROM {self.TABLE} WHERE {where_sql}"),
                params
            )
            rows = result.fetchall()
            
        return [self._map_to_schema(r) for r in rows]

    async def findOne(
        self,
        id: Optional[Union[int, str]] = None,
        flag_id: Optional[str] = None,
        name: Optional[str] = None,
        enabled: Optional[bool] = None,
        category: Optional[str] = None,
    ) -> Optional[FeatureFlag]:
        records = await self.findAll(id=id, flag_id=flag_id, name=name, enabled=enabled, category=category)
        return records[0] if records else None

    async def findById(self, id: str) -> Optional[FeatureFlag]:
        return await self.findOne(id=id)

    async def create(self, data: FeatureFlag) -> FeatureFlag:
        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        now = now_utc()
        flag_id = data.flag_id or data.id
        if not flag_id:
            raise ValueError("featureFlags requires `id` (flag_id)")
        async with factory() as session:
            await session.execute(
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
            await session.commit()
            r = await session.execute(
                text(f"SELECT id FROM {self.TABLE} WHERE flag_id = :flag_id"),
                {"flag_id": flag_id},
            )
            new_id = r.scalar()
        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: FeatureFlag) -> Optional[FeatureFlag]:
        existing = await self.findById(id)
        if not existing:
            return None
        
        flag_id = update_data.flag_id if update_data.flag_id is not None else existing.flag_id
        name = update_data.name if update_data.name is not None else existing.name
        description = update_data.description if update_data.description is not None else existing.description
        enabled = update_data.enabled if update_data.enabled is not None else existing.enabled
        category = update_data.category if update_data.category is not None else existing.category

        factory = self._factory()
        if not factory:
            return None
        now = now_utc()
        fid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    UPDATE {self.TABLE} SET
                        flag_id = :flag_id,
                        name = :name,
                        description = :description,
                        enabled = :enabled,
                        category = :category,
                        updated_at = :updated_at
                    WHERE id = :id
                    """
                ),
                {
                    "id": fid,
                    "flag_id": flag_id,
                    "name": name,
                    "description": description,
                    "enabled": 1 if (enabled if enabled is not None else True) else 0,
                    "category": category,
                    "updated_at": now,
                },
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        fid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": fid},
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

