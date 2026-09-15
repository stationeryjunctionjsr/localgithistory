from typing import Any
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.db.storage_factory import get_storage


class CoachMarkRepository:
    def __init__(self):
        self.storage = get_storage("coachMarks")

    def _get_timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    async def findAll(self) -> List[Dict]:
        return await self.storage.findAll()

    async def findById(self, id: str) -> Optional[Dict]:
        return await self.storage.findById(id)

    async def findByAnchorId(self, anchor_id: str) -> Optional[Dict]:
        marks = await self.storage.findAll()
        for mark in marks:
            if "anchorId" in mark and mark["anchorId"] == anchor_id:
                return mark
        return None

    async def create(self, data: Any) -> Dict:
        mark = {
            **data,
            "isActive": (data.isActive if data.isActive is not None else True),
            "createdAt": self._get_timestamp(),
            "updatedAt": self._get_timestamp(),
        }
        return await self.storage.create(mark)

    async def update(self, id: str, update_data: Any) -> Dict:
        updates = {**update_data, "updatedAt": self._get_timestamp()}
        return await self.storage.update(id, updates)

    async def delete(self, id: str) -> Dict:
        return await self.storage.delete(id)


coach_mark_repository = CoachMarkRepository()
