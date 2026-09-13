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
            tid = getattr(tag, "tagId", "")
            if tid.startswith("ST-"):
                try:
                    num = int(tid.split("-")[1])
                    if num > max_num:
                        max_num = num
                except (ValueError, IndexError) as e:
                    logger.warning("Malformed tag ID '%s' found in migration: %s", tid, str(e))

        # Second pass to assign missing tagIds
        for tag in all_tags:
            if not getattr(tag, "tagId", None):
                max_num += 1
                tag.tagId = f"ST-{max_num}"
                updated = True

        if updated:
            # Persist tagId back via Oracle (per-doc update).
            # FileStorage direct file write is disabled — Oracle is the only supported backend.
            # if hasattr(self.storage, "file_path"):
            #     import json
            #     self.storage.file_path.write_text(
            #         json.dumps(all_tags, indent=2, default=str),
            #         encoding="utf-8",
            #     )
            #     self.storage._invalidate_cache()
            # else:
            for tag in all_tags:
                if tag.id and getattr(tag, "tagId", None):
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
            tag_id_str = getattr(tag, "tagId", "")
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
            "isActive": getattr(data, 'isActive', True),
            "categories": getattr(data, 'categories', []),
            "subCategories": getattr(data, 'subCategories', []),
            "brands": getattr(data, 'brands', []),
            "collections": getattr(data, 'collections', []),
            "productIds": getattr(data, 'productIds', []),
            "excludedProductIds": getattr(data, 'excludedProductIds', []),
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
        return [t for t in all_tags if getattr(t, "isActive", True)]

    async def addProductId(self, tag_id: str, product_id: str) -> Dict:
        """Add a product ID to the tag's productIds and remove from excludedProductIds if present"""
        tag = await self.findById(tag_id)
        if not tag:
            return None
        product_ids = list(set(getattr(tag, "productIds", []) + [product_id]))
        excluded = [pid for pid in getattr(tag, "excludedProductIds", []) if pid != product_id]
        return await self.update(tag_id, {"productIds": product_ids, "excludedProductIds": excluded})

    async def excludeProductId(self, tag_id: str, product_id: str) -> Dict:
        """Add a product ID to excludedProductIds and remove from productIds if present"""
        tag = await self.findById(tag_id)
        if not tag:
            return None
        excluded = list(set(getattr(tag, "excludedProductIds", []) + [product_id]))
        product_ids = [pid for pid in getattr(tag, "productIds", []) if pid != product_id]
        return await self.update(tag_id, {"excludedProductIds": excluded, "productIds": product_ids})

    async def delete(self, id: str) -> Dict:
        return await self.storage.delete(id)


search_tag_repository = SearchTagRepository()
