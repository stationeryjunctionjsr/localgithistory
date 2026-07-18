from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.repositories.notification_repository import notification_repository
from app.utils.auth import require_super_admin
from app.utils.logger import logger

router = APIRouter()


@router.get("")
@router.get("/")
async def get_notifications(
    isRead: Optional[bool] = Query(None),
    type: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    current_user: dict = Depends(require_super_admin),
):
    """Get all notifications for super admin"""
    try:
        filters = {}
        if isRead is not None:
            filters["isRead"] = isRead
        if type:
            filters["type"] = type
        if startDate:
            filters["startDate"] = startDate
        if endDate:
            filters["endDate"] = endDate

        notifications = await notification_repository.findAll(filters)
        return notifications
    except Exception as e:
        logger.error("Failed to fetch notifications: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/unread-count")
async def get_unread_count(current_user: dict = Depends(require_super_admin)):
    """Get count of unread notifications"""
    try:
        notifications = await notification_repository.findAll({"isRead": False})
        return {"count": len(notifications)}
    except Exception as e:
        logger.error("Failed to fetch unread count: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.put("/read-all")
async def mark_all_read(current_user: dict = Depends(require_super_admin)):
    """Mark all notifications as read and acknowledged"""
    try:
        count = await notification_repository.markAllAsRead()
        return {"message": f"{count} notifications marked as read", "count": count}
    except Exception as e:
        logger.error("Failed to mark all as read: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.put("/{notification_id}/acknowledge")
async def acknowledge_notification(notification_id: str, current_user: dict = Depends(require_super_admin)):
    """Acknowledge a notification"""
    try:
        notification = await notification_repository.acknowledge(notification_id)
        return notification
    except Exception as e:
        logger.error("Failed to acknowledge notification: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.put("/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: dict = Depends(require_super_admin)):
    """Mark notification as read"""
    try:
        notification = await notification_repository.markAsRead(notification_id)
        return notification
    except Exception as e:
        logger.error("Failed to mark notification as read: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.delete("/{notification_id}")
async def delete_notification(notification_id: str, current_user: dict = Depends(require_super_admin)):
    """Delete a notification"""
    try:
        await notification_repository.delete(notification_id)
        return {"message": "Notification deleted successfully"}
    except Exception as e:
        logger.error("Failed to delete notification: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")
