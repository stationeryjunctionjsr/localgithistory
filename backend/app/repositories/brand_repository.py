from typing import TYPE_CHECKING, List, Optional
from app.models.brand import Brand
from app.models.schemas import BrandCreate, BrandUpdate

from app.db.storage_factory import get_storage

if TYPE_CHECKING:
    from app.models.daos import BrandInternalCreate, BrandInternalUpdate
    


class BrandRepository:
    def __init__(self) -> None:
        self.storage = get_storage("brands")

    async def findAll(
        self,
        is_active: Optional[bool] = None,
        slug: Optional[str] = None,
        name: Optional[str] = None,
    ) -> List[Brand]:
        items = await self.storage.findAll(is_active=is_active, slug=slug, name=name)
        return sorted(items, key=lambda x: (x.name or "").lower())

    async def findById(self, id: str) -> Optional[Brand]:
        return await self.storage.findById(id)

    async def findActive(self) -> List[Brand]:
        items = await self.storage.findAll(is_active=True)
        return sorted(items, key=lambda x: (x.name or "").lower())

    async def create(self, data: "BrandInternalCreate") -> Brand:
        return await self.storage.create(data)

    async def update(self, id: str, data: "BrandInternalUpdate") -> Optional[Brand]:
        return await self.storage.update(id, data)

    async def delete(self, id: str) -> bool:
        return await self.storage.delete(id)


brand_repository = BrandRepository()
