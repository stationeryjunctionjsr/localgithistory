from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class SellerAvailability(DictCompatibleModel):
    id: str = Field(default=None, alias='_id')
    external_id: Optional[str] = Field(default=None, alias='external_id')
    seller_id: Optional[str] = Field(default=None, alias='seller_id')
    status: Optional[str] = Field(default=None, alias='status')
    start_at: Optional[datetime] = Field(default=None, alias='start_at')
    end_at: Optional[datetime] = Field(default=None, alias='end_at')
    reason: Optional[str] = Field(default=None, alias='reason')
    created_by: Optional[str] = Field(default=None, alias='created_by')
    cancelled_at: Optional[datetime] = Field(default=None, alias='cancelled_at')
    created_at: Optional[datetime] = Field(default=None, alias='created_at')
    updated_at: Optional[datetime] = Field(default=None, alias='updated_at')
    row_id: Optional[str] = Field(default=None, alias='row_id')
