from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel

class SellerPayout(BaseModel):
    id: str = Field(default=None, alias='_id')
    external_id: Optional[str] = Field(default=None, alias='external_id')
    seller_id: Optional[str] = Field(default=None, alias='sellerId')
    amount: float = Field(default=0.0, alias='amount')
    period_start: Optional[str] = Field(default=None, alias='periodStart')
    period_end: Optional[str] = Field(default=None, alias='periodEnd')
    notes: Optional[str] = Field(default=None, alias='notes')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    pid: Optional[str] = Field(default=None, alias='pid')
    soid: Optional[str] = Field(default=None, alias='soid')
    eid: Optional[str] = Field(default=None, alias='eid')
    c: Optional[str] = Field(default=None, alias='c')
    u: Optional[str] = Field(default=None, alias='u')
