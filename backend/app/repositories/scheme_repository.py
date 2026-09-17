from typing import Any, Dict, List, Optional

from app.db.storage_factory import get_storage
from app.models.daos_flat import SchemeInternal

class SchemeRepository:
    """Discount schemes for Business Segment (wholesaler) users."""

    def __init__(self):
        self.storage = get_storage("schemes")

    async def findAll(self, query: Optional[Dict] = None) -> List[SchemeInternal]:
        return await self.storage.findAll(query or {})

    async def findById(self, id: str) -> Optional[SchemeInternal]:
        return await self.storage.findById(id)

    async def findActiveForBusiness(self) -> List[SchemeInternal]:
        """Return active schemes targeted at business/wholesaler users."""
        return await self.storage.findAll({"isActive": True})

    async def findOne(self, query: Any) -> Optional[SchemeInternal]:
        return await self.storage.findOne(query)


scheme_repository = SchemeRepository()
