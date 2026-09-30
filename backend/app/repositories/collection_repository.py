import json
from typing import List, Optional

from app.db.storage_factory import get_storage
from app.models.daos_flat import CollectionInternal, CollectionInternalCreate, CollectionInternalUpdate


class CollectionRepository:
    def __init__(self):
        self.storage = get_storage("collections")

    async def findAll(self, query: Optional[dict] = None) -> List[CollectionInternal]:
        collections = await self.storage.findAll()

        query = query or {}

        # Consolidate all filters into one pass for robustness
        filtered = []
        user_role = query["userRole"] if "userRole" in query else "guest"
        target_page_type = query["pageType"] if "pageType" in query else None or query["visiblePage"] if "visiblePage" in query else None
        target_page_id = query["pageId"] if "pageId" in query else None

        for col in collections:
            # 1. Check isActive
            if "isActive" in query and query["isActive"] is not None:
                if col.is_active != query["isActive"]:
                    continue
            else:
                if not (col.is_active if col.is_active is not None else True):
                    continue

            # 2. Check user segments
            segments = col.user_segments if col.user_segments else ["all"]
            if "all" not in segments and user_role not in segments:
                continue

            # 3. Check page visibility (if a target page is requested)
            if target_page_type:
                # Check legacy visiblePages array
                is_visible_legacy = target_page_type in (col.visible_pages or [])

                # Check new visibilityRules
                is_visible_rules = False
                rules = col.visibility_rules or []
                for rule_str in rules:
                    try:
                        rule = json.loads(rule_str)
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

        # Sort by display_order
        collections.sort(key=lambda x: x.display_order if x.display_order is not None else 0)

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
