import logging
from app.models.user import User
from typing import List
from app.models.schemas import MessageResponse, AvailabilityRequestResponse, AvailabilityRequestListResponse
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from pydantic import BaseModel, Field, ConfigDict
from app.utils.limiter import limiter

from app.models.daos_flat import (
    AvailabilityRequestsInternalCreate,
    AvailabilityRequestsInternalUpdate,
)
from app.db.storage_factory import get_storage
from app.utils.auth import get_optional_user, require_super_admin
from app.utils.logger import logger

from app.models.availability_requests import AvailabilityRequestFilter

router = APIRouter()

_storage = get_storage("availabilityRequests")


class PushNotificationResult(BaseModel):
    deliveredCount: int = Field(default=0, alias="delivered_count")
    totalDevices: int = Field(default=0, alias="total_devices")

    model_config = ConfigDict(populate_by_name=True, extra="forbid")




class AvailabilityRequestCreate(BaseModel):
    productId: str
    productName: str
    pincode: str
    userName: Optional[str] = None
    userEmail: Optional[str] = None


@router.post("", status_code=status.HTTP_201_CREATED, response_model=AvailabilityRequestResponse)
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=AvailabilityRequestResponse)
@limiter.limit("5/minute")
async def create_availability_request(
    request: Request,
    data: AvailabilityRequestCreate,
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Create a product availability request for a specific pincode.
    Can be submitted by authenticated users or guests (providing name/email).
    """
    user_name = (current_user.name if current_user else None) or data.userName
    user_email = (current_user.email if current_user else None) or data.userEmail

    create_data = AvailabilityRequestsInternalCreate(
        product_id=data.productId,
        productName=data.productName,
        pincode=data.pincode.strip(),
        userName=user_name,
        userEmail=user_email,
    )

    result = await _storage.create(create_data)
    return result


@router.get("", response_model=AvailabilityRequestListResponse)
@router.get("/", response_model=AvailabilityRequestListResponse)
async def list_availability_requests(
    pincode: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    productId: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, le=200),
    current_user: User = Depends(require_super_admin),
):
    """List all availability requests. Admin only."""
    if status_filter and status_filter != "pending":
        return AvailabilityRequestListResponse(requests=[], total=0, page=page, limit=limit)

    filters = AvailabilityRequestFilter(
        pincode=pincode.strip() if pincode else None,
        product_id=productId.strip() if productId else None,
    )

    skip = (page - 1) * limit
    total = await _storage.count(filters)
    paginated = await _storage.findAll(
        filters=filters,
        skip=skip,
        limit=limit,
        order_by="created_at DESC, id DESC",
    )

    return AvailabilityRequestListResponse(requests=paginated, total=total, page=page, limit=limit)


@router.post("/{request_id}/fulfill", response_model=MessageResponse)
async def fulfill_availability_request(
    request_id: str,
    current_user: User = Depends(require_super_admin),
):
    """Mark a request as fulfilled and notify the user via push + email."""
    req = await _storage.findById(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    # Mark fulfilled by deleting the processed request
    await _storage.delete(request_id)

    product_id = req.product_id
    product_name = (req.product_name if req.product_name is not None else "Your requested product")
    pincode = req.pincode
    user_id = req.userId
    user_email = req.user_email

    from app.models.push_notifications import PushNotifications
    notification_payload = PushNotifications(
        title="Product Now Available! 🎉",
        message=f"{product_name} is now available for delivery to pincode {pincode}.",
        link=f"/customer/product/{product_id}"
    )

    # Send push notification to user (if authenticated)
    push_delivered = 0
    if user_id:
        try:
            from app.services.push_notification_service import push_notification_service

            result = await push_notification_service.send_to_user(user_id, notification_payload)
            push_res = PushNotificationResult.model_validate(result, from_attributes=True)
            push_delivered = push_res.deliveredCount
        except Exception as e:
            logger.warning("Could not send push notification for availability request %s: %s", request_id, e)

    # Also notify all users who clicked "Notify Me" for this product+pincode
    notify_push = 0
    notify_email_list = []
    if product_id and pincode:
        try:
            from app.db.storage_factory import get_storage as _gs

            tracking_storage = _gs("tracking")
            events = await tracking_storage.findAll(event_type="notify_pincode", product_id=str(product_id))
            matching_events = [
                e
                for e in events
                if e.search_term == str(pincode)
            ]
            for event in matching_events:
                ev_user_id = event.user_id
                ev_email = event.filter_value
                if ev_user_id and ev_user_id != user_id:
                    try:
                        from app.services.push_notification_service import push_notification_service

                        r = await push_notification_service.send_to_user(ev_user_id, notification_payload)
                        r_res = PushNotificationResult.model_validate(r, from_attributes=True)
                        notify_push += (r_res.deliveredCount if r_res.deliveredCount is not None else 0)
                    except Exception as e:
                        logging.warning("availability_requests: push notification failed for user %r (product %r): %s", ev_user_id, product_id, e, exc_info=e)
                if ev_email:
                    notify_email_list.append(ev_email)
                try:
                    ev_id = str(event.id if event.id is not None else "")
                    if ev_id:
                        await tracking_storage.delete(ev_id)
                except Exception as e:
                    logging.warning("availability_requests: failed to remove notified event %r: %s", ev_id, e, exc_info=e)
        except Exception as e:
            logger.warning("Could not notify 'Notify Me' users for product %s at %s: %s", product_id, pincode, e)

    # Send email notifications (best-effort)
    email_delivered = 0
    all_emails = list({e for e in ([user_email] + notify_email_list) if e})
    for email in all_emails:
        try:
            from app.services.email_service import EmailService

            email_service = EmailService()
            email_service.send_email(
                to_emails=email,
                subject=f"'{product_name}' is now available at your pincode!",
                body=f"Great news! The product '{product_name}' you requested is now available for delivery to {pincode}. Visit the app to place your order now!",
            )
            email_delivered += 1
        except Exception as e:
            logger.warning("Could not send email to %s: %s", email, e)

    return MessageResponse(
        message=f"Request fulfilled. Push: {push_delivered + notify_push} delivered, Email: {email_delivered} sent."
    )
