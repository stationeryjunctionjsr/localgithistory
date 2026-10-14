from app.models.schemas import ItemSnippet as OrderItem, Address, ValetDeclineHistoryEntry
from datetime import datetime, timezone
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, ConfigDict, field_validator
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
    id: str = Field(default="")
    order_number: Optional[str] = None
    user: Optional[int] = Field(None, alias='user_id')
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
    ship_address: Optional[str] = None
    ship_district: Optional[str] = None
    ship_country: Optional[str] = None
    ship_google_location: Optional[str] = None
    ship_latitude: Optional[float] = None
    ship_longitude: Optional[float] = None
    bill_name: Optional[str] = None
    bill_phone: Optional[str] = None
    bill_street: Optional[str] = None
    bill_city: Optional[str] = None
    bill_state: Optional[str] = None
    bill_pincode: Optional[str] = None
    bill_address: Optional[str] = None
    bill_district: Optional[str] = None
    bill_country: Optional[str] = None
    bill_google_location: Optional[str] = None
    bill_latitude: Optional[float] = None
    bill_longitude: Optional[float] = None
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
    has_sub_orders: Optional[bool] = None
    sub_order_ids: Optional[List[int]] = None
    idempotency_key: Optional[str] = None
    fulfillment_type: str = Field(default="hyperlocal")
    courier_partner: Optional[str] = None
    tracking_id: Optional[str] = None
    awb_code: Optional[str] = None
    shipping_label_url: Optional[str] = None
    estimated_delivery_date: Optional[datetime] = None
    valet_decline_history: List[ValetDeclineHistoryEntry] = Field(default=[])
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


    @property
    def shipping_address(self) -> Optional[Address]:
        if not self.ship_city and not self.ship_street and not self.ship_name and not self.ship_pincode:
            return None
        return Address(
            name=self.ship_name,
            phone=self.ship_phone,
            street=self.ship_street,
            city=self.ship_city,
            state=self.ship_state,
            pincode=self.ship_pincode,
            address=self.ship_address,
            district=self.ship_district,
            country=self.ship_country or "India",
            google_location=self.ship_google_location,
            latitude=self.ship_latitude,
            longitude=self.ship_longitude,
        )

    @property
    def billing_address(self) -> Optional[Address]:
        if not self.bill_city and not self.bill_street and not self.bill_name and not self.bill_pincode:
            return None
        return Address(
            name=self.bill_name,
            phone=self.bill_phone,
            street=self.bill_street,
            city=self.bill_city,
            state=self.bill_state,
            pincode=self.bill_pincode,
            address=self.bill_address,
            district=self.bill_district,
            country=self.bill_country or "India",
            google_location=self.bill_google_location,
            latitude=self.bill_latitude,
            longitude=self.bill_longitude,
        )

from pydantic import BaseModel, Field
from app.models.base import CamelBaseModel
from typing import Any, Dict, List, Optional

class OrderInternalCreate(CamelBaseModel):
    order_number: Optional[str] = None
    user_role: Optional[str] = None
    user: int
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
    ship_address: Optional[str] = None
    ship_district: Optional[str] = None
    ship_country: Optional[str] = None
    ship_google_location: Optional[str] = None
    ship_latitude: Optional[float] = None
    ship_longitude: Optional[float] = None
    bill_name: Optional[str] = None
    bill_phone: Optional[str] = None
    bill_street: Optional[str] = None
    bill_city: Optional[str] = None
    bill_state: Optional[str] = None
    bill_pincode: Optional[str] = None
    bill_address: Optional[str] = None
    bill_district: Optional[str] = None
    bill_country: Optional[str] = None
    bill_google_location: Optional[str] = None
    bill_latitude: Optional[float] = None
    bill_longitude: Optional[float] = None
    notes: str = ""
    printed_bill: bool = False
    assigned_valet: Optional[str] = None
    is_urgent_delivery: bool = False
    pending_valet_id: Optional[str] = None
    invoice_path: Optional[str] = None
    invoice_generated_at: Optional[datetime] = None
    valet_declined_at: Optional[datetime] = None
    valet_decline_reason: Optional[str] = None
    valet_cascade_count: Optional[int] = 0
    valet_assigned_at: Optional[datetime] = None
    valet_accepted_at: Optional[datetime] = None
    cancelled_by: Optional[str] = None
    turnaround_hours: Optional[float] = None
    shipped_at: Optional[datetime] = None
    valet_decline_history: Optional[List[ValetDeclineHistoryEntry]] = None
    delivered_at: Optional[datetime] = None
    cod_payment_received: bool = False
    cod_payment_received_at: Optional[datetime] = None
    decline_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    idempotency_key: Optional[str] = None
    fulfillment_type: str = "hyperlocal"
    courier_partner: Optional[str] = None
    tracking_id: Optional[str] = None
    awb_code: Optional[str] = None
    shipping_label_url: Optional[str] = None
    estimated_delivery_date: Optional[datetime] = None
    has_sub_orders: Optional[bool] = None
    sub_order_ids: Optional[List[int]] = None

    @field_validator(
        'invoice_generated_at', 'valet_declined_at', 'valet_assigned_at',
        'valet_accepted_at', 'shipped_at', 'delivered_at', 'cod_payment_received_at',
        'cancelled_at', 'created_at', 'estimated_delivery_date', mode='after'
    )
    @classmethod
    def clean_dt(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None and v.tzinfo is not None:
            return v.astimezone(timezone.utc).replace(tzinfo=None)
        return v

class OrderInternalUpdate(CamelBaseModel, extra="forbid"):

    user: Optional[int] = Field(None, alias='user_id')
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
    ship_address: Optional[str] = None
    ship_district: Optional[str] = None
    ship_country: Optional[str] = None
    ship_google_location: Optional[str] = None
    ship_latitude: Optional[float] = None
    ship_longitude: Optional[float] = None
    bill_name: Optional[str] = None
    bill_phone: Optional[str] = None
    bill_street: Optional[str] = None
    bill_city: Optional[str] = None
    bill_state: Optional[str] = None
    bill_pincode: Optional[str] = None
    bill_address: Optional[str] = None
    bill_district: Optional[str] = None
    bill_country: Optional[str] = None
    bill_google_location: Optional[str] = None
    bill_latitude: Optional[float] = None
    bill_longitude: Optional[float] = None
    notes: Optional[str] = None
    printed_bill: Optional[bool] = None
    is_urgent_delivery: Optional[bool] = None
    items: Optional[List['OrderItem']] = None

    status: Optional[str] = None
    shipped_at: Optional[datetime] = None
    valet_decline_history: Optional[List[ValetDeclineHistoryEntry]] = None
    delivered_at: Optional[datetime] = None
    payment_status: Optional[str] = None
    cod_payment_received: Optional[bool] = None
    cod_payment_received_at: Optional[datetime] = None
    turnaround_hours: Optional[float] = None
    cancelled_at: Optional[datetime] = None
    fulfillment_status: Optional[str] = None
    shipping: Optional[float] = None
    total: Optional[float] = None
    assigned_valet: Optional[str] = None
    decline_reason: Optional[str] = None
    pending_valet_id: Optional[str] = None
    invoice_path: Optional[str] = None
    invoice_generated_at: Optional[datetime] = None
    valet_declined_at: Optional[datetime] = None
    valet_decline_reason: Optional[str] = None
    valet_cascade_count: Optional[int] = None
    valet_assigned_at: Optional[datetime] = None
    valet_accepted_at: Optional[datetime] = None
    cancelled_by: Optional[str] = None
    has_sub_orders: Optional[bool] = None
    sub_order_ids: Optional[List[int]] = None
    tracking_id: Optional[str] = None
    courier_partner: Optional[str] = None
    tracking_updated_at: Optional[datetime] = None
    fulfillment_type: Optional[str] = None
    awb_code: Optional[str] = None
    shipping_label_url: Optional[str] = None
    estimated_delivery_date: Optional[datetime] = None

    @field_validator(
        'invoice_generated_at', 'valet_declined_at', 'valet_assigned_at',
        'valet_accepted_at', 'shipped_at', 'delivered_at', 'cod_payment_received_at',
        'cancelled_at', 'estimated_delivery_date', 'tracking_updated_at', mode='after'
    )
    @classmethod
    def clean_dt(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None and v.tzinfo is not None:
            return v.astimezone(timezone.utc).replace(tzinfo=None)
        return v

from app.models.sub_order import SubOrder
Order.model_rebuild()
