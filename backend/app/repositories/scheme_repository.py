from typing import Any
from typing import Dict, List, Optional

from app.db.storage_factory import get_storage


class SchemeRepository:
    """Discount schemes for Business Segment (wholesaler) users."""

    def __init__(self):
        self.storage = get_storage("schemes")

    async def findAll(self, query: Optional[Dict] = None):
        return await self.storage.findAll(query or {})

    async def findById(self, id: str):
        return await self.storage.findById(id)

    async def findActiveForBusiness(self) -> List[Dict]:
        """Return active schemes targeted at business/wholesaler users."""
        all_schemes = await self.storage.findAll({"isActive": True})
        return [s for s in all_schemes if "wholesaler" in (s.applicableRoles or [])]

    async def findOne(self, query: Any):
        return await self.storage.findOne(query)


scheme_repository = SchemeRepository()
