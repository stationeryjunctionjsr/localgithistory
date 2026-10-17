from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel

class CoachMarks(BaseModel):
    id: Optional[int] = None
    anchor_id: Optional[str] = Field(default=None, alias='anchorId')
    title: Optional[str] = Field(default=None, alias='title')
    description: Optional[str] = Field(default=None, alias='description')
    screen_name: Optional[str] = Field(default=None, alias='screenName')
    sequence_order: Optional[str] = Field(default=None, alias='sequenceOrder')
    is_active: bool = Field(default=None, alias='isActive')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    c: Optional[str] = Field(default=None, alias='c')
    u: Optional[str] = Field(default=None, alias='u')
