"""
MySQL DAO for sj_feature_flags. Implements FileStorage-like interface for 'featureFlags'.

This table uses `flag_id` (business key) instead of `external_id`.
We still expose `_id` as numeric PK string for consistency with other DAOs in this codebase.
"""

from typing import Dict
from app.models.feature_flag import FeatureFlag, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc


class MySQLFeatureFlagDAO:
    @property
    def TABLE(self):
        suffix = (settings.table_suffix if settings.table_suffix is not None else "")
        return f"sj_feature_flags{suffix}"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_dict(self, r) -> Dict:
        return {
            "_id": str(r.id),
            "id": r.flag_id,
            "name": r.name,
            "description": r.description,
            "enabled": bool(r.enabled) if r.enabled is not None else True,
            "category": r.category,
            "createdAt": r.created_at.isoformat() if r.created_at else None,
            "updatedAt": r.updated_at.isoformat() if r.updated_at else None,
        }

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        factory = self._factory()
        if not factory:
            return []
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id, flag_id, name, description, enabled, category, created_at, updated_at
                    FROM {self.TABLE}
                    """
                )
            )
            rows = result.fetchall()
        docs = [self._row_to_dict(r) for r in rows]
        if not query:
            return docs
        filtered: List[Dict] = []
        for d in docs:
            match = True
            for k, v in query.items():
                if k in ("_id",):
                    if str(d._id) != str(v):
                        match = False
                        break
                elif d.get(k) != v:
                    match = False
                    break
            if match:
                filtered.append(d)
        return filtered

    async def findOne(self, query: Dict) -> Optional[Dict]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        factory = self._factory()
        if not factory:
            return None
        fid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id, flag_id, name, description, enabled, category, created_at, updated_at
                    FROM {self.TABLE} WHERE id = :id
                    """
                ),
                {"id": fid},
            )
            row = result.fetchone()
        return FeatureFlag.model_validate(self._row_to_dict(row)) if row else None

    async def create(self, data: Dict) -> Dict:
        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        now = now_utc()
        flag_id = data.id or data.flagId or data.flag_id
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

    async def update(self, id: str, update_data: Dict) -> Optional[Dict]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = {**existing, **update_data}
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
                    "flag_id": merged.id,
                    "name": merged.name,
                    "description": merged.description,
                    "enabled": 1 if (merged.enabled if merged.enabled is not None else True) else None,
                    "category": merged.category,
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

    async def deleteMany(self, query: Dict) -> Dict:
        docs = await self.findAll(query)
        deleted = 0
        for d in docs:
            if await self.delete(d._id):
                deleted += 1
        return {"deletedCount": deleted}

    async def count(self, query: Optional[Dict] = None) -> int:
        docs = await self.findAll(query)
        return len(docs)

    find_all = findAll
    find_by_id = findById
    find_one = findOne
