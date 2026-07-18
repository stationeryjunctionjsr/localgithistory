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
        user_role = query.get("userRole", "guest")
        target_page_type = query.get("pageType") or query.get("visiblePage")
        target_page_id = query.get("pageId")

        for col in collections:
            # 1. Check isActive
            if query.get("isActive") is not None:
                if col.get("isActive") != query["isActive"]:
                    continue
            else:
                if not col.get("isActive", True):
                    continue

            # 2. Check user segments
            segments = col.get("userSegments", ["all"])
            if "all" not in segments and user_role not in segments:
                continue

            # 3. Check page visibility (if a target page is requested)
            if target_page_type:
                # Check legacy visiblePages array
                is_visible_legacy = target_page_type in col.get("visiblePages", [])

                # Check new visibilityRules
                is_visible_rules = False
                rules = col.get("visibilityRules", [])
                for rule in rules:
                    rule_pg = rule.get("pageType", "")
                    if (
                        rule_pg == target_page_type
                        or (target_page_type == "Category" and rule_pg == "all_categories")
                        or (target_page_type == "Brand" and rule_pg == "all_brands")
                        or (target_page_type == "category" and rule_pg == "all_categories")
                        or (target_page_type == "brand" and rule_pg == "all_brands")
                    ):
                        page_ids = rule.get("pageIds", [])
                        if not page_ids or target_page_id in page_ids:
                            is_visible_rules = True
                            break

                # If it's not and has no rules, it's not visible for a specific page query
                if not is_visible_legacy and not is_visible_rules:
                    continue

            filtered.append(col)

        collections = filtered

        # Sort by displayOrder
        collections.sort(key=lambda x: x.get("displayOrder", 0))

        return collections

    async def findById(self, id: str):
        return await self.storage.findById(id)

    async def create(self, collection_data: Dict):
        collection = {
            "name": collection_data["name"],
            "description": collection_data.get("description", ""),
            "imageUrl": collection_data.get("imageUrl", ""),
            "isActive": collection_data.get("isActive", True),
            "displayOrder": collection_data.get("displayOrder", 0),
            "visiblePages": collection_data.get("visiblePages", []),
            "userSegments": collection_data.get("userSegments", ["all"]),
            "visibilityRules": collection_data.get("visibilityRules", []),
            "productIds": collection_data.get("productIds", []),
        }

        return await self.storage.create(collection)

    async def update(self, id: str, update_data: Dict):
        return await self.storage.update(id, update_data)

    async def delete(self, id: str):
        return await self.storage.delete(id)


collection_repository = CollectionRepository()
