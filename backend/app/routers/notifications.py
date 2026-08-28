from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.repositories.notification_repository import notification_repository
from app.utils.auth import require_super_admin, get_current_user
from app.utils.logger import logger

router = APIRouter()


@router.get("")
@router.get("/")
async def get_notifications(
    isRead: Optional[bool] = Query(None),
    type: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Get all notifications for user"""
    try:
        filters = {}
        if current_user.get("role") != "super_admin":
            filters["userId"] = current_user.get("_id") or current_user.get("id")

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
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    """Get count of unread notifications for user"""
    try:
        filters = {"isRead": False}
        if current_user.get("role") != "super_admin":
            filters["userId"] = current_user.get("_id") or current_user.get("id")
            
        notifications = await notification_repository.findAll(filters)
        return {"count": len(notifications)}
    except Exception as e:
        logger.error("Failed to fetch unread count: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.put("/read-all")
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read and acknowledged"""
    try:
        user_id = current_user.get("_id") or current_user.get("id")
        update_data = {"isRead": True, "isAcknowledged": True}
        unread = await notification_repository.findAll({"isRead": False, "userId": user_id})
        unack = await notification_repository.findAll({"isAcknowledged": False, "userId": user_id})
        
        count = 0
        seen = set()
        for n in unread + unack:
            if n["_id"] not in seen:
                await notification_repository.update(n["_id"], update_data)
                seen.add(n["_id"])
                count += 1
                
        return {"message": f"{count} notifications marked as read", "count": count}
    except Exception as e:
        logger.error("Failed to mark all as read: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


async def _get_and_verify_notification(notification_id: str, current_user: dict):
    notification = await notification_repository.findById(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    if current_user.get("role") != "super_admin":
        user_id = current_user.get("_id") or current_user.get("id")
        if notification.get("userId") != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this notification")
            
    return notification


@router.put("/{notification_id}/acknowledge")
async def acknowledge_notification(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Acknowledge a notification"""
    try:
        await _get_and_verify_notification(notification_id, current_user)
        notification = await notification_repository.acknowledge(notification_id)
        return notification
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to acknowledge notification: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.put("/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Mark notification as read"""
    try:
        await _get_and_verify_notification(notification_id, current_user)
        notification = await notification_repository.markAsRead(notification_id)
        return notification
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to mark notification as read: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.delete("/{notification_id}")
async def delete_notification(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a notification"""
    try:
        await _get_and_verify_notification(notification_id, current_user)
        await notification_repository.delete(notification_id)
        return {"message": "Notification deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete notification: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")
