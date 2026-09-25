from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel
from app.models.base import CamelBaseModel

class FeatureFlag(CamelBaseModel):
    id: str = Field(default=None)
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    enabled: Optional[str] = Field(default=None)
    category: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)
    flag_id: Optional[str] = Field(default=None)
    deleted_count: int = Field(default=0)
