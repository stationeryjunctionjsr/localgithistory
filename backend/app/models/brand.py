from datetime import datetime
from typing import Optional
from pydantic import Field
from app.models.core import DictCompatibleModel

class Brand(DictCompatibleModel):
    id: int = Field(alias='_id')
    name: str
    slug: str
    image_url: Optional[str] = Field(default=None, alias='imageUrl')
    is_active: bool = Field(default=True, alias='isActive')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
