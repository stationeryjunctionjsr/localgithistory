from datetime import datetime
from typing import Optional
from app.models.base import CamelBaseModel


class SellerAvailability(CamelBaseModel):
    id: Optional[int] = None
    seller_id: Optional[str] = None
    status: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    reason: Optional[str] = None
    created_by: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    row_id: Optional[int] = None


class SellerAvailabilityEnriched(SellerAvailability):
    seller_name: Optional[str] = None
    seller_email: Optional[str] = None
