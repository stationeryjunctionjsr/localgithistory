from typing import Any
import datetime
from datetime import timezone
import uuid
from typing import List, Optional
from app.models.daos_flat import CustomerSegmentInternal

from app.db.storage_factory import get_storage


class CustomerSegmentsRepository:
    def __init__(self):
        self.storage = get_storage("customerSegments")

    async def get_all(self, segment_type: Optional[str] = None) -> List[CustomerSegmentInternal]:
        query = {}
        if segment_type:
            query = {"type": segment_type}
        return await self.storage.findAll(query)

    async def get_by_id(self, segment_id: str) -> Optional[CustomerSegmentInternal]:
        return await self.storage.findById(segment_id)

    async def create(self, data: Any) -> CustomerSegmentInternal:
        now = datetime.datetime.now(timezone.utc).isoformat()
        # timestamps are handled in DAO
        return await self.storage.create(data)

    async def update(self, segment_id: str, data: Any) -> Optional[CustomerSegmentInternal]:
        # timestamps are handled in DAO
        return await self.storage.update(segment_id, data)

    async def delete(self, segment_id: str) -> bool:
        return await self.storage.delete(segment_id)


customer_segments_repository = CustomerSegmentsRepository()
