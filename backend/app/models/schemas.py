from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any, List, Literal, Optional, Union, Dict

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator, AliasChoices, RootModel


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    WHOLESALER = "wholesaler"
    CUSTOMER = "customer"
    VALET = "valet"


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

class AddressSnippet(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    name: Optional[str] = None
    isPrimary: Optional[bool] = None
    phone: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    locationLink: Optional[str] = None

class UserSnippet(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    id: Optional[str] = Field(None, alias="_id")
    userId: Optional[int] = Field(default=None, validation_alias=AliasChoices("userId", "user_id"))
    userIdFormatted: Optional[str] = Field(default=None, validation_alias=AliasChoices("userIdFormatted", "user_id_formatted"))
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    companyName: Optional[str] = Field(default=None, validation_alias=AliasChoices("companyName", "company_name"))

class ProductSellerEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    sellerId: str
    stock: int = 0
    isActive: bool = False
    requestStatus: str = "pending"
    notes: Optional[str] = None

class ItemSnippet(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    productId: Optional[str] = Field(default=None, validation_alias=AliasChoices("productId", "product_id"))
    product: Optional[str] = None
    quantity: Optional[int] = None
    sellAsCase: Optional[bool] = None
    price: Optional[float] = None
    mrp: Optional[float] = None
    name: Optional[str] = None
    image: Optional[str] = None
    status: Optional[str] = None
    variantAttributes: Optional['VariantAttributes'] = Field(default=None, validation_alias=AliasChoices("variantAttributes", "variant_attributes"))


class VariantOption(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    value: Optional[str] = None
    priceModifier: Optional[float] = None
    stock: Optional[int] = None
    sku: Optional[str] = None
    attributes: Optional[VariantAttributes] = None
    price: Optional[float] = None

class VisibilityRuleSnippet(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    type: Optional[str] = None
    value: Optional[str] = None

class SellerPermissionSnippet(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    canManageProducts: Optional[bool] = None
    canManageOrders: Optional[bool] = None
    serviceablePincodes: Optional[List[str]] = None
    urgentPincodes: Optional[List[str]] = None
    slotPincodes: Optional[List[str]] = None
    serviceableZoneIds: Optional[List[str]] = None

# Aliases for models and snippets
CartItem = ItemSnippet
OrderItem = ItemSnippet
VisibilityRule = VisibilityRuleSnippet
SellerPermissions = SellerPermissionSnippet

class ValetSnippet(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    id: Optional[str] = Field(None, alias="_id")
    name: Optional[str] = None
    phone: Optional[str] = None

class ValetDeclineSnippet(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    valetId: Optional[str] = None
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

class NotificationMetadata(BaseModel):
    orderId: Optional[str] = None
    productId: Optional[str] = None
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

class ActivityMetadata(BaseModel):
    page: Optional[str] = None
    reason: Optional[str] = None
    search_query: Optional[str] = None
    ipAddress: Optional[str] = None
    userAgent: Optional[str] = None
    orderId: Optional[str] = None
    productId: Optional[str] = None

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

class SavedAddress(BaseModel):
    id: str
    street: str
    city: str
    state: str
    pincode: str
    isDefault: bool

class SellerPermission(BaseModel):
    module: str
    access: str


class UserBase(BaseModel):
    isActive: Optional[bool] = None
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: UserRole
    phone: Optional[str] = None
    alternatePhone: Optional[str] = None
    companyName: Optional[str] = None
    gstin: Optional[str] = None
    address: Optional[AddressSnippet] = None
    savedAddresses: List[AddressSnippet] = Field(default=[], description="List of saved addresses for the user")
    referralCode: Optional[str] = Field(default=None, description="Referral code used to sign up")
    isEmailVerified: Optional[bool] = False
    preferredLanguage: Optional[str] = Field(default="en", description="User's preferred UI language (BCP-47 code, e.g. 'hi', 'ta')")
    approvalStatus: Optional[str] = "approved"
    isDeactivated: Optional[bool] = Field(default=False, validation_alias=AliasChoices("isDeactivated", "is_deactivated"))
    creditLimit: Optional[float] = 0
    creditUsed: Optional[float] = 0
    paymentTerms: Optional[str] = "30"
    assignedSalesperson: Optional[str] = Field(default=None, validation_alias=AliasChoices("assignedSalesperson", "assigned_salesperson"))
    isSellerAdmin: Optional[bool] = Field(default=False, validation_alias=AliasChoices("isSellerAdmin", "is_seller_admin"))
    isOnDuty: Optional[bool] = False
    commissionOverridePct: Optional[float] = Field(default=None, validation_alias=AliasChoices("commissionOverridePct", "commission_override_pct"))
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = Field(default_factory=list)
    password: Optional[str] = None
    sessionId: Optional[str] = None
    effectiveRole: Optional[str] = Field(default=None, validation_alias=AliasChoices("effectiveRole", "effective_role"))
    upiId: Optional[str] = None
    qrCodeUrl: Optional[str] = None
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


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    alternatePhone: Optional[str] = None
    companyName: Optional[str] = None
    gstin: Optional[str] = None
    address: Optional[AddressSnippet] = None
    savedAddresses: Optional[List[AddressSnippet]] = None
    locationLink: Optional[str] = None
    approvalStatus: Optional[ApprovalStatus] = None
    isActive: Optional[bool] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = Field(default=None, validation_alias=AliasChoices("assignedSalesperson", "assigned_salesperson"))
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = Field(default=None, validation_alias=AliasChoices("commissionOverridePct", "commission_override_pct"))
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = Field(default=None, validation_alias=AliasChoices("referralCode", "referral_code"))
    preferredLanguage: Optional[str] = None
    upiId: Optional[str] = None
    qrCodeUrl: Optional[str] = None


class UserResponse(UserBase):
    id: str = Field(alias="_id")
    userId: Optional[int] = Field(default=None, validation_alias=AliasChoices("userId", "user_id"))
    userIdFormatted: Optional[str] = Field(default=None, validation_alias=AliasChoices("userIdFormatted", "user_id_formatted"))
    role: Optional[str] = None
    effectiveRole: Optional[str] = Field(default=None, validation_alias=AliasChoices("effectiveRole", "effective_role"))
    approvalStatus: Optional[str] = Field(default=None, validation_alias=AliasChoices("approvalStatus", "approval_status"))
    isActive: bool = Field(validation_alias=AliasChoices("isActive", "is_active"))
    isDeactivated: Optional[bool] = Field(default=False, validation_alias=AliasChoices("isDeactivated", "is_deactivated"))
    creditLimit: float = Field(validation_alias=AliasChoices("creditLimit", "credit_limit"))
    creditUsed: float = Field(validation_alias=AliasChoices("creditUsed", "credit_used"))
    paymentTerms: Optional[int] = Field(default=None, validation_alias=AliasChoices("paymentTerms", "payment_terms"))
    assignedSalesperson: Optional[str] = Field(default=None, validation_alias=AliasChoices("assignedSalesperson", "assigned_salesperson"))
    referralCode: Optional[str] = Field(default=None, validation_alias=AliasChoices("referralCode", "referral_code"))
    isSellerAdmin: Optional[bool] = Field(default=False, validation_alias=AliasChoices("isSellerAdmin", "is_seller_admin"))
    sellerPermissions: Optional[SellerPermissionSnippet] = Field(default=None, validation_alias=AliasChoices("sellerPermissions", "seller_permissions"))
    commissionOverridePct: Optional[float] = Field(default=None, validation_alias=AliasChoices("commissionOverridePct", "commission_override_pct"))
    createdAt: datetime = Field(validation_alias=AliasChoices("createdAt", "created_at"))
    updatedAt: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("updatedAt", "updated_at"))

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


# Product Variation Schema
class ProductVariation(BaseModel):
    name: str  # Variation name (e.g., "Color", "Size", "Pages")
    type: str  # Variation type (e.g., "color", "size", "pages", "quantity")
    options: List[VariantOption]  # List of options with value, price, stock, etc.
    # Example: [{"value": "Red", "priceModifier": 0, "stock": 10}, {"value": "Blue", "priceModifier": 5, "stock": 15}]


# Product Schemas

class ProductReviewResponse(BaseModel):
    id: str = Field(alias="_id")
    productId: str
    userId: str
    rating: int
    reviewText: Optional[str] = None
    status: str
    createdAt: Optional[str] = None
    updatedAt: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("updatedAt", "updated_at"))

class ClassificationTagResponse(BaseModel):
    id: str = Field(alias="_id")
    name: str
    isActive: bool = Field(validation_alias=AliasChoices("isActive", "is_active"))
    createdAt: Optional[str] = None
    updatedAt: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("updatedAt", "updated_at"))

class ReviewActionResponse(BaseModel):
    message: str
    review: ProductReviewResponse

class ClassificationActionResponse(BaseModel):
    message: str
    classification: ClassificationTagResponse


class BundleItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    productId: str
    productName: Optional[str] = None
    quantity: int
    image: Optional[str] = None
    price: Optional[float] = None
    discountPrice: Optional[float] = None
    product: Optional['Product'] = None
    lineMrp: Optional[float] = None

class BundleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    external_id: Optional[str] = None
    id: str = Field(alias="_id")
    name: str
    description: Optional[str] = None
    price: float
    discountPercentage: Optional[float] = None
    isActive: bool = Field(validation_alias=AliasChoices("isActive", "is_active"))
    salesCount: Optional[int] = None
    items: List[BundleItemResponse] = []
    createdAt: Optional[str] = None
    updatedAt: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("updatedAt", "updated_at"))
    
    # Enriched fields
    totalMrp: Optional[float] = None
    savings: Optional[float] = None
    savingsPercent: Optional[float] = None
    isAvailable: Optional[bool] = None
    displayImage: Optional[str] = None

class BundlesListResponse(BaseModel):
    bundles: List[BundleResponse]
    total: int

class ProductBase(BaseModel):
    name: str
    sku: Optional[str] = None
    category: str
    subCategory: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    collection: Optional[str] = None
    mrp: float  # MRP per unit (retail; also used for business when selling by unit)
    mrpPerCase: Optional[float] = None  # MRP per case (business only)
    quantityPerCase: Optional[int] = None  # Units per case (for business case pricing and stock)
    stock: Optional[int] = None  # Total units (reduced by units sold or by cases * quantityPerCase)
    images: Optional[List[str]] = None  # Array of image URLs/paths
    videos: Optional[List[str]] = None  # Array of video URLs/paths
    isActive: bool = True
    isExclusive: bool = False
    tags: Optional[List[str]] = Field(default=None, description="Search and categorization tags")

    variantAttributes: Optional[List[str]] = Field(
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


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    subCategory: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    collection: Optional[str] = None
    mrp: Optional[float] = None
    mrpPerCase: Optional[float] = None
    quantityPerCase: Optional[int] = None
    stock: Optional[int] = None
    images: Optional[List[str]] = None
    videos: Optional[List[str]] = None
    isActive: Optional[bool] = None
    isExclusive: Optional[bool] = None
    tags: Optional[List[str]] = None
    variations: Optional[List[VariantOption]] = None
    variantAttributes: Optional[List[str]] = None
    variants: Optional[List[VariantOption]] = None



class CouponValidationDetail(BaseModel):
    code: str
    discountType: str
    discountValue: float

class CouponValidationResponse(BaseModel):
    valid: bool
    coupon: Optional[CouponValidationDetail] = None
    discount: float

class CouponValidateCart(BaseModel):
    """Validate discount against cart: backend computes eligible subtotal from items."""

    code: str
    items: List[ItemSnippet]  # [{ productId, quantity, sellAsCase? }]
    shippingAddress: Optional[AddressSnippet] = None


# Discount Scheme Schemas (Business Segment / wholesaler)
class SchemeResponse(BaseModel):
    id: str = Field(alias="_id")
    name: str
    description: Optional[str] = None
    discountType: str  # percentage | fixed
    discountValue: float
    minOrderValue: float = 0
    validFrom: Optional[str] = None
    validUntil: Optional[str] = None
    isActive: bool = True
    applicableRoles: List[str] = ["wholesaler"]
    code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


# Banner Schemas
class BannerBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    imageUrl: str
    displayOrder: Optional[int] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    isActive: bool = True
    isPublished: bool = False
    visibilityRules: List[VisibilityRuleSnippet] = []
    userSegments: List[str] = ["all"]
    linkUrl: Optional[str] = None
    position: Optional[str] = None
    targetAudience: Optional[str] = None


class BannerCreate(BannerBase):
    pass


class BannerUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    imageUrl: Optional[str] = None
    displayOrder: Optional[int] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    isActive: Optional[bool] = None
    isPublished: Optional[bool] = None
    visibilityRules: Optional[List[VisibilityRuleSnippet]] = None
    userSegments: Optional[List[str]] = None
    linkUrl: Optional[str] = None


class BannerResponse(BannerBase):
    id: str = Field(alias="_id")
    createdAt: datetime = Field(validation_alias=AliasChoices("createdAt", "created_at"))
    updatedAt: str
    user: Optional[UserSnippet] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


# Brand Schemas

class BrandResponse(BaseModel):
    id: str = Field(alias="_id")
    name: str
    slug: str
    logoUrl: Optional[str] = None
    showInMobileHomepage: bool = False
    isActive: bool = True
    createdAt: Optional[str] = None
    updatedAt: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("updatedAt", "updated_at"))

class BrandCreate(BaseModel):
    name: str
    logoUrl: Optional[str] = ""
    showInMobileHomepage: bool = False
    isActive: Optional[bool] = True


class BrandUpdate(BaseModel):
    name: Optional[str] = None
    logoUrl: Optional[str] = None
    showInMobileHomepage: Optional[bool] = None
    isActive: Optional[bool] = None


# Auth Schemas
class LoginRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str

    @model_validator(mode="after")
    def validate_phone_or_email(self):
        # At least one of email or phone must be provided
        if not self.email and not self.phone:
            raise ValueError("Either email or phone must be provided")
        return self


class RegisterRequest(BaseModel):
    # name and email are Optional at the API level to support the checkout
    # registration flow (which only requires phone + password).
    # The regular Create Account pages enforce name & email via frontend validation.
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str
    phone: str  # Always mandatory
    role: UserRole = UserRole.CUSTOMER  # Default to customer
    companyName: Optional[str] = None
    address: Optional[AddressSnippet] = None
    msg91Token: Optional[str] = None  # Token from MSG91 Widget/SDK
    otp: Optional[str] = None
    deviceId: Optional[str] = None
    approvalStatus: Optional[str] = None



class AuthResponse(BaseModel):
    token: str
    refreshToken: Optional[str] = None
    sessionId: Optional[str] = None
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


class ContactBase(BaseModel):
    addresses: Optional[List[Address]] = None  # Up to 2 addresses
    phoneNumbers: Optional[List[str]] = None  # Up to 3 phone numbers
    email: Optional[str] = None
    description: Optional[str] = None
    isActive: bool = True
    displayOrder: Optional[int] = None
    socialMedia: Optional[SocialMedia] = None

    @field_validator("addresses")
    @classmethod
    def validate_addresses(cls, v):
        if v and len(v) > 2:
            raise ValueError("Maximum 2 addresses allowed")
        return v

    @field_validator("phoneNumbers")
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


class ContactUpdate(BaseModel):
    addresses: Optional[List[Address]] = None
    phoneNumbers: Optional[List[str]] = None
    email: Optional[str] = None
    description: Optional[str] = None
    isActive: Optional[bool] = None
    displayOrder: Optional[int] = None
    socialMedia: Optional[SocialMedia] = None


class ContactResponse(ContactBase):
    id: str = Field(alias="_id")
    createdAt: datetime = Field(validation_alias=AliasChoices("createdAt", "created_at"))
    updatedAt: str
    user: Optional[UserSnippet] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


# Support Ticket Schemas
class SupportTicketBase(BaseModel):
    name: str
    email: str
    phone: str
    company: Optional[str] = None
    subject: str
    description: str
    category: str = "general"
    priority: str = "medium"
    attachments: Optional[List[str]] = None
    externalId: Optional[str] = Field(default=None, alias="externalId")


class SupportTicketCreate(SupportTicketBase):
    pass


class SupportTicketUpdate(BaseModel):
    status: Optional[str] = None  # open, in_progress, resolved, closed
    priority: Optional[str] = None
    assignedTo: Optional[str] = None


class TicketResponseCreate(BaseModel):
    message: str
    attachments: Optional[List[str]] = None


class TicketResponseItemInternal(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    user: Optional[str] = None
    message: Optional[str] = None
    attachments: Optional[List[str]] = None
    createdAt: Optional[str] = None

class TicketResponseItem(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    user: Optional[UserSnippet] = None
    message: Optional[str] = None
    attachments: Optional[List[str]] = None
    createdAt: Optional[str] = None


class SupportTicketInternal(SupportTicketBase):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    id: str = Field(alias="_id")
    ticketNumber: str
    user: Optional[str] = None
    status: str
    assignedTo: Optional[str] = None
    responses: Optional[List[TicketResponseItemInternal]] = None
    resolvedAt: Optional[str] = None
    closedAt: Optional[str] = None
    createdAt: datetime = Field(validation_alias=AliasChoices("createdAt", "created_at"))
    updatedAt: str
    externalId: Optional[str] = None


class SupportTicketResponse(SupportTicketBase):
    id: str = Field(alias="_id")
    ticketNumber: str
    user: Optional[UserSnippet] = None
    status: str
    assignedTo: Optional[UserSnippet] = None
    responses: Optional[List[TicketResponseItem]] = None
    resolvedAt: Optional[str] = None
    closedAt: Optional[str] = None
    createdAt: datetime = Field(validation_alias=AliasChoices("createdAt", "created_at"))
    updatedAt: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


# Delivery Charge Schemas
class DeliveryChargeTier(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    minOrderValue: Optional[float] = None
    maxOrderValue: Optional[float] = None
    charge: Optional[float] = None
    minAmount: Optional[float] = None
    maxAmount: Optional[Union[float, str]] = None


class DeliveryChargeBase(BaseModel):
    pincode: str
    state: str
    city: Optional[str] = ""
    district: str
    charge: Optional[float] = None
    minCartValue: Optional[float] = None
    applyDefaultCharge: Optional[bool] = False
    tiers: Optional[List[DeliveryChargeTier]] = None
    serviceableForCustomer: Optional[bool] = False

    serviceableForWholesaler: Optional[bool] = False
    isActive: Optional[bool] = True
    description: Optional[str] = None
    locationId: Optional[int] = None  # Unique ID for state-district-city (for backward compatibility)
    urgentDeliveryAvailable: Optional[bool] = False
    urgentDeliveryCharge: Optional[float] = None


class DeliveryChargeCreate(DeliveryChargeBase):
    pass


class DeliveryChargeUpdate(BaseModel):
    pincode: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    charge: Optional[float] = None
    minCartValue: Optional[float] = None
    applyDefaultCharge: Optional[bool] = None
    tiers: Optional[List[DeliveryChargeTier]] = None
    serviceableForCustomer: Optional[bool] = None

    serviceableForWholesaler: Optional[bool] = None
    isActive: Optional[bool] = None
    description: Optional[str] = None
    urgentDeliveryAvailable: Optional[bool] = None
    urgentDeliveryCharge: Optional[float] = None


class DeliveryChargeResponse(DeliveryChargeBase):
    id: str = Field(alias="_id")
    locationId: Optional[int] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("updatedAt", "updated_at"))

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


# Default Delivery Charge Schema
class DeliveryTier(BaseModel):
    maxAmount: Union[float, str]  # Can be a number or "Infinity"
    charge: float


class DefaultDeliveryChargeBase(BaseModel):
    tiers: List[DeliveryTier]
    applicableToWholesaler: bool = True
    deliveryChargeGst: bool = False
    deliveryChargeGstPercentage: float = 18.0

    isActive: bool = True
    urgentDeliveryCharge: Optional[float] = None


class DefaultDeliveryChargeCreate(DefaultDeliveryChargeBase):
    pass


class DefaultDeliveryChargeResponse(DefaultDeliveryChargeBase):
    id: str = Field(alias="_id")
    createdAt: Optional[str] = None
    updatedAt: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("updatedAt", "updated_at"))

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


# Order Feedback Schemas
class OrderFeedbackBase(BaseModel):
    orderId: Optional[str] = None
    rating: int  # 1-5
    comment: Optional[str] = None
    deliveryRating: Optional[int] = None  # 1-5
    deliveryComment: Optional[str] = None
    feedbackType: str = "order"  # "order" or "general"


class OrderFeedbackCreate(OrderFeedbackBase):
    pass


class OrderFeedbackResponse(OrderFeedbackBase):
    id: str = Field(alias="_id")
    userId: str
    createdAt: datetime = Field(validation_alias=AliasChoices("createdAt", "created_at"))
    updatedAt: str
    user: Optional[UserSnippet] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


# Coach Mark Schemas
class CoachMarkBase(BaseModel):
    anchorId: str
    title: str
    description: str
    screenName: Optional[str] = None
    sequenceOrder: Optional[int] = None
    isActive: bool = True


class CoachMarkCreate(CoachMarkBase):
    pass


class CoachMarkUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    sequenceOrder: Optional[int] = None
    isActive: Optional[bool] = None


class CoachMarkResponse(CoachMarkBase):
    id: str = Field(alias="_id")
    createdAt: datetime = Field(validation_alias=AliasChoices("createdAt", "created_at"))
    updatedAt: str
    user: Optional[UserSnippet] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


# Search Tag Schemas
class SearchTagBase(BaseModel):
    tagId: Optional[str] = None
    name: str
    type: Literal["Occasion", "Intent", "Recipient"]
    isActive: bool = True
    categories: Optional[List[str]] = []
    subCategories: Optional[List[str]] = []
    brands: Optional[List[str]] = []
    collections: Optional[List[str]] = []
    productIds: Optional[List[str]] = []
    excludedProductIds: Optional[List[str]] = []


class SearchTagCreate(SearchTagBase):
    pass


class SearchTagUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[Literal["Occasion", "Intent", "Recipient"]] = None
    isActive: Optional[bool] = None
    categories: Optional[List[str]] = None
    subCategories: Optional[List[str]] = None
    brands: Optional[List[str]] = None
    collections: Optional[List[str]] = None
    productIds: Optional[List[str]] = None
    excludedProductIds: Optional[List[str]] = None


class SearchTagResponse(SearchTagBase):
    id: str = Field(alias="_id")
    createdAt: datetime = Field(validation_alias=AliasChoices("createdAt", "created_at"))
    updatedAt: str
    user: Optional[UserSnippet] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


# Collection Schemas
class CollectionBase(BaseModel):
    name: str
    description: Optional[str] = None
    imageUrl: Optional[str] = None
    isActive: bool = True
    displayOrder: Optional[int] = None
    productIds: List[str] = []
    visiblePages: List[str] = ["Home"]
    userSegments: List[str] = ["all"]
    visibilityRules: List[VisibilityRuleSnippet] = []


class CollectionCreate(CollectionBase):
    pass


class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    imageUrl: Optional[str] = None
    isActive: Optional[bool] = None
    displayOrder: Optional[int] = None
    productIds: Optional[List[str]] = None
    visiblePages: Optional[List[str]] = None
    userSegments: Optional[List[str]] = None
    visibilityRules: Optional[List[VisibilityRuleSnippet]] = None


class CollectionResponse(CollectionBase):
    id: str = Field(alias="_id")
    createdAt: datetime = Field(validation_alias=AliasChoices("createdAt", "created_at"))
    updatedAt: str
    user: Optional[UserSnippet] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


# Referral Schemas
class ReferralSegmentSetting(BaseModel):
    segment: str  # "retail" or "business"
    discountType: DiscountType = DiscountType.PERCENTAGE
    discountValue: float = 0
    isActive: bool = False


class ReferralSettingsResponse(BaseModel):
    retail: ReferralSegmentSetting
    business: ReferralSegmentSetting


class ReferralVerifyRequest(BaseModel):
    code: str


class ReferralVerifyResponse(BaseModel):
    valid: bool
    discountType: DiscountType
    discountValue: float
    referrerName: str


class ReferralEligibilityResponse(BaseModel):
    eligible: bool
    discountType: Optional[DiscountType] = None
    discountValue: Optional[float] = None
    message: Optional[str] = None


class ReferralPublicSchemeResponse(BaseModel):
    isActive: bool = Field(validation_alias=AliasChoices("isActive", "is_active"))
    discountType: DiscountType
    discountValue: float


# Return Feature Schemas
class ReturnSettingsBase(BaseModel):
    returnDays: int = 7


class ReturnSettingsResponse(ReturnSettingsBase):
    pass


class ReturnSettingsUpdate(BaseModel):
    returnDays: Optional[int] = None


class ReturnItemSchema(BaseModel):
    productId: str
    quantity: int
    reason: str


class ReturnRequestBase(BaseModel):
    orderId: str
    items: List[ReturnItemSchema]
    sellerId: Optional[str] = None
    deliverySlotId: Optional[str] = None
    deliverySlotDate: Optional[str] = None
    paymentMethod: str  # 'cod' or 'upi'
    upiPaymentScreenshot: Optional[str] = None
    notes: Optional[str] = None


class ReturnRequestCreate(ReturnRequestBase):
    pass


class ReturnRequestUpdate(BaseModel):
    status: Optional[ReturnRequestStatus] = None
    valetId: Optional[str] = None
    deliveryCharge: Optional[float] = None
    notes: Optional[str] = None


class ReturnRequestResponse(BaseModel):
    id: str = Field(alias="_id")
    orderId: str
    userId: str
    items: List[ItemSnippet]  # populated items
    sellerId: Optional[str] = None
    deliverySlotId: Optional[str] = None
    deliverySlotDate: Optional[str] = None
    paymentMethod: str
    upiPaymentScreenshot: Optional[str] = None
    notes: Optional[str] = None
    status: ReturnRequestStatus
    valetId: Optional[str] = None
    valet: Optional[ValetSnippet] = None  # populated valet
    pendingValetId: Optional[str] = None
    valetDeclineHistory: Optional[List[ValetDeclineSnippet]] = None
    valetCascadeCount: Optional[int] = None
    valetAssignedAt: Optional[str] = None
    user: Optional[UserSnippet] = None  # populated user
    deliveryCharge: float
    createdAt: datetime = Field(validation_alias=AliasChoices("createdAt", "created_at"))
    updatedAt: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


class ReturnRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    id: Optional[str] = Field(None, validation_alias=AliasChoices('_id', 'id'))
    orderId: Optional[str] = None
    userId: Optional[str] = None
    valetId: Optional[str] = None
    pendingValetId: Optional[str] = None
    status: Optional[str] = None
    items: Optional[List[ReturnItemSchema]] = []
    paymentMethod: Optional[str] = None
    upiPaymentScreenshot: Optional[str] = None
    notes: Optional[str] = None
    deliveryCharge: Optional[float] = 0.0
    createdAt: Optional[str] = None
    updatedAt: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("updatedAt", "updated_at"))
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
    createdAt: datetime = Field(validation_alias=AliasChoices("createdAt", "created_at"))
    updatedAt: str
    user: Optional[UserSnippet] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


class SkinnyProductResponse(BaseModel):
    id: str = Field(alias="_id")
    productId: Optional[int] = None
    productIdFormatted: Optional[str] = None
    name: str
    sku: Optional[str] = None
    category: str
    subCategory: Optional[str] = None
    brand: Optional[str] = None
    collection: Optional[str] = None
    mrp: float
    mrpPerCase: Optional[float] = None
    quantityPerCase: Optional[int] = None
    stock: Optional[int] = None
    isActive: bool = True
    tags: Optional[List[str]] = None
    price: Optional[float] = None
    originalPrice: Optional[float] = None
    discountPercentage: Optional[float] = None
    searchTags: Optional[List[str]] = None
    gst: Optional[float] = 0
    displayImage: Optional[str] = None
    createdAt: datetime = Field(validation_alias=AliasChoices("createdAt", "created_at"))
    updatedAt: str
    user: Optional[UserSnippet] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


class PaginatedProductResponse(BaseModel):
    products: List[Union[ProductResponse, SkinnyProductResponse]]
    totalCount: int
    brands: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    subCategories: Optional[List[str]] = None
    collections: Optional[List[str]] = None
    usedFuzzy: Optional[bool] = False
    suggestedQuery: Optional[str] = None


# Discount (Coupon) Schemas
class QuantityTier(BaseModel):
    quantity: int
    discount: float


# typeOfDiscount: product_discount | buy_x_get_y | total_order_discount | shipping_discount
# method: discount_code | automatic
# applicableUserIds: when set, only these user ids can use (Selective Retail/Business)
class CouponBase(BaseModel):
    typeOfDiscount: str = (
        "product_discount"  # product_discount | buy_x_get_y | total_order_discount | shipping_discount
    )
    code: Optional[str] = None  # required when method=discount_code; null for automatic
    method: str = "discount_code"  # discount_code | automatic
    discountType: DiscountType
    discountValue: float
    quantityTiers: Optional[List[QuantityTier]] = None
    minPurchaseAmount: float = 0
    minRequirementType: str = "none"  # none | min_amount | min_quantity
    minQuantityOfEligibleItems: Optional[int] = None  # when minRequirementType=min_quantity
    maxDiscountAmount: Optional[float] = None
    validFrom: Optional[str] = None
    validUntil: Optional[str] = None
    usageLimit: Optional[int] = None
    isActive: bool = True
    applicableRoles: List[str] = ["customer"]
    applicableUserIds: Optional[List[str]] = None  # selective retail/business: only these users
    applicableCategories: Optional[List[str]] = None  # deprecated
    appliesToType: str = "all"
    appliesToValueIds: Optional[List[str]] = None
    excludedProductIds: Optional[List[str]] = None
    applicableItemType: Optional[str] = None  # units | cases
    userBehavior: Optional[str] = None
    maxUsagePerUser: Optional[int] = None
    buyXGetYCustomerGetsQuantity: Optional[int] = None
    buyXGetYCustomerGetsAppliesToType: Optional[str] = None
    buyXGetYCustomerGetsAppliesToValueIds: Optional[List[str]] = None
    buyXGetYCustomerGetsDiscountType: Optional[str] = None
    buyXGetYCustomerGetsDiscountValue: Optional[float] = None
    displayId: Optional[str] = None
    shippingStates: Optional[List[str]] = None
    shippingDistricts: Optional[List[str]] = None
    shippingPincodes: Optional[List[str]] = None
    applicablePaymentMethods: Optional[List[str]] = None
    couponMode: Optional[str] = "override"
    
    @model_validator(mode='after')
    def validate_dates(self):
        if self.validFrom and self.validUntil:
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


class CouponUpdate(BaseModel):
    resolution: Optional[str] = None
    force: bool = False
    typeOfDiscount: Optional[str] = None
    code: Optional[str] = None
    method: Optional[str] = None
    discountType: Optional[DiscountType] = None
    discountValue: Optional[float] = None
    quantityTiers: Optional[List[QuantityTier]] = None
    minPurchaseAmount: Optional[float] = None
    minRequirementType: Optional[str] = None
    minQuantityOfEligibleItems: Optional[int] = None
    maxDiscountAmount: Optional[float] = None
    validFrom: Optional[str] = None
    validUntil: Optional[str] = None
    usageLimit: Optional[int] = None
    isActive: Optional[bool] = None
    applicableRoles: Optional[List[str]] = None
    applicableUserIds: Optional[List[str]] = None
    applicableCategories: Optional[List[str]] = None
    appliesToType: Optional[str] = None
    appliesToValueIds: Optional[List[str]] = None
    excludedProductIds: Optional[List[str]] = None
    applicableItemType: Optional[str] = None
    userBehavior: Optional[str] = None
    maxUsagePerUser: Optional[int] = None
    buyXGetYCustomerGetsQuantity: Optional[int] = None
    buyXGetYCustomerGetsAppliesToType: Optional[str] = None
    buyXGetYCustomerGetsAppliesToValueIds: Optional[List[str]] = None
    buyXGetYCustomerGetsDiscountType: Optional[str] = None
    buyXGetYCustomerGetsDiscountValue: Optional[float] = None
    shippingStates: Optional[List[str]] = None
    shippingDistricts: Optional[List[str]] = None
    shippingPincodes: Optional[List[str]] = None
    applicablePaymentMethods: Optional[List[str]] = None
    couponMode: Optional[str] = None


class CouponResponse(CouponBase):
    id: str = Field(alias="_id")
    usedCount: Optional[int] = None
    createdAt: datetime = Field(validation_alias=AliasChoices("createdAt", "created_at"))
    updatedAt: str
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
class Address(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    address: Optional[str] = None
    street: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    zipCode: Optional[str] = None
    pincode: Optional[str] = None
    country: Optional[str] = "India"
    googleLocation: Optional[str] = None
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



class PaginatedUsersResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    users: List[UserResponse]
    totalCount: int = Field(alias="totalCount")
    page: int
    limit: int

class PreferencesResponse(BaseModel):
    preferredLanguage: str

class DutyStatusResponse(BaseModel):
    message: str

class MessageResponse(BaseModel):
    message: str

class CartResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    items: List[ItemSnippet]
    subtotal: float
    itemCount: int = Field(alias="itemCount")
    expiresAt: Optional[str] = Field(alias="expiresAt")

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


class AdStats(BaseModel):
    impressions: Optional[int] = 0
    clicks: Optional[int] = 0
    leads: Optional[int] = 0
    purchases: Optional[int] = 0
    add_to_cart: Optional[int] = 0
    conversions: Optional[int] = 0
    conversion_value: Optional[float] = 0.0
    ctr: Optional[float] = 0.0
    cvr: Optional[float] = 0.0

class AdBase(BaseModel):
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
    google_conversion_id: Optional[str] = None
    google_conversion_label: Optional[str] = None
    meta_pixel_id: Optional[str] = None
    notes: Optional[str] = None
    launched_at: Optional[str] = None
    stats: Optional[AdStats] = Field(default_factory=AdStats)

class AdCreate(AdBase):
    name: str
    platform: str

class AdUpdate(AdBase):
    pass

class AdStatusUpdate(BaseModel):
    status: str


class AdSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    total_views: int = 0
    total_clicks: int = 0
    active_campaigns: int = 0
    total_spend_estimate: Optional[float] = None
    ctr: Optional[float] = None
    total_ads: Optional[int] = 0
    active: Optional[int] = 0
    paused: Optional[int] = 0
    draft: Optional[int] = 0
    total_impressions: Optional[int] = 0
    total_conversions: Optional[int] = 0
    overall_ctr: Optional[float] = 0.0


class OrderAddress(BaseModel):
    name: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    phone: Optional[str] = None



class CouponCreateInternal(CouponBase):
    resolution: Optional[str] = None
    force: bool = False
    displayId: Optional[str] = None
    usedCount: int = 0



class PromoStripBase(BaseModel):
    text: str
    isActive: Optional[bool] = True

class PromoStripCreate(PromoStripBase):
    pass

class PromoStripUpdate(BaseModel):
    text: Optional[str] = None
    isActive: Optional[bool] = None

class PromoStripResponse(PromoStripBase):
    id: str = Field(alias='_id')
    createdAt: Optional[str] = None
    updatedAt: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("updatedAt", "updated_at"))

















# --- DAO Internal Models ---
class UserInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    userId: int
    isSellerAdmin: bool = False
    sellerPermissions: Optional[List[SellerPermission]] = None
    serviceAreaZones: Optional[List[str]] = None
    savedAddresses: Optional[List[SavedAddress]] = None
    isOnDuty: bool = False
    commissionOverridePct: Optional[float] = Field(default=None, validation_alias=AliasChoices("commissionOverridePct", "commission_override_pct"))
    userIdFormatted: str
    name: str
    email: Optional[str] = None
    password: str
    role: str
    phone: str = ""
    companyName: str = ""
    address: Optional[Address] = None
    isActive: bool = True
    approvalStatus: str
    isDeactivated: bool = False
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: str = "30"
    assignedSalesperson: Optional[str] = Field(default=None, validation_alias=AliasChoices("assignedSalesperson", "assigned_salesperson"))
    referralCode: Optional[str] = Field(default=None, validation_alias=AliasChoices("referralCode", "referral_code"))
    isEmailVerified: bool = False
    allowDeliverySlots: Optional[bool] = None
    allowUrgentDelivery: Optional[bool] = None
    upiId: Optional[str] = None
    qrCodeUrl: Optional[str] = None
    # Device / verification metadata captured at registration time.
    # otp is intentionally excluded — it is verified and deleted before create() is called.
    deviceId: Optional[str] = None
    msg91Token: Optional[str] = None

class UserInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    userId: Optional[int] = Field(default=None, validation_alias=AliasChoices("userId", "user_id"))
    userIdFormatted: Optional[str] = Field(default=None, validation_alias=AliasChoices("userIdFormatted", "user_id_formatted"))
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    companyName: Optional[str] = None
    address: Optional[Address] = None
    savedAddresses: Optional[List[Address]] = None
    isActive: Optional[bool] = None
    approvalStatus: Optional[str] = Field(default=None, validation_alias=AliasChoices("approvalStatus", "approval_status"))
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = Field(default=None, validation_alias=AliasChoices("assignedSalesperson", "assigned_salesperson"))
    referralCode: Optional[str] = Field(default=None, validation_alias=AliasChoices("referralCode", "referral_code"))
    isEmailVerified: Optional[bool] = None
    sellerPermissions: Optional[list] = None
    serviceAreaZones: Optional[List[str]] = None
    allowDeliverySlots: Optional[bool] = None
    allowUrgentDelivery: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    upiId: Optional[str] = None
    qrCodeUrl: Optional[str] = None


# --- Shared Payload DTOs ---

class AnalyticsEventPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    returning: Optional[bool] = False
    productId: Optional[str] = None
    productName: Optional[str] = "Unknown"
    source: Optional[str] = "mobile_app"
    quantity: Optional[int] = 1
    query: Optional[str] = ""
    resultsCount: Optional[int] = 0
    reason: Optional[str] = "unknown"
    testRunId: Optional[str] = None
    device: Optional[str] = None
    screen: Optional[str] = None


class AnalyticsEventCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    type: str
    userId: Optional[str] = None
    sessionId: Optional[str] = None
    source: Optional[str] = None
    filterName: Optional[str] = None
    filterValue: Optional[str] = None
    category: Optional[str] = None
    payload: Optional[AnalyticsEventPayload] = None
    searchTerm: Optional[str] = None
    resultsCount: Optional[int] = None
    segment: Optional[str] = None
    productIds: Optional[List[str]] = None
    productId: Optional[str] = None
    productName: Optional[str] = None
    quantity: Optional[int] = None
    price: Optional[float] = None
    cartValue: Optional[float] = None
    isReturning: Optional[bool] = None
    pageViews: Optional[int] = None
    page: Optional[str] = None
    reason: Optional[str] = None
    orderId: Optional[str] = None
    orderValue: Optional[float] = None
    cartItems: Optional[List[ItemSnippet]] = None
    model_config = ConfigDict(extra="forbid")
    timestamp: Optional[str] = None


class Msg91WebhookPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    status: Optional[str] = None
    Status: Optional[str] = None
    type: Optional[str] = None

    @property
    def effective_status(self) -> Optional[str]:
        return self.Status or self.status or self.type


class TrackBeaconRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event: Optional[str] = None
    page: Optional[str] = None
    sessionId: Optional[str] = None
    timestamp: Optional[str] = None
    userId: Optional[str] = None


class TrackNotifyPincodeRequest(BaseModel):
    productId: str
    pincode: str
    productName: Optional[str] = "Unknown"
    email: Optional[str] = None


class OrderItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    productId: Optional[str] = Field(None, alias="product_id")
    product: Optional[str] = None
    quantity: int = 1
    sellAsCase: Optional[bool] = Field(False, alias="sell_as_case")
    price: Optional[float] = None
    selectedVariation: Optional[VariantAttributes] = None

    @property
    def product_id(self) -> Optional[str]:
        return self.productId or self.product

    @property
    def sell_as_case(self) -> bool:
        return bool(self.sellAsCase)


class SellerDeliveryOption(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sellerId: str
    deliverySlotId: Optional[str] = None
    deliverySlotDate: Optional[str] = None
    deliverySlotConfigId: Optional[str] = None
    isUrgentDelivery: Optional[bool] = False


class PushSubscriptionKeys(BaseModel):
    model_config = ConfigDict(extra="forbid")
    p256dh: str
    auth: str


class PushSubscription(BaseModel):
    model_config = ConfigDict(extra="forbid")
    endpoint: str
    expirationTime: Optional[float] = None
    keys: PushSubscriptionKeys


# --- Router Response and Request DTOs ---

class ActivityLogResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: Optional[str] = Field(None, alias="_id")
    userId: Optional[str] = None
    sessionId: Optional[str] = None
    action: Optional[str] = None
    meta: Optional[ActivityMetadata] = None
    isGuest: Optional[bool] = None


class PromoteGuestResponse(BaseModel):
    updated: int


class AvailabilityRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra="forbid")
    id: Optional[str] = Field(None, alias="_id")
    external_id: Optional[str] = Field(None, alias="externalId")
    productId: Optional[str] = None
    productName: Optional[str] = None
    pincode: Optional[str] = None
    userName: Optional[str] = None
    userEmail: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("updatedAt", "updated_at"))


class AvailabilityRequestListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    requests: List[AvailabilityRequestResponse] = []
    total: int = 0
    page: int = 1
    limit: int = 50


class DeliveryZoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra="forbid")
    id: Optional[str] = Field(None, alias="_id")
    name: Optional[str] = None
    zoneId: Optional[str] = None
    zoneName: Optional[str] = None
    description: Optional[str] = None
    pincodes: Optional[List[str]] = None
    defaultCapacity: Optional[int] = None
    urgentDeliveryAvailable: Optional[bool] = False
    isActive: Optional[bool] = True
    customerType: Optional[str] = "retail"


class EligibleFeedbackResponse(BaseModel):
    eligibleOrderId: Optional[str] = None


class ReturnEligibilityItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra="forbid")
    productId: str
    maxQuantity: int
    reason: Optional[str] = None
    name: Optional[str] = None
    price: Optional[float] = None
    image: Optional[str] = None


class ReturnEligibilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra="forbid")
    eligibleItems: List[ReturnEligibilityItem] = []
    reason: Optional[str] = None
    returnDeliveryCharge: Optional[float] = 0.0


class UPIDetailsResponse(BaseModel):
    upiId: Optional[str] = None
    qrCodeUrl: Optional[str] = None
    instructions: Optional[str] = None
    message: Optional[str] = None


class ValetPayoutSettingsResponse(BaseModel):
    deliveryChargePerOrder: Optional[float] = None
    returnPickupChargePerOrder: Optional[float] = None
    updatedAt: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("updatedAt", "updated_at"))


class PincodeSearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra="forbid")
    id: Optional[str] = Field(None, alias="_id")
    pincode: Optional[str] = None
    isServiceable: Optional[bool] = None
    status: Optional[str] = None
    sellerCount: Optional[int] = 0
    serviceableSellerIds: Optional[List[str]] = []
    userRole: Optional[str] = "customer"
    userId: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    searchedAt: Optional[str] = None
    date: Optional[str] = None


class PincodeSearchStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra="forbid")
    totalSearches: int = 0
    uniquePincodes: int = 0
    uniquePincodesCount: int = 0
    serviceableSearches: int = 0
    unserviceableSearches: int = 0
    topUnserviceablePincodes: List[PincodeStat] = []
    topSearchedPincodes: List[PincodeStat] = []
    topPincodes: List[PincodeStat] = []


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


class PushNotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra="forbid")
    id: Optional[str] = Field(None, alias="_id")
    title: Optional[str] = None
    message: Optional[str] = None
    link: Optional[str] = None
    targetSegmentId: Optional[str] = None
    status: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("updatedAt", "updated_at"))


class PushAnalyticsResponse(BaseModel):
    delivered: int = 0
    clicked: int = 0


class VapidKeyResponse(BaseModel):
    publicKey: str


class SellerRequestCreate(BaseModel):
    subject: str
    description: str
    category: Optional[str] = "general"
    priority: Optional[str] = "medium"
    attachments: Optional[List[str]] = None


class SellerRequestResponseCreate(BaseModel):
    message: str
    attachments: Optional[List[str]] = None


class SellerRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra="forbid")
    id: Optional[str] = Field(None, alias="_id")
    subject: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    user: Optional[UserSnippet] = None
    attachments: Optional[List[str]] = None
    responses: Optional[List[TicketResponseItem]] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("updatedAt", "updated_at"))


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




class ActivityCreate(BaseModel):
    userId: Optional[str] = None
    action: Optional[str] = None
    entityType: Optional[str] = None
    entityId: Optional[str] = None
    sessionId: Optional[str] = None
    metadata: Optional[ActivityMetadata] = None

class ActivityUpdate(BaseModel):
    userId: Optional[str] = None
    action: Optional[str] = None
    entityType: Optional[str] = None
    entityId: Optional[str] = None
    sessionId: Optional[str] = None
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


class PopulatedOrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    product: Optional['Product'] = None
    quantity: Optional[int] = None
    price: Optional[float] = None
    stockStatus: Optional[str] = None
    taxRate: Optional[float] = None
    taxAmount: Optional[float] = None


class PopulatedOrderResponse(BaseModel):
    """Fully-populated order returned by GET /orders endpoints.

    Every field that orders.py passes into this constructor is declared here.
    extra='forbid' ensures nothing is silently dropped.
    """
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')

    id: Optional[str] = Field(default=None, alias="_id")
    orderId: Optional[str] = None
    status: Optional[str] = None
    orderStatus: Optional[str] = None    # router alias for status

    user: Optional[UserSnippet] = None
    assignedValet: Optional[ValetSnippet] = None
    payment: Optional[PaymentSnippet] = None
    paymentEntries: Optional[List['PaymentEntry']] = None
    items: Optional[List[PopulatedOrderItemResponse]] = None

    # Financial summary
    subTotal: Optional[float] = None
    shippingCharge: Optional[float] = None
    total: Optional[float] = None
    totalAmount: Optional[float] = None   # router alias for total
    deliveryFee: Optional[float] = None   # router alias for shipping
    discount: Optional[float] = None
    couponCode: Optional[str] = None      # populated when Order model stores it

    # Payment
    paymentMethod: Optional[str] = None
    paymentStatus: Optional[str] = None

    # Addresses
    shippingAddress: Optional[Address] = None
    billingAddress: Optional[Address] = None
    address: Optional[Address] = None         # router alias for shippingAddress

    # Notes
    notes: Optional[str] = None
    orderNotes: Optional[str] = None      # router alias for notes
    adminNotes: Optional[str] = None      # populated when Order model stores it
    valetNotes: Optional[str] = None      # populated when Order model stores it

    # Zone
    zoneId: Optional[str] = None          # populated when Order model stores it

    # Sub-orders
    sub_orders: Optional[List['SubOrder']] = Field(default=None, alias="subOrders")

    # Timestamps
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

UserResponse.model_rebuild()

from app.models.payment import PaymentEntry
from app.models.product import Product
from app.models.sub_order import SubOrder

PaymentSnippet.model_rebuild()
PopulatedOrderItemResponse.model_rebuild()
PopulatedOrderResponse.model_rebuild()
BundleItemResponse.model_rebuild()
