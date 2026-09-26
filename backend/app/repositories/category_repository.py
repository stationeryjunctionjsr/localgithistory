from datetime import datetime, timezone
from typing import TYPE_CHECKING, Dict, List, Optional, Any
from app.models.category import Category
# Note: Router defines CategoryBase and CategoryUpdate inline, Any
from app.models.category import Category
# Note: Router defines CategoryBase and CategoryUpdate inline, Any
from app.models.category import Category
# Note: Router defines CategoryBase and CategoryUpdate inline

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

    async def create(self, category_data: 'CategoryInternalCreate') -> Category:
        from app.models.daos import CategoryInternalCreate
        if isinstance(category_data, dict):
            category_data = CategoryInternalCreate(**category_data)
        elif not isinstance(category_data, CategoryInternalCreate):
            fields = {}
            for f in getattr(category_data, "model_fields_set", []):
                match f:
                    case "name": fields["name"] = category_data.name
                    case "description": fields["description"] = category_data.description
                    case "parentId" | "parent_id": fields["parentId"] = category_data.parentId
                    case "isActive" | "is_active": fields["isActive"] = category_data.is_active
            category_data = CategoryInternalCreate(**fields)
        return await self.storage.create(category_data)

    async def update(self, id: str, update_data: 'CategoryInternalUpdate') -> Category:
        from app.models.daos import CategoryInternalUpdate
        # Synchronize categoryTag and categoryTags for backward compatibility
        if isinstance(update_data, dict):
            update_data = CategoryInternalUpdate(**update_data)
        update_dict = {}
        for field in getattr(update_data, "model_fields_set", update_data.__dict__.keys() if hasattr(update_data, "__dict__") else []):
            match field:
                case "name": update_dict["name"] = update_data.name
                case "description": update_dict["description"] = update_data.description
                case "images": update_dict["images"] = update_data.images
                case "subCategories" | "sub_categories": update_dict["subCategories"] = update_data.sub_categories
                case "minimumQuantity" | "minimum_quantity": update_dict["minimumQuantity"] = update_data.minimum_quantity
                case "categoryTag" | "category_tag": update_dict["categoryTag"] = update_data.category_tag
                case "isActive" | "is_active": update_dict["isActive"] = update_data.is_active
                case "showInMobileHomepage" | "show_in_mobile_homepage": update_dict["showInMobileHomepage"] = update_data.show_in_mobile_homepage
                case "gst": update_dict["gst"] = update_data.gst
                case "isReturnable" | "is_returnable": update_dict["isReturnable"] = update_data.is_returnable
                case "parentId" | "parent_id": update_dict["parentId"] = update_data.parent_id
        if "categoryTag" in update_dict:
            tag = update_dict["categoryTag"]
            update_dict["categoryTags"] = [tag] if tag else []
        elif "categoryTags" in update_dict:
            tags = update_dict["categoryTags"]
            update_dict["categoryTag"] = tags[0] if isinstance(tags, list) and tags else ""

        updates = {**update_dict, "updatedAt": self._get_timestamp()}
        print("UPDATE_DATA:", type(update_data), update_data)
        print("UPDATES:", updates)
        internal_update = CategoryInternalUpdate.model_validate(updates)
        return await self.storage.update(id, internal_update)

    async def delete(self, id: str) -> Category:
        # Soft delete - set isActive to false
        from app.models.daos import CategoryInternalUpdate
        return await self.update(id, CategoryInternalUpdate(isActive=False))


category_repository = CategoryRepository()






