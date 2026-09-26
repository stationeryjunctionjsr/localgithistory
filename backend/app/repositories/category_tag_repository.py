from typing import Any
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.db.storage_factory import get_storage
from app.models.daos_flat import CategoryTagInternal, CategoryTagInternalCreate, CategoryTagInternalUpdate


class CategoryTagRepository:
    def __init__(self):
        self.storage = get_storage("categoryTags")

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now(timezone.utc).isoformat()

    async def findAll(self) -> List[CategoryTagInternal]:
        return await self.storage.findAll()

    async def findById(self, id: str) -> Optional[CategoryTagInternal]:
        return await self.storage.findById(id)

    async def findByName(self, name: str) -> Optional[CategoryTagInternal]:
        tags = await self.storage.findAll()
        for tag in tags:
            if (tag.name if tag.name is not None else "").lower() == name.lower():
                return tag
        return None

    async def create(self, tag_data: CategoryTagInternalCreate) -> CategoryTagInternal:
        if tag_data.is_active is None:
            tag_data.is_active = True
        return await self.storage.create(tag_data)

    async def update(self, id: str, update_data: CategoryTagInternalUpdate) -> CategoryTagInternal:
        return await self.storage.update(id, update_data)

    async def delete(self, id: str) -> CategoryTagInternal:
        # Soft delete - set isActive to false
        return await self.storage.update(id, CategoryTagInternalUpdate(is_active=False))


category_tag_repository = CategoryTagRepository()
