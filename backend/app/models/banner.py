from datetime import datetime
from typing import Optional, List, Any
from pydantic import Field
from pydantic import BaseModel
from app.models.schemas import VisibilityRuleSnippet

from app.models.base import CamelBaseModel
class Banner(CamelBaseModel):
    id: str = Field(default=None)
    title: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    image_url: Optional[str] = Field(default=None)
    link_url: Optional[str] = Field(default=None)
    display_order: Optional[str] = Field(default=None)
    start_date: Optional[datetime] = Field(default=None)
    end_date: Optional[datetime] = Field(default=None)
    is_active: bool = Field(default=None)
    is_published: bool = Field(default=None)
    target_audience: Optional[str] = Field(default=None)
    position: Optional[str] = Field(default=None)
    user_segments: Optional[str] = Field(default=None)
    visibility_rules: Optional[List[VisibilityRuleSnippet]] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)
    bid: Optional[str] = Field(default=None)
    seg: Optional[str] = Field(default=None)
    rule: Optional[str] = Field(default=None)
    external_id: Optional[str] = Field(default=None)
    eid: Optional[str] = Field(default=None)
