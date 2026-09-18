from datetime import datetime
from typing import Optional, List, Any
from pydantic import Field
from pydantic import BaseModel
from app.models.schemas import VisibilityRuleSnippet

class Banner(BaseModel):
    id: str = Field(default=None, alias='_id')
    title: Optional[str] = Field(default=None, alias='title')
    description: Optional[str] = Field(default=None, alias='description')
    image_url: Optional[str] = Field(default=None, alias='imageUrl')
    link_url: Optional[str] = Field(default=None, alias='linkUrl')
    display_order: Optional[str] = Field(default=None, alias='displayOrder')
    start_date: Optional[datetime] = Field(default=None, alias='startDate')
    end_date: Optional[datetime] = Field(default=None, alias='endDate')
    is_active: bool = Field(default=None, alias='isActive')
    is_published: bool = Field(default=None, alias='isPublished')
    target_audience: Optional[str] = Field(default=None, alias='targetAudience')
    position: Optional[str] = Field(default=None, alias='position')
    user_segments: Optional[str] = Field(default=None, alias='userSegments')
    visibility_rules: Optional[List[VisibilityRuleSnippet]] = Field(default=None, alias='visibilityRules')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    bid: Optional[str] = Field(default=None, alias='bid')
    seg: Optional[str] = Field(default=None, alias='seg')
    rule: Optional[str] = Field(default=None, alias='rule')
    external_id: Optional[str] = Field(default=None, alias='external_id')
    eid: Optional[str] = Field(default=None, alias='eid')
