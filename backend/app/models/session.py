from datetime import datetime
from typing import Optional, List, Any
from pydantic import Field
from pydantic import BaseModel
from app.models.daos import DeviceSnippet

class Session(BaseModel):
    id: str = Field(default=None, alias='_id')
    user: Optional[str] = Field(default=None, alias='user')
    user_id: Optional[str] = Field(default=None, alias='userId')
    refresh_token_id: Optional[str] = Field(default=None, alias='refreshTokenId')
    status: Optional[str] = Field(default=None, alias='status')
    last_active_at: Optional[datetime] = Field(default=None, alias='lastActiveAt')
    revoked_at: Optional[datetime] = Field(default=None, alias='revokedAt')
    revoked_reason: Optional[str] = Field(default=None, alias='revokedReason')
    device: Optional[DeviceSnippet] = Field(default=None, alias='device')
    is_guest: bool = Field(default=None, alias='isGuest')
    comment: Optional[str] = Field(default=None, alias='comment')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    external_id: Optional[str] = Field(default=None, alias='external_id')
    comments: Optional[str] = Field(default=None, alias='comments')
    eid: Optional[str] = Field(default=None, alias='eid')
    now: Optional[str] = Field(default=None, alias='now')
    deleted_count: int = Field(default=0, alias='deletedCount')
    uid: Optional[str] = Field(default=None, alias='uid')
