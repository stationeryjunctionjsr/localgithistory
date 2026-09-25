from app.models.base import CamelBaseModel
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel

class CategoryTags(CamelBaseModel):
    id: str = Field(default=None)
    external_id: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    is_active: bool = Field(default=None)
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)
    eid: Optional[str] = Field(default=None)
    c: Optional[str] = Field(default=None)
    u: Optional[str] = Field(default=None)
