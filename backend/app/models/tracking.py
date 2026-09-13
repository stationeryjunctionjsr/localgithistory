from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel

class Tracking(BaseModel):
    id: str = Field(default=None, alias='_id')
    external_id: Optional[str] = Field(default=None, alias='externalId')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    product_ids: List[str] = Field(default=[], alias='product_ids')
    payload: Optional[Dict] = Field(default=None, alias='payload')
    product_id: Optional[str] = Field(default=None, alias='productId')
    quantity: int = Field(default=0, alias='quantity')
    tid: Optional[str] = Field(default=None, alias='tid')
    pid: Optional[str] = Field(default=None, alias='pid')
    k: Optional[str] = Field(default=None, alias='k')
    v: Optional[str] = Field(default=None, alias='v')
    eid: Optional[str] = Field(default=None, alias='eid')
    c: Optional[str] = Field(default=None, alias='c')
    u: Optional[str] = Field(default=None, alias='u')
    timestamp: Optional[str] = Field(default=None, alias='timestamp')
