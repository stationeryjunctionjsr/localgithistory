from typing import Any
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

    async def findAll(self, filters: Any = None) -> List[Dict]:
        if filters is None:
            from app.models.daos import NotificationFilter
            filters = NotificationFilter()

        # Build DB query to offload exact filtering
        db_query = {}
        if filters.userId:
            db_query["userId"] = filters.userId
        if filters.isRead is not None:
            db_query["isRead"] = filters.isRead
        if filters.isAcknowledged is not None:
            db_query["isAcknowledged"] = filters.isAcknowledged
        if filters.type:
            db_query["type"] = filters.type

        notifications = await self.storage.findAll(db_query)

        if filters.startDate:
            start = datetime.fromisoformat(filters.startDate.replace("Z", "+00:00"))
            notifications = [
                n
                for n in notifications
                if n.createdAt and datetime.fromisoformat(n.createdAt.replace("Z", "+00:00")) >= start
            ]
        if filters.endDate:
            end = datetime.fromisoformat(filters.endDate.replace("Z", "+00:00"))
            end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
            notifications = [
                n for n in notifications if n.createdAt and datetime.fromisoformat(n.createdAt.replace("Z", "+00:00")) <= end
            ]

        return sorted(notifications, key=lambda x: x.createdAt or "", reverse=True)

    async def findById(self, id: str) -> Optional[Dict]:
        return await self.storage.findById(id)

    async def create(self, notification_data: Any) -> Dict:
        if notification_data.createdAt is None:
            notification_data.createdAt = self._get_timestamp()
        if notification_data.updatedAt is None:
            notification_data.updatedAt = self._get_timestamp()
        return await self.storage.create(notification_data)

    async def update(self, id: str, update_data: Any) -> Dict:
        update_data.updatedAt = self._get_timestamp()
        return await self.storage.update(id, update_data)

    async def acknowledge(self, id: str) -> Dict:
        from app.models.daos import NotificationInternalUpdate
        return await self.update(id, NotificationInternalUpdate(isAcknowledged=True))

    async def markAsRead(self, id: str) -> Dict:
        from app.models.daos import NotificationInternalUpdate
        return await self.update(id, NotificationInternalUpdate(isRead=True))

    async def markAllAsRead(self) -> int:
        """Mark all unread notifications as read and acknowledged"""
        from app.models.daos import NotificationInternalUpdate, NotificationFilter
        update_model = NotificationInternalUpdate(isRead=True, isAcknowledged=True, updatedAt=self._get_timestamp())
        unread_notifs = await self.storage.findAll(NotificationFilter(isRead=False))
        count1 = 0
        for n in unread_notifs:
            await self.storage.update(n.id, update_model)
            count1 += 1
            
        unack_notifs = await self.storage.findAll(NotificationFilter(isAcknowledged=False))
        count2 = 0
        for n in unack_notifs:
            if n.id not in [u.id for u in unread_notifs]:
                await self.storage.update(n.id, update_model)
                count2 += 1
                
        return count1 + count2

    async def delete(self, id: str) -> bool:
        return await self.storage.delete(id)

    def _generate_id(self) -> str:
        import random

        return datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(100000, 999999))


notification_repository = NotificationRepository()
