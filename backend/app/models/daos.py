from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from app.models.schemas import VisibilityRuleSnippet, ProductDetails
from datetime import datetime

class CartItemInternal(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    product: Optional[str] = None
    quantity: Optional[int] = 0
    sellAsCase: Optional[bool] = False
    bundleId: Optional[str] = None
    bundleName: Optional[str] = None
    price: Optional[float] = None
    variantAttributes: Optional[Dict[str, str]] = None
    id_: Optional[str] = Field(default=None, alias="_id")

class CartInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    user: Optional[str] = None
    items: Optional[List[CartItemInternal]] = []

class CartInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    user: Optional[str] = None
    items: Optional[List[CartItemInternal]] = None

class PaymentEntryInternal(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    entryId: Optional[int] = None
    amount: Optional[float] = 0.0
    paymentMethod: Optional[str] = None
    paidAt: Optional[str] = None
    image: Optional[str] = None
    notes: Optional[str] = None
    verified: Optional[bool] = False
    createdAt: Optional[str] = None

class PaymentInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
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
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
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
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    pageType: Optional[str] = None
    pageIds: Optional[List[str]] = None

class BannerInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
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
    visibilityRules: Optional[List[VisibilityRuleSnippet]] = []
    position: Optional[str] = None

class BannerInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    title: Optional[str] = None
    description: Optional[str] = None
    imageUrl: Optional[str] = None
    linkUrl: Optional[str] = None
    displayOrder: Optional[int] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    isActive: Optional[bool] = None
    salesCount: Optional[int] = None
    updatedAt: Optional[str] = None
    isPublished: Optional[bool] = None
    targetAudience: Optional[str] = None
    userSegments: Optional[List[str]] = None
    visibilityRules: Optional[List[VisibilityRuleSnippet]] = None
    position: Optional[str] = None

class SellerPayoutInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    sellerId: Optional[str] = None
    amount: Optional[float] = 0.0
    periodStart: Optional[str] = None
    periodEnd: Optional[str] = None
    notes: Optional[str] = None
    subOrderIds: Optional[List[str]] = []

class SellerPayoutInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    sellerId: Optional[str] = None
    amount: Optional[float] = None
    periodStart: Optional[str] = None
    periodEnd: Optional[str] = None
    notes: Optional[str] = None
    subOrderIds: Optional[List[str]] = None

class ValetAvailabilityInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    valetId: Optional[str] = None
    date: Optional[str] = None
    availabilityType: Optional[str] = None
    slots: Optional[List[str]] = []
    zones: Optional[List[str]] = []

class ValetAvailabilityInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    valetId: Optional[str] = None
    date: Optional[str] = None
    availabilityType: Optional[str] = None
    slots: Optional[List[str]] = None
    zones: Optional[List[str]] = None

class SessionInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    user: Optional[str] = None
    userId: Optional[str] = None
    deviceInfo: Optional[dict] = None
    ipAddress: Optional[str] = None
    refreshTokenId: Optional[str] = None
    status: Optional[str] = None
    lastActiveAt: Optional[str] = None
    revokedAt: Optional[str] = None
    revokedReason: Optional[str] = None
    device: Optional[dict] = None
    isGuest: Optional[bool] = None
    comment: Optional[str] = None
    id: Optional[str] = None
    user_id: Optional[str] = None
    refresh_token_id: Optional[str] = None
    last_active_at: Optional[str] = None
    revoked_at: Optional[str] = None
    revoked_reason: Optional[str] = None
    is_guest: Optional[bool] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class SessionInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True, from_attributes=True)
    user: Optional[str] = None
    userId: Optional[str] = None
    deviceInfo: Optional[dict] = None
    ipAddress: Optional[str] = None
    isActive: Optional[bool] = None
    salesCount: Optional[int] = None
    updatedAt: Optional[str] = None
    refreshTokenId: Optional[str] = None
    status: Optional[str] = None
    lastActiveAt: Optional[str] = None
    revokedAt: Optional[str] = None
    revokedReason: Optional[str] = None
    device: Optional[dict] = None
    isGuest: Optional[bool] = None
    comment: Optional[str] = None
    id_: Optional[str] = Field(default=None, alias="_id")
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    external_id: Optional[str] = None
    comments: Optional[str] = None
    eid: Optional[str] = None
    now: Optional[str] = None
    deletedCount: Optional[int] = None
    uid: Optional[str] = None
    id: Optional[str] = None
    user_id: Optional[str] = None
    refresh_token_id: Optional[str] = None
    last_active_at: Optional[str] = None
    revoked_at: Optional[str] = None
    revoked_reason: Optional[str] = None
    is_guest: Optional[bool] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class WishlistItemInternal(BaseModel):
    product: str

class WishlistInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    user: str
    items: Optional[List[WishlistItemInternal]] = []

class WishlistInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    user: Optional[str] = None
    items: Optional[List[WishlistItemInternal]] = None

class TrackingInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    orderId: str
    status: str
    details: Optional[str] = None

class TrackingInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    orderId: Optional[str] = None
    status: Optional[str] = None
    details: Optional[str] = None

class BusinessDetailsInternal(BaseModel):
    companyName: Optional[str] = None
    gstNumber: Optional[str] = None
    panNumber: Optional[str] = None
    address: Optional[str] = None

class SellerRequestInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    requestNumber: Optional[str] = None
    user: str
    subject: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = "general"
    priority: Optional[str] = "medium"
    status: str = "open"
    attachments: Optional[List[str]] = None
    responses: Optional[List['TicketResponseItem']] = None
    resolvedAt: Optional[str] = None
    closedAt: Optional[str] = None
    createdAt: Optional[str] = None
    businessDetails: Optional[BusinessDetailsInternal] = None

class SellerRequestInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    requestNumber: Optional[str] = None
    user: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    attachments: Optional[List[str]] = None
    responses: Optional[List['TicketResponseItem']] = None
    resolvedAt: Optional[str] = None
    closedAt: Optional[str] = None
    createdAt: Optional[str] = None
    businessDetails: Optional[BusinessDetailsInternal] = None


class ProductInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    description: Optional[str] = None
    price: float
    mrp: Optional[float] = None
    categoryId: str = "1"
    brandId: Optional[str] = None
    images: List[str] = []
    isActive: bool = True
    sellerId: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    subCategory: Optional[str] = None
    brand: Optional[str] = None
    mrpPerCase: Optional[float] = None
    pricePerCase: Optional[float] = None
    itemsPerCase: Optional[int] = None
    isReturnable: Optional[bool] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    minimumQuantity: Optional[int] = 1
    searchTags: Optional[list] = []
    attributes: Optional[dict] = {}
    salesCount: Optional[int] = 0
    viewCount: Optional[int] = 0
    isNewArrival: Optional[bool] = False
    newArrivalUntil: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    sellers: Optional[list] = []
    stock: Optional[int] = 0
    productId: Optional[int] = None
    productIdFormatted: Optional[str] = None
    unit: Optional[str] = "pc"
    tags: Optional[list] = []
    thumbnail: Optional[str] = None
    variants: Optional[list] = []
    variantAttributes: Optional[list] = []
    details: Optional[dict] = {}
    videos: Optional[list] = []
    quantityPerCase: Optional[int] = None

class ProductInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    sellers: Optional[List['ProductSellerEntry']] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    subCategory: Optional[str] = None
    brand: Optional[str] = None
    mrpPerCase: Optional[float] = None
    quantityPerCase: Optional[int] = None
    stock: Optional[int] = None
    rating: Optional[float] = None
    reviews: Optional[int] = None
    videos: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    variantAttributes: Optional[List[str]] = None
    variants: Optional[List['VariantOption']] = None
    details: Optional[ProductDetails] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    mrp: Optional[float] = None
    categoryId: Optional[str] = None
    brandId: Optional[str] = None
    images: Optional[List[str]] = None
    isActive: Optional[bool] = None
    salesCount: Optional[int] = None
    updatedAt: Optional[str] = None
    sellerId: Optional[str] = None

class CategoryInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    description: Optional[str] = None
    parentId: Optional[str] = None
    isActive: bool = True
    images: Optional[list] = []
    subCategories: Optional[list] = []
    minimumQuantity: Optional[int] = 1
    categoryTag: Optional[str] = None
    categoryTags: Optional[list] = []
    showInMobileHomepage: Optional[bool] = False
    gst: Optional[float] = None
    isReturnable: Optional[bool] = True

class CategoryInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: Optional[str] = None
    description: Optional[str] = None
    parentId: Optional[str] = None
    isActive: Optional[bool] = None
    salesCount: Optional[int] = None
    updatedAt: Optional[str] = None
    images: Optional[list] = None
    subCategories: Optional[list] = None
    minimumQuantity: Optional[int] = 1
    categoryTag: Optional[str] = None
    categoryTags: Optional[list] = None
    showInMobileHomepage: Optional[bool] = None
    gst: Optional[float] = None
    isReturnable: Optional[bool] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class BrandInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    description: Optional[str] = None
    isActive: bool = True

class BrandInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: Optional[str] = None
    description: Optional[str] = None
    isActive: Optional[bool] = None
    salesCount: Optional[int] = None
    updatedAt: Optional[str] = None


class BundleItemInternal(BaseModel):
    productId: str
    productName: Optional[str] = None
    quantity: int
    price: Optional[float] = None
    discountPrice: Optional[float] = None

class BundleInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    items: Optional[List[BundleItemInternal]] = []
    products: Optional[List[BundleItemInternal]] = []
    salesCount: Optional[int] = 0
    price: float
    isActive: bool = True

class BundleInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: Optional[str] = None
    items: Optional[List[BundleItemInternal]] = None
    price: Optional[float] = None
    isActive: Optional[bool] = None
    salesCount: Optional[int] = None
    updatedAt: Optional[str] = None

class ReturnRequestInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True, from_attributes=True)
    id: Optional[str] = Field(default=None, alias="_id")
    returnId: Optional[str] = None
    orderId: Optional[str] = None
    userId: Optional[str] = None
    items: Optional[List['ReturnItemSchema']] = []
    paymentMethod: Optional[str] = None
    upiPaymentScreenshot: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = "pending"
    sellerId: Optional[str] = None
    deliverySlotId: Optional[str] = None
    deliverySlotConfigId: Optional[str] = None
    deliverySlotDate: Optional[str] = None
    valetId: Optional[str] = None
    pendingValetId: Optional[str] = None
    valetAssignedAt: Optional[str] = None
    valetCascadeCount: Optional[int] = 0
    valetDeclineHistory: Optional[List['ValetDeclineHistoryEntry']] = []
    valetAcceptedAt: Optional[str] = None
    valetDeclinedAt: Optional[str] = None
    valetDeclineReason: Optional[str] = None
    deliveryCharge: Optional[float] = 0.0
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class ReturnRequestInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True, from_attributes=True)
    orderId: Optional[str] = None
    userId: Optional[str] = None
    items: Optional[List['ReturnItemSchema']] = None
    paymentMethod: Optional[str] = None
    upiPaymentScreenshot: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    sellerId: Optional[str] = None
    deliverySlotId: Optional[str] = None
    deliverySlotConfigId: Optional[str] = None
    deliverySlotDate: Optional[str] = None
    valetId: Optional[str] = None
    pendingValetId: Optional[str] = None
    valetAssignedAt: Optional[str] = None
    valetCascadeCount: Optional[int] = None
    valetDeclineHistory: Optional[List['ValetDeclineHistoryEntry']] = None
    valetAcceptedAt: Optional[str] = None
    valetDeclinedAt: Optional[str] = None
    valetDeclineReason: Optional[str] = None
    deliveryCharge: Optional[float] = None
    updatedAt: Optional[str] = None

class ReturnRequestInternal(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    id: Optional[str] = Field(default=None, alias="_id")
    returnId: Optional[str] = None
    orderId: Optional[str] = None
    userId: Optional[str] = None
    items: Optional[List['ReturnItemSchema']] = []
    paymentMethod: Optional[str] = None
    upiPaymentScreenshot: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = "pending"
    sellerId: Optional[str] = None
    deliverySlotId: Optional[str] = None
    deliverySlotConfigId: Optional[str] = None
    deliverySlotDate: Optional[str] = None
    valetId: Optional[str] = None
    pendingValetId: Optional[str] = None
    valetAssignedAt: Optional[str] = None
    valetCascadeCount: Optional[int] = 0
    valetDeclineHistory: Optional[List['ValetDeclineHistoryEntry']] = []
    valetAcceptedAt: Optional[str] = None
    valetDeclinedAt: Optional[str] = None
    valetDeclineReason: Optional[str] = None
    deliveryCharge: Optional[float] = 0.0
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

from app.models.schemas import TicketResponseItem, ProductSellerEntry, VariantOption, ReturnItemSchema, ValetDeclineHistoryEntry
