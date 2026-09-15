from typing import Any
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.db.storage_factory import get_storage


class PushNotificationRepository:
    def __init__(self):
        self.storage = get_storage("pushNotifications")
        self.device_storage = get_storage("deviceSubscriptions")

    async def findAll(self, query: Optional[Dict] = None):
        """Get all push notifications with optional filters"""
        all_notifications = await self.storage.findAll()

        if not query:
            return all_notifications

        filtered = all_notifications
        if query["status"] if "status" in query else None:
            filtered = [n for n in filtered if (n["status"] if "status" in n else None) == (query["status"] if "status" in query else None)]

        if query["startDate"] if "startDate" in query else None:
            start_date = datetime.fromisoformat(query["startDate"] if "startDate" in query else None)
            filtered = [
                n
                for n in filtered
                if datetime.fromisoformat(n["createdAt"] if "createdAt" in n else "".replace("Z", "+00:00").replace("+00:00", ""))
                >= start_date
            ]

        if query["endDate"] if "endDate" in query else None:
            end_date = datetime.fromisoformat(query["endDate"] if "endDate" in query else None)
            filtered = [
                n
                for n in filtered
                if datetime.fromisoformat(n["createdAt"] if "createdAt" in n else "".replace("Z", "+00:00").replace("+00:00", ""))
                <= end_date
            ]

        return filtered

    async def findById(self, id: str):
        """Get a push notification by ID"""
        return await self.storage.findById(id)

    async def create(self, notification_data: Any):
        """Create a new push notification"""
        notification = {
            "title": notification_data["title"] if "title" in notification_data else "",
            "message": notification_data["message"] if "message" in notification_data else "",
            "link": notification_data["link"] if "link" in notification_data else "",
            "image": notification_data["image"] if "image" in notification_data else None,
            "status": notification_data["status"] if "status" in notification_data else "published",
            "scheduledFor": notification_data["scheduledFor"] if "scheduledFor" in notification_data else None,
            "deliveredCount": 0,
            "readCount": 0,
            "userSegment": notification_data["userSegment"] if "userSegment" in notification_data else "all",
            "userBehavior": notification_data["userBehavior"] if "userBehavior" in notification_data else "none",
            "createdBy": notification_data["createdBy"] if "createdBy" in notification_data else None,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        }
        return await self.storage.create(notification)

    async def update(self, id: str, update_data: Any):
        """Update a push notification"""
        update_data.updatedAt = datetime.now(timezone.utc).isoformat()
        return await self.storage.update(id, update_data)

    async def delete(self, id: str):
        """Delete a push notification"""
        return await self.storage.delete(id)

    async def updateStats(self, id: str, stats: Any, userId: Optional[str] = None):
        """Update delivery/read statistics for a notification"""
        notification = await self.findById(id)
        if notification:
            if "deliveredCount" in stats:
                notification["deliveredCount"] = stats["deliveredCount"] if "deliveredCount" in stats else (notification["deliveredCount"] if "deliveredCount" in notification else 0)

            if "targetedUserIds" in stats:
                notification["targetedUserIds"] = stats["targetedUserIds"] if "targetedUserIds" in stats else []

            if userId:
                # Idempotent read tracking
                if "readByUserIds" not in notification:
                    notification["readByUserIds"] = []

                if userId not in notification["readByUserIds"]:
                    notification["readByUserIds"].append(userId)
                    notification["readCount"] = len(notification["readByUserIds"])
            elif "readCount" in stats:
                # Fallback for manual updates or legacy logic
                notification["readCount"] = stats["readCount"] if "readCount" in stats else (notification["readCount"] if "readCount" in notification else 0)

            notification["updatedAt"] = datetime.now(timezone.utc).isoformat()
            return await self.storage.update(id, notification)
        return None

    async def registerDevice(
        self, userId: Optional[str], subscription: Optional[Dict], expoToken: Optional[str] = None
    ):
        """Register a device for push notifications (web subscription or Expo push token)"""
        # Look up only the matching device — no full table scan
        if expoToken:
            matches = await self.device_storage.findAll({"expoToken": expoToken})
            existing_device = matches[0] if matches else None
        elif subscription and ('endpoint' in subscription and subscription['endpoint']):
            matches = await self.device_storage.findAll({"endpoint": subscription['endpoint']})
            existing_device = matches[0] if matches else None
        else:
            existing_device = None

        if existing_device:
            # Update existing device
            existing_device["userId"] = userId
            if subscription:
                existing_device["subscription"] = subscription
                existing_device["endpoint"] = subscription['endpoint'] if 'endpoint' in subscription else None
                existing_device["keys"] = subscription['keys'] if 'keys' in subscription else {}
            if expoToken is not None:
                existing_device["expoToken"] = expoToken
            existing_device["updatedAt"] = datetime.now(timezone.utc).isoformat()
            return await self.device_storage.update(existing_device["_id"], existing_device)
        else:
            # Create new device
            device = {
                "userId": userId,
                "endpoint": (subscription['endpoint'] if 'endpoint' in subscription else None) if subscription else None,
                "keys": (subscription['keys'] if 'keys' in subscription else {}) if subscription else {},
                "subscription": subscription or {},
                "expoToken": expoToken,
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "updatedAt": datetime.now(timezone.utc).isoformat(),
            }
            return await self.device_storage.create(device)

    async def getAllDeviceSubscriptions(self) -> List[Dict]:
        """Get all device subscriptions"""
        devices = await self.device_storage.findAll()
        # Return subscriptions including expoToken for mobile devices
        return [
            {
                "userId": d.userId,
                "endpoint": d.endpoint,
                "keys": (d.keys if d.keys is not None else {}),
                "expoToken": d.expoToken,
                "_id": d._id,
            }
            for d in devices
        ]

    async def getDeviceSubscriptionsByUser(self, userId: str) -> List[Dict]:
        """Get device subscriptions for a specific user"""
        user_devices = await self.device_storage.findAll({"userId": userId})
        return [
            {
                "endpoint": d.endpoint,
                "keys": (d.keys if d.keys is not None else {}),
                "expoToken": d.expoToken,
                "_id": d._id,
            }
            for d in user_devices
        ]

    async def removeDeviceSubscription(self, device_id: str):
        """Remove a device subscription"""
        return await self.device_storage.delete(device_id)


push_notification_repository = PushNotificationRepository()

