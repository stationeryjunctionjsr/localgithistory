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
        query = {}
        if id is not None: query["id"] = id
        if name is not None: query["name"] = name
        if is_active is not None: query["is_active"] = is_active
        if code is not None: query["code"] = code
        return await self.storage.findAll(query or None)

    async def findById(self, id: str) -> Optional[SchemeInternal]:
        return await self.storage.findById(id)

    async def findActiveForBusiness(self) -> List[SchemeInternal]:
        """Return active schemes targeted at business/wholesaler users."""
        return await self.storage.findAll({"is_active": True})

    async def findOne(
        self,
        id: Optional[str] = None,
        name: Optional[str] = None,
        is_active: Optional[bool] = None,
        code: Optional[str] = None
    ) -> Optional[SchemeInternal]:
        query = {}
        if id is not None: query["id"] = id
        if name is not None: query["name"] = name
        if is_active is not None: query["is_active"] = is_active
        if code is not None: query["code"] = code
        return await self.storage.findOne(query or None)


scheme_repository = SchemeRepository()
