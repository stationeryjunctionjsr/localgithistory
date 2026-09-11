from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class SellerPayout(DictCompatibleModel):
    id: str = Field(default=None, alias='_id')
    external_id: Optional[Any] = Field(default=None, alias='external_id')
    seller_id: Optional[Any] = Field(default=None, alias='sellerId')
    amount: Optional[Any] = Field(default=None, alias='amount')
    period_start: Optional[Any] = Field(default=None, alias='periodStart')
    period_end: Optional[Any] = Field(default=None, alias='periodEnd')
    notes: Optional[Any] = Field(default=None, alias='notes')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    pid: Optional[Any] = Field(default=None, alias='pid')
    soid: Optional[Any] = Field(default=None, alias='soid')
    eid: Optional[Any] = Field(default=None, alias='eid')
    c: Optional[Any] = Field(default=None, alias='c')
    u: Optional[Any] = Field(default=None, alias='u')
