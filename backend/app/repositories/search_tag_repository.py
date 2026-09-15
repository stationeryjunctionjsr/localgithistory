from typing import Any
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.db.storage_factory import get_storage
from app.utils.logger import logger


class SearchTagRepository:
    def __init__(self):
        self.storage = get_storage("searchTags")

    def _get_timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    async def findAll(self) -> List[Dict]:
        all_tags = await self.storage.findAll()
        # Migration: Assign tagId to existing tags if missing
        updated = False
        max_num = 0

        # First pass to find max_num
        for tag in all_tags:
            tid = (tag.tagId if tag.tagId is not None else "")
            if tid.startswith("ST-"):
                try:
                    num = int(tid.split("-")[1])
                    if num > max_num:
                        max_num = num
                except (ValueError, IndexError) as e:
                    logger.warning("Malformed tag ID '%s' found in migration: %s", tid, str(e))

        # Second pass to assign missing tagIds
        for tag in all_tags:
            if not tag.tagId:
                max_num += 1
                tag.tagId = f"ST-{max_num}"
                updated = True

        if updated:
            # Persist tagId back via Oracle (per-doc update).

            for tag in all_tags:
                if tag.id and tag.tagId:
                    await self.storage.update(
                        tag.id,
                        {"tagId": tag.tagId, "updatedAt": self._get_timestamp()},
                    )

        return all_tags

    async def findById(self, id: str) -> Optional[Dict]:
        return await self.storage.findById(id)

    async def create(self, data: Any) -> Dict:
        # Get all tags to find the next tagId
        all_tags = await self.storage.findAll()
        max_num = 0
        for tag in all_tags:
            tag_id_str = (tag.tagId if tag.tagId is not None else "")
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

        tag = {
            "tagId": new_tag_id,
            "name": data.name,
            "type": data.type,
            "isActive": (data.isActive if data.isActive is not None else True),
            "categories": (data.categories if data.categories is not None else []),
            "subCategories": (data.subCategories if data.subCategories is not None else []),
            "brands": (data.brands if data.brands is not None else []),
            "collections": (data.collections if data.collections is not None else []),
            "productIds": (data.productIds if data.productIds is not None else []),
            "excludedProductIds": (data.excludedProductIds if data.excludedProductIds is not None else []),
            "createdAt": self._get_timestamp(),
            "updatedAt": self._get_timestamp(),
        }
        return await self.storage.create(tag)

    async def update(self, id: str, update_data: Any) -> Dict:
        updates = {**update_data, "updatedAt": self._get_timestamp()}
        return await self.storage.update(id, updates)

    async def findAllActive(self) -> List[Dict]:
        """Return only active search tags"""
        all_tags = await self.findAll()
        return [t for t in all_tags if (t.isActive if t.isActive is not None else True)]

    async def addProductId(self, tag_id: str, product_id: str) -> Dict:
        """Add a product ID to the tag's productIds and remove from excludedProductIds if present"""
        tag = await self.findById(tag_id)
        if not tag:
            return None
        product_ids = list(set((tag.productIds if tag.productIds is not None else []) + [product_id]))
        excluded = [pid for pid in (tag.excludedProductIds if tag.excludedProductIds is not None else []) if pid != product_id]
        return await self.update(tag_id, {"productIds": product_ids, "excludedProductIds": excluded})

    async def excludeProductId(self, tag_id: str, product_id: str) -> Dict:
        """Add a product ID to excludedProductIds and remove from productIds if present"""
        tag = await self.findById(tag_id)
        if not tag:
            return None
        excluded = list(set((tag.excludedProductIds if tag.excludedProductIds is not None else []) + [product_id]))
        product_ids = [pid for pid in (tag.productIds if tag.productIds is not None else []) if pid != product_id]
        return await self.update(tag_id, {"excludedProductIds": excluded, "productIds": product_ids})

    async def delete(self, id: str) -> Dict:
        return await self.storage.delete(id)


search_tag_repository = SearchTagRepository()
