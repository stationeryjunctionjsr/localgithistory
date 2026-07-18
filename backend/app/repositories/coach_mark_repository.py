from datetime import datetime
from typing import Dict, List, Optional

from app.db.storage_factory import get_storage


class CoachMarkRepository:
    def __init__(self):
        self.storage = get_storage("coachMarks")

    def _get_timestamp(self) -> str:
        return datetime.utcnow().isoformat()

    async def findAll(self) -> List[Dict]:
        return await self.storage.findAll()

    async def findById(self, id: str) -> Optional[Dict]:
        return await self.storage.findById(id)

    async def findByAnchorId(self, anchor_id: str) -> Optional[Dict]:
        marks = await self.storage.findAll()
        for mark in marks:
            if mark.get("anchorId") == anchor_id:
                return mark
        return None

    async def create(self, data: Dict) -> Dict:
        mark = {
            **data,
            "isActive": data.get("isActive", True),
            "createdAt": self._get_timestamp(),
            "updatedAt": self._get_timestamp(),
        }
        return await self.storage.create(mark)

    async def update(self, id: str, update_data: Dict) -> Dict:
        updates = {**update_data, "updatedAt": self._get_timestamp()}
        return await self.storage.update(id, updates)

    async def delete(self, id: str) -> Dict:
        return await self.storage.delete(id)


coach_mark_repository = CoachMarkRepository()
