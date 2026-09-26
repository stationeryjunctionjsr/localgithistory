from typing import Any
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.db.storage_factory import get_storage
from app.utils.logger import logger
from app.models.daos_flat import SearchTagInternal, SearchTagInternalCreate, SearchTagInternalUpdate


class SearchTagRepository:
    def __init__(self):
        self.storage = get_storage("searchTags")

    def _get_timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    async def findAll(self) -> List[SearchTagInternal]:
        all_tags = await self.storage.findAll()
        # Migration: Assign tagId to existing tags if missing
        updated = False
        max_num = 0

        # First pass to find max_num
        for tag in all_tags:
            tid = tag.tag_id if tag.tag_id is not None else ""
            if tid.startswith("ST-"):
                try:
                    num = int(tid.split("-")[1])
                    if num > max_num:
                        max_num = num
                except (ValueError, IndexError) as e:
                    logger.warning("Malformed tag ID '%s' found in migration: %s", tid, str(e))

        # Second pass to assign missing tagIds
        for tag in all_tags:
            if not tag.tag_id:
                max_num += 1
                tag.tag_id = f"ST-{max_num}"
                updated = True

        if updated:
            # Persist tagId back via Oracle (per-doc update).
            for tag in all_tags:
                if tag.id and tag.tag_id:
                    await self.storage.update(
                        tag.id,
                        SearchTagInternalUpdate(tagId=tag.tag_id)
                    )

        return all_tags

    async def findById(self, id: str) -> Optional[SearchTagInternal]:
        return await self.storage.findById(id)

    async def create(self, data: SearchTagInternalCreate) -> SearchTagInternal:
        # Get all tags to find the next tagId
        all_tags = await self.storage.findAll()
        max_num = 0
        for tag in all_tags:
            tag_id_str = tag.tag_id if tag.tag_id is not None else ""
            if tag_id_str.startswith("ST-"):
                try:
                    # Extract number from "ST-X"
                    parts = tag_id_str.split("-")
                    if len(parts) > 1:
                        num = int(parts[1])
                        if num > max_num:
                            max_num = num
                except (ValueError, IndexError):
                    continue

        new_tag_id = f"ST-{max_num + 1}"

        tag_internal = SearchTagInternalCreate(
            tagId=new_tag_id,
            name=data.name,
            type=data.type,
            isActive=data.is_active if data.is_active is not None else True,
            categories=data.categories if data.categories is not None else [],
            subCategories=data.sub_categories if data.sub_categories is not None else [],
            brands=data.brands if data.brands is not None else [],
            collections=data.collections if data.collections is not None else [],
            productIds=data.product_ids if data.product_ids is not None else [],
            excludedProductIds=data.excluded_product_ids if data.excluded_product_ids is not None else [],
        )
        return await self.storage.create(tag_internal)

    async def update(self, id: str, update_data: SearchTagInternalUpdate) -> SearchTagInternal:
        return await self.storage.update(id, update_data)

    async def findAllActive(self) -> List[SearchTagInternal]:
        """Return only active search tags"""
        all_tags = await self.findAll()
        return [t for t in all_tags if (t.is_active if t.is_active is not None else True)]

    async def addProductId(self, tag_id: str, product_id: str) -> Optional[SearchTagInternal]:
        """Add a product ID to the tag's productIds and remove from excludedProductIds if present"""
        tag = await self.findById(tag_id)
        if not tag:
            return None
        product_ids = list(set((tag.product_ids if tag.product_ids is not None else []) + [product_id]))
        excluded = [pid for pid in (tag.excluded_product_ids if tag.excluded_product_ids is not None else []) if pid != product_id]
        return await self.update(tag_id, SearchTagInternalUpdate(productIds=product_ids, excludedProductIds=excluded))

    async def excludeProductId(self, tag_id: str, product_id: str) -> Optional[SearchTagInternal]:
        """Add a product ID to excludedProductIds and remove from productIds if present"""
        tag = await self.findById(tag_id)
        if not tag:
            return None
        excluded = list(set((tag.excluded_product_ids if tag.excluded_product_ids is not None else []) + [product_id]))
        product_ids = [pid for pid in (tag.product_ids if tag.product_ids is not None else []) if pid != product_id]
        return await self.update(tag_id, SearchTagInternalUpdate(excludedProductIds=excluded, productIds=product_ids))

    async def delete(self, id: str) -> bool:
        return await self.storage.delete(id)

search_tag_repository = SearchTagRepository()