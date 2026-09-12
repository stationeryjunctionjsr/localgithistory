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
        if query.get("status"):
            filtered = [n for n in filtered if n.get("status") == query.get("status")]

        if query.get("startDate"):
            start_date = datetime.fromisoformat(query.get("startDate"))
            filtered = [
                n
                for n in filtered
                if datetime.fromisoformat(n.get("createdAt", "").replace("Z", "+00:00").replace("+00:00", ""))
                >= start_date
            ]

        if query.get("endDate"):
            end_date = datetime.fromisoformat(query.get("endDate"))
            filtered = [
                n
                for n in filtered
                if datetime.fromisoformat(n.get("createdAt", "").replace("Z", "+00:00").replace("+00:00", ""))
                <= end_date
            ]

        return filtered

    async def findById(self, id: str):
        """Get a push notification by ID"""
        return await self.storage.findById(id)

    async def create(self, notification_data: Any):
        """Create a new push notification"""
        notification = {
            "title": notification_data.get("title", ""),
            "message": notification_data.get("message", ""),
            "link": notification_data.get("link", ""),
            "image": notification_data.get("image"),
            "status": notification_data.get("status", "published"),
            "scheduledFor": notification_data.get("scheduledFor"),
            "deliveredCount": 0,
            "readCount": 0,
            "userSegment": notification_data.get("userSegment", "all"),
            "userBehavior": notification_data.get("userBehavior", "none"),
            "createdBy": notification_data.get("createdBy"),
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
                notification["deliveredCount"] = stats.get("deliveredCount", notification.get("deliveredCount", 0))

            if "targetedUserIds" in stats:
                notification["targetedUserIds"] = stats.get("targetedUserIds", [])

            if userId:
                # Idempotent read tracking
                if "readByUserIds" not in notification:
                    notification["readByUserIds"] = []

                if userId not in notification["readByUserIds"]:
                    notification["readByUserIds"].append(userId)
                    notification["readCount"] = len(notification["readByUserIds"])
            elif "readCount" in stats:
                # Fallback for manual updates or legacy logic
                notification["readCount"] = stats.get("readCount", notification.get("readCount", 0))

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
        elif subscription and subscription.get("endpoint"):
            matches = await self.device_storage.findAll({"endpoint": subscription.get("endpoint")})
            existing_device = matches[0] if matches else None
        else:
            existing_device = None

        if existing_device:
            # Update existing device
            existing_device["userId"] = userId
            if subscription:
                existing_device["subscription"] = subscription
                existing_device["endpoint"] = subscription.get("endpoint")
                existing_device["keys"] = subscription.get("keys", {})
            if expoToken is not None:
                existing_device["expoToken"] = expoToken
            existing_device["updatedAt"] = datetime.now(timezone.utc).isoformat()
            return await self.device_storage.update(existing_device["_id"], existing_device)
        else:
            # Create new device
            device = {
                "userId": userId,
                "endpoint": subscription.get("endpoint") if subscription else None,
                "keys": subscription.get("keys", {}) if subscription else {},
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
                "userId": getattr(d, "userId", None),
                "endpoint": getattr(d, "endpoint", None),
                "keys": getattr(d, 'keys', {}),
                "expoToken": getattr(d, "expoToken", None),
                "_id": getattr(d, "_id", None),
            }
            for d in devices
        ]

    async def getDeviceSubscriptionsByUser(self, userId: str) -> List[Dict]:
        """Get device subscriptions for a specific user"""
        user_devices = await self.device_storage.findAll({"userId": userId})
        return [
            {
                "endpoint": getattr(d, "endpoint", None),
                "keys": getattr(d, 'keys', {}),
                "expoToken": getattr(d, "expoToken", None),
                "_id": getattr(d, "_id", None),
            }
            for d in user_devices
        ]

    async def removeDeviceSubscription(self, device_id: str):
        """Remove a device subscription"""
        return await self.device_storage.delete(device_id)


push_notification_repository = PushNotificationRepository()
