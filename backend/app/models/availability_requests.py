from datetime import datetime
from typing import Optional
from app.models.base import CamelBaseModel

class AvailabilityRequests(CamelBaseModel):
    id: Optional[int] = None
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    pincode: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    status: Optional[str] = "pending"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class AvailabilityRequestResponse(AvailabilityRequests):
    pass

class AvailabilityRequestFilter(CamelBaseModel):
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    pincode: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None


