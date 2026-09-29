from app.models.base import CamelBaseModel
from datetime import datetime
from typing import Optional, List
from pydantic import Field, ConfigDict

class CommissionTierInternal(CamelBaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    pct: float

class CommissionSettings(CamelBaseModel):
    model_config = ConfigDict(extra='ignore', populate_by_name=True)
    
    id: str
    external_id: Optional[str] = None
    default_commission_pct: float = Field(default=5.0)
    tiers: List[CommissionTierInternal] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CommissionSettingsInternalCreate(CamelBaseModel):
    default_commission_pct: float = Field(default=5.0)
    tiers: List[CommissionTierInternal] = []

class CommissionSettingsInternalUpdate(CamelBaseModel):
    default_commission_pct: Optional[float] = None
    tiers: Optional[List[CommissionTierInternal]] = None
