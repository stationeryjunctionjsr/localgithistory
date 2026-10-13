from typing import TYPE_CHECKING
from datetime import datetime, timezone
from typing import List, Optional

from app.db.storage_factory import get_storage

from app.models.feature_flag import FeatureFlag, FeatureFlagUpdate


class FeatureFlagRepository:
    def __init__(self) -> None:
        self.storage = get_storage("featureFlags")

    async def find_all(
        self,
        enabled: Optional[bool] = None,
        category: Optional[str] = None,
    ) -> List[FeatureFlag]:
        """Get all feature flags, optionally filtered"""
        return await self.storage.findAll(enabled=enabled, category=category)

    async def find_by_id(self, id: int) -> Optional[FeatureFlag]:
        """Find feature flag by PK id"""
        return await self.storage.findById(id)

    async def find_one(
        self,
        id: Optional[int] = None,
        flag_id: Optional[str] = None,
    ) -> Optional[FeatureFlag]:
        """Find one feature flag matching filters"""
        return await self.storage.findOne(id=id, flag_id=flag_id)

    async def find_by_flag_id(self, flag_id: str) -> Optional[FeatureFlag]:
        """Find feature flag by flag_id"""
        return await self.storage.findOne(flag_id=flag_id)

    async def create(self, flag_data: FeatureFlag) -> FeatureFlag:
        """Create a new feature flag"""
        now = datetime.now(timezone.utc)
        flag_data.created_at = now
        flag_data.updated_at = now
        return await self.storage.create(flag_data)

    async def update(self, id: int, update_data: FeatureFlagUpdate) -> Optional[FeatureFlag]:
        """Update a feature flag"""
        return await self.storage.update(id, update_data)

    async def delete(self, id: int) -> bool:
        """Delete a feature flag"""
        return await self.storage.delete(id)

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
        return await self.find_all(category=category)

feature_flag_repository = FeatureFlagRepository()
