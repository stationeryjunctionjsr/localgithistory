from typing import List, Optional

from app.db.storage_factory import get_storage
from app.models.daos_flat import SchemeInternal

class SchemeRepository:
    """Discount schemes for Business Segment (wholesaler) users."""

    def __init__(self):
        self.storage = get_storage("schemes")

    async def findAll(
        self,
        id: Optional[str] = None,
        name: Optional[str] = None,
        is_active: Optional[bool] = None,
        code: Optional[str] = None
    ) -> List[SchemeInternal]:
        if id is not None:
            record = await self.storage.findById(id)
            return [record] if record else []
        schemes = await self.storage.findAll(is_active=is_active, code=code)
        if name is not None:
            schemes = [s for s in schemes if s.name == name]
        return schemes

    async def findById(self, id: str) -> Optional[SchemeInternal]:
        return await self.storage.findById(id)

    async def findActiveForBusiness(self) -> List[SchemeInternal]:
        """Return active schemes targeted at business/wholesaler users."""
        return await self.storage.findAll(is_active=True)

    async def findOne(
        self,
        id: Optional[str] = None,
        name: Optional[str] = None,
        is_active: Optional[bool] = None,
        code: Optional[str] = None
    ) -> Optional[SchemeInternal]:
        if id is not None:
            return await self.storage.findById(id)
        if code is not None:
            return await self.storage.findByCode(code)
        schemes = await self.findAll(name=name, is_active=is_active)
        return schemes[0] if schemes else None


scheme_repository = SchemeRepository()
