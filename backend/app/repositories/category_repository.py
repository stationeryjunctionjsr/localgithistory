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
        from app.models.daos import CategoryInternalCreate
        if isinstance(category_data, dict):
            category_data = CategoryInternalCreate.model_validate(category_data)
        elif not isinstance(category_data, CategoryInternalCreate):
            fields = {}
            for f in category_data.model_fields_set:
                match f:
                    case "name": fields["name"] = category_data.name
                    case "description": fields["description"] = category_data.description
                    case "parentId": fields["parentId"] = category_data.parentId
                    case "isActive": fields["isActive"] = category_data.isActive
            category_data = CategoryInternalCreate(**fields)
        return await self.storage.create(category_data)

    async def update(self, id: str, update_data: Any) -> Category:
        from app.models.daos import CategoryInternalUpdate
        # Synchronize categoryTag and categoryTags for backward compatibility
        update_dict = {}
        if isinstance(update_data, dict):
            update_dict = update_data
        else:
            for field in update_data.model_fields_set:
                match field:
                    case "name": update_dict["name"] = update_data.name
                    case "description": update_dict["description"] = update_data.description
                    case "images": update_dict["images"] = update_data.images
                    case "subCategories": update_dict["subCategories"] = update_data.subCategories
                    case "minimumQuantity": update_dict["minimumQuantity"] = update_data.minimumQuantity
                    case "categoryTag": update_dict["categoryTag"] = update_data.categoryTag
                    case "isActive": update_dict["isActive"] = update_data.isActive
                    case "showInMobileHomepage": update_dict["showInMobileHomepage"] = update_data.showInMobileHomepage
                    case "gst": update_dict["gst"] = update_data.gst
                    case "isReturnable": update_dict["isReturnable"] = update_data.isReturnable
                    case "parentId": update_dict["parentId"] = update_data.parentId
        if "categoryTag" in update_dict:
            tag = update_dict["categoryTag"]
            update_dict["categoryTags"] = [tag] if tag else []
        elif "categoryTags" in update_dict:
            tags = update_dict["categoryTags"]
            update_dict["categoryTag"] = tags[0] if isinstance(tags, list) and tags else ""

        updates = {**update_dict, "updatedAt": self._get_timestamp()}
        internal_update = CategoryInternalUpdate.model_validate(updates)
        return await self.storage.update(id, internal_update)

    async def delete(self, id: str) -> Category:
        # Soft delete - set isActive to false
        return await self.storage.update(id, {"isActive": False})


category_repository = CategoryRepository()


