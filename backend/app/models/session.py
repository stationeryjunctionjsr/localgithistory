from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class Session(DictCompatibleModel):
    id: str = Field(default=None, alias='_id')
    user: Optional[Any] = Field(default=None, alias='user')
    user_id: Optional[Any] = Field(default=None, alias='userId')
    refresh_token_id: Optional[Any] = Field(default=None, alias='refreshTokenId')
    status: Optional[Any] = Field(default=None, alias='status')
    last_active_at: Optional[datetime] = Field(default=None, alias='lastActiveAt')
    revoked_at: Optional[datetime] = Field(default=None, alias='revokedAt')
    revoked_reason: Optional[Any] = Field(default=None, alias='revokedReason')
    device: Optional[Any] = Field(default=None, alias='device')
    is_guest: bool = Field(default=None, alias='isGuest')
    comment: Optional[Any] = Field(default=None, alias='comment')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    external_id: Optional[Any] = Field(default=None, alias='external_id')
    comments: Optional[Any] = Field(default=None, alias='comments')
    eid: Optional[Any] = Field(default=None, alias='eid')
    now: Optional[Any] = Field(default=None, alias='now')
    deleted_count: Optional[Any] = Field(default=None, alias='deletedCount')
    uid: Optional[Any] = Field(default=None, alias='uid')
