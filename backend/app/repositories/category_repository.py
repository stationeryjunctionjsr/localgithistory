from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.db.storage_factory import get_storage


class CategoryRepository:
    def __init__(self):
        self.storage = get_storage("categories")

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now(timezone.utc).isoformat()

    async def findAll(self) -> List[Dict]:
        return await self.storage.findAll()

    async def findById(self, id: str) -> Optional[Dict]:
        return await self.storage.findById(id)

    async def findByName(self, name: str) -> Optional[Dict]:
        categories = await self.storage.findAll({"name": name})
        return categories[0] if categories else None

    async def create(self, category_data: Dict) -> Dict:
        # Migrate categoryTags list to singular categoryTag if necessary
        tag = category_data.get("categoryTags", [])
        if isinstance(tag, list):
            tag = tag[0] if tag else ""

        category = {
            "name": category_data["name"],
            "description": category_data.get("description", ""),
            "images": category_data.get("images", []),
            "subCategories": category_data.get("subCategories", []),  # Array of sub-category names
            "minimumQuantity": category_data.get("minimumQuantity", 0),  # Minimum quantity required for category
            "categoryTag": category_data.get("categoryTag", tag),  # Single category tag
            "isActive": category_data.get("isActive", True),
            "showInMobileHomepage": category_data.get("showInMobileHomepage", False),
            "gst": category_data.get("gst", 0.0),
            "isReturnable": category_data.get("isReturnable", False),
            "createdAt": self._get_timestamp(),
            "updatedAt": self._get_timestamp(),
        }
        return await self.storage.create(category)

    async def update(self, id: str, update_data: Dict) -> Dict:
        # Synchronize categoryTag and categoryTags for backward compatibility
        if "categoryTag" in update_data:
            tag = update_data["categoryTag"]
            update_data["categoryTags"] = [tag] if tag else []
        elif "categoryTags" in update_data:
            tags = update_data["categoryTags"]
            update_data["categoryTag"] = tags[0] if isinstance(tags, list) and tags else ""

        updates = {**update_data, "updatedAt": self._get_timestamp()}
        return await self.storage.update(id, updates)

    async def delete(self, id: str) -> Dict:
        # Soft delete - set isActive to false
        return await self.storage.update(id, {"isActive": False})


category_repository = CategoryRepository()
