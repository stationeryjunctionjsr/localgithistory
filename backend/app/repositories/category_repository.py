from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from app.models.category import Category

from app.db.storage_factory import get_storage

if TYPE_CHECKING:
    from app.models.daos import CategoryInternalCreate, CategoryInternalUpdate
    


class CategoryRepository:
    def __init__(self):
        self.storage = get_storage("categories")

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now(timezone.utc).isoformat()

    async def findAll(self) -> List[Category]:
        return await self.storage.findAll()

    async def findById(self, id: str) -> Optional[Category]:
        return await self.storage.findById(id)

    async def findByName(self, name: str) -> Optional[Category]:
        categories = await self.storage.findAll({"name": name})
        return categories[0] if categories else None

    async def create(self, category_data: "CategoryInternalCreate") -> Category:
        return await self.storage.create(category_data)

    async def update(self, id: str, update_data: "CategoryInternalUpdate") -> Category:
        # Synchronize categoryTag and categoryTags for backward compatibility
        if "category_tag" in update_data.model_fields_set:
            tag = update_data.category_tag
            update_data.category_tags = [tag] if tag else []
        elif "category_tags" in update_data.model_fields_set:
            tags = update_data.category_tags
            update_data.category_tag = tags[0] if tags else ""
            
        return await self.storage.update(id, update_data)

    async def delete(self, id: str) -> Category:
        # Soft delete - set isActive to false
        from app.models.daos import CategoryInternalUpdate
        return await self.update(id, CategoryInternalUpdate(is_active=False))


category_repository = CategoryRepository()
