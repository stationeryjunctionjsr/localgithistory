from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel
from app.models.base import CamelBaseModel

class SellerPayout(CamelBaseModel):
    id: str = None
    external_id: Optional[str] = None
    seller_id: Optional[str] = None
    amount: float = Field(default=0.0)
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    pid: Optional[str] = None
    soid: Optional[str] = None
    eid: Optional[str] = None
    c: Optional[str] = None
    u: Optional[str] = None
