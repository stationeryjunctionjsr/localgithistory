import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.repositories.order_repository import order_repository
from app.repositories.push_notification_repository import push_notification_repository
from app.repositories.user_repository import user_repository
from app.utils.logger import logger

try:
    import pywebpush

    WEB_PUSH_AVAILABLE = True
except ImportError:
    WEB_PUSH_AVAILABLE = False
    logger.warning("pywebpush not installed. Push notifications will not work.")

try:
    import requests as http_requests

    HTTP_AVAILABLE = True
except ImportError:
    HTTP_AVAILABLE = False


class PushNotificationService:
    def __init__(self):
        # Configure VAPID keys (set in environment variables)
        self.vapid_public_key = os.getenv("VAPID_PUBLIC_KEY", "")
        self.vapid_private_key = os.getenv("VAPID_PRIVATE_KEY", "")
        self.vapid_email = os.getenv("VAPID_EMAIL", "mailto:your-email@example.com")
        self.expo_push_url = "https://exp.host/--/api/v2/push/send"

    def _send_expo_push(self, expo_tokens: list, notification: Dict) -> int:
        """Send push notifications to Expo mobile devices in batches of 100."""
        if not expo_tokens or not HTTP_AVAILABLE:
            return 0

        messages = [
            {
                "to": token,
                "title": notification.get("title", ""),
                "body": notification.get("message", ""),
                "data": {
                    "url": notification.get("link") or "/",
                    "notificationId": notification.get("_id"),
                },
                "sound": "default",
                "channelId": "default",
                **({"image": notification["image"]} if notification.get("image") else {}),
            }
            for token in expo_tokens
        ]

        delivered = 0
        # Expo recommends batches of ≤ 100
        batch_size = 100
        for i in range(0, len(messages), batch_size):
            batch = messages[i : i + batch_size]
            try:
                resp = http_requests.post(
                    self.expo_push_url,
                    json=batch,
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                    timeout=15,
                )
                if resp.status_code == 200:
                    data = resp.json().get("data", [])
                    for item in data:
                        if item.get("status") == "ok":
                            delivered += 1
                        else:
                            logger.warning("[Expo Push] Ticket error: %s", item)
                else:
                    logger.warning("[Expo Push] HTTP %s: %s", resp.status_code, resp.text[:200])
            except Exception as e:
                logger.error("[Expo Push] Batch send failed: %s", str(e), exc_info=True)

        return delivered

    async def send_to_all_devices(self, notification: Dict):
        """Send push notification to registered devices based on targeting criteria (Optimized)"""
        try:
            # 1. Fetch all registered devices first
            all_devices = await push_notification_repository.device_storage.findAll()

            target_segment = notification.get("userSegment", "all")
            target_behavior = notification.get("userBehavior", "none")

            # Reference date for behavior calculation
            reference_date_str = notification.get("scheduledFor")
            if reference_date_str:
                reference_date = datetime.fromisoformat(reference_date_str.replace("Z", "+00:00"))
            else:
                reference_date = datetime.now(timezone.utc).replace(tzinfo=None)

            # Get unique users who have registered a device
            downloaded_user_ids = set()
            has_guest_download = False
            for d in all_devices:
                uid = d.get("userId")
                if uid:
                    downloaded_user_ids.add(str(uid))
                else:
                    has_guest_download = True

            targeted_user_ids = set()
            downloaded_user_ids_list = list(downloaded_user_ids)
            
            # Process users in chunks to prevent OOM
            CHUNK_SIZE = 500
            for i in range(0, len(downloaded_user_ids_list), CHUNK_SIZE):
                chunk_uids = downloaded_user_ids_list[i:i + CHUNK_SIZE]
                
                # Fetch users and orders only for this chunk
                chunk_users = await user_repository.findAll({"allowed_ids": chunk_uids})
                chunk_orders = await order_repository.findAll({"user": {"$in": chunk_uids}})
                
                user_map = {str(u.get("_id")): u for u in chunk_users}
                
                # Group orders by user, filtering by reference date
                orders_per_user = {}
                for order in chunk_orders:
                    try:
                        o_date = datetime.fromisoformat(order.get("createdAt", "").replace("Z", "+00:00")).replace(tzinfo=None)
                        if o_date > reference_date:
                            continue
                    except Exception as exc:
                        logger.warning("Failed to parse createdAt for order %s: %s", order.get("_id"), exc)
                        continue

                    uid = str(order.get("user"))
                    if uid not in orders_per_user:
                        orders_per_user[uid] = []
                    orders_per_user[uid].append(order)
                
                # Filter logic for this chunk
                for u_id in chunk_uids:
                    user = user_map.get(u_id)
                    user_orders = orders_per_user.get(u_id, [])
                    if await self.is_user_targeted(
                        u_id, notification, user=user, user_orders=user_orders, reference_date=reference_date
                    ):
                        targeted_user_ids.add(u_id)

            targeted_guest_match = False
            # Check Guest Users (userId is None)
            if has_guest_download:
                # Segment filter: Guests only match if segment is 'all'
                if target_segment == "all":
                    # Behavior filter: Guests only match 'behavior1' (no orders) or 'none' (all)
                    if target_behavior == "none" or target_behavior == "behavior1":
                        targeted_guest_match = True

            # 3. Filter targeted devices
            targeted_devices = []
            if target_segment == "all" and target_behavior == "none":
                targeted_devices = all_devices
            else:
                for d in all_devices:
                    uid = d.get("userId")
                    if uid:
                        if str(uid) in targeted_user_ids:
                            targeted_devices.append(d)
                    elif targeted_guest_match:
                        targeted_devices.append(d)

            # 4. Send via dual channel: web push for browser devices, Expo for native mobile
            delivered_count = 0

            # --- 4a. Web Push (browser/PWA) devices ---
            if WEB_PUSH_AVAILABLE:
                web_devices = [d for d in targeted_devices if d.get("endpoint") and d.get("keys")]
                for device in web_devices:
                    try:
                        payload = {
                            "title": notification.get("title", ""),
                            "body": notification.get("message", ""),
                            "icon": notification.get("image") or "/logo192.png",
                            "badge": "/logo192.png",
                            "image": notification.get("image") or None,
                            "data": {"url": notification.get("link") or "/", "notificationId": notification.get("_id")},
                            "tag": notification.get("_id", ""),
                            "requireInteraction": False,
                        }
                        pywebpush.webpush(
                            subscription_info={"endpoint": device.get("endpoint"), "keys": device.get("keys", {})},
                            data=json.dumps(payload),
                            vapid_private_key=self.vapid_private_key,
                            vapid_claims={"sub": self.vapid_email},
                        )
                        delivered_count += 1
                    except Exception as e:
                        logger.error("Failed to send to web device %s: %s", device.get("_id"), str(e))
                        if "410" in str(e) or "404" in str(e):
                            await push_notification_repository.removeDeviceSubscription(device.get("_id"))

            # --- 4b. Expo Push (native mobile) devices ---
            expo_tokens = [d.get("expoToken") for d in targeted_devices if d.get("expoToken")]
            delivered_count += self._send_expo_push(expo_tokens, notification)

            # Update stats and persist targeted user list for strict ownership validation
            update_data = {"deliveredCount": delivered_count, "targetedUserIds": list(targeted_user_ids)}
            await push_notification_repository.updateStats(notification.get("_id"), update_data)

            return {"deliveredCount": delivered_count, "totalDevices": len(targeted_devices)}
        except Exception as e:
            logger.error("Error in sending targeted push: %s", str(e), exc_info=True)
            raise

    async def send_to_user(self, user_id: str, notification: Dict):
        """Send push notification to a specific user's devices"""
        try:
            devices = await push_notification_repository.getDeviceSubscriptionsByUser(user_id)
            delivered_count = 0

            # --- Web Push (browser/PWA) devices ---
            if WEB_PUSH_AVAILABLE:
                web_devices = [d for d in devices if d.get("endpoint") and d.get("keys")]
                for device in web_devices:
                    try:
                        payload = {
                            "title": notification.get("title", ""),
                            "body": notification.get("message", ""),
                            "icon": notification.get("image") or "/logo192.png",
                            "badge": "/logo192.png",
                            "image": notification.get("image") or None,
                            "data": {"url": notification.get("link") or "/", "notificationId": notification.get("_id")},
                            "tag": notification.get("_id", ""),
                        }
                        pywebpush.webpush(
                            subscription_info={"endpoint": device.get("endpoint"), "keys": device.get("keys", {})},
                            data=json.dumps(payload),
                            vapid_private_key=self.vapid_private_key,
                            vapid_claims={"sub": self.vapid_email},
                        )
                        delivered_count += 1
                    except Exception as e:
                        logger.error("Failed to send to web device %s: %s", device.get("_id"), str(e))
                        if "410" in str(e) or "404" in str(e):
                            await push_notification_repository.removeDeviceSubscription(device.get("_id"))

            # --- Expo Push (native mobile) devices ---
            expo_tokens = [d.get("expoToken") for d in devices if d.get("expoToken")]
            delivered_count += self._send_expo_push(expo_tokens, notification)

            return {"deliveredCount": delivered_count, "totalDevices": len(devices)}
        except Exception as e:
            logger.error("Error sending push notification to user: %s", str(e), exc_info=True)
            raise

    async def is_user_targeted(
        self,
        user_id: str,
        notification: Dict,
        user: Optional[Dict] = None,
        user_orders: Optional[List[Dict]] = None,
        reference_date: Optional[datetime] = None,
    ) -> bool:
        """Check if a specific user satisfies the targeting criteria of a notification."""
        target_segment = notification.get("userSegment", "all")
        target_behavior = notification.get("userBehavior", "none")

        if not reference_date:
            reference_date_str = notification.get("scheduledFor")
            if reference_date_str:
                reference_date = datetime.fromisoformat(reference_date_str.replace("Z", "+00:00"))
            else:
                reference_date = datetime.fromisoformat(
                    notification.get("createdAt", datetime.now().isoformat()).replace("Z", "+00:00")
                )

        if not user:
            user = await user_repository.findById(user_id)
        if not user:
            return False

        # Segment check
        role_map = {"customers": "customer", "wholesalers": "wholesaler"}
        if target_segment != "all":
            if user.role != role_map.get(target_segment):
                return False

        # Behavior check
        if target_behavior and target_behavior != "none":
            behaviors = [b.strip() for b in target_behavior.split(",") if b.strip()]
            matched_any = False
            for single_behavior in behaviors:
                if single_behavior.startswith("segment_"):
                    seg_id = single_behavior[len("segment_") :]
                    from app.repositories.customer_segments_repository import customer_segments_repository

                    seg = await customer_segments_repository.get_by_id(seg_id)
                    if seg and "userIds" in seg and str(user_id) in [str(x) for x in seg["userIds"]]:
                        matched_any = True
                        break
                else:
                    if user_orders is None:
                        all_orders = await order_repository.findAll({"user": user_id})
                        user_orders = []
                        for order in all_orders:
                            try:
                                o_date = datetime.fromisoformat(order.get("createdAt").replace("Z", "+00:00"))
                                if o_date <= reference_date:
                                    user_orders.append(order)
                            except Exception as exc:
                                logger.warning(
                                    "Failed to parse createdAt for order %s of user %s: %s",
                                    order.get("_id"),
                                    user_id,
                                    exc,
                                )
                                continue

                    order_count = len(user_orders)

                    if single_behavior == "behavior1" and order_count == 0:
                        matched_any = True
                        break
                    elif single_behavior == "behavior2" and order_count == 1:
                        matched_any = True
                        break
                    elif single_behavior == "behavior3":
                        three_months_ago = reference_date - timedelta(days=90)
                        recent_orders = [
                            o
                            for o in user_orders
                            if three_months_ago
                            <= datetime.fromisoformat(o.get("createdAt").replace("Z", "+00:00"))
                            <= reference_date
                        ]
                        if len(recent_orders) >= 12:
                            matched_any = True
                            break
                    elif single_behavior == "behavior4":
                        three_months_ago = reference_date - timedelta(days=90)
                        recent_orders = [
                            o
                            for o in user_orders
                            if three_months_ago
                            <= datetime.fromisoformat(o.get("createdAt").replace("Z", "+00:00"))
                            <= reference_date
                        ]
                        if 3 < len(recent_orders) <= 9:
                            matched_any = True
                            break
            if not matched_any:
                return False

        return True


push_notification_service = PushNotificationService()
