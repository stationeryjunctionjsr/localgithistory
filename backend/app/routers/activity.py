from app.models.user import User
from typing import Dict, Any, List
from app.models.schemas import MessageResponse
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.repositories.activity_repository import activity_repository
from app.utils.auth import get_current_user, verify_token
from app.utils.device import parse_device

router = APIRouter()


async def optional_user(request: Request):
    auth_header = request.headers.get("authorization")
    if not auth_header:
        return None
    token = auth_header.split(" ")[-1]
    try:
        return await verify_token(token)
    except Exception as e:
        from app.utils.logger import logger

        logger.warning("Optional auth token verification failed in activity logging: %s", str(e))
        return None


class LogActivityBody(BaseModel):
    type: Optional[str] = None
    action: Optional[str] = None
    detail: Optional[Any] = None
    meta: Optional[Any] = None
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
    meta = body.meta or body.detail or {}
    sid = body.sessionId or (request.headers.get("x-session-id") if request else None)
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
