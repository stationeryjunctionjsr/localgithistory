from typing import Dict, List, Optional, Any
from app.models.brand import Brand
from app.models.schemas import BrandCreate, BrandUpdate, Any
from app.models.brand import Brand
from app.models.schemas import BrandCreate, BrandUpdate, Any
from app.models.brand import Brand
from app.models.schemas import BrandCreate, BrandUpdate

from app.db.storage_factory import get_storage


class BrandRepository:
    def __init__(self):
        self.storage = get_storage("brands")

    async def findAll(self, query: Optional[Dict] = None) -> List[Brand]:
        items = await self.storage.findAll(query or {})
        if query and query.get("isActive") is not None:
            items = [b for b in items if b.is_active == query.get('isActive')]
        return sorted(items, key=lambda x: (x.name or '').lower())

    async def findById(self, id: str):
        return await self.storage.findById(id)

    async def findActive(self) -> List[Brand]:
        items = await self.storage.findAll()
        return sorted(
            [b for b in items if b.is_active is True], key=lambda x: (x.name or '').lower()
        )

    async def create(self, data: Any) -> Brand:
        from app.models.daos import BrandInternalCreate
        if isinstance(data, dict):
            internal_data = BrandInternalCreate.model_validate(data)
        elif not isinstance(data, BrandInternalCreate):
            internal_data = BrandInternalCreate.model_validate(data.model_dump(exclude_unset=True))
        else:
            internal_data = data
        return await self.storage.create(internal_data)

    async def update(self, id: str, data: Any) -> Optional[Brand]:
        from app.models.daos import BrandInternalUpdate
        if isinstance(data, dict):
            internal_data = BrandInternalUpdate.model_validate(data)
        elif not isinstance(data, BrandInternalUpdate):
            internal_data = BrandInternalUpdate.model_validate(data.model_dump(exclude_unset=True))
        else:
            internal_data = data
        return await self.storage.update(id, internal_data)

    async def delete(self, id: str) -> bool:
        return await self.storage.delete(id)


brand_repository = BrandRepository()
