from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class CartItemInternal(BaseModel):
    model_config = ConfigDict(extra='forbid')
    product: Optional[str] = None
    quantity: Optional[int] = 0
    sellAsCase: Optional[bool] = False
    bundleId: Optional[str] = None
    bundleName: Optional[str] = None
    price: Optional[float] = None
    variantAttributes: Optional[Dict[str, str]] = None
    _id: Optional[str] = None

class CartInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    user: Optional[str] = None
    items: Optional[List[CartItemInternal]] = []

class CartInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    user: Optional[str] = None
    items: Optional[List[CartItemInternal]] = None

class PaymentEntryInternal(BaseModel):
    model_config = ConfigDict(extra='forbid')
    entryId: Optional[int] = None
    amount: Optional[float] = 0.0
    paymentMethod: Optional[str] = None
    paidAt: Optional[str] = None
    image: Optional[str] = None
    notes: Optional[str] = None
    verified: Optional[bool] = False
    createdAt: Optional[str] = None

class PaymentInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    orderId: Optional[str] = None
    userId: Optional[str] = None
    userIdFormatted: Optional[str] = None
    customerName: Optional[str] = None
    orderDate: Optional[str] = None
    paymentMethod: Optional[str] = None
    amountPaid: Optional[float] = 0.0
    amountRemaining: Optional[float] = 0.0
    totalAmount: Optional[float] = 0.0
    paymentId: Optional[str] = None
    paymentEntries: Optional[List[PaymentEntryInternal]] = []
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class PaymentInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    orderId: Optional[str] = None
    userId: Optional[str] = None
    userIdFormatted: Optional[str] = None
    customerName: Optional[str] = None
    orderDate: Optional[str] = None
    paymentMethod: Optional[str] = None
    amountPaid: Optional[float] = None
    amountRemaining: Optional[float] = None
    totalAmount: Optional[float] = None
    paymentId: Optional[str] = None
    paymentEntries: Optional[List[PaymentEntryInternal]] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class VisibilityRuleInternal(BaseModel):
    model_config = ConfigDict(extra='forbid')
    pageType: Optional[str] = None
    pageIds: Optional[List[str]] = None

class BannerInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    title: Optional[str] = None
    description: Optional[str] = None
    imageUrl: Optional[str] = None
    linkUrl: Optional[str] = None
    displayOrder: Optional[int] = 0
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    isActive: Optional[bool] = True
    isPublished: Optional[bool] = False
    targetAudience: Optional[str] = None
    userSegments: Optional[List[str]] = []
    visibilityRules: Optional[List[Dict[str, Any]]] = []
    position: Optional[str] = None

class BannerInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    title: Optional[str] = None
    description: Optional[str] = None
    imageUrl: Optional[str] = None
    linkUrl: Optional[str] = None
    displayOrder: Optional[int] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    isActive: Optional[bool] = None
    isPublished: Optional[bool] = None
    targetAudience: Optional[str] = None
    userSegments: Optional[List[str]] = None
    visibilityRules: Optional[List[Dict[str, Any]]] = None
    position: Optional[str] = None

class SellerPayoutInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    sellerId: Optional[str] = None
    amount: Optional[float] = 0.0
    periodStart: Optional[str] = None
    periodEnd: Optional[str] = None
    notes: Optional[str] = None
    subOrderIds: Optional[List[str]] = []

class SellerPayoutInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    sellerId: Optional[str] = None
    amount: Optional[float] = None
    periodStart: Optional[str] = None
    periodEnd: Optional[str] = None
    notes: Optional[str] = None
    subOrderIds: Optional[List[str]] = None

class ValetAvailabilityInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    valetId: Optional[str] = None
    date: Optional[str] = None
    availabilityType: Optional[str] = None
    slots: Optional[List[str]] = []
    zones: Optional[List[str]] = []

class ValetAvailabilityInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    valetId: Optional[str] = None
    date: Optional[str] = None
    availabilityType: Optional[str] = None
    slots: Optional[List[str]] = None
    zones: Optional[List[str]] = None

class SessionInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    user: str
    userId: Optional[str] = None
    deviceInfo: Optional[Any] = None
    ipAddress: Optional[str] = None

class SessionInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    user: Optional[str] = None
    userId: Optional[str] = None
    deviceInfo: Optional[Any] = None
    ipAddress: Optional[str] = None
    isActive: Optional[bool] = None

class WishlistInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    user: str
    items: List[Any] = []

class WishlistInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    user: Optional[str] = None
    items: Optional[List[Any]] = None

class TrackingInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    orderId: str
    status: str
    details: Optional[str] = None

class TrackingInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    orderId: Optional[str] = None
    status: Optional[str] = None
    details: Optional[str] = None

class SellerRequestInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    user: str
    status: str = "pending"
    businessDetails: Optional[Dict[str, Any]] = None

class SellerRequestInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    user: Optional[str] = None
    status: Optional[str] = None
    businessDetails: Optional[Dict[str, Any]] = None


class ProductInternalCreate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    name: str
    description: Optional[str] = None
    price: float
    mrp: float = 0.0
    categoryId: str
    brandId: Optional[str] = None
    images: List[str] = []
    isActive: bool = True
    sellerId: Optional[str] = None

class ProductInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    mrp: Optional[float] = None
    categoryId: Optional[str] = None
    brandId: Optional[str] = None
    images: Optional[List[str]] = None
    isActive: Optional[bool] = None
    sellerId: Optional[str] = None

class CategoryInternalCreate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    name: str
    description: Optional[str] = None
    parentId: Optional[str] = None
    isActive: bool = True

class CategoryInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    name: Optional[str] = None
    description: Optional[str] = None
    parentId: Optional[str] = None
    isActive: Optional[bool] = None

class BrandInternalCreate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    name: str
    description: Optional[str] = None
    isActive: bool = True

class BrandInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    name: Optional[str] = None
    description: Optional[str] = None
    isActive: Optional[bool] = None

class BundleInternalCreate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    name: str
    items: List[Any] = []
    price: float
    isActive: bool = True

class BundleInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    name: Optional[str] = None
    items: Optional[List[Any]] = None
    price: Optional[float] = None
    isActive: Optional[bool] = None

