from app.models.schemas import AddressSnippet as Address, ItemSnippet as CartItem, ItemSnippet as OrderItem
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel
from app.models.base import CamelBaseModel

class CouponInfo(CamelBaseModel):
    code: Optional[str] = None
    discountType: Optional[str] = None
    discountValue: Optional[float] = None

class DeliverySlotInfo(CamelBaseModel):
    date: Optional[str] = None
    time: Optional[str] = None
    slotId: Optional[str] = None

class SubOrderItem(CamelBaseModel):
    product_id: Optional[str] = Field(default=None)
    name: Optional[str] = None
    qty: Optional[int] = None
    price: Optional[float] = None

class SubOrder(CamelBaseModel):
    id: str = Field(default="", alias='_id')
    external_id: Optional[str] = Field(default=None)
    sub_order_number: Optional[str] = Field(default=None)
    parent_order_id: Optional[str] = Field(default=None)
    parent_order_number: Optional[str] = Field(default=None)
    seller_id: Optional[str] = Field(default=None)
    seller_name: Optional[str] = Field(default=None)
    user_id: Optional[str] = Field(default=None, alias='user')
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
    subOrderNumber: str
    parentOrderId: str
    parentOrderNumber: str
    sellerId: Optional[str] = None
    sellerName: str = ""
    user: str
    items: List[SubOrderItem] = Field(default_factory=list)
    subtotal: float
    tax: float
    shipping: float
    deliveryGst: float
    discount: float
    total: float
    orderType: str = "b2c"
    status: str = "pending"
    paymentMethod: str = "cod"
    paymentStatus: str = "pending"
    isUrgentDelivery: bool = False
    deliverySlot: Optional[DeliverySlotInfo] = None
    shippingAddress: Optional['Address'] = None
    billingAddress: Optional['Address'] = None
    notes: str = ""
    couponCode: Optional[str] = None
    couponInfo: Optional[CouponInfo] = None
    assignedValet: Optional[str] = None
    pickupStatus: str = "pending_pickup"
    pickedUpAt: Optional[str] = None
    shippedAt: Optional[str] = None
    deliveredAt: Optional[str] = None
    cancelledAt: Optional[str] = None
    cancelledBy: Optional[str] = None
    declineReason: Optional[str] = None
    commissionPct: Optional[float] = None
    commissionAmount: Optional[float] = None
    commissionStatus: Optional[str] = None
    createdAt: Optional[str] = None

class SubOrderInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid')
    status: Optional[str] = None
    shippedAt: Optional[str] = None
    deliveredAt: Optional[str] = None
    cancelledAt: Optional[str] = None
    pickupStatus: Optional[str] = None
    pickedUpAt: Optional[str] = None
    commissionPct: Optional[float] = None
    commissionAmount: Optional[float] = None
    commissionStatus: Optional[str] = None
    assignedValet: Optional[str] = None



