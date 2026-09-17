from app.models.user import User
from typing import List, Optional
from app.models.schemas import MessageResponse, ActivityLogResponse, PromoteGuestResponse

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.repositories.activity_repository import activity_repository
from app.utils.auth import get_current_user, verify_token
from app.utils.device import parse_device

router = APIRouter()


async def optional_user(request: Request):
    auth_header = (request.headers["authorization"] if "authorization" in request.headers else None)
    if not auth_header:
        return None
    token = auth_header.split(" ")[-1]
    try:
        return await verify_token(token)
    except Exception as e:
        from app.utils.logger import logger

        logger.warning("Optional auth token verification failed in activity logging: %s", str(e))
        return None


class ActivityMeta(BaseModel):
    """Free-form but strictly-typed activity metadata payload from clients."""
    productId: Optional[str] = None
    productName: Optional[str] = None
    categoryId: Optional[str] = None
    categoryName: Optional[str] = None
    searchQuery: Optional[str] = None
    pageUrl: Optional[str] = None
    referrer: Optional[str] = None
    sessionId: Optional[str] = None
    orderId: Optional[str] = None
    couponCode: Optional[str] = None
    filterType: Optional[str] = None
    filterValue: Optional[str] = None
    sortBy: Optional[str] = None
    value: Optional[float] = None
    quantity: Optional[int] = None
    source: Optional[str] = None
    extra: Optional[str] = None


class LogActivityBody(BaseModel):
    type: Optional[str] = None
    action: Optional[str] = None
    detail: Optional[ActivityMeta] = None
    meta: Optional[ActivityMeta] = None
    sessionId: Optional[str] = None


class PromoteGuestBody(BaseModel):
    sessionId: str
    userId: Optional[str] = None


@router.post("", response_model=ActivityLogResponse)
async def log_activity(
    body: LogActivityBody,
    request: Request = None,
    current_user: User = Depends(optional_user),
):
    action = body.action or body.type
    meta: ActivityMeta = body.meta or body.detail or ActivityMeta()
    sid = body.sessionId or ((request.headers["x-session-id"] if "x-session-id" in request.headers else None) if request else None)
    if not sid:
        raise HTTPException(status_code=400, detail="sessionId is required")
    if not action:
        raise HTTPException(status_code=400, detail="action (or type) is required")
    device = parse_device(request, default_type="web") if request else {}
    user_id = current_user.id if current_user else None
    is_guest = user_id is None
    return await activity_repository.log_activity(user_id, sid, action, meta, device, is_guest=is_guest)


@router.post("/promote", response_model=PromoteGuestResponse)
async def promote_guest(body: PromoteGuestBody, request: Request, current_user: User = Depends(get_current_user)):
    return await activity_repository.promote_guest_activities(body.sessionId, current_user.id)
