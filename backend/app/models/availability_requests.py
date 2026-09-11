from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class AvailabilityRequests(DictCompatibleModel):
    id: str = Field(default=None, alias='_id')
    external_id: Optional[Any] = Field(default=None, alias='external_id')
    product_id: Optional[Any] = Field(default=None, alias='productId')
    product_name: Optional[Any] = Field(default=None, alias='productName')
    pincode: Optional[Any] = Field(default=None, alias='pincode')
    user_name: Optional[Any] = Field(default=None, alias='userName')
    user_email: Optional[Any] = Field(default=None, alias='userEmail')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    eid: Optional[Any] = Field(default=None, alias='eid')
    c: Optional[Any] = Field(default=None, alias='c')
    u: Optional[Any] = Field(default=None, alias='u')
