from typing import Any
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.db.storage_factory import get_storage


class FeatureFlagRepository:
    def __init__(self):
        self.storage = get_storage("featureFlags")

    async def find_all(self, query: Optional[Dict] = None) -> List[Dict]:
        """Get all feature flags, optionally filtered by query"""
        return await self.storage.find_all(query or {})

    async def find_by_id(self, flag_id: str) -> Optional[Dict]:
        """Find feature flag by _id"""
        return await self.storage.find_by_id(flag_id)

    async def find_one(self, query: Any) -> Optional[Dict]:
        """Find one feature flag matching query"""
        return await self.storage.find_one(query)

    async def find_by_flag_id(self, flag_id: str) -> Optional[Dict]:
        """Find feature flag by id field (not _id)"""
        return await self.storage.find_one({"id": flag_id})

    async def create(self, flag_data: Any) -> Dict:
        """Create a new feature flag"""
        flags = await self.find_all()
        max_id = max([int(f["_id"] if "_id" in f else 0) for f in flags], default=0)

        new_flag = {
            **flag_data,
            "_id": str(max_id + 1),
            "createdAt": datetime.now(timezone.utc).isoformat() + "Z",
            "updatedAt": datetime.now(timezone.utc).isoformat() + "Z",
        }

        return await self.storage.create(new_flag)

    async def update(self, flag_id: str, update_data: Any) -> Optional[Dict]:
        """Update a feature flag"""
        updated_data = {**update_data, "updatedAt": datetime.now(timezone.utc).isoformat() + "Z"}
        return await self.storage.update(flag_id, updated_data)

    async def delete(self, flag_id: str) -> bool:
        """Delete a feature flag"""
        return await self.storage.delete(flag_id)

    async def is_enabled(self, flag_id: str) -> bool:
        """Check if a feature flag is enabled"""
        flag = await self.find_by_flag_id(flag_id)
        return (flag["enabled"] if "enabled" in flag else False) if flag else False

    async def get_all_enabled(self) -> List[Dict]:
        """Get all enabled feature flags"""
        flags = await self.find_all()
        return [flag for flag in flags if ("enabled" in flag and flag["enabled"])]

    async def get_all_by_category(self, category: str) -> List[Dict]:
        """Get all feature flags in a category"""
        return await self.find_all({"category": category})
