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

    async def findActive(self, zone_id: Optional[str] = None) -> List[PromoStripsInternal]:
        """
        Return active promo strips, optionally filtered by zone.

        zone_id = None  -> wholesaler / no pincode: show strips that have no zone
                          restriction (zoneIds is None/empty = global strips).
        zone_id = "42" -> retail with pincode: show strips that either have no
                          zone restriction OR explicitly include this zone.
        """
        strips = await self.storage.findAll()
        result = []
        for s in strips:
            if not (s.isActive if s.isActive is not None else True):
                continue
            if zone_id:
                # zone_id given: show global strips (no zoneIds) OR zone-matched strips
                if s.zone_ids and zone_id not in s.zone_ids:
                    continue
            else:
                # No zone_id (wholesaler / guest without pincode): show only global strips
                if s.zone_ids:
                    continue
            result.append(s)
        return result

    async def create(self, data: PromoStripsInternalCreate) -> PromoStripsInternal:
        if data.isActive is None:
            data.isActive = True
        return await self.storage.create(data)

    async def update(self, id: str, update_data: PromoStripsInternalUpdate) -> PromoStripsInternal:
        return await self.storage.update(id, update_data)

    async def delete(self, id: str) -> bool:
        return await self.storage.delete(id)


promo_strip_repository = PromoStripRepository()
