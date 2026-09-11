from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class SellerRequest(DictCompatibleModel):
    id: str = Field(default=None, alias='_id')
    external_id: Optional[str] = Field(default=None, alias='externalId')
    request_number: Optional[str] = Field(default=None, alias='requestNumber')
    user: Optional[str] = Field(default=None, alias='user')
    subject: Optional[str] = Field(default=None, alias='subject')
    description: Optional[str] = Field(default=None, alias='description')
    category: Optional[str] = Field(default=None, alias='category')
    priority: Optional[str] = Field(default=None, alias='priority')
    status: Optional[str] = Field(default=None, alias='status')
    attachments: Optional[str] = Field(default=None, alias='attachments')
    responses: Optional[str] = Field(default=None, alias='responses')
    resolved_at: Optional[datetime] = Field(default=None, alias='resolvedAt')
    closed_at: Optional[datetime] = Field(default=None, alias='closedAt')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    admin_id: Optional[str] = Field(default=None, alias='adminId')
    response: Optional[str] = Field(default=None, alias='response')
    rid: Optional[str] = Field(default=None, alias='rid')
    url: Optional[str] = Field(default=None, alias='url')
    admin: Optional[str] = Field(default=None, alias='admin')
    text: Optional[str] = Field(default=None, alias='text')
    c: Optional[str] = Field(default=None, alias='c')
    user_id: Optional[str] = Field(default=None, alias='user_id')
    eid: Optional[str] = Field(default=None, alias='eid')
    deleted_count: int = Field(default=0, alias='deletedCount')
