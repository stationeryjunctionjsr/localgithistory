from app.models.schemas import ItemSnippet as OrderItem, Address, ValetDeclineHistoryEntry
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field
from app.models.base import CamelBaseModel
from pydantic import ConfigDict, AliasChoices
from app.models.base import CamelBaseModel

class OrderAddress(CamelBaseModel):
    name: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    district: Optional[str] = None
    country: Optional[str] = None
    google_location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class Order(CamelBaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    session_id: Optional[str] = None
    id: str = Field(default="", validation_alias=AliasChoices("_id", "id"))
    order_number: Optional[str] = None
    user: Optional[str] = None
    status: Optional[str] = None
    total: Optional[float] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    shipping: Optional[float] = None
    discount: Optional[float] = None
    order_type: Optional[str] = None
    payment_status: Optional[str] = None
    seller_id: Optional[str] = None
    payment_method: Optional[str] = None
    upi_payment_screenshot: Optional[str] = None
    ship_name: Optional[str] = None
    ship_phone: Optional[str] = None
    ship_street: Optional[str] = None
    ship_city: Optional[str] = None
    ship_state: Optional[str] = None
    ship_pincode: Optional[str] = None
    bill_name: Optional[str] = None
    bill_phone: Optional[str] = None
    bill_street: Optional[str] = None
    bill_city: Optional[str] = None
    bill_state: Optional[str] = None
    bill_pincode: Optional[str] = None
    notes: Optional[str] = None
    printed_bill: bool = Field(default=False)
    assigned_valet: Optional[str] = None
    pending_valet_id: Optional[str] = None
    valet_assigned_at: Optional[datetime] = None
    valet_cascade_count: Optional[int] = Field(default=0)
    is_urgent_delivery: bool = Field(default=False)
    delivery_slot_id: Optional[str] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    cod_payment_received: bool = Field(default=False)
    cod_payment_received_at: Optional[datetime] = None
    decline_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[str] = None
    turnaround_hours: Optional[float] = None
    items: List['OrderItem'] = []
    sub_orders: Optional[List['SubOrder']] = None
    idempotency_key: Optional[str] = None
    valet_decline_history: List[ValetDeclineHistoryEntry] = Field(default=[])
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

from pydantic import BaseModel, Field
from app.models.base import CamelBaseModel
from typing import Any, Dict, List, Optional

class OrderInternalCreate(CamelBaseModel):
    order_number: Optional[str] = None
    user_role: Optional[str] = None
    user: str
    session_id: Optional[str] = None
    items: List['OrderItem'] = Field(default_factory=list)
    subtotal: float
    tax: float
    shipping: float
    discount: float
    total: float
    order_type: str
    status: str = "pending"
    payment_status: str = "pending"
    payment_method: str = "cod"
    upi_payment_screenshot: Optional[str] = None
    ship_name: Optional[str] = None
    ship_phone: Optional[str] = None
    ship_street: Optional[str] = None
    ship_city: Optional[str] = None
    ship_state: Optional[str] = None
    ship_pincode: Optional[str] = None
    bill_name: Optional[str] = None
    bill_phone: Optional[str] = None
    bill_street: Optional[str] = None
    bill_city: Optional[str] = None
    bill_state: Optional[str] = None
    bill_pincode: Optional[str] = None
    notes: str = ""
    printed_bill: bool = False
    assigned_valet: Optional[str] = None
    is_urgent_delivery: bool = False
    pending_valet_id: Optional[str] = None
    invoice_path: Optional[str] = None
    invoice_generated_at: Optional[str] = None
    valet_declined_at: Optional[str] = None
    valet_decline_reason: Optional[str] = None
    valet_cascade_count: Optional[int] = None
    valet_assigned_at: Optional[str] = None
    valet_accepted_at: Optional[str] = None
    cancelled_by: Optional[str] = None
    valet_assigned_at: Optional[str] = None
    valet_cascade_count: Optional[int] = 0
    turnaround_hours: Optional[float] = None
    shipped_at: Optional[str] = None
    valet_decline_history: Optional[List[ValetDeclineHistoryEntry]] = None
    delivered_at: Optional[str] = None
    cod_payment_received: bool = False
    cod_payment_received_at: Optional[str] = None
    decline_reason: Optional[str] = None
    cancelled_at: Optional[str] = None
    cancelled_by: Optional[str] = None
    created_at: Optional[str] = None
    idempotency_key: Optional[str] = None

class OrderInternalUpdate(CamelBaseModel, extra="forbid"):

    user: Optional[str] = None
    order_number: Optional[str] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    discount: Optional[float] = None
    order_type: Optional[str] = None
    payment_method: Optional[str] = None
    upi_payment_screenshot: Optional[str] = None
    ship_name: Optional[str] = None
    ship_phone: Optional[str] = None
    ship_street: Optional[str] = None
    ship_city: Optional[str] = None
    ship_state: Optional[str] = None
    ship_pincode: Optional[str] = None
    bill_name: Optional[str] = None
    bill_phone: Optional[str] = None
    bill_street: Optional[str] = None
    bill_city: Optional[str] = None
    bill_state: Optional[str] = None
    bill_pincode: Optional[str] = None
    notes: Optional[str] = None
    printed_bill: Optional[bool] = None
    is_urgent_delivery: Optional[bool] = None
    items: Optional[List['OrderItem']] = None

    status: Optional[str] = None
    shipped_at: Optional[str] = None
    valet_decline_history: Optional[List[ValetDeclineHistoryEntry]] = None
    delivered_at: Optional[str] = None
    payment_status: Optional[str] = None
    cod_payment_received: Optional[bool] = None
    cod_payment_received_at: Optional[str] = None
    turnaround_hours: Optional[float] = None
    cancelled_at: Optional[str] = None
    fulfillment_status: Optional[str] = None
    shipping: Optional[float] = None
    total: Optional[float] = None
    assigned_valet: Optional[str] = None
    decline_reason: Optional[str] = None
    pending_valet_id: Optional[str] = None
    invoice_path: Optional[str] = None
    invoice_generated_at: Optional[str] = None
    valet_declined_at: Optional[str] = None
    valet_decline_reason: Optional[str] = None
    valet_cascade_count: Optional[int] = None
    valet_assigned_at: Optional[str] = None
    valet_accepted_at: Optional[str] = None
    cancelled_by: Optional[str] = None
    valet_assigned_at: Optional[str] = None
    cancelled_by: Optional[str] = None
    has_sub_orders: Optional[bool] = None
    sub_order_ids: Optional[List[str]] = None
    tracking_id: Optional[str] = None
    courier_partner: Optional[str] = None
    tracking_updated_at: Optional[str] = None

from app.models.sub_order import SubOrder
Order.model_rebuild()
