from datetime import datetime
from typing import Optional
from pydantic import Field
from pydantic import BaseModel

class Brand(BaseModel):
    id: int = Field(alias='_id')
    name: str
    slug: str
    image_url: Optional[str] = Field(default=None, alias='imageUrl')
    is_active: bool = Field(default=True, alias='isActive')
    show_in_mobile_homepage: bool = Field(default=False, alias='showInMobileHomepage')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
