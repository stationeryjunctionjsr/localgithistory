from app.models.base import CamelBaseModel
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field
from app.models.schemas import (
    VisibilityRuleSnippet, ProductDetails, VariantAttributes,
    TicketResponseItem, NotificationMetadata, ProductSellerEntry, VariantOption
)
from datetime import datetime

class CartItemInternal(CamelBaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    product: Optional[str] = None
    quantity: Optional[int] = 0
    sell_as_case: Optional[bool] = False
    bundle_id: Optional[str] = None
    bundle_name: Optional[str] = None
    price: Optional[float] = None
    variant_attributes: Optional[VariantAttributes] = None
    id_: Optional[str] = Field(default=None, alias="_id")

    @property
    def product_id(self) -> Optional[str]:
        return self.product

    @property
    def bundle_id(self) -> Optional[str]:
        return self.bundle_id

    @property
    def sell_as_case(self) -> Optional[bool]:
        return self.sell_as_case

    @property
    def bundle_name(self) -> Optional[str]:
        return self.bundle_name

    @property
    def selectedVariation(self) -> Optional[VariantAttributes]:
        return self.variant_attributes

    @property
    def variant_attributes(self) -> Optional[VariantAttributes]:
        return self.variant_attributes

class CartInternalCreate(CamelBaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    user: Optional[str] = None
    items: Optional[List[CartItemInternal]] = []

class CartInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    user: Optional[str] = None
    items: Optional[List[CartItemInternal]] = None

class PaymentEntryInternal(CamelBaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    entry_id: Optional[int] = None
    amount: Optional[float] = 0.0
    payment_method: Optional[str] = None
    paid_at: Optional[str] = None
    image: Optional[str] = None
    notes: Optional[str] = None
    verified: Optional[bool] = False
    created_at: Optional[Any] = None

class PaymentInternalCreate(CamelBaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    order_id: Optional[str] = None
    user_id: Optional[str] = None
    user_id_formatted: Optional[str] = None
    customer_name: Optional[str] = None
    order_date: Optional[str] = None
    payment_method: Optional[str] = None
    amount_paid: Optional[float] = 0.0
    amount_remaining: Optional[float] = 0.0
    total_amount: Optional[float] = 0.0
    payment_id: Optional[str] = None
    payment_entries: Optional[List[PaymentEntryInternal]] = []
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None

class PaymentInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    order_id: Optional[str] = None
    user_id: Optional[str] = None
    user_id_formatted: Optional[str] = None
    customer_name: Optional[str] = None
    order_date: Optional[str] = None
    payment_method: Optional[str] = None
    amount_paid: Optional[float] = None
    amount_remaining: Optional[float] = None
    total_amount: Optional[float] = None
    payment_id: Optional[str] = None
    payment_entries: Optional[List[PaymentEntryInternal]] = None
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None

class VisibilityRuleInternal(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    pageType: Optional[str] = None
    pageIds: Optional[List[str]] = None

class BannerInternalCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    title: Optional[str] = None
    description: Optional[str] = None
    imageUrl: Optional[str] = None
    linkUrl: Optional[str] = None
    displayOrder: Optional[int] = 0
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    is_active: Optional[bool] = True
    isPublished: Optional[bool] = False
    targetAudience: Optional[str] = None
    user_segments: Optional[List[str]] = []
    visibility_rules: Optional[List[VisibilityRuleSnippet]] = []
    position: Optional[str] = None
    zoneIds: Optional[List[str]] = None

class BannerInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    external_id: Optional[str] = Field(None, alias='externalId')
    title: Optional[str] = None
    description: Optional[str] = None
    imageUrl: Optional[str] = None
    linkUrl: Optional[str] = None
    displayOrder: Optional[int] = None
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    is_active: Optional[bool] = None
    sales_count: Optional[int] = None
    updated_at: Optional[Any] = None
    isPublished: Optional[bool] = None
    targetAudience: Optional[str] = None
    user_segments: Optional[List[str]] = None
    visibility_rules: Optional[List[VisibilityRuleSnippet]] = None
    position: Optional[str] = None
    zoneIds: Optional[List[str]] = None

class BannerChildrenData(BaseModel):
    user_segments: Optional[List[str]] = None
    visibility_rules: Optional[List[VisibilityRuleSnippet]] = None

class SellerPayoutInternalCreate(CamelBaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    seller_id: Optional[str] = None
    amount: Optional[float] = 0.0
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    status: Optional[str] = 'pending_payment'
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    admin_paid_at: Optional[str] = None
    admin_paid_by: Optional[str] = None
    seller_received_at: Optional[str] = None
    notes: Optional[str] = None
    sub_order_ids: Optional[List[str]] = []

class SellerPayoutInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    seller_id: Optional[str] = None
    amount: Optional[float] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    status: Optional[str] = None
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    admin_paid_at: Optional[str] = None
    admin_paid_by: Optional[str] = None
    seller_received_at: Optional[str] = None
    notes: Optional[str] = None
    sub_order_ids: Optional[List[str]] = None

class ValetPayoutInternalCreate(CamelBaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', populate_by_name=True)
    valet_id: Optional[str] = None
    amount: Optional[float] = 0.0
    delivery_count: Optional[int] = 0
    return_count: Optional[int] = 0
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    status: Optional[str] = 'pending_payment'
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
    admin_paid_at: Optional[str] = None
    admin_paid_by: Optional[str] = None
    valet_received_at: Optional[str] = None

class ValetPayoutInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', populate_by_name=True)
    valet_id: Optional[str] = None
    amount: Optional[float] = None
    delivery_count: Optional[int] = None
    return_count: Optional[int] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    status: Optional[str] = None
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
    admin_paid_at: Optional[str] = None
    admin_paid_by: Optional[str] = None
    valet_received_at: Optional[str] = None

class ValetAvailabilityInternalCreate(CamelBaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    valet_id: Optional[str] = None
    date: Optional[str] = None
    availability_type: Optional[str] = None
    slots: Optional[List[str]] = []
    zones: Optional[List[str]] = []

class ValetAvailabilityInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    valet_id: Optional[str] = None
    date: Optional[str] = None
    availability_type: Optional[str] = None
    slots: Optional[List[str]] = None
    zones: Optional[List[str]] = None

class DeviceSnippet(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', populate_by_name=True)
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

class SessionInternalCreate(CamelBaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    user: Optional[str] = None
    user_id: Optional[str] = None
    device_info: Optional[DeviceSnippet] = None
    ip_address: Optional[str] = None
    refresh_token_id: Optional[str] = None
    status: Optional[str] = None
    last_active_at: Optional[str] = None
    revoked_at: Optional[str] = None
    revoked_reason: Optional[str] = None
    device: Optional[DeviceSnippet] = None
    is_guest: Optional[bool] = None
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

class SessionInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True, from_attributes=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    user: Optional[str] = None
    user_id: Optional[str] = None
    device_info: Optional[DeviceSnippet] = None
    ip_address: Optional[str] = None
    is_active: Optional[bool] = None
    sales_count: Optional[int] = None
    updated_at: Optional[Any] = None
    refresh_token_id: Optional[str] = None
    status: Optional[str] = None
    last_active_at: Optional[str] = None
    revoked_at: Optional[str] = None
    revoked_reason: Optional[str] = None
    device: Optional[DeviceSnippet] = None
    is_guest: Optional[bool] = None
    comment: Optional[str] = None
    id_: Optional[str] = Field(default=None, alias="_id")
    created_at: Optional[Any] = None
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


class WishlistItemInternal(CamelBaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    id_: Optional[str] = Field(default=None, alias="_id")
    product: str
    quantity: Optional[int] = 1
    addedAt: Optional[str] = None

class WishlistInternalCreate(CamelBaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    user: str
    items: Optional[List[WishlistItemInternal]] = []

class WishlistInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    user: Optional[str] = None
    items: Optional[List[WishlistItemInternal]] = None

class TrackingInternalCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    order_id: str
    status: str
    details: Optional[str] = None

class TrackingInternalUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    order_id: Optional[str] = None
    status: Optional[str] = None
    details: Optional[str] = None

class BusinessDetailsInternal(BaseModel):
    companyName: Optional[str] = None
    gstNumber: Optional[str] = None
    panNumber: Optional[str] = None
    address: Optional[str] = None

class SellerRequestInternalCreate(CamelBaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    request_number: Optional[str] = None
    user: str
    subject: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = "general"
    priority: Optional[str] = "medium"
    status: str = "open"
    attachments: Optional[List[str]] = None
    responses: Optional[List['TicketResponseItem']] = None
    resolved_at: Optional[str] = None
    closed_at: Optional[str] = None
    created_at: Optional[Any] = None
    business_details: Optional[BusinessDetailsInternal] = None

class SellerRequestInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    request_number: Optional[str] = None
    user: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    attachments: Optional[List[str]] = None
    responses: Optional[List['TicketResponseItem']] = None
    resolved_at: Optional[str] = None
    closed_at: Optional[str] = None
    created_at: Optional[Any] = None
    business_details: Optional[BusinessDetailsInternal] = None


class ProductInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid')
    external_id: Optional[str] = Field(None, alias='externalId')
    name: str
    description: Optional[str] = None
    price: float
    mrp: Optional[float] = None
    category_id: str = "1"
    brand_id: Optional[str] = None
    images: List[str] = []
    is_active: bool = True
    is_system: bool = False
    seller_id: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    brand: Optional[str] = None
    mrp_per_case: Optional[float] = None
    price_per_case: Optional[float] = None
    items_per_case: Optional[int] = None
    is_returnable: Optional[bool] = None
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None
    minimum_quantity: Optional[int] = 1
    search_tags: Optional[List[str]] = []
    sales_count: Optional[int] = 0
    view_count: Optional[int] = 0
    is_new_arrival: Optional[bool] = False
    new_arrival_until: Optional[str] = None
    sellers: Optional[List[ProductSellerEntry]] = []
    stock: Optional[int] = 0
    product_id: Optional[int] = None
    productIdFormatted: Optional[str] = None
    unit: Optional[str] = "pc"
    tags: Optional[List[str]] = []
    thumbnail: Optional[str] = None
    variants: Optional[List[VariantOption]] = []
    variant_attributes: Optional[List[str]] = []
    details: Optional[ProductDetails] = None
    videos: Optional[List[str]] = []
    quantity_per_case: Optional[int] = None
    rating: Optional[float] = None
    reviews: Optional[int] = None
    isExclusive: Optional[bool] = None
    collection: Optional[str] = None
    catalogSellerIds: Optional[List[str]] = None

class ProductInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid')
    external_id: Optional[str] = Field(None, alias='externalId')
    sellers: Optional[List[ProductSellerEntry]] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    brand: Optional[str] = None
    mrp_per_case: Optional[float] = None
    quantity_per_case: Optional[int] = None
    stock: Optional[int] = None
    rating: Optional[float] = None
    reviews: Optional[int] = None
    videos: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    variant_attributes: Optional[List[str]] = None
    variants: Optional[List[VariantOption]] = None
    details: Optional[ProductDetails] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    mrp: Optional[float] = None
    category_id: Optional[str] = None
    brand_id: Optional[str] = None
    images: Optional[List[str]] = None
    is_active: Optional[bool] = None
    sales_count: Optional[int] = None
    updated_at: Optional[Any] = None
    seller_id: Optional[str] = None

class CategoryInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid')
    external_id: Optional[str] = Field(None, alias='externalId')
    name: str
    description: Optional[str] = None
    parentId: Optional[str] = None
    is_active: bool = True
    is_system: bool = False
    images: Optional[List[str]] = []
    subCategories: Optional[List[str]] = []
    minimum_quantity: Optional[int] = 1
    category_tag: Optional[str] = None
    categoryTags: Optional[List[str]] = []
    showInMobileHomepage: Optional[bool] = False
    gst: Optional[float] = None
    isReturnable: Optional[bool] = True

class CategoryChildrenData(CamelBaseModel):
    images: Optional[List[str]] = None
    sub_categories: Optional[List[str]] = None
    category_tags: Optional[List[str]] = None

class CategoryInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid')
    external_id: Optional[str] = Field(None, alias='externalId')
    name: Optional[str] = None
    description: Optional[str] = None
    parentId: Optional[str] = None
    is_active: Optional[bool] = None
    sales_count: Optional[int] = None
    updated_at: Optional[Any] = None
    images: Optional[List[str]] = None
    sub_categories: Optional[List[str]] = None
    minimum_quantity: Optional[int] = 1
    category_tag: Optional[str] = None
    category_tags: Optional[List[str]] = None
    show_in_mobile_homepage: Optional[bool] = None
    gst: Optional[float] = None
    is_returnable: Optional[bool] = None
    created_at: Optional[Any] = None

class BrandInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    external_id: Optional[str] = Field(None, alias='externalId')
    name: str
    description: Optional[str] = None
    is_active: bool = True
    is_system: bool = False
    logoUrl: Optional[str] = None
    showInMobileHomepage: Optional[bool] = False

class BrandInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    external_id: Optional[str] = Field(None, alias='externalId')
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    sales_count: Optional[int] = None
    updated_at: Optional[Any] = None
    slug: Optional[str] = None
    logoUrl: Optional[str] = None
    show_in_mobile_homepage: Optional[bool] = None


class BundleItemInternal(CamelBaseModel):
    product_id: str
    product_name: Optional[str] = None
    quantity: int
    price: Optional[float] = None
    discount_price: Optional[float] = None

class BundleInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid')
    external_id: Optional[str] = None
    name: str
    items: Optional[List[BundleItemInternal]] = []
    products: Optional[List[BundleItemInternal]] = []
    sales_count: Optional[int] = 0
    price: float
    is_active: bool = True
    is_system: bool = False

class BundleInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid')
    external_id: Optional[str] = None
    name: Optional[str] = None
    items: Optional[List[BundleItemInternal]] = None
    price: Optional[float] = None
    is_active: Optional[bool] = None
    sales_count: Optional[int] = None
    updated_at: Optional[Any] = None

class ReturnRequestInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True, from_attributes=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    id: Optional[str] = Field(default=None, alias="_id")
    return_id: Optional[str] = None
    order_id: Optional[str] = None
    user_id: Optional[str] = None
    items: Optional[List['ReturnItemSchema']] = []
    payment_method: Optional[str] = None
    upi_payment_screenshot: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = "pending"
    seller_id: Optional[str] = None
    delivery_slot_id: Optional[str] = None
    delivery_slot_config_id: Optional[str] = None
    delivery_slot_date: Optional[str] = None
    valet_id: Optional[str] = None
    pending_valet_id: Optional[str] = None
    valet_assigned_at: Optional[str] = None
    valet_cascade_count: Optional[int] = 0
    valet_decline_history: Optional[List['ValetDeclineHistoryEntry']] = []
    valet_accepted_at: Optional[str] = None
    valet_declined_at: Optional[str] = None
    valet_decline_reason: Optional[str] = None
    delivery_charge: Optional[float] = 0.0
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None

class ReturnRequestInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True, from_attributes=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    order_id: Optional[str] = None
    user_id: Optional[str] = None
    items: Optional[List['ReturnItemSchema']] = None
    payment_method: Optional[str] = None
    upi_payment_screenshot: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    seller_id: Optional[str] = None
    delivery_slot_id: Optional[str] = None
    delivery_slot_config_id: Optional[str] = None
    delivery_slot_date: Optional[str] = None
    valet_id: Optional[str] = None
    pending_valet_id: Optional[str] = None
    valet_assigned_at: Optional[str] = None
    valet_cascade_count: Optional[int] = None
    valet_decline_history: Optional[List['ValetDeclineHistoryEntry']] = None
    valet_accepted_at: Optional[str] = None
    valet_declined_at: Optional[str] = None
    valet_decline_reason: Optional[str] = None
    delivery_charge: Optional[float] = None
    updated_at: Optional[Any] = None

class ReturnRequestInternal(CamelBaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    id: Optional[str] = Field(default=None, alias="_id")
    return_id: Optional[str] = None
    order_id: Optional[str] = None
    user_id: Optional[str] = None
    items: Optional[List['ReturnItemSchema']] = []
    payment_method: Optional[str] = None
    upi_payment_screenshot: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = "pending"
    seller_id: Optional[str] = None
    delivery_slot_id: Optional[str] = None
    delivery_slot_config_id: Optional[str] = None
    delivery_slot_date: Optional[str] = None
    valet_id: Optional[str] = None
    pending_valet_id: Optional[str] = None
    valet_assigned_at: Optional[str] = None
    valet_cascade_count: Optional[int] = 0
    valet_decline_history: Optional[List['ValetDeclineHistoryEntry']] = []
    valet_accepted_at: Optional[str] = None
    valet_declined_at: Optional[str] = None
    valet_decline_reason: Optional[str] = None
    delivery_charge: Optional[float] = 0.0
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None

from app.models.schemas import TicketResponseItem, ProductSellerEntry, VariantOption, ReturnItemSchema, ValetDeclineHistoryEntry

class CustomerSegmentFilters(CamelBaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', populate_by_name=True)
    minOrderCount: Optional[int] = None
    maxOrderCount: Optional[int] = None
    minOrderValue: Optional[float] = None
    maxOrderValue: Optional[float] = None
    city: Optional[str] = None
    role: Optional[str] = None

class CustomerSegmentInternalCreate(CamelBaseModel):
    id: str = Field(alias="_id")
    name: str
    type: str
    userIds: List[str]
    filters: Optional[CustomerSegmentFilters] = None
    is_active: bool = True
    is_system: bool = False
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None
    lastRefreshedAt: Optional[str] = None

class CustomerSegmentInternalUpdate(CamelBaseModel):
    name: Optional[str] = None
    userIds: Optional[List[str]] = None
    filters: Optional[CustomerSegmentFilters] = None
    is_active: Optional[bool] = None
    updated_at: Optional[Any] = None
    lastRefreshedAt: Optional[str] = None

class NotificationInternalCreate(CamelBaseModel):
    id: str = Field(alias="_id")
    user_id: str
    type: str
    title: str
    message: str
    metadata: Optional[NotificationMetadata] = None
    is_read: bool = False
    is_acknowledged: bool = False
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None

class NotificationInternalUpdate(CamelBaseModel):
    is_read: Optional[bool] = None
    is_acknowledged: Optional[bool] = None
    updated_at: Optional[Any] = None

class NotificationFilter(BaseModel):
    user_id: Optional[str] = None
    is_read: Optional[bool] = None
    is_acknowledged: Optional[bool] = None
    type: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None

class NotificationInternal(CamelBaseModel):
    id: str = Field(alias="_id")
    user_id: str
    type: str
    title: str
    message: str
    is_read: bool
    is_acknowledged: bool
    metadata: Optional[NotificationMetadata] = None
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None