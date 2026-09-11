from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class PromoStrips(DictCompatibleModel):
    id: str = Field(default=None, alias='_id')
    external_id: Optional[str] = Field(default=None, alias='external_id')
    text: Optional[str] = Field(default=None, alias='text')
    is_active: bool = Field(default=None, alias='isActive')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    eid: Optional[str] = Field(default=None, alias='eid')
    c: Optional[str] = Field(default=None, alias='c')
    u: Optional[str] = Field(default=None, alias='u')
