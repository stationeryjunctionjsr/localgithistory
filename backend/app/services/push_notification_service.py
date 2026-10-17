import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from app.models.daos import OrderFilter
from app.models.order import Order
from app.repositories.order_repository import order_repository
from app.repositories.push_notification_repository import push_notification_repository
from app.models.user import User, UserFilter
from app.repositories.user_repository import user_repository
from app.models.schemas import PushNotificationPayload
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

    def _send_expo_push(self, expo_tokens: list[str], notification: PushNotificationPayload) -> int:
        """Send push notifications to Expo mobile devices in batches of 100."""
        if not expo_tokens or not HTTP_AVAILABLE:
            return 0

        messages = []
        for token in expo_tokens:
            msg = {
                "to": token,
                "title": notification.title or "",
                "body": notification.message or "",
                "data": {
                    "url": notification.link or "/",
                    "notificationId": notification.id,
                },
                "sound": "default",
                "channelId": "default",
            }
            if notification.image:
                msg["image"] = notification.image
            messages.append(msg)

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
                    resp_data = resp.json()
                    data = resp_data["data"] if "data" in resp_data else []
                    for item in data:
                        if (item["status"] if "status" in item else None) == "ok":
                            delivered += 1
                        else:
                            logger.warning("[Expo Push] Ticket error: %s", item)
                else:
                    logger.warning("[Expo Push] HTTP %s: %s", resp.status_code, resp.text[:200])
            except Exception as e:
                logger.error("[Expo Push] Batch send failed: %s", str(e), exc_info=True)

        return delivered

    async def send_to_all_devices(self, notification: PushNotificationPayload):
        """Send push notification to registered devices based on targeting criteria (Optimized)"""
        try:
            # 1. Fetch registered user IDs directly via SQL pushdown
            reg_users = await push_notification_repository.device_storage.get_distinct_registered_user_ids()
            downloaded_user_ids = reg_users.user_ids
            has_guest_download = reg_users.has_guest

            target_segment = notification.user_segment or "all"
            target_behavior = notification.user_behavior or "none"

            # Reference date for behavior calculation
            reference_date_str = notification.scheduled_for
            if reference_date_str:
                reference_date = datetime.fromisoformat(reference_date_str.replace("Z", "+00:00"))
            else:
                reference_date = datetime.now(timezone.utc).replace(tzinfo=None)

            targeted_user_ids: set[int] = set()
            downloaded_user_ids_list = list(downloaded_user_ids)
            
            # Process users in chunks to prevent OOM
            CHUNK_SIZE = 500
            for i in range(0, len(downloaded_user_ids_list), CHUNK_SIZE):
                chunk_uids = downloaded_user_ids_list[i:i + CHUNK_SIZE]
                
                # Fetch users and orders only for this chunk
                chunk_users = await user_repository.findAll(UserFilter(allowed_ids=chunk_uids))
                chunk_orders = await order_repository.findAll(
                    OrderFilter(user_ids=[str(uid) for uid in chunk_uids])
                )
                
                user_map = {u.id: u for u in chunk_users}
                
                # Group orders by user, filtering by reference date
                orders_per_user: dict[int, List[Order]] = {}
                for order in chunk_orders:
                    try:
                        o_date = (
                            order.created_at.replace(tzinfo=None)
                            if isinstance(order.created_at, datetime)
                            else datetime.fromisoformat((order.created_at or "").replace("Z", "+00:00")).replace(tzinfo=None)
                        )
                        if o_date > reference_date:
                            continue
                    except Exception as exc:
                        logger.warning("Failed to parse createdAt for order %s: %s", order.id, exc)
                        continue

                    try:
                        uid = int(order.user) if order.user is not None else None
                    except (ValueError, TypeError):
                        uid = None

                    if uid is not None:
                        if uid not in orders_per_user:
                            orders_per_user[uid] = []
                        orders_per_user[uid].append(order)
                
                # Filter logic for this chunk
                for u_id in chunk_uids:
                    user = user_map.get(u_id)
                    if not user:
                        continue
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

            # 3. Filter targeted devices via SQL pushdown
            if target_segment == "all" and target_behavior == "none":
                targeted_devices = await push_notification_repository.device_storage.findAll()
            elif not targeted_user_ids and not targeted_guest_match:
                targeted_devices = []
            else:
                targeted_devices = await push_notification_repository.device_storage.findAll(
                    user_ids=targeted_user_ids,
                    include_guests=targeted_guest_match,
                )

            # 4. Send via dual channel: web push for browser devices, Expo for native mobile
            delivered_count = 0

            # --- 4a. Web Push (browser/PWA) devices ---
            if WEB_PUSH_AVAILABLE:
                web_devices = [d for d in targeted_devices if d.endpoint and d.keys]
                for device in web_devices:
                    try:
                        payload = {
                            "title": notification.title or "",
                            "body": notification.message or "",
                            "icon": notification.image or "/logo192.png",
                            "badge": "/logo192.png",
                            "image": notification.image or None,
                            "data": {"url": notification.link or "/", "notificationId": notification.id},
                            "tag": notification.id or "",
                            "requireInteraction": False,
                        }
                        device_keys_dict = {k.key: k.value for k in (device.keys or [])}
                        pywebpush.webpush(
                            subscription_info={"endpoint": device.endpoint, "keys": device_keys_dict},
                            data=json.dumps(payload),
                            vapid_private_key=self.vapid_private_key,
                            vapid_claims={"sub": self.vapid_email},
                        )
                        delivered_count += 1
                    except Exception as e:
                        logger.error("Failed to send to web device %s: %s", device.id, str(e))
                        if "410" in str(e) or "404" in str(e):
                            await push_notification_repository.removeDeviceSubscription(device.id)

            # --- 4b. Expo Push (native mobile) devices ---
            expo_tokens = [d.expo_token for d in targeted_devices if d.expo_token]
            delivered_count += self._send_expo_push(expo_tokens, notification)

            # Update stats and persist targeted user list for strict ownership validation
            update_data = {"deliveredCount": delivered_count, "targetedUserIds": list(targeted_user_ids)}
            await push_notification_repository.updateStats(notification.id, update_data)

            return {"deliveredCount": delivered_count, "totalDevices": len(targeted_devices)}
        except Exception as e:
            logger.error("Error in sending targeted push: %s", str(e), exc_info=True)
            raise

    async def send_to_user(self, user_id: int, notification: PushNotificationPayload):
        """Send push notification to a specific user's devices"""
        try:
            devices = await push_notification_repository.getDeviceSubscriptionsByUser(user_id)
            delivered_count = 0

            # --- Web Push (browser/PWA) devices ---
            if WEB_PUSH_AVAILABLE:
                web_devices = [d for d in devices if d.endpoint and d.keys]
                for device in web_devices:
                    try:
                        payload = {
                            "title": notification.title or "",
                            "body": notification.message or "",
                            "icon": notification.image or "/logo192.png",
                            "badge": "/logo192.png",
                            "image": notification.image or None,
                            "data": {"url": notification.link or "/", "notificationId": notification.id},
                            "tag": notification.id or "",
                        }
                        device_keys_dict = {k.key: k.value for k in (device.keys or [])}
                        pywebpush.webpush(
                            subscription_info={"endpoint": device.endpoint, "keys": device_keys_dict},
                            data=json.dumps(payload),
                            vapid_private_key=self.vapid_private_key,
                            vapid_claims={"sub": self.vapid_email},
                        )
                        delivered_count += 1
                    except Exception as e:
                        logger.error("Failed to send to web device %s: %s", device.id, str(e))
                        if "410" in str(e) or "404" in str(e):
                            await push_notification_repository.removeDeviceSubscription(device.id)

            # --- Expo Push (native mobile) devices ---
            expo_tokens = [d.expo_token for d in devices if d.expo_token]
            delivered_count += self._send_expo_push(expo_tokens, notification)

            return {"deliveredCount": delivered_count, "totalDevices": len(devices)}
        except Exception as e:
            logger.error("Error sending push notification to user: %s", str(e), exc_info=True)
            raise

    async def is_user_targeted(
        self,
        user_id: int,
        notification: PushNotificationPayload,
        user: Optional[User] = None,
        user_orders: Optional[List[Order]] = None,
        reference_date: Optional[datetime] = None,
    ) -> bool:
        """Check if a specific user satisfies the targeting criteria of a notification."""
        target_segment = notification.user_segment or "all"
        target_behavior = notification.user_behavior or "none"

        if not reference_date:
            reference_date_str = notification.scheduled_for
            if reference_date_str:
                reference_date = datetime.fromisoformat(reference_date_str.replace("Z", "+00:00"))
            else:
                reference_date = datetime.fromisoformat(
                    (notification.created_at or datetime.now().isoformat()).replace("Z", "+00:00")
                )

        if not user:
            user = await user_repository.findById(user_id)
        if not user:
            return False

        # Segment check
        role_map = {"customers": "customer", "wholesalers": "wholesaler"}
        if target_segment != "all":
            if user.role != (role_map[target_segment] if target_segment in role_map else None):
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
                    if seg and seg.user_ids and user_id in seg.user_ids:
                        matched_any = True
                        break
                else:
                    if user_orders is None:
                        all_orders = await order_repository.findByUser(user_id)
                        user_orders = []
                        for order in all_orders:
                            try:
                                o_date = datetime.fromisoformat(order.created_at.replace("Z", "+00:00"))
                                if o_date <= reference_date:
                                    user_orders.append(order)
                            except Exception as exc:
                                logger.warning(
                                    "Failed to parse createdAt for order %s of user %s: %s",
                                    order.id,
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
                            <= datetime.fromisoformat(o.created_at.replace("Z", "+00:00"))
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
                            <= datetime.fromisoformat(o.created_at.replace("Z", "+00:00"))
                            <= reference_date
                        ]
                        if 3 < len(recent_orders) <= 9:
                            matched_any = True
                            break
            if not matched_any:
                return False

        return True


push_notification_service = PushNotificationService()
