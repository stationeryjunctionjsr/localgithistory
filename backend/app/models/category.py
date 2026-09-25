from app.models.base import CamelBaseModel
from datetime import datetime
from typing import Optional, List, Any
from pydantic import Field
from pydantic import BaseModel

class Category(CamelBaseModel):
    id: str 
    name: str
    description: Optional[str] = None
    is_active: bool = Field(default=True)
    show_in_mobile_homepage: bool = Field(default=False)
    category_tag: Optional[str] = Field(default=None)
    minimum_quantity: Optional[int] = Field(default=1)
    gst: Optional[float] = None
    is_returnable: bool = Field(default=True)
    images: List[str] = []
    sub_categories: List[str] = Field(default=[])
    category_tags: List[str] = Field(default=[])
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)
