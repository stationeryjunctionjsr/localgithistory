from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class FeatureFlag(DictCompatibleModel):
    id: str = Field(default=None, alias='_id')
    name: Optional[Any] = Field(default=None, alias='name')
    description: Optional[Any] = Field(default=None, alias='description')
    enabled: Optional[Any] = Field(default=None, alias='enabled')
    category: Optional[Any] = Field(default=None, alias='category')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    flag_id: Optional[Any] = Field(default=None, alias='flag_id')
    deleted_count: Optional[Any] = Field(default=None, alias='deletedCount')
