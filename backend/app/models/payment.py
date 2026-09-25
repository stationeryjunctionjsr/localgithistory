from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel
from app.models.base import CamelBaseModel

class PaymentEntry(CamelBaseModel):
    entry_id: Optional[str] = None
    amount: Optional[float] = None
    payment_method: Optional[str] = None
    paid_at: Optional[datetime] = None
    image: Optional[str] = None
    notes: Optional[str] = None
    verified: bool = False
    created_at: Optional[datetime] = None

class Payment(CamelBaseModel):
    id: str 
    order_id: Optional[str] = None
    user_id: Optional[str] = None
    user_id_formatted: Optional[str] = None
    customer_name: Optional[str] = None
    order_date: Optional[datetime] = None
    payment_method: Optional[str] = None
    amount_paid: Optional[float] = None
    amount_remaining: Optional[float] = None
    total_amount: Optional[float] = None
    payment_id: Optional[str] = None
    payment_entries: List[PaymentEntry] = Field(default=[])
    updated_at: Optional[datetime] = None
