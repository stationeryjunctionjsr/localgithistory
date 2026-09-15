from typing import Any
from typing import Dict, Optional

from app.db.storage_factory import get_storage


class CollectionRepository:
    def __init__(self):
        self.storage = get_storage("collections")

    async def findAll(self, query: Optional[Dict] = None):
        collections = await self.storage.findAll()

        query = query or {}

        # Consolidate all filters into one pass for robustness
        filtered = []
        user_role = query["userRole"] if "userRole" in query else "guest"
        target_page_type = (query["pageType"] if "pageType" in query else None) or (query["visiblePage"] if "visiblePage" in query else None)
        target_page_id = query["pageId"] if "pageId" in query else None

        for col in collections:
            # 1. Check isActive
            if "isActive" in query and query["isActive"] is not None:
                col_active = col["isActive"] if "isActive" in col else None
                if col_active != query["isActive"]:
                    continue
            else:
                if not (col["isActive"] if "isActive" in col else True):
                    continue

            # 2. Check user segments
            segments = col["userSegments"] if "userSegments" in col else ["all"]
            if "all" not in segments and user_role not in segments:
                continue

            # 3. Check page visibility (if a target page is requested)
            if target_page_type:
                # Check legacy visiblePages array
                is_visible_legacy = target_page_type in (col["visiblePages"] if "visiblePages" in col else [])

                # Check new visibilityRules
                is_visible_rules = False
                rules = col["visibilityRules"] if "visibilityRules" in col else []
                for rule in rules:
                    rule_pg = rule["pageType"] if "pageType" in rule else ""
                    if (
                        rule_pg == target_page_type
                        or (target_page_type == "Category" and rule_pg == "all_categories")
                        or (target_page_type == "Brand" and rule_pg == "all_brands")
                        or (target_page_type == "category" and rule_pg == "all_categories")
                        or (target_page_type == "brand" and rule_pg == "all_brands")
                    ):
                        page_ids = rule["pageIds"] if "pageIds" in rule else []
                        if not page_ids or target_page_id in page_ids:
                            is_visible_rules = True
                            break

                # If it's not and has no rules, it's not visible for a specific page query
                if not is_visible_legacy and not is_visible_rules:
                    continue

            filtered.append(col)

        collections = filtered

        # Sort by displayOrder
        collections.sort(key=lambda x: x["displayOrder"] if "displayOrder" in x else 0)

        return collections

    async def findById(self, id: str):
        return await self.storage.findById(id)

    async def create(self, collection_data: Any):
        collection = {
            "name": collection_data["name"],
            "description": collection_data["description"] if "description" in collection_data else "",
            "imageUrl": collection_data["imageUrl"] if "imageUrl" in collection_data else "",
            "isActive": collection_data["isActive"] if "isActive" in collection_data else True,
            "displayOrder": collection_data["displayOrder"] if "displayOrder" in collection_data else 0,
            "visiblePages": collection_data["visiblePages"] if "visiblePages" in collection_data else [],
            "userSegments": collection_data["userSegments"] if "userSegments" in collection_data else ["all"],
            "visibilityRules": collection_data["visibilityRules"] if "visibilityRules" in collection_data else [],
            "productIds": collection_data["productIds"] if "productIds" in collection_data else [],
        }

        return await self.storage.create(collection)

    async def update(self, id: str, update_data: Any):
        return await self.storage.update(id, update_data)

    async def delete(self, id: str):
        return await self.storage.delete(id)


collection_repository = CollectionRepository()
