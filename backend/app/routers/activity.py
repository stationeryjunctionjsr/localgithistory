from app.models.user import User
from typing import Optional
from app.models.schemas import ActivityLogResponse, PromoteGuestResponse

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.repositories.tracking_repository import tracking_repository
from app.utils.auth import get_current_user, verify_token

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
    pageUrl: Optional[str] = None
    source: Optional[str] = None


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
    user_id = str(current_user.id) if current_user else None
    await tracking_repository.trackAuthEvent(
        user_id=user_id,
        session_id=sid,
        action=action,
        source=meta.source if meta else None,
        page=meta.pageUrl if meta else None,
    )
    return ActivityLogResponse(success=True)


@router.post("/promote", response_model=PromoteGuestResponse)
async def promote_guest(body: PromoteGuestBody, request: Request, current_user: User = Depends(get_current_user)):
    # Guest promotion is now handled automatically at login (user_id links via session_id in sj_tracking).
    # This endpoint is kept for frontend backward compatibility.
    return PromoteGuestResponse(updated=0)
