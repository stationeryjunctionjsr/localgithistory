from app.models.schemas import AddressSnippet as Address, ItemSnippet as CartItem, ItemSnippet as OrderItem
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel
from app.models.base import CamelBaseModel

class CouponInfo(CamelBaseModel):
    code: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None

class DeliverySlotInfo(CamelBaseModel):
    date: Optional[str] = None
    time: Optional[str] = None
    slot_id: Optional[str] = None

class SubOrderItem(CamelBaseModel):
    product_id: Optional[str] = Field(default=None)
    name: Optional[str] = None
    qty: Optional[int] = None
    price: Optional[float] = None

class SubOrder(CamelBaseModel):
    id: str = Field(default="")
    external_id: Optional[str] = Field(default=None)
    sub_order_number: Optional[str] = Field(default=None)
    parent_order_id: Optional[str] = Field(default=None)
    parent_order_number: Optional[str] = Field(default=None)
    seller_id: Optional[str] = Field(default=None)
    seller_name: Optional[str] = Field(default=None)
    user_id: Optional[str] = Field(default=None)
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    shipping: Optional[float] = None
    delivery_gst: float = Field(default=0.0)
    discount: Optional[float] = None
    total: Optional[float] = None
    order_type: Optional[str] = Field(default=None)
    status: str = "pending"
    payment_method: Optional[str] = Field(default=None)
    payment_status: str = Field(default="pending")
    is_urgent_delivery: bool = Field(default=False)
    delivery_slot: Optional[DeliverySlotInfo] = Field(default=None)
    notes: Optional[str] = None
    coupon_code: Optional[str] = Field(default=None)
    coupon_info: Optional[CouponInfo] = Field(default=None)
    commission_status: str = Field(default="unrealized")
    commission_amount: Optional[float] = Field(default=0.0)
    commission_pct: Optional[float] = Field(default=None)
    shipping_address: Optional['Address'] = Field(default=None)
    billing_address: Optional['Address'] = Field(default=None)
    pickup_status: str = Field(default="pending_pickup")
    assigned_valet: Optional[str] = Field(default=None)
    return_status: Optional[str] = Field(default=None)
    items: List[SubOrderItem] = []
    
    # Dates
    delivered_at: Optional[datetime] = Field(default=None)
    dispatched_at: Optional[datetime] = Field(default=None)
    cancelled_at: Optional[datetime] = Field(default=None)
    picked_up_at: Optional[datetime] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

from pydantic import BaseModel, Field, ConfigDict
from app.models.base import CamelBaseModel

class SubOrderInternalCreate(CamelBaseModel):
    sub_order_number: str
    parent_order_id: str
    parent_order_number: str
    seller_id: Optional[str] = None
    seller_name: str = ""
    user: str
    items: List[SubOrderItem] = Field(default_factory=list)
    subtotal: float
    tax: float
    shipping: float
    delivery_gst: float
    discount: float
    total: float
    order_type: str = "b2c"
    status: str = "pending"
    payment_method: str = "cod"
    payment_status: str = "pending"
    is_urgent_delivery: bool = False
    delivery_slot: Optional[DeliverySlotInfo] = None
    shipping_address: Optional['Address'] = None
    billing_address: Optional['Address'] = None
    notes: str = ""
    coupon_code: Optional[str] = None
    coupon_info: Optional[CouponInfo] = None
    assigned_valet: Optional[str] = None
    pickup_status: str = "pending_pickup"
    picked_up_at: Optional[str] = None
    shipped_at: Optional[str] = None
    delivered_at: Optional[str] = None
    cancelled_at: Optional[str] = None
    cancelled_by: Optional[str] = None
    decline_reason: Optional[str] = None
    commission_pct: Optional[float] = None
    commission_amount: Optional[float] = None
    commission_status: Optional[str] = None
    created_at: Optional[str] = None

class SubOrderInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid')
    status: Optional[str] = None
    shipped_at: Optional[str] = None
    delivered_at: Optional[str] = None
    cancelled_at: Optional[str] = None
    pickup_status: Optional[str] = None
    picked_up_at: Optional[str] = None
    commission_pct: Optional[float] = None
    commission_amount: Optional[float] = None
    commission_status: Optional[str] = None
    assigned_valet: Optional[str] = None



