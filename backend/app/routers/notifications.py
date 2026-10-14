from app.models.user import User
from app.models.schemas import BulkUpdateResponse, MessageResponse, NotificationMetadata
from typing import Optional, List
from datetime import datetime

from app.models.base import CamelBaseModel

class NotificationResponse(CamelBaseModel):
    id: int
    user_id: str
    type: str
    title: str
    message: str
    is_read: bool = False
    is_acknowledged: bool = False
    metadata: Optional[NotificationMetadata] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class UnreadCountResponse(CamelBaseModel):
    unread_count: int = 0
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.repositories.notification_repository import notification_repository
from app.utils.auth import require_super_admin, get_current_user
from app.utils.logger import logger

router = APIRouter()


@router.get("", response_model=List[NotificationResponse])
@router.get("/")
async def get_notifications(
    isRead: Optional[bool] = Query(None),
    type: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
):
    """Get all notifications for user"""
    try:
        from app.models.daos import NotificationFilter
        filters = NotificationFilter()
        if current_user.role != "super_admin":
            filters.user_id = str(current_user.id)

        if isRead is not None:
            filters.isRead = isRead
        if type:
            filters.type = type
        if startDate:
            filters.start_date = startDate
        if endDate:
            filters.end_date = endDate

        notifications = await notification_repository.findAll(filters)
        return notifications
    except Exception as e:
        logger.error("Failed to fetch notifications: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(current_user: User = Depends(get_current_user)):
    """Get count of unread notifications for user"""
    try:
        from app.models.daos import NotificationFilter
        filters = NotificationFilter(is_read=False)
        if current_user.role != "super_admin":
            filters.user_id = str(current_user.id)
            
        notifications = await notification_repository.findAll(filters)
        return UnreadCountResponse(unread_count=len(notifications))
    except Exception as e:
        logger.error("Failed to fetch unread count: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.put("/read-all", response_model=BulkUpdateResponse)
async def mark_all_read(current_user: User = Depends(get_current_user)):
    """Mark all notifications as read and acknowledged"""
    try:
        count = await notification_repository.markAllAsRead(user_id=current_user.id)
        return {"message": f"{count} notifications marked as read", "count": count}
    except Exception as e:
        logger.error("Failed to mark all as read: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


async def _get_and_verify_notification(notification_id: int, current_user: User):
    notification = await notification_repository.findById(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    if current_user.role != "super_admin":
        if notification.user_id != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to access this notification")
            
    return notification


@router.put("/{notification_id}/acknowledge", response_model=NotificationResponse)
async def acknowledge_notification(notification_id: int, current_user: User = Depends(get_current_user)):
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


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(notification_id: int, current_user: User = Depends(get_current_user)):
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


@router.delete("/{notification_id}", response_model=MessageResponse)
async def delete_notification(notification_id: int, current_user: User = Depends(get_current_user)):
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
