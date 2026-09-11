from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class CommissionSettings(DictCompatibleModel):
    id: str = Field(default=None, alias='_id')
    external_id: Optional[str] = Field(default=None, alias='externalId')
    default_commission_pct: float = Field(default=0.0, alias='defaultCommissionPct')
    tiers: Optional[str] = Field(default=None, alias='tiers')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    min: Optional[str] = Field(default=None, alias='min')
    max: Optional[str] = Field(default=None, alias='max')
    pct: Optional[str] = Field(default=None, alias='pct')
    sid: Optional[str] = Field(default=None, alias='sid')
    minv: Optional[str] = Field(default=None, alias='minv')
    maxv: Optional[str] = Field(default=None, alias='maxv')
    eid: Optional[str] = Field(default=None, alias='eid')
    upd: Optional[str] = Field(default=None, alias='upd')
