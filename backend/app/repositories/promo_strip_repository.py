from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from app.models.daos_flat import PromoStripsInternal, PromoStripsInternalCreate, PromoStripsInternalUpdate

from app.db.storage_factory import get_storage


class PromoStripRepository:
    def __init__(self):
        self.storage = get_storage("promoStrips")

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now(timezone.utc).isoformat()

    async def findAll(self) -> List[PromoStripsInternal]:
        return await self.storage.findAll()

    async def findById(self, id: str) -> Optional[PromoStripsInternal]:
        return await self.storage.findById(id)

    async def create(self, data: PromoStripsInternalCreate) -> PromoStripsInternal:
        if data.isActive is None:
            data.isActive = True
        return await self.storage.create(data)

    async def update(self, id: str, update_data: PromoStripsInternalUpdate) -> PromoStripsInternal:
        return await self.storage.update(id, update_data)

    async def delete(self, id: str) -> bool:
        return await self.storage.delete(id)


promo_strip_repository = PromoStripRepository()
