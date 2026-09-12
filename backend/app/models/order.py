from app.models.schemas import ItemSnippet as OrderItem
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class OrderAddress(DictCompatibleModel):
    name: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    phone: Optional[str] = None

class Order(DictCompatibleModel):
    session_id: Optional[str] = Field(default=None, alias="sessionId")
    id: str = Field(alias="_id")
    order_number: Optional[str] = Field(default=None, alias="orderNumber")
    user: str
    status: Optional[str] = None
    total: Optional[float] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    shipping: Optional[float] = None
    discount: Optional[float] = None
    order_type: Optional[str] = Field(default=None, alias="orderType")
    payment_status: Optional[str] = Field(default=None, alias="paymentStatus")
    payment_method: Optional[str] = Field(default=None, alias="paymentMethod")
    upi_payment_screenshot: Optional[str] = Field(default=None, alias="upiPaymentScreenshot")
    shipping_address: OrderAddress = Field(default_factory=OrderAddress, alias="shippingAddress")
    billing_address: OrderAddress = Field(default_factory=OrderAddress, alias="billingAddress")
    notes: Optional[str] = None
    printed_bill: bool = Field(default=False, alias="printedBill")
    assigned_valet: Optional[str] = Field(default=None, alias="assignedValet")
    pending_valet_id: Optional[str] = Field(default=None, alias="pendingValetId")
    valet_assigned_at: Optional[datetime] = Field(default=None, alias="valetAssignedAt")
    valet_cascade_count: Optional[int] = Field(default=0, alias="valetCascadeCount")
    is_urgent_delivery: bool = Field(default=False, alias="isUrgentDelivery")
    shipped_at: Optional[datetime] = Field(default=None, alias="shippedAt")
    delivered_at: Optional[datetime] = Field(default=None, alias="deliveredAt")
    cod_payment_received: bool = Field(default=False, alias="codPaymentReceived")
    cod_payment_received_at: Optional[datetime] = Field(default=None, alias="codPaymentReceivedAt")
    decline_reason: Optional[str] = Field(default=None, alias="declineReason")
    cancelled_at: Optional[datetime] = Field(default=None, alias="cancelledAt")
    cancelled_by: Optional[str] = Field(default=None, alias="cancelledBy")
    turnaround_hours: Optional[float] = Field(default=None, alias="turnaroundHours")
    items: List['OrderItem'] = []
    valet_decline_history: List[Any] = Field(default=[], alias="valetDeclineHistory")
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

class OrderInternalCreate(BaseModel):
    userRole: Optional[str] = None
    user: str
    sessionId: Optional[str] = None
    items: List['OrderItem'] = Field(default_factory=list)
    subtotal: float
    tax: float
    shipping: float
    discount: float
    total: float
    orderType: str
    status: str = "pending"
    paymentStatus: str = "pending"
    paymentMethod: str = "cod"
    upiPaymentScreenshot: Optional[str] = None
    shippingAddress: Dict[str, Any] = Field(default_factory=dict)
    billingAddress: Dict[str, Any] = Field(default_factory=dict)
    notes: str = ""
    printedBill: bool = False
    assignedValet: Optional[str] = None
    shippedAt: Optional[str] = None
    deliveredAt: Optional[str] = None
    codPaymentReceived: bool = False
    codPaymentReceivedAt: Optional[str] = None
    declineReason: Optional[str] = None
    cancelledAt: Optional[str] = None
    cancelledBy: Optional[str] = None
    createdAt: Optional[str] = None

class OrderInternalUpdate(BaseModel, extra='forbid'):
    status: Optional[str] = None
    shippedAt: Optional[str] = None
    deliveredAt: Optional[str] = None
    paymentStatus: Optional[str] = None
    codPaymentReceived: Optional[bool] = None
    codPaymentReceivedAt: Optional[str] = None
    turnaroundHours: Optional[float] = None
    cancelledAt: Optional[str] = None
    fulfillmentStatus: Optional[str] = None
    shipping: Optional[float] = None
    total: Optional[float] = None
    assignedValet: Optional[str] = None
    declineReason: Optional[str] = None
    pendingValetId: Optional[str] = None
    valetAssignedAt: Optional[str] = None
    cancelledBy: Optional[str] = None




