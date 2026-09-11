from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class FeatureFlag(DictCompatibleModel):
    id: str = Field(default=None, alias='_id')
    name: Optional[str] = Field(default=None, alias='name')
    description: Optional[str] = Field(default=None, alias='description')
    enabled: Optional[str] = Field(default=None, alias='enabled')
    category: Optional[str] = Field(default=None, alias='category')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    flag_id: Optional[str] = Field(default=None, alias='flag_id')
    deleted_count: int = Field(default=0, alias='deletedCount')
