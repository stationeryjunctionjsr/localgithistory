from app.models.schemas import AddressSnippet as Address, ItemSnippet as CartItem, ItemSnippet as OrderItem
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel

class CouponInfo(BaseModel):
    code: Optional[str] = None
    discountType: Optional[str] = None
    discountValue: Optional[float] = None

class DeliverySlotInfo(BaseModel):
    date: Optional[str] = None
    time: Optional[str] = None
    slotId: Optional[str] = None

class SubOrderItem(BaseModel):
    product_id: Optional[str] = Field(default=None, alias='productId')
    name: Optional[str] = None
    qty: Optional[int] = None
    price: Optional[float] = None

class SubOrder(BaseModel):
    id: str = Field(default="", alias='_id')
    external_id: Optional[str] = Field(default=None, alias='externalId')
    sub_order_number: Optional[str] = Field(default=None, alias='subOrderNumber')
    parent_order_id: Optional[str] = Field(default=None, alias='parentOrderId')
    parent_order_number: Optional[str] = Field(default=None, alias='parentOrderNumber')
    seller_id: Optional[str] = Field(default=None, alias='sellerId')
    seller_name: Optional[str] = Field(default=None, alias='sellerName')
    user_id: Optional[str] = Field(default=None, alias='user')
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    shipping: Optional[float] = None
    delivery_gst: float = Field(default=0.0, alias='deliveryGst')
    discount: Optional[float] = None
    total: Optional[float] = None
    order_type: Optional[str] = Field(default=None, alias='orderType')
    status: str = "pending"
    payment_method: Optional[str] = Field(default=None, alias='paymentMethod')
    payment_status: str = Field(default="pending", alias='paymentStatus')
    is_urgent_delivery: bool = Field(default=False, alias='isUrgentDelivery')
    delivery_slot: Optional[DeliverySlotInfo] = Field(default=None, alias='deliverySlot')
    notes: Optional[str] = None
    coupon_code: Optional[str] = Field(default=None, alias='couponCode')
    coupon_info: Optional[CouponInfo] = Field(default=None, alias='couponInfo')
    commission_status: str = Field(default="unrealized", alias='commissionStatus')
    shipping_address: Optional['Address'] = Field(default=None, alias='shippingAddress')
    billing_address: Optional['Address'] = Field(default=None, alias='billingAddress')
    pickup_status: str = Field(default="pending_pickup", alias='pickupStatus')
    assigned_valet: Optional[str] = Field(default=None, alias='assignedValet')
    return_status: Optional[str] = Field(default=None, alias='returnStatus')
    items: List[SubOrderItem] = []
    
    # Dates
    delivered_at: Optional[datetime] = Field(default=None, alias='deliveredAt')
    dispatched_at: Optional[datetime] = Field(default=None, alias='dispatchedAt')
    cancelled_at: Optional[datetime] = Field(default=None, alias='cancelledAt')
    picked_up_at: Optional[datetime] = Field(default=None, alias='pickedUpAt')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')

from pydantic import BaseModel, Field, ConfigDict

class SubOrderInternalCreate(BaseModel):
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

class SubOrderInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
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



