from app.models.daos import NotificationInternal
from typing import TYPE_CHECKING, Any
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.db.storage_factory import get_storage

if TYPE_CHECKING:
    from app.models.daos import NotificationInternalCreate, NotificationInternalUpdate
    

IST = timezone(timedelta(hours=5, minutes=30))


class NotificationRepository:
    def __init__(self):
        self.storage = get_storage("notifications")

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format with IST timezone"""
        return datetime.now(IST).isoformat()

    async def findAll(self, filters: dict = None) -> List[NotificationInternal]:
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

        if filters.start_date:
            start = datetime.fromisoformat(filters.start_date.replace("Z", "+00:00"))
            notifications = [
                n
                for n in notifications
                if n.created_at and datetime.fromisoformat(n.created_at.replace("Z", "+00:00")) >= start
            ]
        if filters.end_date:
            end = datetime.fromisoformat(filters.end_date.replace("Z", "+00:00"))
            end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
            notifications = [
                n for n in notifications if n.created_at and datetime.fromisoformat(n.created_at.replace("Z", "+00:00")) <= end
            ]

        sorted_notifs = sorted(notifications, key=lambda x: x.created_at or "", reverse=True)
        return [NotificationInternal.model_validate(n, from_attributes=True) for n in sorted_notifs]

    async def findById(self, id: str) -> Optional[NotificationInternal]:
        result = await self.storage.findById(id)
        if not result: return None
        return NotificationInternal.model_validate(result, from_attributes=True)

    async def create(self, notification_data: 'NotificationInternalCreate') -> NotificationInternal:
        if notification_data.created_at is None:
            notification_data.created_at = self._get_timestamp()
        if notification_data.updated_at is None:
            notification_data.updated_at = self._get_timestamp()
        
        result = await self.storage.create(notification_data)
        return NotificationInternal.model_validate(result, from_attributes=True)

    async def update(self, id: str, update_data: 'NotificationInternalUpdate') -> NotificationInternal:
        update_data.updated_at = self._get_timestamp()
        result = await self.storage.update(id, update_data)
        return NotificationInternal.model_validate(result, from_attributes=True)

    async def acknowledge(self, id: str) -> NotificationInternal:
        from app.models.daos import NotificationInternalUpdate
        return await self.update(id, NotificationInternalUpdate(is_acknowledged=True))

    async def markAsRead(self, id: str) -> NotificationInternal:
        from app.models.daos import NotificationInternalUpdate
        return await self.update(id, NotificationInternalUpdate(is_read=True))

    async def markAllAsRead(self) -> int:
        """Mark all unread notifications as read and acknowledged"""
        from app.models.daos import NotificationInternalUpdate, NotificationFilter
        update_model = NotificationInternalUpdate(is_read=True, is_acknowledged=True, updated_at=self._get_timestamp())
        unread_notifs = await self.storage.findAll(NotificationFilter(is_read=False))
        count1 = 0
        for n in unread_notifs:
            await self.storage.update(n.id, update_model)
            count1 += 1
            
        unack_notifs = await self.storage.findAll(NotificationFilter(is_acknowledged=False))
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
