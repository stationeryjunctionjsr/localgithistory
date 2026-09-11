from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class ProductNotifications(DictCompatibleModel):
    id: str = Field(default=None, alias='_id')
    external_id: Optional[str] = Field(default=None, alias='external_id')
    product_id: Optional[str] = Field(default=None, alias='productId')
    user_id: Optional[str] = Field(default=None, alias='userId')
    email: Optional[str] = Field(default=None, alias='email')
    phone: Optional[str] = Field(default=None, alias='phone')
    status: Optional[str] = Field(default=None, alias='status')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    eid: Optional[str] = Field(default=None, alias='eid')
    c: Optional[str] = Field(default=None, alias='c')
    u: Optional[str] = Field(default=None, alias='u')
