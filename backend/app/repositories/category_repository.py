from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from app.models.category import Category
# Note: Router defines CategoryBase and CategoryUpdate inline, Any
from app.models.category import Category
# Note: Router defines CategoryBase and CategoryUpdate inline, Any
from app.models.category import Category
# Note: Router defines CategoryBase and CategoryUpdate inline

from app.db.storage_factory import get_storage


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

    async def create(self, category_data: Any) -> Category:
        # Migrate categoryTags list to singular categoryTag if necessary
        return await self.storage.create(category_data)

    async def update(self, id: str, update_data: Any) -> Category:
        # Synchronize categoryTag and categoryTags for backward compatibility
        if "categoryTag" in update_data:
            tag = update_data.categoryTag
            update_data.categoryTags = [tag] if tag else []
        elif "categoryTags" in update_data:
            tags = update_data.categoryTags
            update_data.categoryTag = tags[0] if isinstance(tags, list) and tags else ""

        updates = {**update_data, "updatedAt": self._get_timestamp()}
        return await self.storage.update(id, updates)

    async def delete(self, id: str) -> Category:
        # Soft delete - set isActive to false
        return await self.storage.update(id, {"isActive": False})


category_repository = CategoryRepository()


