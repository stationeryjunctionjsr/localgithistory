from datetime import datetime
from typing import Optional
from app.models.base import CamelBaseModel


class FeatureFlag(CamelBaseModel):
    id: Optional[int] = None
    flag_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    category: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class FeatureFlagCreate(CamelBaseModel):
    id: Optional[int] = None
    flag_id: Optional[str] = None
    name: str
    description: Optional[str] = ""
    enabled: Optional[bool] = False
    category: Optional[str] = "features"


class FeatureFlagUpdate(CamelBaseModel):
    flag_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    category: Optional[str] = None
