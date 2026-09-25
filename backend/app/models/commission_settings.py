from app.models.base import CamelBaseModel
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel

class CommissionSettings(CamelBaseModel):
    id: str = Field(default=None)
    external_id: Optional[str] = Field(default=None)
    default_commission_pct: float = Field(default=0.0)
    tiers: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)
    min: Optional[str] = Field(default=None)
    max: Optional[str] = Field(default=None)
    pct: Optional[str] = Field(default=None)
    sid: Optional[str] = Field(default=None)
    minv: Optional[str] = Field(default=None)
    maxv: Optional[str] = Field(default=None)
    eid: Optional[str] = Field(default=None)
    upd: Optional[str] = Field(default=None)
