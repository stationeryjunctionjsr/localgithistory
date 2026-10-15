from datetime import datetime, timezone
from typing import List, Optional

from app.db.storage_factory import get_storage
from app.models.category import Category
from app.models.daos_flat import (
    CategoryTagInternal,
    CategoryTagInternalCreate,
    CategoryTagInternalUpdate,
)


class CategoryTagRepository:
    def __init__(self) -> None:
        self.storage = get_storage("categoryTags")

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now(timezone.utc).isoformat()

    async def findAll(
        self,
        is_active: Optional[bool] = None,
        name: Optional[str] = None,
        division_id: Optional[int] = None,
        category_head_id: Optional[int] = None,
    ) -> List[CategoryTagInternal]:
        target_did = division_id if division_id is not None else category_head_id
        return await self.storage.findAll(
            is_active=is_active,
            name=name,
            division_id=target_did,
        )

    async def findById(self, id: int) -> Optional[CategoryTagInternal]:
        return await self.storage.findById(id)

    async def findByName(self, name: str) -> Optional[CategoryTagInternal]:
        return await self.storage.findOne(name=name)

    async def findByDivision(self, division_id: int) -> List[CategoryTagInternal]:
        return await self.storage.findAll(division_id=division_id)

    async def findByCategoryHead(self, category_head_id: int) -> List[CategoryTagInternal]:
        return await self.storage.findAll(division_id=category_head_id)

    async def findCategoriesByTag(self, tag_id: int) -> List[Category]:
        return await self.storage.findCategoriesByTag(tag_id)

    async def create(self, tag_data: CategoryTagInternalCreate) -> CategoryTagInternal:
        if tag_data.is_active is None:
            tag_data.is_active = True
        return await self.storage.create(tag_data)

    async def update(self, id: int, update_data: CategoryTagInternalUpdate) -> Optional[CategoryTagInternal]:
        return await self.storage.update(id, update_data)

    async def delete(self, id: int) -> Optional[CategoryTagInternal]:
        # Soft delete - set isActive to false
        return await self.storage.update(id, CategoryTagInternalUpdate(is_active=False))

    async def hardDelete(self, id: int) -> bool:
        return await self.storage.delete(id)


category_tag_repository = CategoryTagRepository()
