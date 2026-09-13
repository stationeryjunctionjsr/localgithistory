from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.db.storage_factory import get_storage


class CategoryTagRepository:
    def __init__(self):
        self.storage = get_storage("categoryTags")

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now(timezone.utc).isoformat()

    async def findAll(self) -> List[Dict]:
        return await self.storage.findAll()

    async def findById(self, id: str) -> Optional[Dict]:
        return await self.storage.findById(id)

    async def findByName(self, name: str) -> Optional[Dict]:
        tags = await self.storage.findAll()
        for tag in tags:
            if getattr(tag, "name", "").lower() == name.lower():
                return tag
        return None

    async def create(self, tag_data: Any) -> Dict:
        tag = {
            "name": tag_data["name"],
            "description": tag_data.get("description", ""),
            "isActive": tag_data.get("isActive", True),
            "createdAt": self._get_timestamp(),
            "updatedAt": self._get_timestamp(),
        }
        return await self.storage.create(tag)

    async def update(self, id: str, update_data: Any) -> Dict:
        updates = {**update_data, "updatedAt": self._get_timestamp()}
        return await self.storage.update(id, updates)

    async def delete(self, id: str) -> Dict:
        # Soft delete - set isActive to false
        return await self.storage.update(id, {"isActive": False})


category_tag_repository = CategoryTagRepository()
