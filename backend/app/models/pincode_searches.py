from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class PincodeSearches(DictCompatibleModel):
    id: str = Field(default=None, alias='_id')
    external_id: Optional[Any] = Field(default=None, alias='external_id')
    pincode: Optional[Any] = Field(default=None, alias='pincode')
    query: Optional[Any] = Field(default=None, alias='query')
    is_serviceable: bool = Field(default=None, alias='isServiceable')
    timestamp: Optional[Any] = Field(default=None, alias='timestamp')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    eid: Optional[Any] = Field(default=None, alias='eid')
    c: Optional[Any] = Field(default=None, alias='c')
    u: Optional[Any] = Field(default=None, alias='u')
