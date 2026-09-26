from typing import TYPE_CHECKING, Dict, List, Optional, Any
from app.models.brand import Brand
from app.models.schemas import BrandCreate, BrandUpdate, Any
from app.models.brand import Brand
from app.models.schemas import BrandCreate, BrandUpdate, Any
from app.models.brand import Brand
from app.models.schemas import BrandCreate, BrandUpdate

from app.db.storage_factory import get_storage

if TYPE_CHECKING:
    from app.models.daos import BrandInternalCreate, BrandInternalUpdate
    


class BrandRepository:
    def __init__(self):
        self.storage = get_storage("brands")

    async def findAll(self, query: Optional[Dict] = None) -> List[Brand]:
        items = await self.storage.findAll(query or {})
        if query and 'isActive' in query and query["isActive"] is not None:
            items = [b for b in items if b.is_active == query['isActive']]
        return sorted(items, key=lambda x: (x.name or '').lower())

    async def findById(self, id: str):
        return await self.storage.findById(id)

    async def findActive(self) -> List[Brand]:
        items = await self.storage.findAll()
        return sorted(
            [b for b in items if b.is_active is True], key=lambda x: (x.name or '').lower()
        )

    async def create(self, data: 'BrandInternalCreate') -> Brand:
        return await self.storage.create(data)

    async def update(self, id: str, data: 'BrandInternalUpdate') -> Optional[Brand]:
        return await self.storage.update(id, data)

    async def delete(self, id: str) -> bool:
        return await self.storage.delete(id)


brand_repository = BrandRepository()
