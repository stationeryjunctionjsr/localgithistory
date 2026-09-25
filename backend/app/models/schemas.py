from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any, List, Literal, Optional, Union, Dict

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator, AliasChoices, RootModel
from app.models.base import CamelBaseModel


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    WHOLESALER = "wholesaler"
    CUSTOMER = "customer"
    VALET = "valet"
    SELLER = "seller"
    SELLER_ADMIN = "seller_admin"


class ReturnRequestStatus(str, Enum):
    PENDING = "pending"
    PENDING_VALET = "pending_valet"
    ASSIGNED = "assigned"
    COLLECTED = "collected"
    RETURNED = "returned"
    REJECTED = "rejected"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class DiscountType(str, Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class TargetAudience(str, Enum):
    ALL = "all"
    CUSTOMER = "customer"
    WHOLESALER = "wholesaler"


class BannerPosition(str, Enum):
    HOMEPAGE = "homepage"
    HOMEPAGE_WEB = "homepage_web"
    HOMEPAGE_MOBILE = "homepage_mobile"
    CATEGORY = "category"
    BRAND = "brand"
    CATEGORY_TAG = "category_tag"
    PRODUCT = "product"
    CART = "cart"
    CHECKOUT = "checkout"
    WISHLIST = "wishlist"
    SEARCH = "search"
    NEW_ARRIVALS = "new_arrivals"
    TRENDING = "trending"
    CUSTOMER_FAVOURITES = "customer_favourites"
    BUSINESS_FAVOURITES = "business_favourites"
    LAUNCH_MODAL = "launch_modal"

    # PascalCase variants for compatibility with various frontend components
    HOME_P = "Home"
    CATEGORY_P = "Category"
    BRAND_P = "Brand"
    CATEGORY_TAG_P = "CategoryTag"
    PRODUCT_P = "Product"
    CART_P = "Cart"
    CHECKOUT_P = "Checkout"
    WISHLIST_P = "Wishlist"
    SEARCH_P = "Search"
    NEW_ARRIVALS_P = "NewArrivals"
    TRENDING_P = "Trending"
    CUSTOMER_FAVOURITES_P = "CustomerFavourites"
    BUSINESS_FAVOURITES_P = "BusinessFavourites"
    LAUNCH_MODAL_P = "LaunchModal"


# User Schemas

class AddressSnippet(CamelBaseModel):
    model_config = ConfigDict(extra='ignore')
    name: Optional[str] = None
    is_primary: Optional[bool] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    country: Optional[str] = "India"
    pincode: Optional[str] = None
    zip_code: Optional[str] = None
    location_link: Optional[str] = None
    google_location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class UserSnippet(CamelBaseModel):
    model_config = ConfigDict(extra='forbid')
    id: Optional[str] = Field(None, alias="_id")
    user_id: Optional[int] = None
    user_id_formatted: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    company_name: Optional[str] = None

class ProductSellerEntry(CamelBaseModel):
    model_config = ConfigDict(extra='forbid')
    seller_id: str
    stock: int = 0
    is_active: bool = False
    request_status: str = "pending"
    notes: Optional[str] = None

class ItemSnippet(CamelBaseModel):
    model_config = ConfigDict(extra='forbid')
    id: Optional[str] = Field(default=None, alias="_id")
    product_id: Optional[str] = None
    product: Optional[str] = None
    quantity: Optional[int] = None
    sell_as_case: Optional[bool] = None
    price: Optional[float] = None
    mrp: Optional[float] = None
    name: Optional[str] = None
    image: Optional[str] = None
    images: Optional[list] = None
    status: Optional[str] = None
    subtotal: Optional[float] = None
    out_of_stock: Optional[bool] = None
    sku: Optional[str] = None
    mrpPerCase: Optional[float] = None
    quantityPerCase: Optional[int] = None
    bundleId: Optional[str] = None
    bundleName: Optional[str] = None
    variantAttributes: Optional['VariantAttributes'] = None


class VariantOption(CamelBaseModel):
    model_config = ConfigDict(extra='forbid')
    value: Optional[str] = None
    price_modifier: Optional[float] = None
    stock: Optional[int] = None
    sku: Optional[str] = None
    attributes: Optional[VariantAttributes] = None
    price: Optional[float] = None

class VisibilityRuleSnippet(CamelBaseModel):
    model_config = ConfigDict(extra='forbid')
    page_type: Optional[str] = None
    page_ids: Optional[List[str]] = None

# Aliases for models and snippets
CartItem = ItemSnippet
OrderItem = ItemSnippet
VisibilityRule = VisibilityRuleSnippet

class ValetSnippet(CamelBaseModel):
    model_config = ConfigDict(extra='forbid')
    id: Optional[str] = Field(None, alias="_id")
    name: Optional[str] = None
    phone: Optional[str] = None

class ValetDeclineSnippet(CamelBaseModel):
    model_config = ConfigDict(extra='forbid')
    valet_id: Optional[str] = None
    reason: Optional[str] = None

ValetDeclineHistoryEntry = ValetDeclineSnippet

class DiscountSnippet(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    name: Optional[str] = None
    value: Optional[float] = None



class VariantAttributes(BaseModel):
    size: Optional[str] = None
    color: Optional[str] = None
    material: Optional[str] = None
    style: Optional[str] = None
    weight: Optional[str] = None
    flavor: Optional[str] = None

class NotificationMetadata(CamelBaseModel):
    order_id: Optional[str] = None
    product_id: Optional[str] = None
    url: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None

class ProductDetails(BaseModel):
    material: Optional[str] = None
    weight: Optional[str] = None
    dimensions: Optional[str] = None
    manufacturer: Optional[str] = None
    origin: Optional[str] = None
    warranty: Optional[str] = None

class ActivityMetadata(CamelBaseModel):
    page: Optional[str] = None
    reason: Optional[str] = None
    search_query: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    order_id: Optional[str] = None
    product_id: Optional[str] = None

class PincodeStat(BaseModel):
    pincode: str
    count: int
    
class SearchResultItem(BaseModel):
    id: str
    name: str
    type: str

class RecordItem(BaseModel):
    id: str
    amount: float
    date: str
    status: str

class SavedAddress(CamelBaseModel):
    id: str
    street: str
    city: str
    state: str
    pincode: str
    is_default: bool


class UserBase(CamelBaseModel):
    is_active: Optional[bool] = None
    max_concurrent_orders: Optional[int] = None
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: UserRole
    phone: Optional[str] = None
    alternate_phone: Optional[str] = None
    company_name: Optional[str] = None
    gstin: Optional[str] = None
    address: Optional[AddressSnippet] = None
    saved_addresses: List[AddressSnippet] = Field(default=[], description="List of saved addresses for the user")
    referral_code: Optional[str] = Field(default=None, description="Referral code used to sign up")
    is_email_verified: Optional[bool] = False
    device_token: Optional[str] = None
    preferredLanguage: Optional[str] = Field(default="en", description="User's preferred UI language (BCP-47 code, e.g. 'hi', 'ta')")
    approvalStatus: Optional[str] = "approved"
    isDeactivated: Optional[bool] = Field(default=False, validation_alias=AliasChoices("isDeactivated", "is_deactivated"))
    creditLimit: Optional[float] = 0
    creditUsed: Optional[float] = 0
    paymentTerms: Optional[str] = "30"
    assignedSalesperson: Optional[str] = None
    isSellerAdmin: Optional[bool] = Field(default=False, validation_alias=AliasChoices("isSellerAdmin", "is_seller_admin"))
    isOnDuty: Optional[bool] = False
    commissionOverridePct: Optional[float] = None
    serviceAreaZones: Optional[List[str]] = Field(default_factory=list)
    password: Optional[str] = None
    sessionId: Optional[str] = None
    effectiveRole: Optional[str] = None
    upiId: Optional[str] = None
    qrCodeUrl: Optional[str] = None
    bankAccountNumber: Optional[str] = None
    bankIfscCode: Optional[str] = None
    bankAccountHolder: Optional[str] = None
    bankName: Optional[str] = None
    # Device / verification metadata — populated at registration time, None for admin-created users.
    deviceId: Optional[str] = None
    msg91Token: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Jane Doe",
                "email": "jane@example.com",
                "role": "customer",
                "phone": "+919876543210",
                "companyName": "Jane Designs",
            }
        }
    )


class UserCreate(UserBase):
    email: EmailStr
    password: str


# Supported language codes for UI localisation (GIGW 3.0 compliance)
SUPPORTED_LANGUAGES = {"en", "hi", "bn", "te", "mr", "ta", "gu", "kn", "ml", "pa", "or", "ur"}


class UserUpdate(CamelBaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    alternate_phone: Optional[str] = None
    company_name: Optional[str] = None
    gstin: Optional[str] = None
    address: Optional[AddressSnippet] = None
    saved_addresses: Optional[List[AddressSnippet]] = None
    location_link: Optional[str] = None
    approval_status: Optional[ApprovalStatus] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_deactivated: Optional[bool] = None
    is_seller_admin: Optional[bool] = None
    is_on_duty: Optional[bool] = None
    credit_limit: Optional[float] = None
    credit_used: Optional[float] = None
    payment_terms: Optional[str] = None
    assigned_salesperson: Optional[str] = None
    is_email_verified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    preferredLanguage: Optional[str] = None
    upiId: Optional[str] = None
    qrCodeUrl: Optional[str] = None
    bankAccountNumber: Optional[str] = None
    bankIfscCode: Optional[str] = None
    bankAccountHolder: Optional[str] = None
    bankName: Optional[str] = None


class UserResponse(UserBase):
    id: str = Field(alias="_id")
    userId: Optional[int] = None
    userIdFormatted: Optional[str] = None
    role: Optional[str] = None
    effectiveRole: Optional[str] = None
    approvalStatus: Optional[str] = None
    is_active: bool = Field(validation_alias=AliasChoices("isActive", "is_active"))
    isDeactivated: Optional[bool] = Field(default=False, validation_alias=AliasChoices("isDeactivated", "is_deactivated"))
    creditLimit: float = Field(validation_alias=AliasChoices("creditLimit", "credit_limit"))
    creditUsed: float = Field(validation_alias=AliasChoices("creditUsed", "credit_used"))
    paymentTerms: Optional[int] = None
    assignedSalesperson: Optional[str] = None
    referralCode: Optional[str] = None
    isSellerAdmin: Optional[bool] = Field(default=False, validation_alias=AliasChoices("isSellerAdmin", "is_seller_admin"))
    commissionOverridePct: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


# Product Variation Schema
class ProductVariation(CamelBaseModel):
    name: str  # Variation name (e.g., "Color", "Size", "Pages")
    type: str  # Variation type (e.g., "color", "size", "pages", "quantity")
    options: List[VariantOption]  # List of options with value, price, stock, etc.
    # Example: [{"value": "Red", "priceModifier": 0, "stock": 10}, {"value": "Blue", "priceModifier": 5, "stock": 15}]


# Product Schemas

class ProductReviewResponse(CamelBaseModel):
    id: str = Field(alias="_id")
    product_id: str
    user_id: str
    rating: int
    review_text: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ClassificationTagResponse(CamelBaseModel):
    id: str = Field(alias="_id")
    name: str
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ReviewActionResponse(BaseModel):
    message: str
    review: ProductReviewResponse

class ClassificationActionResponse(BaseModel):
    message: str
    classification: ClassificationTagResponse


class BundleItemResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid')
    product_id: str
    product_name: Optional[str] = None
    quantity: int
    image: Optional[str] = None
    price: Optional[float] = None
    discount_price: Optional[float] = None
    product: Optional['Product'] = None
    line_mrp: Optional[float] = None

class BundleResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid')
    external_id: Optional[str] = None
    id: str = Field(alias="_id")
    name: str
    description: Optional[str] = None
    price: float
    discount_percentage: Optional[float] = None
    is_active: bool = True
    sales_count: Optional[int] = None
    items: List[BundleItemResponse] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Enriched fields
    totalMrp: Optional[float] = None
    savings: Optional[float] = None
    savingsPercent: Optional[float] = None
    isAvailable: Optional[bool] = None
    displayImage: Optional[str] = None

class BundlesListResponse(BaseModel):
    bundles: List[BundleResponse]
    total: int

class ProductBase(CamelBaseModel):
    name: str
    sku: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    collection: Optional[str] = None
    mrp: Optional[float] = None  # MRP per unit (retail; also used for business when selling by unit)
    mrp_per_case: Optional[float] = None  # MRP per case (business only)
    quantity_per_case: Optional[int] = None  # Units per case (for business case pricing and stock)
    stock: Optional[int] = None  # Total units (reduced by units sold or by cases * quantityPerCase)
    images: Optional[List[str]] = None  # Array of image URLs/paths
    videos: Optional[List[str]] = None  # Array of video URLs/paths
    is_active: bool = True
    is_exclusive: bool = False
    tags: Optional[List[str]] = Field(default=None, description="Search and categorization tags")

    variant_attributes: Optional[List[str]] = Field(
        default=None, description="List of variant attribute names like Color, Size"
    )
    variants: Optional[List[VariantOption]] = Field(
        default=None, description="Actual combinations of attributes with stock and price"
    )
    sellers: Optional[List[ProductSellerEntry]] = None
    catalogSellerIds: Optional[List[str]] = None
    rating: Optional[float] = None
    reviews: Optional[int] = None
    details: Optional[ProductDetails] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "A4 Notebook 200 Pages",
                "sku": "NB-A4-200",
                "category": "Notebooks",
                "mrp": 120.0,
                "stock": 500,
                "isActive": True,
                "description": "High quality ruled A4 notebook.",
            }
        }
    )


class ProductCreate(ProductBase):
    pass


class ProductUpdate(CamelBaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    collection: Optional[str] = None
    mrp: Optional[float] = None
    mrp_per_case: Optional[float] = None
    quantity_per_case: Optional[int] = None
    stock: Optional[int] = None
    images: Optional[List[str]] = None
    videos: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_exclusive: Optional[bool] = None
    tags: Optional[List[str]] = None
    variations: Optional[List[VariantOption]] = None
    variant_attributes: Optional[List[str]] = None
    variants: Optional[List[VariantOption]] = None



class BxGyEvaluationResponse(CamelBaseModel):
    discount: float = 0.0
    item_discounts: Optional[Dict[int, float]] = None
    bxgy_item_indices: Optional[List[int]] = None


class CouponValidationDetail(CamelBaseModel):
    code: str
    discount_type: str
    discount_value: float
    id: Optional[str] = None
    method: Optional[str] = None
    coupon_mode: Optional[str] = "override"
    type_of_discount: Optional[str] = None


class CouponValidationResponse(CamelBaseModel):
    valid: bool
    coupon: Optional[CouponValidationDetail] = None
    discount: float = 0.0
    message: Optional[str] = None
    eligible_item_indices: Optional[List[int]] = None
    item_discounts: Optional[Dict[int, float]] = None
    bxgy_item_indices: Optional[List[int]] = None

class CouponValidateCart(CamelBaseModel):
    """Validate discount against cart: backend computes eligible subtotal from items."""

    code: str
    items: List[ItemSnippet]  # [{ productId, quantity, sellAsCase? }]
    shipping_address: Optional[AddressSnippet] = None


# Discount Scheme Schemas (Business Segment / wholesaler)
class SchemeResponse(CamelBaseModel):
    id: str = Field(alias="_id")
    name: str
    description: Optional[str] = None
    discount_type: str  # percentage | fixed
    discount_value: float
    min_order_value: float = 0
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    is_active: bool = True
    applicable_roles: List[str] = ["wholesaler"]
    code: Optional[str] = None

    model_config = ConfigDict(extra='forbid')


# Banner Schemas
class BannerBase(CamelBaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: str
    display_order: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool = True
    is_published: bool = False
    visibility_rules: List[VisibilityRuleSnippet] = []
    user_segments: List[str] = ["all"]
    link_url: Optional[str] = None
    position: Optional[str] = None
    target_audience: Optional[str] = None
    zone_ids: Optional[List[str]] = None


class BannerCreate(BannerBase):
    pass


class BannerUpdate(CamelBaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    display_order: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    is_published: Optional[bool] = None
    visibility_rules: Optional[List[VisibilityRuleSnippet]] = None
    user_segments: Optional[List[str]] = None
    link_url: Optional[str] = None
    position: Optional[str] = None
    target_audience: Optional[str] = None
    zone_ids: Optional[List[str]] = None


class BannerResponse(BannerBase):
    id: str = Field(alias="_id")
    created_at: Optional[datetime] = None
    updated_at: datetime = Field(validation_alias=AliasChoices("updatedAt", "updated_at"))
    user: Optional[UserSnippet] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


# Brand Schemas

class BrandResponse(CamelBaseModel):
    id: str = Field(alias="_id")
    name: str
    slug: str
    logo_url: Optional[str] = None
    show_in_mobile_homepage: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class BrandCreate(CamelBaseModel):
    name: str
    logo_url: Optional[str] = ""
    show_in_mobile_homepage: bool = False
    is_active: Optional[bool] = True


class BrandUpdate(CamelBaseModel):
    name: Optional[str] = None
    logo_url: Optional[str] = None
    show_in_mobile_homepage: Optional[bool] = None
    is_active: Optional[bool] = None


# Auth Schemas
class LoginRequest(CamelBaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str

    @model_validator(mode="after")
    def validate_phone_or_email(self):
        # At least one of email or phone must be provided
        if not self.email and not self.phone:
            raise ValueError("Either email or phone must be provided")
        return self


class RegisterRequest(CamelBaseModel):
    # name and email are Optional at the API level to support the checkout
    # registration flow (which only requires phone + password).
    # The regular Create Account pages enforce name & email via frontend validation.
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str
    phone: str  # Always mandatory
    role: UserRole = UserRole.CUSTOMER  # Default to customer
    company_name: Optional[str] = None
    gstin: Optional[str] = None
    address: Optional[AddressSnippet] = None
    msg91Token: Optional[str] = None  # Token from MSG91 Widget/SDK
    otp: Optional[str] = None
    deviceId: Optional[str] = None
    approvalStatus: Optional[str] = None



class AuthResponse(CamelBaseModel):
    token: str
    refresh_token: Optional[str] = None
    session_id: Optional[str] = None
    user: UserResponse
    message: Optional[str] = None


# Contact Schemas



class SocialMedia(BaseModel):
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    twitter: Optional[str] = None
    whatsapp: Optional[str] = None
    youtube: Optional[str] = None
    linkedin: Optional[str] = None


class ContactBase(CamelBaseModel):
    addresses: Optional[List[Address]] = None  # Up to 2 addresses
    phone_numbers: Optional[List[str]] = None  # Up to 3 phone numbers
    email: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    display_order: Optional[int] = None
    social_media: Optional[SocialMedia] = None

    @field_validator("addresses")
    @classmethod
    def validate_addresses(cls, v):
        if v and len(v) > 2:
            raise ValueError("Maximum 2 addresses allowed")
        return v

    @field_validator("phone_numbers")
    @classmethod
    def validate_phone_numbers(cls, v):
        if v and len(v) > 3:
            raise ValueError("Maximum 3 phone numbers allowed")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if v is None or v == "":
            return None  # Allow None or empty string
        # Validate email format if value is provided
        import re

        email_pattern = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
        if not re.match(email_pattern, v):
            raise ValueError("Invalid email format")
        return v


class ContactCreate(ContactBase):
    pass


class ContactUpdate(CamelBaseModel):
    addresses: Optional[List[Address]] = None
    phone_numbers: Optional[List[str]] = None
    email: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    social_media: Optional[SocialMedia] = None


class ContactResponse(ContactBase):
    id: str = Field(alias="_id")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user: Optional[UserSnippet] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


# Support Ticket Schemas
class SupportTicketBase(CamelBaseModel):
    name: str
    email: str
    phone: str
    company: Optional[str] = None
    subject: str
    description: str
    category: str = "general"
    priority: str = "medium"
    attachments: Optional[List[str]] = None
    external_id: Optional[str] = None


class SupportTicketCreate(SupportTicketBase):
    pass


class SupportTicketUpdate(CamelBaseModel):
    status: Optional[str] = None  # open, in_progress, resolved, closed
    priority: Optional[str] = None
    assigned_to: Optional[str] = None


class TicketResponseCreate(BaseModel):
    message: str
    attachments: Optional[List[str]] = None


class TicketResponseItemInternal(CamelBaseModel):
    model_config = ConfigDict(extra="forbid")
    user: Optional[str] = None
    message: Optional[str] = None
    attachments: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    is_admin_response: Optional[bool] = None

class TicketResponseItem(CamelBaseModel):
    model_config = ConfigDict(extra="forbid")
    user: Optional[UserSnippet] = None
    message: Optional[str] = None
    attachments: Optional[List[str]] = None
    created_at: Optional[datetime] = None


class SupportTicketInternal(SupportTicketBase):
    # We rely on SupportTicketBase which is CamelBaseModel
    model_config = ConfigDict(extra='forbid')
    id: str = Field(alias="_id")
    ticket_number: str
    user: Optional[str] = None
    status: str
    assigned_to: Optional[str] = None
    responses: Optional[List[TicketResponseItemInternal]] = None
    resolved_at: Optional[str] = None
    closed_at: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    external_id: Optional[str] = None


class SupportTicketResponse(SupportTicketBase):
    id: str = Field(alias="_id")
    ticketNumber: str
    user: Optional[UserSnippet] = None
    status: str
    assignedTo: Optional[UserSnippet] = None
    responses: Optional[List[TicketResponseItem]] = None
    resolved_at: Optional[str] = None
    closed_at: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


# Delivery Charge Schemas
class DeliveryChargeTier(CamelBaseModel):
    model_config = ConfigDict(extra="forbid")
    min_order_value: Optional[float] = None
    max_order_value: Optional[float] = None
    charge: Optional[float] = None
    min_amount: Optional[float] = None
    max_amount: Optional[Union[float, str]] = None


class DeliveryChargeBase(CamelBaseModel):
    pincode: str
    state: str
    city: Optional[str] = ""
    district: str
    charge: Optional[float] = None
    min_cart_value: Optional[float] = None
    apply_default_charge: Optional[bool] = False
    tiers: Optional[List[DeliveryChargeTier]] = None
    serviceable_for_customer: Optional[bool] = False

    serviceable_for_wholesaler: Optional[bool] = False
    is_active: Optional[bool] = True
    description: Optional[str] = None
    location_id: Optional[int] = None  # Unique ID for state-district-city (for backward compatibility)
    urgent_delivery_available: Optional[bool] = False
    urgentDeliveryCharge: Optional[float] = None


class DeliveryChargeCreate(DeliveryChargeBase):
    pass


class DeliveryChargeUpdate(CamelBaseModel):
    pincode: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    charge: Optional[float] = None
    min_cart_value: Optional[float] = None
    apply_default_charge: Optional[bool] = None
    tiers: Optional[List[DeliveryChargeTier]] = None
    serviceable_for_customer: Optional[bool] = None

    serviceable_for_wholesaler: Optional[bool] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None
    urgent_delivery_available: Optional[bool] = None
    urgentDeliveryCharge: Optional[float] = None


class DeliveryChargeResponse(DeliveryChargeBase):
    id: str = Field(alias="_id")
    location_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


# Default Delivery Charge Schema
class DeliveryTier(CamelBaseModel):
    max_amount: Union[float, str]  # Can be a number or "Infinity"
    charge: float


class DefaultDeliveryChargeBase(CamelBaseModel):
    tiers: List[DeliveryTier]
    applicable_to_wholesaler: bool = True
    delivery_charge_gst: bool = False
    delivery_charge_gst_percentage: float = 18.0

    is_active: bool = True
    urgent_delivery_charge: Optional[float] = None


class DefaultDeliveryChargeCreate(DefaultDeliveryChargeBase):
    pass


class DefaultDeliveryChargeResponse(DefaultDeliveryChargeBase):
    id: str = Field(alias="_id")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


# Order Feedback Schemas
class OrderFeedbackBase(CamelBaseModel):
    order_id: Optional[str] = None
    rating: int  # 1-5
    comment: Optional[str] = None
    delivery_rating: Optional[int] = None  # 1-5
    delivery_comment: Optional[str] = None
    feedback_type: str = "order"  # "order" or "general"


class OrderFeedbackCreate(OrderFeedbackBase):
    pass


class OrderFeedbackResponse(OrderFeedbackBase):
    id: str = Field(alias="_id")
    userId: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user: Optional[UserSnippet] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


# Coach Mark Schemas
class CoachMarkBase(CamelBaseModel):
    anchor_id: str
    title: str
    description: str
    screen_name: Optional[str] = None
    sequence_order: Optional[int] = None
    is_active: bool = True


class CoachMarkCreate(CoachMarkBase):
    pass


class CoachMarkUpdate(CamelBaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    sequence_order: Optional[int] = None
    is_active: Optional[bool] = None


class CoachMarkResponse(CoachMarkBase):
    id: str = Field(alias="_id")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user: Optional[UserSnippet] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


# Search Tag Schemas
class SearchTagBase(CamelBaseModel):
    tag_id: Optional[str] = None
    name: str
    type: Literal["Occasion", "Intent", "Recipient"]
    is_active: bool = True
    categories: Optional[List[str]] = []
    sub_categories: Optional[List[str]] = []
    brands: Optional[List[str]] = []
    collections: Optional[List[str]] = []
    product_ids: Optional[List[str]] = []
    excluded_product_ids: Optional[List[str]] = []


class SearchTagCreate(SearchTagBase):
    pass


class SearchTagUpdate(CamelBaseModel):
    name: Optional[str] = None
    type: Optional[Literal["Occasion", "Intent", "Recipient"]] = None
    is_active: Optional[bool] = None
    categories: Optional[List[str]] = None
    sub_categories: Optional[List[str]] = None
    brands: Optional[List[str]] = None
    collections: Optional[List[str]] = None
    product_ids: Optional[List[str]] = None
    excluded_product_ids: Optional[List[str]] = None


class SearchTagResponse(SearchTagBase):
    id: str = Field(alias="_id")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user: Optional[UserSnippet] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


# Collection Schemas
class CollectionBase(CamelBaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool = True
    display_order: Optional[int] = None
    product_ids: List[str] = []
    visible_pages: List[str] = ["Home"]
    user_segments: List[str] = ["all"]
    visibility_rules: List[VisibilityRuleSnippet] = []


class CollectionCreate(CollectionBase):
    pass


class CollectionUpdate(CamelBaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    product_ids: Optional[List[str]] = None
    visible_pages: Optional[List[str]] = None
    user_segments: Optional[List[str]] = None
    visibility_rules: Optional[List[VisibilityRuleSnippet]] = None


class CollectionResponse(CollectionBase):
    id: str = Field(alias="_id")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user: Optional[UserSnippet] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


# Referral Schemas
class ReferralSegmentSetting(CamelBaseModel):
    segment: str  # "retail" or "business"
    discount_type: DiscountType = DiscountType.PERCENTAGE
    discount_value: float = 0
    is_active: bool = False


class ReferralSettingsResponse(BaseModel):
    retail: ReferralSegmentSetting
    business: ReferralSegmentSetting


class ReferralVerifyRequest(BaseModel):
    code: str


class ReferralVerifyResponse(CamelBaseModel):
    valid: bool
    discount_type: DiscountType
    discount_value: float
    referrer_name: str


class ReferralEligibilityResponse(CamelBaseModel):
    eligible: bool
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[float] = None
    message: Optional[str] = None


class ReferralPublicSchemeResponse(CamelBaseModel):
    is_active: bool
    discount_type: DiscountType
    discount_value: float


# Return Feature Schemas
class ReturnSettingsBase(CamelBaseModel):
    return_days: int = 7


class ReturnSettingsResponse(ReturnSettingsBase):
    pass


class ReturnSettingsUpdate(CamelBaseModel):
    return_days: Optional[int] = None


class ReturnItemSchema(CamelBaseModel):
    product_id: str
    quantity: int
    reason: str


class ReturnRequestBase(CamelBaseModel):
    order_id: str
    items: List[ReturnItemSchema]
    seller_id: Optional[str] = None
    delivery_slot_id: Optional[str] = None
    delivery_slot_date: Optional[str] = None
    payment_method: str  # 'cod' or 'upi'
    upi_payment_screenshot: Optional[str] = None
    notes: Optional[str] = None


class ReturnRequestCreate(ReturnRequestBase):
    pass


class ReturnRequestUpdate(CamelBaseModel):
    status: Optional[ReturnRequestStatus] = None
    valet_id: Optional[str] = None
    delivery_charge: Optional[float] = None
    notes: Optional[str] = None


class ReturnRequestResponse(CamelBaseModel):
    id: str = Field(alias="_id")
    order_id: str
    user_id: str
    items: List[ItemSnippet]  # populated items
    seller_id: Optional[str] = None
    delivery_slot_id: Optional[str] = None
    delivery_slot_date: Optional[str] = None
    payment_method: str
    upi_payment_screenshot: Optional[str] = None
    notes: Optional[str] = None
    status: ReturnRequestStatus
    valet_id: Optional[str] = None
    valet: Optional[ValetSnippet] = None  # populated valet
    pending_valet_id: Optional[str] = None
    valetDeclineHistory: Optional[List[ValetDeclineSnippet]] = None
    valetCascadeCount: Optional[int] = None
    valetAssignedAt: Optional[str] = None
    user: Optional[UserSnippet] = None  # populated user
    deliveryCharge: float
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


class ReturnRequest(CamelBaseModel):
    model_config = ConfigDict(extra='forbid')
    id: Optional[str] = Field(None, validation_alias=AliasChoices('_id', 'id'))
    order_id: Optional[str] = None
    user_id: Optional[str] = None
    valet_id: Optional[str] = None
    pending_valet_id: Optional[str] = None
    status: Optional[str] = None
    items: Optional[List[ReturnItemSchema]] = []
    payment_method: Optional[str] = None
    upi_payment_screenshot: Optional[str] = None
    notes: Optional[str] = None
    delivery_charge: Optional[float] = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    sellerId: Optional[str] = None
    deliverySlotId: Optional[str] = None
    deliverySlotDate: Optional[str] = None
    valetAssignedAt: Optional[str] = None
    valetCascadeCount: Optional[int] = 0
    valetDeclineHistory: Optional[List[ValetDeclineHistoryEntry]] = []
    user: Optional[UserSnippet] = None
    valet: Optional[ValetSnippet] = None


class ProductResponse(ProductBase):
    id: str = Field(alias="_id")
    productId: Optional[int] = None
    productIdFormatted: Optional[str] = None
    price: Optional[float] = None
    originalPrice: Optional[float] = None
    discountPercentage: Optional[float] = None
    defaultDiscountPercentage: Optional[float] = None
    applicableDiscounts: Optional[List[DiscountSnippet]] = None
    variations: Optional[List[VariantOption]] = None
    searchTags: Optional[List[str]] = None
    gst: Optional[float] = 0  # Evaluated from category level
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user: Optional[UserSnippet] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')



class RecommendationResponse(CamelBaseModel):
    new_arrivals: List[SkinnyProductResponse] = Field(default_factory=list)
    customer_favourites: List[SkinnyProductResponse] = Field(default_factory=list)
    trending_now: List[SkinnyProductResponse] = Field(default_factory=list)
    explore: List[SkinnyProductResponse] = Field(default_factory=list)
    wholesaler_favourites: List[SkinnyProductResponse] = Field(default_factory=list)
    business_favourites: List[SkinnyProductResponse] = Field(default_factory=list)
    section_order: List[str] = Field(default_factory=list)

class SkinnyProductResponse(CamelBaseModel):
    id: str = Field(alias="_id")
    product_id: Optional[int] = None
    product_id_formatted: Optional[str] = None
    name: str
    sku: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    brand: Optional[str] = None
    collection: Optional[str] = None
    mrp: float
    mrp_per_case: Optional[float] = None
    quantity_per_case: Optional[int] = None
    stock: Optional[int] = None
    is_active: bool = True
    tags: Optional[List[str]] = None
    price: Optional[float] = None
    originalPrice: Optional[float] = None
    discountPercentage: Optional[float] = None
    searchTags: Optional[List[str]] = None
    gst: Optional[float] = 0
    displayImage: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user: Optional[UserSnippet] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


class PaginatedProductResponse(CamelBaseModel):
    products: List[Union[ProductResponse, SkinnyProductResponse]]
    total_count: int
    brands: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    sub_categories: Optional[List[str]] = None
    collections: Optional[List[str]] = None
    used_fuzzy: Optional[bool] = False
    suggested_query: Optional[str] = None


# Discount (Coupon) Schemas
class QuantityTier(CamelBaseModel):
    quantity: int
    discount: float


# typeOfDiscount: product_discount | buy_x_get_y | total_order_discount | shipping_discount
# method: discount_code | automatic
# applicable_user_ids: when set, only these user ids can use (Selective Retail/Business)
class CouponBase(CamelBaseModel):
    type_of_discount: str = (
        "product_discount"  # product_discount | buy_x_get_y | total_order_discount | shipping_discount
    )
    code: Optional[str] = None  # required when method=discount_code; null for automatic
    method: str = "discount_code"  # discount_code | automatic
    discount_type: DiscountType
    discount_value: float
    quantity_tiers: Optional[List[QuantityTier]] = None
    min_purchase_amount: float = 0
    min_requirement_type: str = "none"  # none | min_amount | min_quantity
    min_quantity_of_eligible_items: Optional[int] = None  # when minRequirementType=min_quantity
    max_discount_amount: Optional[float] = None
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    usage_limit: Optional[int] = None
    is_active: bool = True
    applicable_roles: List[str] = ["customer"]
    applicable_user_ids: Optional[List[str]] = None  # selective retail/business: only these users
    applicable_categories: Optional[List[str]] = None  # deprecated
    applies_to_type: str = "all"
    applies_to_value_ids: Optional[List[str]] = None
    excluded_product_ids: Optional[List[str]] = None
    applicable_item_type: Optional[str] = None  # units | cases
    user_behavior: Optional[str] = None
    max_usage_per_user: Optional[int] = None
    buy_x_get_y_customer_gets_quantity: Optional[int] = None
    buy_x_get_y_customer_gets_applies_to_type: Optional[str] = None
    buy_x_get_y_customer_gets_applies_to_value_ids: Optional[List[str]] = None
    buy_x_get_y_customer_gets_discount_type: Optional[str] = None
    buy_x_get_y_customer_gets_discount_value: Optional[float] = None
    displayId: Optional[str] = None
    shippingStates: Optional[List[str]] = None
    shippingDistricts: Optional[List[str]] = None
    shippingPincodes: Optional[List[str]] = None
    applicablePaymentMethods: Optional[List[str]] = None
    couponMode: Optional[str] = "override"
    
    @model_validator(mode='after')
    def validate_dates(self):
        if self.validFrom and self.valid_until:
            from datetime import datetime, timezone
            try:
                start_dt = datetime.fromisoformat(self.validFrom.replace("Z", "+00:00")).replace(tzinfo=timezone.utc)
                end_dt = datetime.fromisoformat(self.validUntil.replace("Z", "+00:00")).replace(tzinfo=timezone.utc)
                if start_dt > end_dt:
                    raise ValueError("validUntil must be after validFrom")
            except ValueError as e:
                if str(e) == "validUntil must be after validFrom":
                    raise
        return self


class CouponCreate(CouponBase):
    pass


class CouponUpdate(CamelBaseModel):
    resolution: Optional[str] = None
    force: bool = False
    type_of_discount: Optional[str] = None
    code: Optional[str] = None
    method: Optional[str] = None
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[float] = None
    quantity_tiers: Optional[List[QuantityTier]] = None
    min_purchase_amount: Optional[float] = None
    min_requirement_type: Optional[str] = None
    min_quantity_of_eligible_items: Optional[int] = None
    max_discount_amount: Optional[float] = None
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    usage_limit: Optional[int] = None
    is_active: Optional[bool] = None
    applicable_roles: Optional[List[str]] = None
    applicable_user_ids: Optional[List[str]] = None
    applicable_categories: Optional[List[str]] = None
    applies_to_type: Optional[str] = None
    applies_to_value_ids: Optional[List[str]] = None
    excluded_product_ids: Optional[List[str]] = None
    applicable_item_type: Optional[str] = None
    user_behavior: Optional[str] = None
    max_usage_per_user: Optional[int] = None
    buy_x_get_y_customer_gets_quantity: Optional[int] = None
    buy_x_get_y_customer_gets_applies_to_type: Optional[str] = None
    buy_x_get_y_customer_gets_applies_to_value_ids: Optional[List[str]] = None
    buy_x_get_y_customer_gets_discount_type: Optional[str] = None
    buy_x_get_y_customer_gets_discount_value: Optional[float] = None
    shippingStates: Optional[List[str]] = None
    shippingDistricts: Optional[List[str]] = None
    shippingPincodes: Optional[List[str]] = None
    applicablePaymentMethods: Optional[List[str]] = None
    couponMode: Optional[str] = None


class CouponResponse(CouponBase):
    id: str = Field(alias="_id")
    used_count: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user: Optional[UserSnippet] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


class CouponValidate(BaseModel):
    code: str
    amount: float
    category: Optional[str] = None







# Discount Scheme Schemas (Business Segment / wholesaler)


# Banner Schemas








# Brand Schemas






# Auth Schemas






# Contact Schemas
class Address(CamelBaseModel):
    model_config = ConfigDict(extra="forbid")
    address: Optional[str] = None
    street: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    zip_code: Optional[str] = None
    pincode: Optional[str] = None
    country: Optional[str] = "India"
    google_location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @property
    def effective_pincode(self) -> Optional[str]:
        return self.pincode or self.zipCode












# Support Ticket Schemas












# Delivery Charge Schemas








# Default Delivery Charge Schema








# Order Feedback Schemas






# Coach Mark Schemas








# Search Tag Schemas








# Collection Schemas








# Referral Schemas



class PaginatedUsersResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid')
    users: List[UserResponse]
    total_count: int
    page: int
    limit: int

class PreferencesResponse(CamelBaseModel):
    preferred_language: str

class DutyStatusResponse(BaseModel):
    message: str

class MessageResponse(BaseModel):
    message: str

class CartResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid')
    items: List[ItemSnippet]
    subtotal: float
    item_count: int
    expires_at: Optional[str] = None

class SavedForLaterResponse(BaseModel):
    items: List[ItemSnippet]

class CheckPhoneResponse(BaseModel):
    status: str
    message: str

class VerifyOtpResponse(BaseModel):
    valid: bool
    message: str

class Msg91WebhookResponse(BaseModel):
    status: str

class VerifyMsg91TokenResponse(BaseModel):
    valid: bool
    phone: Optional[str] = None
    token: Optional[str] = None


class AdStats(CamelBaseModel):
    impressions: Optional[int] = 0
    clicks: Optional[int] = 0
    leads: Optional[int] = 0
    purchases: Optional[int] = 0
    add_to_cart: Optional[int] = 0
    conversions: Optional[int] = 0
    conversion_value: Optional[float] = 0.0
    ctr: Optional[float] = 0.0
    cvr: Optional[float] = 0.0

class AdBase(CamelBaseModel):
    name: Optional[str] = None
    platform: Optional[str] = None
    objective: Optional[str] = None
    status: Optional[str] = None
    budget_daily: Optional[float] = None
    budget_total: Optional[float] = None
    currency: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    target_url: Optional[str] = None
    headline: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    google_campaign_id: Optional[str] = None
    google_ad_group_id: Optional[str] = None
    meta_campaign_id: Optional[str] = None
    meta_ad_set_id: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    device: Optional[str] = None
    google_conversion_id: Optional[str] = None
    google_conversion_label: Optional[str] = None
    meta_pixel_id: Optional[str] = None
    notes: Optional[str] = None
    launched_at: Optional[str] = None
    stat_impressions: Optional[int] = 0
    stat_clicks: Optional[int] = 0
    stat_leads: Optional[int] = 0
    stat_purchases: Optional[int] = 0
    stat_add_to_cart: Optional[int] = 0
    stat_conversions: Optional[int] = 0
    stat_conversion_value: Optional[float] = 0.0
    stat_ctr: Optional[float] = 0.0
    stat_cvr: Optional[float] = 0.0

class AdCreate(AdBase):
    name: str
    platform: str

class AdUpdate(AdBase):
    pass

class AdStatusUpdate(BaseModel):
    status: str


class AdSummaryResponse(CamelBaseModel):
    model_config = ConfigDict(extra="forbid")
    total_views: int = Field(default=0)
    total_clicks: int = Field(default=0)
    active_campaigns: int = Field(default=0)
    total_spend_estimate: Optional[float] = Field(default=None)
    ctr: Optional[float] = None
    total_ads: Optional[int] = Field(default=0)
    active: Optional[int] = Field(default=0)
    paused: Optional[int] = Field(default=0)
    draft: Optional[int] = Field(default=0)
    total_impressions: Optional[int] = Field(default=0)
    total_conversions: Optional[int] = Field(default=0)
    overall_ctr: Optional[float] = Field(default=0.0)


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



class CouponCreateInternal(CouponBase):
    resolution: Optional[str] = None
    force: bool = False
    displayId: Optional[str] = None
    used_count: int = 0



class PromoStripBase(CamelBaseModel):
    text: str
    is_active: Optional[bool] = True
    zone_ids: Optional[List[str]] = None

class PromoStripCreate(PromoStripBase):
    pass

class PromoStripUpdate(CamelBaseModel):
    text: Optional[str] = None
    is_active: Optional[bool] = None
    zone_ids: Optional[List[str]] = None

class PromoStripResponse(PromoStripBase):
    id: str = Field(alias='_id')
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

















# --- DAO Internal Models ---
class UserInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid')
    user_id: int
    is_seller_admin: bool = False
    service_area_zones: Optional[List[str]] = None
    saved_addresses: Optional[List[SavedAddress]] = None
    is_on_duty: bool = False
    commission_override_pct: Optional[float] = None
    user_id_formatted: str
    name: str
    email: Optional[str] = None
    password: str
    role: str
    phone: str = ""
    company_name: str = ""
    gstin: Optional[str] = None
    address: Optional[Address] = None
    is_active: bool = True
    approval_status: str
    is_deactivated: bool = False
    credit_limit: Optional[float] = None
    credit_used: Optional[float] = None
    payment_terms: str = "30"
    assigned_salesperson: Optional[str] = None
    referral_code: Optional[str] = None
    is_email_verified: bool = False
    upi_id: Optional[str] = None
    qr_code_url: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_ifsc_code: Optional[str] = None
    bankAccountHolder: Optional[str] = None
    bankName: Optional[str] = None
    # Device / verification metadata captured at registration time.
    # otp is intentionally excluded — it is verified and deleted before create() is called.
    deviceId: Optional[str] = None
    msg91Token: Optional[str] = None

class UserInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid')
    user_id: Optional[int] = None
    user_id_formatted: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    gstin: Optional[str] = None
    address: Optional[Address] = None
    saved_addresses: Optional[List[Address]] = None
    is_active: Optional[bool] = None
    approval_status: Optional[str] = None
    is_deactivated: Optional[bool] = None
    is_seller_admin: Optional[bool] = None
    is_on_duty: Optional[bool] = None
    credit_limit: Optional[float] = None
    credit_used: Optional[float] = None
    payment_terms: Optional[str] = None
    assigned_salesperson: Optional[str] = None
    referral_code: Optional[str] = None
    is_email_verified: Optional[bool] = None
    service_area_zones: Optional[List[str]] = None
    commission_override_pct: Optional[float] = None
    upi_id: Optional[str] = None
    qr_code_url: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_ifsc_code: Optional[str] = None
    bankAccountHolder: Optional[str] = None
    bankName: Optional[str] = None


# --- Shared Payload DTOs ---

class AnalyticsEventPayload(CamelBaseModel):
    model_config = ConfigDict(extra="allow")
    returning: Optional[bool] = False
    product_id: Optional[str] = None
    product_name: Optional[str] = "Unknown"
    source: Optional[str] = "mobile_app"
    quantity: Optional[int] = 1
    query: Optional[str] = ""
    results_count: Optional[int] = 0
    reason: Optional[str] = "unknown"
    test_run_id: Optional[str] = None
    device: Optional[str] = None
    screen: Optional[str] = None


class AnalyticsEventCreate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid')
    type: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    source: Optional[str] = None
    filter_name: Optional[str] = None
    filter_value: Optional[str] = None
    category: Optional[str] = None
    payload: Optional[AnalyticsEventPayload] = None
    search_term: Optional[str] = None
    results_count: Optional[int] = None
    segment: Optional[str] = None
    product_ids: Optional[List[str]] = None
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    quantity: Optional[int] = None
    price: Optional[float] = None
    cart_value: Optional[float] = None
    is_returning: Optional[bool] = None
    page_views: Optional[int] = None
    page: Optional[str] = None
    reason: Optional[str] = None
    order_id: Optional[str] = None
    order_value: Optional[float] = None
    cartItems: Optional[List[ItemSnippet]] = None
    timestamp: Optional[str] = None
    os: Optional[str] = None
    browser: Optional[str] = None
    ipAddress: Optional[str] = None
    campaign: Optional[str] = None
    device: Optional[str] = None
    deviceType: Optional[str] = None
    deviceOsVersion: Optional[str] = None
    deviceModel: Optional[str] = None
    deviceAppVersion: Optional[str] = None


class Msg91WebhookPayload(CamelBaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Optional[str] = None
    type: Optional[str] = None


class TrackBeaconRequest(CamelBaseModel):
    model_config = ConfigDict(extra="forbid")
    event: Optional[str] = None
    page: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: Optional[str] = None
    user_id: Optional[str] = None


class TrackNotifyPincodeRequest(CamelBaseModel):
    product_id: str
    pincode: str
    product_name: Optional[str] = "Unknown"
    email: Optional[str] = None


class OrderItemCreate(CamelBaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: Optional[str] = None
    product: Optional[str] = None
    quantity: int = 1
    sell_as_case: Optional[bool] = False
    price: Optional[float] = None
    selected_variation: Optional[VariantAttributes] = None
    bundle_id: Optional[str] = None
    bundle_name: Optional[str] = None

    @model_validator(mode="after")
    def resolve_aliases(self) -> 'OrderItemCreate':
        if not self.product_id and self.product:
            self.product_id = self.product
        return self

    @property
    def variant_attributes(self) -> Optional[VariantAttributes]:
        return self.selected_variation

    @property
    def variantAttributes(self) -> Optional[VariantAttributes]:
        return self.selected_variation


class SellerDeliveryOption(CamelBaseModel):
    model_config = ConfigDict(extra="forbid")
    seller_id: str
    delivery_slot_id: Optional[str] = None
    delivery_slot_date: Optional[str] = None
    delivery_slot_config_id: Optional[str] = None
    is_urgent_delivery: Optional[bool] = False


class PushSubscriptionKeys(BaseModel):
    model_config = ConfigDict(extra="forbid")
    p256dh: str
    auth: str


class PushSubscription(CamelBaseModel):
    model_config = ConfigDict(extra="forbid")
    endpoint: str
    expiration_time: Optional[float] = None
    keys: PushSubscriptionKeys


# --- Router Response and Request DTOs ---

class ActivityLogResponse(CamelBaseModel):
    model_config = ConfigDict(extra="forbid")
    id: Optional[str] = Field(None, alias="_id")
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    action: Optional[str] = None
    meta: Optional[ActivityMetadata] = None
    is_guest: Optional[bool] = None


class PromoteGuestResponse(BaseModel):
    updated: int


class AvailabilityRequestResponse(CamelBaseModel):
    model_config = ConfigDict(extra="forbid")
    id: Optional[str] = Field(None, alias="_id")
    external_id: Optional[str] = None
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    pincode: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AvailabilityRequestListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    requests: List[AvailabilityRequestResponse] = []
    total: int = 0
    page: int = 1
    limit: int = 50


class DeliveryZoneResponse(CamelBaseModel):
    model_config = ConfigDict(extra="forbid")
    id: Optional[str] = Field(None, alias="_id")
    name: Optional[str] = None
    zone_id: Optional[str] = None
    zone_name: Optional[str] = None
    description: Optional[str] = None
    pincodes: Optional[List[str]] = None
    default_capacity: Optional[int] = None
    urgent_delivery_available: Optional[bool] = False
    is_active: Optional[bool] = True
    customer_type: Optional[str] = "retail"


class EligibleFeedbackResponse(CamelBaseModel):
    eligible_order_id: Optional[str] = None


class ReturnEligibilityItem(CamelBaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: str
    max_quantity: int
    reason: Optional[str] = None
    name: Optional[str] = None
    price: Optional[float] = None
    image: Optional[str] = None


class ReturnEligibilityResponse(CamelBaseModel):
    model_config = ConfigDict(extra="forbid")
    eligible_items: List[ReturnEligibilityItem] = []
    reason: Optional[str] = None
    return_delivery_charge: Optional[float] = 0.0


class UPIDetailsResponse(CamelBaseModel):
    upi_id: Optional[str] = None
    qr_code_url: Optional[str] = None
    instructions: Optional[str] = None
    message: Optional[str] = None


class ValetPayoutSettingsResponse(CamelBaseModel):
    delivery_charge_per_order: Optional[float] = None
    return_pickup_charge_per_order: Optional[float] = None
    updated_at: Optional[datetime] = None


class PincodeSearchResponse(CamelBaseModel):
    model_config = ConfigDict(extra="forbid")
    id: Optional[str] = Field(None, alias="_id")
    pincode: Optional[str] = None
    is_serviceable: Optional[bool] = None
    status: Optional[str] = None
    seller_count: Optional[int] = 0
    serviceable_seller_ids: Optional[List[str]] = []
    user_role: Optional[str] = "customer"
    user_id: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    searched_at: Optional[str] = None
    date: Optional[str] = None


class PincodeSearchStatsResponse(CamelBaseModel):
    model_config = ConfigDict(extra="forbid")
    total_searches: int = 0
    unique_pincodes: int = 0
    unique_pincodes_count: int = 0
    serviceable_searches: int = 0
    unserviceable_searches: int = 0
    top_unserviceable_pincodes: List[PincodeStat] = []
    top_searched_pincodes: List[PincodeStat] = []
    top_pincodes: List[PincodeStat] = []


class UploadImagesResponse(BaseModel):
    urls: List[str]


class UploadCSVResponse(BaseModel):
    success: bool
    imported: int
    failed: int


class SearchSuggestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    products: List[SearchResultItem] = []
    brands: List[SearchResultItem] = []
    categories: List[SearchResultItem] = []


class PushNotificationResponse(CamelBaseModel):
    model_config = ConfigDict(extra="forbid")
    id: Optional[str] = Field(None, alias="_id")
    title: Optional[str] = None
    message: Optional[str] = None
    link: Optional[str] = None
    target_segment_id: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PushAnalyticsResponse(BaseModel):
    delivered: int = 0
    clicked: int = 0


class VapidKeyResponse(CamelBaseModel):
    public_key: str


class SellerRequestCreate(BaseModel):
    subject: str
    description: str
    category: Optional[str] = "general"
    priority: Optional[str] = "medium"
    attachments: Optional[List[str]] = None


class SellerRequestResponseCreate(BaseModel):
    message: str
    attachments: Optional[List[str]] = None


class SellerRequestResponse(CamelBaseModel):
    model_config = ConfigDict(extra="forbid")
    id: Optional[str] = Field(None, alias="_id")
    subject: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    user: Optional[UserSnippet] = None
    attachments: Optional[List[str]] = None
    responses: Optional[List[TicketResponseItem]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UploadQRResponse(BaseModel):
    qrCodeUrl: str


class ValetEarningsResponse(BaseModel):
    valetId: str
    totalDeliveries: int = 0
    totalReturnPickups: int = 0
    deliveryRatePerOrder: Optional[float] = None
    returnRatePerOrder: Optional[float] = None
    totalEarned: Optional[float] = None
    records: List[RecordItem] = []




class ActivityCreate(CamelBaseModel):
    user_id: Optional[str] = None
    action: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[ActivityMetadata] = None

class ActivityUpdate(CamelBaseModel):
    user_id: Optional[str] = None
    action: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[ActivityMetadata] = None

class ActivityResponse(ActivityCreate):
    id: Optional[str] = Field(default='', alias='_id')

class SellerProductRequestCreate(BaseModel):
    stock: Optional[int] = 0
    notes: Optional[str] = None

class SellerProductApprove(BaseModel):
    status: str
    notes: Optional[str] = None

# --- Populated-order response models (used by orders router) ---
# NOTE: UserSnippet and ValetSnippet are the canonical ones defined at the
# top of this file with extra='forbid'. No duplicates here.

class PaymentSnippet(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    entries: List['PaymentEntry'] = []


class PopulatedOrderItemResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid')
    product: Optional['Product'] = None
    quantity: Optional[int] = None
    price: Optional[float] = None
    stock_status: Optional[str] = None
    tax_rate: Optional[float] = None
    tax_amount: Optional[float] = None


class PopulatedOrderResponse(CamelBaseModel):
    """Fully-populated order returned by GET /orders endpoints.

    Every field that orders.py passes into this constructor is declared here.
    extra='forbid' ensures nothing is silently dropped.
    """
    model_config = ConfigDict(extra='forbid')

    id: Optional[str] = Field(default=None, alias="_id")
    order_id: Optional[str] = None
    status: Optional[str] = None
    order_status: Optional[str] = None    # router alias for status

    user: Optional[UserSnippet] = None
    assigned_valet: Optional[ValetSnippet] = None
    payment: Optional[PaymentSnippet] = None
    payment_entries: Optional[List['PaymentEntry']] = None
    items: Optional[List[PopulatedOrderItemResponse]] = None

    # Financial summary
    sub_total: Optional[float] = None
    shipping_charge: Optional[float] = None
    total: Optional[float] = None
    total_amount: Optional[float] = None   # router alias for total
    delivery_fee: Optional[float] = None   # router alias for shipping
    discount: Optional[float] = None
    coupon_code: Optional[str] = None      # populated when Order model stores it

    # Payment
    payment_method: Optional[str] = None
    payment_status: Optional[str] = None

    # Addresses
    shipping_address: Optional[Address] = None
    billing_address: Optional[Address] = None
    address: Optional[Address] = None         # router alias for shippingAddress

    # Notes
    notes: Optional[str] = None
    order_notes: Optional[str] = None      # router alias for notes
    admin_notes: Optional[str] = None      # populated when Order model stores it
    valet_notes: Optional[str] = None      # populated when Order model stores it

    # Zone
    zone_id: Optional[str] = None          # populated when Order model stores it

    # Sub-orders
    sub_orders: Optional[List['SubOrder']] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class PaymentDetailsResponse(CamelBaseModel):
    upi_id: Optional[str] = None
    qr_code_url: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_ifsc_code: Optional[str] = None
    bank_account_holder: Optional[str] = None
    bank_name: Optional[str] = None

class SellerPayoutDetailResponse(CamelBaseModel):
    id: str
    seller_id: str
    seller_name: Optional[str] = None
    amount: float
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    status: str
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
    sub_order_ids: List[str] = []
    created_by: Optional[str] = None
    admin_paid_at: Optional[str] = None
    admin_paid_by: Optional[str] = None
    seller_received_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    # Seller payment details (shown to admin at payout time)
    seller_upi_id: Optional[str] = None
    seller_qr_code_url: Optional[str] = None
    seller_bank_account_number: Optional[str] = None
    seller_bank_ifsc_code: Optional[str] = None
    seller_bank_account_holder: Optional[str] = None
    seller_bank_name: Optional[str] = None

class ValetPayoutCreate(CamelBaseModel):
    valet_id: str
    amount: float = Field(..., ge=0)
    delivery_count: int = Field(default=0, ge=0)
    return_count: int = Field(default=0, ge=0)
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    notes: Optional[str] = None

class ValetPayoutDetailResponse(CamelBaseModel):
    id: str
    valet_id: str
    valet_name: Optional[str] = None
    valet_phone: Optional[str] = None
    amount: float
    delivery_count: int = 0
    return_count: int = 0
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    status: str
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
    admin_paid_at: Optional[str] = None
    admin_paid_by: Optional[str] = None
    valet_received_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    # Valet payment details
    valet_upi_id: Optional[str] = None
    valet_qr_code_url: Optional[str] = None
    valet_bank_account_number: Optional[str] = None
    valet_bank_ifsc_code: Optional[str] = None
    valet_bank_account_holder: Optional[str] = None
    valet_bank_name: Optional[str] = None

class MarkPaidRequest(CamelBaseModel):
    payment_method: str  # 'upi', 'bank_transfer', 'cash'
    payment_reference: Optional[str] = None
    notes: Optional[str] = None

UserResponse.model_rebuild()

from app.models.payment import PaymentEntry
from app.models.product import Product
from app.models.sub_order import SubOrder

PaymentSnippet.model_rebuild()
PopulatedOrderItemResponse.model_rebuild()
PopulatedOrderResponse.model_rebuild()
BundleItemResponse.model_rebuild()
