from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.db.storage_factory import get_storage

IST = timezone(timedelta(hours=5, minutes=30))


class NotificationRepository:
    def __init__(self):
        self.storage = get_storage("notifications")

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format with IST timezone"""
        return datetime.now(IST).isoformat()

    async def findAll(self, filters: Optional[Dict] = None) -> List[Dict]:
        filters = filters or {}

        # Build DB query to offload exact filtering
        db_query = {}
        if filters["userId"] if "userId" in filters else None:
            db_query["userId"] = filters["userId"]
        if (filters["isRead"] if "isRead" in filters else None) is not None:
            db_query["isRead"] = filters["isRead"]
        if filters["type"] if "type" in filters else None:
            db_query["type"] = filters["type"]

        notifications = await self.storage.findAll(db_query)

        if filters["startDate"] if "startDate" in filters else None:
            start = datetime.fromisoformat(filters["startDate"].replace("Z", "+00:00"))
            notifications = [
                n
                for n in notifications
                if datetime.fromisoformat((n["createdAt"] if "createdAt" in n else "").replace("Z", "+00:00")) >= start
            ]
        if filters["endDate"] if "endDate" in filters else None:
            end = datetime.fromisoformat(filters["endDate"].replace("Z", "+00:00"))
            end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
            notifications = [
                n for n in notifications if datetime.fromisoformat((n["createdAt"] if "createdAt" in n else "").replace("Z", "+00:00")) <= end
            ]

        return sorted(notifications, key=lambda x: x["createdAt"] if "createdAt" in x else "", reverse=True)

    async def findById(self, id: str) -> Optional[Dict]:
        return await self.storage.findById(id)

    async def create(self, notification_data: Any) -> Dict:
        notification = {
            "_id": self._generate_id(),
            **notification_data,
            "isRead": False,
            "isAcknowledged": False,
            "createdAt": self._get_timestamp(),
            "updatedAt": self._get_timestamp(),
        }
        return await self.storage.create(notification)

    async def update(self, id: str, update_data: Any) -> Dict:
        updates = {**update_data, "updatedAt": self._get_timestamp()}
        return await self.storage.update(id, updates)

    async def acknowledge(self, id: str) -> Dict:
        return await self.update(id, {"isAcknowledged": True})

    async def markAsRead(self, id: str) -> Dict:
        return await self.update(id, {"isRead": True})

    async def markAllAsRead(self) -> int:
        """Mark all unread notifications as read and acknowledged"""
        update_data = {"isRead": True, "isAcknowledged": True, "updatedAt": self._get_timestamp()}
        unread_notifs = await self.storage.findAll({"isRead": False})
        count1 = 0
        for n in unread_notifs:
            await self.storage.update(n["_id"], update_data)
            count1 += 1
            
        unack_notifs = await self.storage.findAll({"isAcknowledged": False})
        count2 = 0
        for n in unack_notifs:
            if n["_id"] not in [u.id for u in unread_notifs]:
                await self.storage.update(n["_id"], update_data)
                count2 += 1
                
        return count1 + count2

    async def delete(self, id: str) -> bool:
        return await self.storage.delete(id)

    def _generate_id(self) -> str:
        import random

        return datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(100000, 999999))


notification_repository = NotificationRepository()
