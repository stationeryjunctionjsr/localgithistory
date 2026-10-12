from datetime import datetime, timezone
from typing import List, Optional

from app.db.storage_factory import get_storage
from app.models.division import (
    DivisionInternal,
    DivisionInternalCreate,
    DivisionInternalUpdate,
)


class DivisionRepository:
    def __init__(self):
        self.storage = get_storage("divisions")

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now(timezone.utc).isoformat()

    async def findAll(
        self,
        is_active: Optional[bool] = None,
        name: Optional[str] = None,
    ) -> List[DivisionInternal]:
        return await self.storage.findAll(is_active=is_active, name=name)

    async def findById(self, id: int) -> Optional[DivisionInternal]:
        return await self.storage.findById(id)

    async def findByName(self, name: str) -> Optional[DivisionInternal]:
        return await self.storage.findByName(name)

    async def create(self, data: DivisionInternalCreate) -> DivisionInternal:
        if data.is_active is None:
            data.is_active = True
        return await self.storage.create(data)

    async def update(self, id: int, update_data: DivisionInternalUpdate) -> Optional[DivisionInternal]:
        return await self.storage.update(id, update_data)

    async def delete(self, id: int) -> Optional[DivisionInternal]:
        # Soft delete - set isActive to false
        return await self.storage.update(id, DivisionInternalUpdate(is_active=False))

    async def hardDelete(self, id: int) -> bool:
        return await self.storage.delete(id)


division_repository = DivisionRepository()
