import datetime
import uuid
from typing import Dict, List, Optional

from app.db.storage_factory import get_storage


class CustomerSegmentsRepository:
    def __init__(self):
        self.storage = get_storage("customerSegments")

    async def get_all(self, segment_type: Optional[str] = None) -> List[Dict]:
        query = {}
        if segment_type:
            query = {"type": segment_type}
        return await self.storage.findAll(query)

    async def get_by_id(self, segment_id: str) -> Optional[Dict]:
        return await self.storage.findById(segment_id)

    async def create(self, data: Dict) -> Dict:
        now = datetime.datetime.now(timezone.utc).isoformat()
        if "_id" not in data and "id" not in data:
            data["_id"] = str(uuid.uuid4())
        data["createdAt"] = data.get("createdAt", now)
        data["updatedAt"] = data.get("updatedAt", now)
        return await self.storage.create(data)

    async def update(self, segment_id: str, data: Dict) -> Optional[Dict]:
        data["updatedAt"] = datetime.datetime.now(timezone.utc).isoformat()
        return await self.storage.update(segment_id, data)

    async def delete(self, segment_id: str) -> bool:
        return await self.storage.delete(segment_id)


customer_segments_repository = CustomerSegmentsRepository()
