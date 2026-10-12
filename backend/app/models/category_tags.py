from datetime import datetime
from typing import Optional
from pydantic import Field
from app.models.base import CamelBaseModel

class CategoryTags(CamelBaseModel):
    id: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    is_active: Optional[bool] = Field(default=True)
    division_id: Optional[int] = Field(default=None)
    division_name: Optional[str] = Field(default=None)
    category_head_id: Optional[int] = Field(default=None)
    category_head_name: Optional[str] = Field(default=None)
    category_count: Optional[int] = Field(default=0)
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)
