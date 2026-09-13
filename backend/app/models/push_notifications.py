from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel

class PushNotifications(BaseModel):
    id: str = Field(default=None, alias='_id')
    external_id: Optional[str] = Field(default=None, alias='external_id')
    title: Optional[str] = Field(default=None, alias='title')
    message: Optional[str] = Field(default=None, alias='message')
    link: Optional[str] = Field(default=None, alias='link')
    image: Optional[str] = Field(default=None, alias='image')
    status: Optional[str] = Field(default=None, alias='status')
    scheduled_for: Optional[str] = Field(default=None, alias='scheduledFor')
    delivered_count: int = Field(default=0, alias='deliveredCount')
    read_count: int = Field(default=0, alias='readCount')
    user_segment: Optional[str] = Field(default=None, alias='userSegment')
    user_behavior: Optional[str] = Field(default=None, alias='userBehavior')
    created_by: Optional[str] = Field(default=None, alias='createdBy')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    eid: Optional[str] = Field(default=None, alias='eid')
    c: Optional[str] = Field(default=None, alias='c')
    u: Optional[str] = Field(default=None, alias='u')
