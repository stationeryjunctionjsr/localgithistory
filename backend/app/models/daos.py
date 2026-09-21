from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field
from app.models.schemas import (
    VisibilityRuleSnippet, ProductDetails, VariantAttributes,
    TicketResponseItem, NotificationMetadata, ProductSellerEntry, VariantOption
)
from datetime import datetime

class CartItemInternal(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    externalId: Optional[str] = Field(None, alias='externalId')
    product: Optional[str] = None
    quantity: Optional[int] = 0
    sellAsCase: Optional[bool] = False
    bundleId: Optional[str] = None
    bundleName: Optional[str] = None
    price: Optional[float] = None
    variantAttributes: Optional[VariantAttributes] = None
    id_: Optional[str] = Field(default=None, alias="_id")

    @property
    def product_id(self) -> Optional[str]:
        return self.product

    @property
    def bundle_id(self) -> Optional[str]:
        return self.bundleId

    @property
    def sell_as_case(self) -> Optional[bool]:
        return self.sellAsCase

    @property
    def bundle_name(self) -> Optional[str]:
        return self.bundleName

    @property
    def selectedVariation(self) -> Optional[VariantAttributes]:
        return self.variantAttributes

    @property
    def variant_attributes(self) -> Optional[VariantAttributes]:
        return self.variantAttributes

class CartInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    externalId: Optional[str] = Field(None, alias='externalId')
    user: Optional[str] = None
    items: Optional[List[CartItemInternal]] = []

class CartInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    externalId: Optional[str] = Field(None, alias='externalId')
    user: Optional[str] = None
    items: Optional[List[CartItemInternal]] = None

class PaymentEntryInternal(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    externalId: Optional[str] = Field(None, alias='externalId')
    entryId: Optional[int] = None
    amount: Optional[float] = 0.0
    paymentMethod: Optional[str] = None
    paidAt: Optional[str] = None
    image: Optional[str] = None
    notes: Optional[str] = None
    verified: Optional[bool] = False
    createdAt: Optional[Any] = None

class PaymentInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    externalId: Optional[str] = Field(None, alias='externalId')
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
    createdAt: Optional[Any] = None
    updatedAt: Optional[Any] = None

class PaymentInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    externalId: Optional[str] = Field(None, alias='externalId')
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
    createdAt: Optional[Any] = None
    updatedAt: Optional[Any] = None

class VisibilityRuleInternal(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    externalId: Optional[str] = Field(None, alias='externalId')
    pageType: Optional[str] = None
    pageIds: Optional[List[str]] = None

class BannerInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    externalId: Optional[str] = Field(None, alias='externalId')
    title: Optional[str] = None
    description: Optional[str] = None
    imageUrl: Optional[str] = None
    linkUrl: Optional[str] = None
    displayOrder: Optional[int] = 0
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    isActive: Optional[bool] = True
    isPublished: Optional[bool] = False
    targetAudience: Optional[str] = None
    userSegments: Optional[List[str]] = []
    visibilityRules: Optional[List[VisibilityRuleSnippet]] = []
    position: Optional[str] = None

class BannerInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    externalId: Optional[str] = Field(None, alias='externalId')
    title: Optional[str] = None
    description: Optional[str] = None
    imageUrl: Optional[str] = None
    linkUrl: Optional[str] = None
    displayOrder: Optional[int] = None
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    isActive: Optional[bool] = None
    salesCount: Optional[int] = None
    updatedAt: Optional[Any] = None
    isPublished: Optional[bool] = None
    targetAudience: Optional[str] = None
    userSegments: Optional[List[str]] = None
    visibilityRules: Optional[List[VisibilityRuleSnippet]] = None
    position: Optional[str] = None

class BannerChildrenData(BaseModel):
    userSegments: Optional[List[str]] = None
    visibilityRules: Optional[List[VisibilityRuleSnippet]] = None

class SellerPayoutInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    externalId: Optional[str] = Field(None, alias='externalId')
    sellerId: Optional[str] = None
    amount: Optional[float] = 0.0
    periodStart: Optional[str] = None
    periodEnd: Optional[str] = None
    notes: Optional[str] = None
    subOrderIds: Optional[List[str]] = []

class SellerPayoutInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    externalId: Optional[str] = Field(None, alias='externalId')
    sellerId: Optional[str] = None
    amount: Optional[float] = None
    periodStart: Optional[str] = None
    periodEnd: Optional[str] = None
    notes: Optional[str] = None
    subOrderIds: Optional[List[str]] = None

class ValetAvailabilityInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    externalId: Optional[str] = Field(None, alias='externalId')
    valetId: Optional[str] = None
    date: Optional[str] = None
    availabilityType: Optional[str] = None
    slots: Optional[List[str]] = []
    zones: Optional[List[str]] = []

class ValetAvailabilityInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    externalId: Optional[str] = Field(None, alias='externalId')
    valetId: Optional[str] = None
    date: Optional[str] = None
    availabilityType: Optional[str] = None
    slots: Optional[List[str]] = None
    zones: Optional[List[str]] = None

class DeviceSnippet(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    type: Optional[str] = None
    os: Optional[str] = None
    osVersion: Optional[str] = None
    appVersion: Optional[str] = None
    userAgent: Optional[str] = None
    deviceType: Optional[str] = None
    deviceModel: Optional[str] = None
    locale: Optional[str] = None
    ip: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    fcmToken: Optional[str] = None

class SessionInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    externalId: Optional[str] = Field(None, alias='externalId')
    user: Optional[str] = None
    userId: Optional[str] = None
    deviceInfo: Optional[DeviceSnippet] = None
    ipAddress: Optional[str] = None
    refreshTokenId: Optional[str] = None
    status: Optional[str] = None
    lastActiveAt: Optional[str] = None
    revokedAt: Optional[str] = None
    revokedReason: Optional[str] = None
    device: Optional[DeviceSnippet] = None
    isGuest: Optional[bool] = None
    comment: Optional[str] = None
    id: Optional[str] = None
    user_id: Optional[str] = None
    refresh_token_id: Optional[str] = None
    last_active_at: Optional[str] = None
    revoked_at: Optional[str] = None
    revoked_reason: Optional[str] = None
    is_guest: Optional[bool] = None
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None

class SessionInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True, from_attributes=True)
    externalId: Optional[str] = Field(None, alias='externalId')
    user: Optional[str] = None
    userId: Optional[str] = None
    deviceInfo: Optional[DeviceSnippet] = None
    ipAddress: Optional[str] = None
    isActive: Optional[bool] = None
    salesCount: Optional[int] = None
    updatedAt: Optional[Any] = None
    refreshTokenId: Optional[str] = None
    status: Optional[str] = None
    lastActiveAt: Optional[str] = None
    revokedAt: Optional[str] = None
    revokedReason: Optional[str] = None
    device: Optional[DeviceSnippet] = None
    isGuest: Optional[bool] = None
    comment: Optional[str] = None
    id_: Optional[str] = Field(default=None, alias="_id")
    createdAt: Optional[Any] = None
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
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None


class WishlistItemInternal(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    externalId: Optional[str] = Field(None, alias='externalId')
    id_: Optional[str] = Field(default=None, alias="_id")
    product: str
    quantity: Optional[int] = 1
    addedAt: Optional[str] = None

class WishlistInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    externalId: Optional[str] = Field(None, alias='externalId')
    user: str
    items: Optional[List[WishlistItemInternal]] = []

class WishlistInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    externalId: Optional[str] = Field(None, alias='externalId')
    user: Optional[str] = None
    items: Optional[List[WishlistItemInternal]] = None

class TrackingInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    externalId: Optional[str] = Field(None, alias='externalId')
    orderId: str
    status: str
    details: Optional[str] = None

class TrackingInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    externalId: Optional[str] = Field(None, alias='externalId')
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
    externalId: Optional[str] = Field(None, alias='externalId')
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
    createdAt: Optional[Any] = None
    businessDetails: Optional[BusinessDetailsInternal] = None

class SellerRequestInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    externalId: Optional[str] = Field(None, alias='externalId')
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
    createdAt: Optional[Any] = None
    businessDetails: Optional[BusinessDetailsInternal] = None


class ProductInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    externalId: Optional[str] = Field(None, alias='externalId')
    name: str
    description: Optional[str] = None
    price: float
    mrp: Optional[float] = None
    categoryId: str = "1"
    brandId: Optional[str] = None
    images: List[str] = []
    isActive: bool = True
    isSystem: bool = False
    sellerId: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    subCategory: Optional[str] = None
    brand: Optional[str] = None
    mrpPerCase: Optional[float] = None
    pricePerCase: Optional[float] = None
    itemsPerCase: Optional[int] = None
    isReturnable: Optional[bool] = None
    createdAt: Optional[Any] = None
    updatedAt: Optional[Any] = None
    minimumQuantity: Optional[int] = 1
    searchTags: Optional[List[str]] = []
    salesCount: Optional[int] = 0
    viewCount: Optional[int] = 0
    isNewArrival: Optional[bool] = False
    newArrivalUntil: Optional[str] = None
    sellers: Optional[List[ProductSellerEntry]] = []
    stock: Optional[int] = 0
    productId: Optional[int] = None
    productIdFormatted: Optional[str] = None
    unit: Optional[str] = "pc"
    tags: Optional[List[str]] = []
    thumbnail: Optional[str] = None
    variants: Optional[List[VariantOption]] = []
    variantAttributes: Optional[List[str]] = []
    details: Optional[ProductDetails] = None
    videos: Optional[List[str]] = []
    quantityPerCase: Optional[int] = None
    rating: Optional[float] = None
    reviews: Optional[int] = None
    isExclusive: Optional[bool] = None
    collection: Optional[str] = None
    catalogSellerIds: Optional[List[str]] = None

class ProductInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    externalId: Optional[str] = Field(None, alias='externalId')
    sellers: Optional[List[ProductSellerEntry]] = None
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
    variants: Optional[List[VariantOption]] = None
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
    updatedAt: Optional[Any] = None
    sellerId: Optional[str] = None

class CategoryInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    externalId: Optional[str] = Field(None, alias='externalId')
    name: str
    description: Optional[str] = None
    parentId: Optional[str] = None
    isActive: bool = True
    isSystem: bool = False
    images: Optional[List[str]] = []
    subCategories: Optional[List[str]] = []
    minimumQuantity: Optional[int] = 1
    categoryTag: Optional[str] = None
    categoryTags: Optional[List[str]] = []
    showInMobileHomepage: Optional[bool] = False
    gst: Optional[float] = None
    isReturnable: Optional[bool] = True

class CategoryChildrenData(BaseModel):
    images: Optional[List[str]] = None
    subCategories: Optional[List[str]] = None
    categoryTags: Optional[List[str]] = None

class CategoryInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    externalId: Optional[str] = Field(None, alias='externalId')
    name: Optional[str] = None
    description: Optional[str] = None
    parentId: Optional[str] = None
    isActive: Optional[bool] = None
    salesCount: Optional[int] = None
    updatedAt: Optional[Any] = None
    images: Optional[List[str]] = None
    subCategories: Optional[List[str]] = None
    minimumQuantity: Optional[int] = 1
    categoryTag: Optional[str] = None
    categoryTags: Optional[List[str]] = None
    showInMobileHomepage: Optional[bool] = None
    gst: Optional[float] = None
    isReturnable: Optional[bool] = None
    createdAt: Optional[Any] = None

class BrandInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    externalId: Optional[str] = Field(None, alias='externalId')
    name: str
    description: Optional[str] = None
    isActive: bool = True
    isSystem: bool = False
    logoUrl: Optional[str] = None
    showInMobileHomepage: Optional[bool] = False

class BrandInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    externalId: Optional[str] = Field(None, alias='externalId')
    name: Optional[str] = None
    description: Optional[str] = None
    isActive: Optional[bool] = None
    salesCount: Optional[int] = None
    updatedAt: Optional[Any] = None
    slug: Optional[str] = None
    logoUrl: Optional[str] = None
    showInMobileHomepage: Optional[bool] = None


class BundleItemInternal(BaseModel):
    productId: str
    productName: Optional[str] = None
    quantity: int
    price: Optional[float] = None
    discountPrice: Optional[float] = None

class BundleInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    externalId: Optional[str] = Field(None, alias='externalId')
    name: str
    items: Optional[List[BundleItemInternal]] = []
    products: Optional[List[BundleItemInternal]] = []
    salesCount: Optional[int] = 0
    price: float
    isActive: bool = True
    isSystem: bool = False

class BundleInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    externalId: Optional[str] = Field(None, alias='externalId')
    name: Optional[str] = None
    items: Optional[List[BundleItemInternal]] = None
    price: Optional[float] = None
    isActive: Optional[bool] = None
    salesCount: Optional[int] = None
    updatedAt: Optional[Any] = None

class ReturnRequestInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True, from_attributes=True)
    externalId: Optional[str] = Field(None, alias='externalId')
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
    createdAt: Optional[Any] = None
    updatedAt: Optional[Any] = None

class ReturnRequestInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True, from_attributes=True)
    externalId: Optional[str] = Field(None, alias='externalId')
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
    updatedAt: Optional[Any] = None

class ReturnRequestInternal(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    externalId: Optional[str] = Field(None, alias='externalId')
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
    createdAt: Optional[Any] = None
    updatedAt: Optional[Any] = None

from app.models.schemas import TicketResponseItem, ProductSellerEntry, VariantOption, ReturnItemSchema, ValetDeclineHistoryEntry

class CustomerSegmentFilters(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    minOrderCount: Optional[int] = None
    maxOrderCount: Optional[int] = None
    minOrderValue: Optional[float] = None
    maxOrderValue: Optional[float] = None
    city: Optional[str] = None
    role: Optional[str] = None

class CustomerSegmentInternalCreate(BaseModel):
    id: str = Field(alias="_id")
    name: str
    type: str
    userIds: List[str]
    filters: Optional[CustomerSegmentFilters] = None
    isActive: bool = True
    isSystem: bool = False
    createdAt: Optional[Any] = None
    updatedAt: Optional[Any] = None
    lastRefreshedAt: Optional[str] = None

class CustomerSegmentInternalUpdate(BaseModel):
    name: Optional[str] = None
    userIds: Optional[List[str]] = None
    filters: Optional[CustomerSegmentFilters] = None
    isActive: Optional[bool] = None
    updatedAt: Optional[Any] = None
    lastRefreshedAt: Optional[str] = None

class NotificationInternalCreate(BaseModel):
    id: str = Field(alias="_id")
    userId: str
    type: str
    title: str
    message: str
    metadata: Optional[NotificationMetadata] = None
    isRead: bool = False
    isAcknowledged: bool = False
    createdAt: Optional[Any] = None
    updatedAt: Optional[Any] = None

class NotificationInternalUpdate(BaseModel):
    isRead: Optional[bool] = None
    isAcknowledged: Optional[bool] = None
    updatedAt: Optional[Any] = None

class NotificationFilter(BaseModel):
    userId: Optional[str] = None
    isRead: Optional[bool] = None
    isAcknowledged: Optional[bool] = None
    type: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None

class NotificationInternal(BaseModel):
    id: str = Field(alias="_id")
    userId: str
    type: str
    title: str
    message: str
    isRead: bool
    isAcknowledged: bool
    metadata: Optional[NotificationMetadata] = None
    createdAt: Optional[Any] = None
    updatedAt: Optional[Any] = None