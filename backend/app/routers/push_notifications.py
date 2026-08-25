from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.repositories.push_notification_repository import push_notification_repository
from app.utils.auth import get_current_user, require_super_admin, verify_token
from app.utils.logger import logger

router = APIRouter()
optional_security = HTTPBearer(auto_error=False)


@router.get("")
@router.get("/")
async def get_push_notifications(
    status: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    current_user: dict = Depends(require_super_admin),
):
    """Get all push notifications (super admin only)"""
    try:
        filters = {}
        if status:
            filters["status"] = status
        if startDate:
            filters["startDate"] = startDate
        if endDate:
            filters["endDate"] = endDate

        notifications = await push_notification_repository.findAll(filters)
        return notifications
    except Exception as e:
        logger.error("Failed to fetch push notifications: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.post("")
@router.post("/")
async def create_push_notification(
    title: str = Form(...),
    message: str = Form(...),
    link: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    scheduledFor: Optional[str] = Form(None),
    publishNow: str = Form("true"),
    userSegment: str = Form("all"),
    userBehavior: str = Form("none"),
    current_user: dict = Depends(require_super_admin),
):
    """Create a new push notification"""
    try:
        if not title or not message:
            raise HTTPException(status_code=400, detail="Title and message are required")

        notification_data = {
            "title": title,
            "message": message,
            "link": link or None,
            "image": None,
            "scheduledFor": None if publishNow == "true" else scheduledFor,
            "userSegment": userSegment,
            "userBehavior": userBehavior,
            "createdBy": current_user.get("id"),
        }

        # Handle image upload
        if image and image.filename:
            from app.services.oci_storage import upload_image_and_return_path

            notification_data["image"] = await upload_image_and_return_path(
                image, "push-notifications", filename_prefix="notification"
            )

        notification = await push_notification_repository.create(notification_data)

        # If publishing now, send immediately
        if publishNow == "true":
            try:
                from app.services.push_notification_service import push_notification_service

                await push_notification_service.send_to_all_devices(notification)
            except Exception as e:
                logger.error("Error sending push notification: %s", str(e), exc_info=True)
                # Don't fail the request if sending fails

        return notification
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create push notification: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.put("/{notification_id}")
async def update_push_notification(
    notification_id: str,
    title: Optional[str] = Form(None),
    message: Optional[str] = Form(None),
    link: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    scheduledFor: Optional[str] = Form(None),
    publishNow: Optional[str] = Form(None),
    userSegment: Optional[str] = Form(None),
    userBehavior: Optional[str] = Form(None),
    current_user: dict = Depends(require_super_admin),
):
    """Update a push notification"""
    try:
        notification = await push_notification_repository.findById(notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        update_data = {}
        if title is not None:
            update_data["title"] = title
        if message is not None:
            update_data["message"] = message
        if link is not None:
            update_data["link"] = link
        if scheduledFor is not None or publishNow is not None:
            if publishNow == "true":
                update_data["scheduledFor"] = None
                update_data["status"] = "published"
            else:
                update_data["scheduledFor"] = scheduledFor
                update_data["status"] = "scheduled" if scheduledFor else "published"
        if userSegment is not None:
            update_data["userSegment"] = userSegment
        if userBehavior is not None:
            update_data["userBehavior"] = userBehavior

        # Handle image upload
        if image and image.filename:
            from app.services.oci_storage import upload_image_and_return_path

            update_data["image"] = await upload_image_and_return_path(
                image, "push-notifications", filename_prefix="notification"
            )

        updated = await push_notification_repository.update(notification_id, update_data)

        # If publishing now and wasn't published before, send immediately
        if publishNow == "true" and notification.get("status") != "published":
            try:
                from app.services.push_notification_service import push_notification_service

                await push_notification_service.send_to_all_devices(updated)
            except Exception as e:
                logger.error("Error sending push notification: %s", str(e), exc_info=True)

        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update push notification: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.delete("/{notification_id}")
async def delete_push_notification(notification_id: str, current_user: dict = Depends(require_super_admin)):
    """Delete a push notification"""
    try:
        notification = await push_notification_repository.findById(notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        # Delete image if exists
        if notification.get("image"):
            image_path = Path(notification["image"].lstrip("/"))
            if image_path.exists():
                image_path.unlink()

        await push_notification_repository.delete(notification_id)
        return {"message": "Push notification deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete push notification: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/{notification_id}/analytics")
async def get_push_notification_analytics(notification_id: str, current_user: dict = Depends(require_super_admin)):
    """Get analytics for a push notification"""
    try:
        notification = await push_notification_repository.findById(notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        devices = await push_notification_repository.getAllDeviceSubscriptions()

        return {
            "deliveredCount": notification.get("deliveredCount", 0),
            "readCount": notification.get("readCount", 0),
            "totalDevices": len(devices),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch push notification analytics: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/inbox")
async def get_notification_inbox():
    """Return published notifications for the user-facing inbox (public endpoint)."""
    try:
        notifications = await push_notification_repository.findAll({"status": "published"})
        # Return only the fields needed by the mobile inbox — omit internal delivery details
        inbox = [
            {
                "_id": n.get("_id"),
                "title": n.get("title", ""),
                "message": n.get("message", ""),
                "image": n.get("image"),
                "link": n.get("link"),
                "createdAt": n.get("createdAt"),
            }
            for n in notifications
        ]
        # Newest first
        inbox.sort(key=lambda n: n.get("createdAt") or "", reverse=True)
        return inbox
    except Exception as e:
        logger.error("Failed to fetch notification inbox: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


class DeviceRegistrationRequest(BaseModel):
    userId: Optional[str] = None
    subscription: Optional[dict] = None
    expoToken: Optional[str] = None


@router.get("/vapid-public-key")
async def get_vapid_public_key():
    """Get VAPID public key for client-side subscription"""
    try:
        import os

        public_key = os.getenv("VAPID_PUBLIC_KEY")
        if not public_key:
            raise HTTPException(
                status_code=404,
                detail="VAPID public key not configured. Set VAPID_PUBLIC_KEY environment variable to enable push notifications.",
            )
        return {"publicKey": public_key}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get VAPID public key: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/{notification_id}")
async def get_push_notification(notification_id: str, current_user: dict = Depends(require_super_admin)):
    """Get push notification by ID"""
    try:
        notification = await push_notification_repository.findById(notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        return notification
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch push notification: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.post("/register-device")
async def register_device(
    request: DeviceRegistrationRequest, credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)
):
    """Register device for push notifications (public endpoint, optional auth)"""
    try:
        # Must have at least one identifier
        has_web_subscription = request.subscription and request.subscription.get("endpoint")
        has_expo_token = bool(request.expoToken)

        if not has_web_subscription and not has_expo_token:
            raise HTTPException(
                status_code=400, detail="Either a web push subscription or an Expo push token is required"
            )

        # Try to get userId from token if authenticated (optional)
        userId = request.userId
        if not userId and credentials:
            try:
                current_user = await verify_token(credentials.credentials)
                userId = current_user.get("_id") or current_user.get("userId")
            except Exception as e:
                # Not authenticated or invalid token — continue as guest
                logger.warning("Optional device registration auth token verification failed: %s", str(e))

        await push_notification_repository.registerDevice(
            userId, request.subscription if has_web_subscription else None, expoToken=request.expoToken
        )
        return {"message": "Device registered successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to register device: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.post("/{notification_id}/mark-read")
async def mark_notification_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Mark notification as read (for analytics). Requires authentication and published status."""
    try:
        notification = await push_notification_repository.findById(notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        # Ownership/User-link validation: Only published notifications can be marked read by users
        if notification.get("status") != "published":
            raise HTTPException(status_code=403, detail="Cannot mark unpublished notification as read")

        # Strict Ownership/Membership Validation
        user_id = str(current_user.get("_id") or current_user.get("id"))

        # Strict Ownership/Membership Validation
        targeted_ids = notification.get("targetedUserIds")
        if targeted_ids is not None:
            # High-performance O(1) check for new notifications
            if user_id not in [str(tid) for tid in targeted_ids]:
                raise HTTPException(status_code=403, detail="Notification was not delivered to your account")
        else:
            # Robust O(N) fallback for legacy notifications: re-calculate inclusion
            from app.services.push_notification_service import push_notification_service

            is_targeted = await push_notification_service.is_user_targeted(user_id, notification, user=current_user)
            if not is_targeted:
                raise HTTPException(status_code=403, detail="Notification not targeted to your account")

        # Device ownership check: Ensure user has at least one registered device to receive push
        user_devices = await push_notification_repository.getDeviceSubscriptionsByUser(user_id)
        if not user_devices:
            raise HTTPException(status_code=403, detail="No registered devices found for this account")

        # Idempotency: Use repository's user-based tracking to avoid double-counting
        await push_notification_repository.updateStats(notification_id, {}, userId=user_id)

        return {"message": "Notification marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to mark notification as read: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")
