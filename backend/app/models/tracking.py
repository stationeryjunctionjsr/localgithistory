from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class Tracking(DictCompatibleModel):
    id: str = Field(default=None, alias='_id')
    external_id: Optional[Any] = Field(default=None, alias='externalId')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    product_ids: Optional[Any] = Field(default=None, alias='product_ids')
    payload: Optional[Any] = Field(default=None, alias='payload')
    product_id: Optional[Any] = Field(default=None, alias='productId')
    quantity: Optional[Any] = Field(default=None, alias='quantity')
    tid: Optional[Any] = Field(default=None, alias='tid')
    pid: Optional[Any] = Field(default=None, alias='pid')
    k: Optional[Any] = Field(default=None, alias='k')
    v: Optional[Any] = Field(default=None, alias='v')
    eid: Optional[Any] = Field(default=None, alias='eid')
    c: Optional[Any] = Field(default=None, alias='c')
    u: Optional[Any] = Field(default=None, alias='u')
    timestamp: Optional[Any] = Field(default=None, alias='timestamp')
