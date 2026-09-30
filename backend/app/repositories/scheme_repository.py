from typing import List, Optional

from app.db.storage_factory import get_storage
from app.models.daos_flat import SchemeInternal

class SchemeRepository:
    """Discount schemes for Business Segment (wholesaler) users."""

    def __init__(self):
        self.storage = get_storage("schemes")

    async def findAll(self, **kwargs) -> List[SchemeInternal]:
        return await self.storage.findAll(kwargs)

    async def findById(self, id: str) -> Optional[SchemeInternal]:
        return await self.storage.findById(id)

    async def findActiveForBusiness(self) -> List[SchemeInternal]:
        """Return active schemes targeted at business/wholesaler users."""
        return await self.storage.findAll({"is_active": True})

    async def findOne(self, **kwargs) -> Optional[SchemeInternal]:
        return await self.storage.findOne(kwargs)


scheme_repository = SchemeRepository()
