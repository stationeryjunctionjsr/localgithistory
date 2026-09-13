from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel

class AvailabilityRequests(BaseModel):
    id: str = Field(default=None, alias='_id')
    external_id: Optional[str] = Field(default=None, alias='external_id')
    product_id: Optional[str] = Field(default=None, alias='productId')
    product_name: Optional[str] = Field(default=None, alias='productName')
    pincode: Optional[str] = Field(default=None, alias='pincode')
    user_name: Optional[str] = Field(default=None, alias='userName')
    user_email: Optional[str] = Field(default=None, alias='userEmail')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    eid: Optional[str] = Field(default=None, alias='eid')
    c: Optional[str] = Field(default=None, alias='c')
    u: Optional[str] = Field(default=None, alias='u')

class AvailabilityRequestResponse(AvailabilityRequests):
    pass

