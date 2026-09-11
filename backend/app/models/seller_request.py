from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class SellerRequest(DictCompatibleModel):
    id: str = Field(default=None, alias='_id')
    external_id: Optional[Any] = Field(default=None, alias='externalId')
    request_number: Optional[Any] = Field(default=None, alias='requestNumber')
    user: Optional[Any] = Field(default=None, alias='user')
    subject: Optional[Any] = Field(default=None, alias='subject')
    description: Optional[Any] = Field(default=None, alias='description')
    category: Optional[Any] = Field(default=None, alias='category')
    priority: Optional[Any] = Field(default=None, alias='priority')
    status: Optional[Any] = Field(default=None, alias='status')
    attachments: Optional[Any] = Field(default=None, alias='attachments')
    responses: Optional[Any] = Field(default=None, alias='responses')
    resolved_at: Optional[datetime] = Field(default=None, alias='resolvedAt')
    closed_at: Optional[datetime] = Field(default=None, alias='closedAt')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    admin_id: Optional[Any] = Field(default=None, alias='adminId')
    response: Optional[Any] = Field(default=None, alias='response')
    rid: Optional[Any] = Field(default=None, alias='rid')
    url: Optional[Any] = Field(default=None, alias='url')
    admin: Optional[Any] = Field(default=None, alias='admin')
    text: Optional[Any] = Field(default=None, alias='text')
    c: Optional[Any] = Field(default=None, alias='c')
    user_id: Optional[Any] = Field(default=None, alias='user_id')
    eid: Optional[Any] = Field(default=None, alias='eid')
    deleted_count: Optional[Any] = Field(default=None, alias='deletedCount')
