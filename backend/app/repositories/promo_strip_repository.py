from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.db.storage_factory import get_storage


class PromoStripRepository:
    def __init__(self):
        self.storage = get_storage("promoStrips")

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now(timezone.utc).isoformat()

    async def findAll(self) -> List[Dict]:
        return await self.storage.findAll()

    async def findById(self, id: str) -> Optional[Dict]:
        return await self.storage.findById(id)

    async def create(self, data: Dict) -> Dict:
        strip = {
            "text": data["text"],
            "isActive": data.get("isActive", True),
            "createdAt": self._get_timestamp(),
            "updatedAt": self._get_timestamp(),
        }
        return await self.storage.create(strip)

    async def update(self, id: str, update_data: Dict) -> Dict:
        updates = {**update_data, "updatedAt": self._get_timestamp()}
        return await self.storage.update(id, updates)

    async def delete(self, id: str) -> Dict:
        return await self.storage.delete(id)


promo_strip_repository = PromoStripRepository()
