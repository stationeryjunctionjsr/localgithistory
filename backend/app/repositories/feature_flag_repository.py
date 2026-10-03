from typing import TYPE_CHECKING
from datetime import datetime, timezone
from typing import List, Optional

from app.db.storage_factory import get_storage

if TYPE_CHECKING:
        from app.models.schemas import FeatureFlag



class FeatureFlagRepository:
    def __init__(self):
        self.storage = get_storage("featureFlags")

    async def find_all(self, query: Optional[dict] = None) -> List['FeatureFlag']:
        """Get all feature flags, optionally filtered by query"""
        return await self.storage.findAll(query or {})

    async def find_by_id(self, flag_id: str) -> Optional['FeatureFlag']:
        """Find feature flag by _id"""
        return await self.storage.findById(flag_id)

    async def find_one(self, query: dict) -> Optional['FeatureFlag']:
        """Find one feature flag matching query"""
        return await self.storage.findOne(query)

    async def find_by_flag_id(self, flag_id: str) -> Optional['FeatureFlag']:
        """Find feature flag by id field (not _id)"""
        return await self.storage.findOne({"id": flag_id})

    async def create(self, flag_data: 'FeatureFlag') -> 'FeatureFlag':
        """Create a new feature flag"""
        flags = await self.find_all()
        max_id = 0
        for f in flags:
            try:
                fid = int(f.id) if f.id is not None else 0
                max_id = max(max_id, fid)
            except (ValueError, TypeError):
                continue

        flag_data.id = str(max_id + 1)
        now = datetime.now(timezone.utc)
        flag_data.created_at = now
        flag_data.updated_at = now

        return await self.storage.create(flag_data)

    async def update(self, flag_id: str, update_data: 'FeatureFlag') -> Optional['FeatureFlag']:
        """Update a feature flag"""
        update_data.updated_at = datetime.now(timezone.utc)
        return await self.storage.update(flag_id, update_data)

    async def delete(self, flag_id: str) -> bool:
        """Delete a feature flag"""
        return await self.storage.delete(flag_id)

    async def is_enabled(self, flag_id: str) -> bool:
        """Check if a feature flag is enabled"""
        flag = await self.find_by_flag_id(flag_id)
        return bool(flag.enabled) if flag else False

    async def get_all_enabled(self) -> List['FeatureFlag']:
        """Get all enabled feature flags"""
        flags = await self.find_all()
        return [flag for flag in flags if bool(flag.enabled)]

    async def get_all_by_category(self, category: str) -> List['FeatureFlag']:
        """Get all feature flags in a category"""
        return await self.find_all({"category": category})

feature_flag_repository = FeatureFlagRepository()
