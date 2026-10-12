from datetime import datetime
from typing import Optional
from app.models.base import CamelBaseModel

class ProductNotifications(CamelBaseModel):
    id: Optional[int] = None
    product_id: Optional[str] = None
    user_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
