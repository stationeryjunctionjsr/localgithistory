from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel

class PaymentEntry(BaseModel):
    entry_id: Optional[str] = Field(default=None, alias="entryId")
    amount: Optional[float] = None
    payment_method: Optional[str] = Field(default=None, alias="paymentMethod")
    paid_at: Optional[datetime] = Field(default=None, alias="paidAt")
    image: Optional[str] = None
    notes: Optional[str] = None
    verified: bool = False
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")

class Payment(BaseModel):
    id: str = Field(alias="_id")
    order_id: Optional[str] = Field(default=None, alias="orderId")
    user_id: Optional[str] = Field(default=None, alias="userId")
    user_id_formatted: Optional[str] = Field(default=None, alias="userIdFormatted")
    customer_name: Optional[str] = Field(default=None, alias="customerName")
    order_date: Optional[datetime] = Field(default=None, alias="orderDate")
    payment_method: Optional[str] = Field(default=None, alias="paymentMethod")
    amount_paid: Optional[float] = Field(default=None, alias="amountPaid")
    amount_remaining: Optional[float] = Field(default=None, alias="amountRemaining")
    total_amount: Optional[float] = Field(default=None, alias="totalAmount")
    payment_id: Optional[str] = Field(default=None, alias="paymentId")
    payment_entries: List[PaymentEntry] = Field(default=[], alias="paymentEntries")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")
