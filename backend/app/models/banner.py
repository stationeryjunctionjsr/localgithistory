from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class Banner(DictCompatibleModel):
    id: str = Field(default=None, alias='_id')
    title: Optional[Any] = Field(default=None, alias='title')
    description: Optional[Any] = Field(default=None, alias='description')
    image_url: Optional[Any] = Field(default=None, alias='imageUrl')
    link_url: Optional[Any] = Field(default=None, alias='linkUrl')
    display_order: Optional[Any] = Field(default=None, alias='displayOrder')
    start_date: Optional[datetime] = Field(default=None, alias='startDate')
    end_date: Optional[datetime] = Field(default=None, alias='endDate')
    is_active: bool = Field(default=None, alias='isActive')
    is_published: bool = Field(default=None, alias='isPublished')
    target_audience: Optional[Any] = Field(default=None, alias='targetAudience')
    position: Optional[Any] = Field(default=None, alias='position')
    user_segments: Optional[Any] = Field(default=None, alias='userSegments')
    visibility_rules: Optional[Any] = Field(default=None, alias='visibilityRules')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    bid: Optional[Any] = Field(default=None, alias='bid')
    seg: Optional[Any] = Field(default=None, alias='seg')
    rule: Optional[Any] = Field(default=None, alias='rule')
    external_id: Optional[Any] = Field(default=None, alias='external_id')
    eid: Optional[Any] = Field(default=None, alias='eid')
