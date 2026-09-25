from datetime import datetime
from typing import Optional, List, Any
from pydantic import Field
from pydantic import BaseModel
from app.models.base import CamelBaseModel
from app.models.daos import DeviceSnippet

class Session(CamelBaseModel):
    id: str = None
    user: Optional[str] = None
    user_id: Optional[str] = None
    refresh_token_id: Optional[str] = None
    status: Optional[str] = None
    last_active_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    revoked_reason: Optional[str] = None
    device: Optional[DeviceSnippet] = None
    is_guest: bool = None
    comment: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    external_id: Optional[str] = None
    comments: Optional[str] = None
    eid: Optional[str] = None
    now: Optional[str] = None
    deleted_count: int = 0
    uid: Optional[str] = None
