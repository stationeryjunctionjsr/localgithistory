from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class PushNotifications(DictCompatibleModel):
    id: str = Field(default=None, alias='_id')
    external_id: Optional[Any] = Field(default=None, alias='external_id')
    title: Optional[Any] = Field(default=None, alias='title')
    message: Optional[Any] = Field(default=None, alias='message')
    link: Optional[Any] = Field(default=None, alias='link')
    image: Optional[Any] = Field(default=None, alias='image')
    status: Optional[Any] = Field(default=None, alias='status')
    scheduled_for: Optional[Any] = Field(default=None, alias='scheduledFor')
    delivered_count: Optional[Any] = Field(default=None, alias='deliveredCount')
    read_count: Optional[Any] = Field(default=None, alias='readCount')
    user_segment: Optional[Any] = Field(default=None, alias='userSegment')
    user_behavior: Optional[Any] = Field(default=None, alias='userBehavior')
    created_by: Optional[Any] = Field(default=None, alias='createdBy')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    eid: Optional[Any] = Field(default=None, alias='eid')
    c: Optional[Any] = Field(default=None, alias='c')
    u: Optional[Any] = Field(default=None, alias='u')
