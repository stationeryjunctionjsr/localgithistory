import json
from typing import Any, Dict, List, Optional

from app.db.storage_factory import get_storage
from app.models.daos_flat import CollectionInternal, CollectionInternalCreate, CollectionInternalUpdate


class CollectionRepository:
    def __init__(self):
        self.storage = get_storage("collections")

    async def findAll(self, query: Optional[Dict] = None) -> List[CollectionInternal]:
        collections = await self.storage.findAll()

        query = query or {}

        # Consolidate all filters into one pass for robustness
        filtered = []
        user_role = query.get("userRole", "guest")
        target_page_type = query.get("pageType") or query.get("visiblePage")
        target_page_id = query.get("pageId")

        for col in collections:
            # 1. Check isActive
            if "isActive" in query and query["isActive"] is not None:
                if col.isActive != query["isActive"]:
                    continue
            else:
                if not (col.isActive if col.isActive is not None else True):
                    continue

            # 2. Check user segments
            segments = col.userSegments if col.userSegments else ["all"]
            if "all" not in segments and user_role not in segments:
                continue

            # 3. Check page visibility (if a target page is requested)
            if target_page_type:
                # Check legacy visiblePages array
                is_visible_legacy = target_page_type in (col.visiblePages or [])

                # Check new visibilityRules
                is_visible_rules = False
                rules = col.visibilityRules or []
                for rule_str in rules:
                    try:
                        rule = json.loads(rule_str) if isinstance(rule_str, str) else rule_str
                    except:
                        continue

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
        collections.sort(key=lambda x: x.displayOrder if x.displayOrder is not None else 0)

        return collections

    async def findById(self, id: str) -> Optional[CollectionInternal]:
        return await self.storage.findById(id)

    async def create(self, collection_data: CollectionInternalCreate) -> CollectionInternal:
        return await self.storage.create(collection_data)

    async def update(self, id: str, update_data: CollectionInternalUpdate) -> CollectionInternal:
        return await self.storage.update(id, update_data)

    async def delete(self, id: str) -> bool:
        return await self.storage.delete(id)


collection_repository = CollectionRepository()
