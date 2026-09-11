from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class CommissionSettings(DictCompatibleModel):
    id: str = Field(default=None, alias='_id')
    external_id: Optional[Any] = Field(default=None, alias='externalId')
    default_commission_pct: Optional[Any] = Field(default=None, alias='defaultCommissionPct')
    tiers: Optional[Any] = Field(default=None, alias='tiers')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    min: Optional[Any] = Field(default=None, alias='min')
    max: Optional[Any] = Field(default=None, alias='max')
    pct: Optional[Any] = Field(default=None, alias='pct')
    sid: Optional[Any] = Field(default=None, alias='sid')
    minv: Optional[Any] = Field(default=None, alias='minv')
    maxv: Optional[Any] = Field(default=None, alias='maxv')
    eid: Optional[Any] = Field(default=None, alias='eid')
    upd: Optional[Any] = Field(default=None, alias='upd')
