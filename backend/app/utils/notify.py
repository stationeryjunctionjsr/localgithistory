"""
notify.py — Unified notification helper
========================================
Call `notify_user()` to simultaneously:
  1. Create an in-app notification (sj_notifications / notification_repository)
  2. Send a push notification (PushNotificationService — web-push + Expo)

Both channels are fire-and-forget; a failure in one never raises to the caller.

Usage
-----
    from app.utils.notify import notify_user

    await notify_user(
        user_id    = "42",
        notif_type = "return_completed",
        title      = "Return processed ✅",
        message    = "Your return has been collected. Refund incoming.",
        link       = "/customer/orders",
        metadata   = NotificationMetadata(order_id="ORD-123"),   # optional
    )
"""

from __future__ import annotations

import uuid
from typing import Optional

from app.models.schemas import NotificationMetadata


async def notify_user(
    *,
    user_id: str,
    notif_type: str,
    title: str,
    message: str,
    link: str = "/",
    image: Optional[str] = None,
    metadata: Optional[NotificationMetadata] = None,
) -> None:
    """
    Fire-and-forget: create in-app notification AND send push.
    Never raises — all errors are logged as warnings.

    Parameters
    ----------
    user_id    : str   — internal user ID (numeric string or external UUID)
    notif_type : str   — machine-readable type, e.g. "review_approved"
    title      : str   — short heading shown in notification centre
    message    : str   — body text
    link       : str   — relative URL the user is taken to on tap/click
    image      : str | None — optional image URL for push banner
    metadata   : NotificationMetadata | None — extra metadata stored on the in-app record
    """
    from app.utils.logger import logger

    # ── 1. In-app notification ────────────────────────────────────────────────
    try:
        from app.models.daos import NotificationInternalCreate
        from app.repositories.notification_repository import notification_repository

        meta = None
        if metadata is not None:
            meta = NotificationMetadata(
                url=metadata.url or link,
                type=metadata.type or notif_type,
                order_id=metadata.order_id,
                order_number=metadata.order_number,
                product_id=metadata.product_id,
                status=metadata.status,
                amount=metadata.amount,
                user_id=metadata.user_id,
                created_at=metadata.created_at,
                payment_id=metadata.payment_id,
                payment_id_formatted=metadata.payment_id_formatted,
                payment_method=metadata.payment_method,
                sub_order_id=metadata.sub_order_id,
                sub_order_number=metadata.sub_order_number,
                parent_order_id=metadata.parent_order_id,
                courier_partner=metadata.courier_partner,
            )
        elif link:
            meta = NotificationMetadata(
                url=link,
                type=notif_type,
            )

        try:
            numeric_uid = int(user_id)
        except (ValueError, TypeError):
            numeric_uid = 0

        await notification_repository.create(
            NotificationInternalCreate(
                user_id=numeric_uid,
                type=notif_type,
                title=title,
                message=message,
                metadata=meta,
            )
        )
    except Exception as exc:
        from app.utils.logger import logger as _log
        _log.warning("[notify_user] In-app notification failed for user %s (%s): %s", user_id, notif_type, exc)

    # ── 2. Push notification ──────────────────────────────────────────────────
    try:
        from app.models.push_notifications import PushNotifications
        from app.services.push_notification_service import push_notification_service

        await push_notification_service.send_to_user(
            str(user_id),
            PushNotifications(
                id=f"{notif_type}_{user_id}_{uuid.uuid4().hex[:8]}",
                title=title,
                message=message,
                link=link,
                image=image,
            ),
        )
    except Exception as exc:
        from app.utils.logger import logger as _log
        _log.warning("[notify_user] Push failed for user %s (%s): %s", user_id, notif_type, exc)
