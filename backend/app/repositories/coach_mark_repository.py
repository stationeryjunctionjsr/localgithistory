from typing import Any
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.db.storage_factory import get_storage
from app.models.daos_flat import CoachMarkInternal, CoachMarkInternalCreate, CoachMarkInternalUpdate


class CoachMarkRepository:
    def __init__(self):
        self.storage = get_storage("coachMarks")

    def _get_timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    async def findAll(self) -> List[CoachMarkInternal]:
        return await self.storage.findAll()

    async def findById(self, id: str) -> Optional[CoachMarkInternal]:
        return await self.storage.findById(id)

    async def findByAnchorId(self, anchor_id: str) -> Optional[CoachMarkInternal]:
        marks = await self.storage.findAll()
        for mark in marks:
            if mark.anchor_id == anchor_id:
                return mark
        return None

    async def create(self, data: CoachMarkInternalCreate) -> CoachMarkInternal:
        if data.is_active is None:
            data.is_active = True
        return await self.storage.create(data)

    async def update(self, id: str, update_data: CoachMarkInternalUpdate) -> CoachMarkInternal:
        return await self.storage.update(id, update_data)

    async def delete(self, id: str) -> bool:
        return await self.storage.delete(id)


coach_mark_repository = CoachMarkRepository()
