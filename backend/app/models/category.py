from datetime import datetime
from typing import Optional, List, Any
from pydantic import Field
from pydantic import BaseModel

class Category(BaseModel):
    id: str = Field(alias='_id')
    name: str
    description: Optional[str] = None
    is_active: bool = Field(default=True, alias='isActive')
    show_in_mobile_homepage: bool = Field(default=False, alias='showInMobileHomepage')
    category_tag: Optional[str] = Field(default=None, alias='categoryTag')
    minimum_quantity: Optional[int] = Field(default=None, alias='minimumQuantity')
    gst: Optional[float] = None
    is_returnable: bool = Field(default=True, alias='isReturnable')
    images: List[str] = []
    sub_categories: List[str] = Field(default=[], alias='subCategories')
    category_tags: List[str] = Field(default=[], alias='categoryTags')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
