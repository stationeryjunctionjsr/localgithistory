from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


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
    phone: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    locationLink: Optional[str] = None

class UserSnippet(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    id: Optional[str] = Field(None, alias="_id")
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None

class ItemSnippet(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    productId: Optional[str] = None
    product: Optional[Any] = None
    quantity: Optional[int] = None
    sellAsCase: Optional[bool] = None
    price: Optional[float] = None
    mrp: Optional[float] = None
    name: Optional[str] = None
    image: Optional[str] = None
    status: Optional[str] = None

class VariantOption(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    value: Optional[str] = None
    priceModifier: Optional[float] = None
    stock: Optional[int] = None
    sku: Optional[str] = None
    attributes: Optional[Dict[str, str]] = None
    price: Optional[float] = None

class VisibilityRuleSnippet(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    type: Optional[str] = None
    value: Optional[str] = None

class SellerPermissionSnippet(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    canManageProducts: Optional[bool] = None
    canManageOrders: Optional[bool] = None

class ValetSnippet(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    id: Optional[str] = Field(None, alias="_id")
    name: Optional[str] = None
    phone: Optional[str] = None

class ValetDeclineSnippet(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    valetId: Optional[str] = None
    reason: Optional[str] = None

class DiscountSnippet(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    name: Optional[str] = None
    value: Optional[float] = None

class UserBase(BaseModel):
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
    isDeactivated: Optional[bool] = False
    creditLimit: Optional[float] = 0
    creditUsed: Optional[float] = 0
    paymentTerms: Optional[str] = "30"
    assignedSalesperson: Optional[str] = None
    isSellerAdmin: Optional[bool] = False
    isOnDuty: Optional[bool] = False
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = Field(default_factory=list)
    password: Optional[str] = None
    approvalStatus: Optional[str] = "approved"
    isDeactivated: Optional[bool] = False
    creditLimit: Optional[float] = 0
    creditUsed: Optional[float] = 0
    paymentTerms: Optional[str] = "30"
    assignedSalesperson: Optional[str] = None
    isSellerAdmin: Optional[bool] = False
    isOnDuty: Optional[bool] = False
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = Field(default_factory=list)
    password: Optional[str] = None
    approvalStatus: Optional[str] = "approved"
    isDeactivated: Optional[bool] = False
    creditLimit: Optional[float] = 0
    creditUsed: Optional[float] = 0
    paymentTerms: Optional[str] = "30"
    assignedSalesperson: Optional[str] = None
    isSellerAdmin: Optional[bool] = False
    isOnDuty: Optional[bool] = False
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = Field(default_factory=list)
    password: Optional[str] = None
    approvalStatus: Optional[str] = "approved"
    isDeactivated: Optional[bool] = False
    creditLimit: Optional[float] = 0
    creditUsed: Optional[float] = 0
    paymentTerms: Optional[str] = "30"
    assignedSalesperson: Optional[str] = None
    isSellerAdmin: Optional[bool] = False
    isOnDuty: Optional[bool] = False
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = Field(default_factory=list)
    password: Optional[str] = None

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
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    creditLimit: Optional[float] = None
    paymentTerms: Optional[int] = None
    assignedSalesperson: Optional[str] = None
    referralCode: Optional[str] = None
    isSellerAdmin: Optional[bool] = None
    sellerPermissions: Optional[SellerPermissionSnippet] = None
    commissionOverridePct: Optional[float] = None
    preferredLanguage: Optional[str] = None


class UserResponse(UserBase):
    id: str = Field(alias="_id")
    userId: Optional[int] = None
    userIdFormatted: Optional[str] = None
    role: Optional[str] = None
    effectiveRole: Optional[str] = None
    approvalStatus: Optional[str] = None
    isActive: bool
    isDeactivated: Optional[bool] = False
    creditLimit: float
    creditUsed: float
    paymentTerms: Optional[int] = None
    assignedSalesperson: Optional[str] = None
    referralCode: Optional[str] = None
    isSellerAdmin: Optional[bool] = False
    sellerPermissions: Optional[SellerPermissionSnippet] = None
    commissionOverridePct: Optional[float] = None
    createdAt: str
    updatedAt: Optional[str] = None

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
    updatedAt: Optional[str] = None

class ClassificationTagResponse(BaseModel):
    id: str = Field(alias="_id")
    name: str
    isActive: bool
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class ReviewActionResponse(BaseModel):
    message: str
    review: ProductReviewResponse

class ClassificationActionResponse(BaseModel):
    message: str
    classification: ClassificationTagResponse


class BundleItemResponse(BaseModel):
    productId: str
    productName: Optional[str] = None
    quantity: int
    image: Optional[str] = None
    price: Optional[float] = None
    discountPrice: Optional[float] = None

class BundleResponse(BaseModel):
    id: str = Field(alias="_id")
    name: str
    description: Optional[str] = None
    price: float
    discountPercentage: Optional[float] = None
    isActive: bool
    salesCount: Optional[int] = None
    items: List[BundleItemResponse] = []
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

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
    sellers: Optional[List[UserSnippet]] = None
    catalogSellerIds: Optional[List[str]] = None
    rating: Optional[float] = None
    reviews: Optional[int] = None
    details: Optional[Dict[str, Any]] = None

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
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
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
    startDate: str
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
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    isPublished: Optional[bool] = None
    visibilityRules: Optional[List[VisibilityRuleSnippet]] = None
    userSegments: Optional[List[str]] = None
    linkUrl: Optional[str] = None


class BannerResponse(BannerBase):
    id: str = Field(alias="_id")
    createdAt: str
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
    updatedAt: Optional[str] = None

class BrandCreate(BaseModel):
    name: str
    logoUrl: Optional[str] = ""
    showInMobileHomepage: bool = False
    isActive: Optional[bool] = True
    isActive: Optional[bool] = True


class BrandUpdate(BaseModel):
    name: Optional[str] = None
    logoUrl: Optional[str] = None
    showInMobileHomepage: Optional[bool] = None
    isActive: Optional[bool] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    isActive: Optional[bool] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None


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


class AuthResponse(BaseModel):
    token: str
    refreshToken: Optional[str] = None
    sessionId: Optional[str] = None
    user: UserResponse
    message: Optional[str] = None


# Contact Schemas
class Address(BaseModel):
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    zipCode: Optional[str] = None
    country: Optional[str] = "India"
    googleLocation: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


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
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    displayOrder: Optional[int] = None
    socialMedia: Optional[SocialMedia] = None


class ContactResponse(ContactBase):
    id: str = Field(alias="_id")
    createdAt: str
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


class SupportTicketCreate(SupportTicketBase):
    pass


class SupportTicketUpdate(BaseModel):
    status: Optional[str] = None  # open, in_progress, resolved, closed
    priority: Optional[str] = None
    assignedTo: Optional[str] = None


class TicketResponseCreate(BaseModel):
    message: str
    attachments: Optional[List[str]] = None


class SupportTicketResponse(SupportTicketBase):
    id: str = Field(alias="_id")
    ticketNumber: str
    user: dict
    status: str
    assignedTo: Optional[dict] = None
    responses: Optional[List[dict]] = None
    resolvedAt: Optional[str] = None
    closedAt: Optional[str] = None
    createdAt: str
    updatedAt: str
    user: Optional[UserSnippet] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


# Delivery Charge Schemas
class DeliveryChargeBase(BaseModel):
    pincode: str
    state: str
    city: Optional[str] = ""
    district: str
    charge: Optional[float] = None
    minCartValue: Optional[float] = None
    applyDefaultCharge: Optional[bool] = False
    tiers: Optional[List[Dict]] = None
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
    tiers: Optional[List[Dict]] = None
    serviceableForCustomer: Optional[bool] = None

    serviceableForWholesaler: Optional[bool] = None
    isActive: Optional[bool] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    description: Optional[str] = None


class DeliveryChargeResponse(DeliveryChargeBase):
    id: str = Field(alias="_id")
    locationId: Optional[int] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

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
    updatedAt: Optional[str] = None

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
    createdAt: str
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
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None


class CoachMarkResponse(CoachMarkBase):
    id: str = Field(alias="_id")
    createdAt: str
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
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    categories: Optional[List[str]] = None
    subCategories: Optional[List[str]] = None
    brands: Optional[List[str]] = None
    collections: Optional[List[str]] = None
    productIds: Optional[List[str]] = None
    excludedProductIds: Optional[List[str]] = None


class SearchTagResponse(SearchTagBase):
    id: str = Field(alias="_id")
    createdAt: str
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
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    displayOrder: Optional[int] = None
    productIds: Optional[List[str]] = None
    visiblePages: Optional[List[str]] = None
    userSegments: Optional[List[str]] = None
    visibilityRules: Optional[List[VisibilityRuleSnippet]] = None


class CollectionResponse(CollectionBase):
    id: str = Field(alias="_id")
    createdAt: str
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
    isActive: bool
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
    createdAt: str
    updatedAt: str
    user: Optional[UserSnippet] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


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
    createdAt: str
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
    createdAt: str
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
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
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
    createdAt: str
    updatedAt: str
    user: Optional[UserSnippet] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


class CouponValidate(BaseModel):
    code: str
    amount: float
    category: Optional[str] = None



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
    startDate: str
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
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    isPublished: Optional[bool] = None
    visibilityRules: Optional[List[VisibilityRuleSnippet]] = None
    userSegments: Optional[List[str]] = None
    linkUrl: Optional[str] = None


class BannerResponse(BannerBase):
    id: str = Field(alias="_id")
    createdAt: str
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
    updatedAt: Optional[str] = None

class BrandCreate(BaseModel):
    name: str
    logoUrl: Optional[str] = ""
    showInMobileHomepage: bool = False
    isActive: Optional[bool] = True
    isActive: Optional[bool] = True


class BrandUpdate(BaseModel):
    name: Optional[str] = None
    logoUrl: Optional[str] = None
    showInMobileHomepage: Optional[bool] = None
    isActive: Optional[bool] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    isActive: Optional[bool] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None


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


class AuthResponse(BaseModel):
    token: str
    refreshToken: Optional[str] = None
    sessionId: Optional[str] = None
    user: UserResponse
    message: Optional[str] = None


# Contact Schemas
class Address(BaseModel):
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    zipCode: Optional[str] = None
    country: Optional[str] = "India"
    googleLocation: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


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
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    displayOrder: Optional[int] = None
    socialMedia: Optional[SocialMedia] = None


class ContactResponse(ContactBase):
    id: str = Field(alias="_id")
    createdAt: str
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


class SupportTicketCreate(SupportTicketBase):
    pass


class SupportTicketUpdate(BaseModel):
    status: Optional[str] = None  # open, in_progress, resolved, closed
    priority: Optional[str] = None
    assignedTo: Optional[str] = None


class TicketResponseCreate(BaseModel):
    message: str
    attachments: Optional[List[str]] = None


class SupportTicketResponse(SupportTicketBase):
    id: str = Field(alias="_id")
    ticketNumber: str
    user: dict
    status: str
    assignedTo: Optional[dict] = None
    responses: Optional[List[dict]] = None
    resolvedAt: Optional[str] = None
    closedAt: Optional[str] = None
    createdAt: str
    updatedAt: str
    user: Optional[UserSnippet] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')


# Delivery Charge Schemas
class DeliveryChargeBase(BaseModel):
    pincode: str
    state: str
    city: Optional[str] = ""
    district: str
    charge: Optional[float] = None
    minCartValue: Optional[float] = None
    applyDefaultCharge: Optional[bool] = False
    tiers: Optional[List[Dict]] = None
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
    tiers: Optional[List[Dict]] = None
    serviceableForCustomer: Optional[bool] = None

    serviceableForWholesaler: Optional[bool] = None
    isActive: Optional[bool] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    description: Optional[str] = None


class DeliveryChargeResponse(DeliveryChargeBase):
    id: str = Field(alias="_id")
    locationId: Optional[int] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

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
    updatedAt: Optional[str] = None

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
    createdAt: str
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
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None


class CoachMarkResponse(CoachMarkBase):
    id: str = Field(alias="_id")
    createdAt: str
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
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    categories: Optional[List[str]] = None
    subCategories: Optional[List[str]] = None
    brands: Optional[List[str]] = None
    collections: Optional[List[str]] = None
    productIds: Optional[List[str]] = None
    excludedProductIds: Optional[List[str]] = None


class SearchTagResponse(SearchTagBase):
    id: str = Field(alias="_id")
    createdAt: str
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
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    isDeactivated: Optional[bool] = None
    creditLimit: Optional[float] = None
    creditUsed: Optional[float] = None
    paymentTerms: Optional[str] = None
    assignedSalesperson: Optional[str] = None
    isEmailVerified: Optional[bool] = None
    isSellerAdmin: Optional[bool] = None
    isOnDuty: Optional[bool] = None
    commissionOverridePct: Optional[float] = None
    sellerPermissions: Optional[SellerPermissions] = None
    serviceAreaZones: Optional[List[str]] = None
    referralCode: Optional[str] = None
    displayOrder: Optional[int] = None
    productIds: Optional[List[str]] = None
    visiblePages: Optional[List[str]] = None
    userSegments: Optional[List[str]] = None
    visibilityRules: Optional[List[VisibilityRuleSnippet]] = None


class CollectionResponse(CollectionBase):
    id: str = Field(alias="_id")
    createdAt: str
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

class PaginatedUsersResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    users: List[UserResponse]
    totalCount: int = Field(alias="totalCount")
    page: int
    limit: int

class PreferencesResponse(BaseModel):
    preferredLanguage: str

class DutyStatusResponse(BaseModel):
    isOnDuty: bool
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


class OrderAddress(BaseModel):
    name: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    phone: Optional[str] = None

class OrderCreateInternal(BaseModel):
    user: str
    userRole: Optional[str] = None
    sessionId: Optional[str] = None
    items: List[Any] = Field(default_factory=list)
    subtotal: float
    tax: float = 0.0
    shipping: float = 0.0
    discount: float = 0.0
    total: float
    orderType: str
    status: str = "pending"
    paymentStatus: str = "pending"
    paymentMethod: str = "cod"
    upiPaymentScreenshot: Optional[str] = None
    shippingAddress: Optional[OrderAddress] = None
    billingAddress: Optional[OrderAddress] = None
    notes: Optional[str] = ""
    printedBill: bool = False
    isUrgentDelivery: bool = False
    orderNumber: Optional[str] = None



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
    updatedAt: Optional[str] = None
















