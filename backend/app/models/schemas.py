from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    WHOLESALER = "wholesaler"
    CUSTOMER = "customer"
    VALET = "valet"


class ReturnRequestStatus(str, Enum):
    PENDING = "pending"
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
class UserBase(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: UserRole
    phone: Optional[str] = None
    alternatePhone: Optional[str] = None
    companyName: Optional[str] = None
    gstin: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    savedAddresses: List[Dict[str, Any]] = Field(default=[], description="List of saved addresses for the user")
    referralCode: Optional[str] = Field(default=None, description="Referral code used to sign up")
    isEmailVerified: Optional[bool] = False

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
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    alternatePhone: Optional[str] = None
    companyName: Optional[str] = None
    gstin: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    savedAddresses: Optional[List[Dict[str, Any]]] = None
    locationLink: Optional[str] = None
    approvalStatus: Optional[ApprovalStatus] = None
    isActive: Optional[bool] = None
    creditLimit: Optional[float] = None
    paymentTerms: Optional[int] = None
    assignedSalesperson: Optional[str] = None
    referralCode: Optional[str] = None


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
    createdAt: str
    updatedAt: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# Product Variation Schema
class ProductVariation(BaseModel):
    name: str  # Variation name (e.g., "Color", "Size", "Pages")
    type: str  # Variation type (e.g., "color", "size", "pages", "quantity")
    options: List[Dict[str, Any]]  # List of options with value, price, stock, etc.
    # Example: [{"value": "Red", "priceModifier": 0, "stock": 10}, {"value": "Blue", "priceModifier": 5, "stock": 15}]


# Product Schemas
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
    stock: int = 0  # Total units (reduced by units sold or by cases * quantityPerCase)
    images: Optional[List[str]] = None  # Array of image URLs/paths
    videos: Optional[List[str]] = None  # Array of video URLs/paths
    isActive: bool = True
    isExclusive: bool = False
    tags: Optional[List[str]] = Field(default=None, description="Search and categorization tags")

    variantAttributes: Optional[List[str]] = Field(
        default=None, description="List of variant attribute names like Color, Size"
    )
    variantCombinations: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Actual combinations of attributes with stock and price"
    )

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
    variations: Optional[List[Dict[str, Any]]] = None
    variantAttributes: Optional[List[str]] = None
    variantCombinations: Optional[List[Dict[str, Any]]] = None


class CouponValidateCart(BaseModel):
    """Validate discount against cart: backend computes eligible subtotal from items."""

    code: str
    items: List[Dict[str, Any]]  # [{ productId, quantity, sellAsCase? }]
    shippingAddress: Optional[Dict[str, Any]] = None


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

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# Banner Schemas
class BannerBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    imageUrl: str
    displayOrder: int = 0
    startDate: str
    endDate: Optional[str] = None
    isActive: bool = True
    isPublished: bool = False
    visibilityRules: List[Dict[str, Any]] = []
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
    visibilityRules: Optional[List[Dict[str, Any]]] = None
    userSegments: Optional[List[str]] = None
    linkUrl: Optional[str] = None


class BannerResponse(BannerBase):
    id: str = Field(alias="_id")
    createdAt: str
    updatedAt: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# Brand Schemas
class BrandCreate(BaseModel):
    name: str
    logoUrl: Optional[str] = ""
    showInMobileHomepage: bool = False


class BrandUpdate(BaseModel):
    name: Optional[str] = None
    logoUrl: Optional[str] = None
    showInMobileHomepage: Optional[bool] = None


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
    address: Optional[Dict[str, Any]] = None
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
    displayOrder: int = 0
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
    createdAt: str
    updatedAt: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


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

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


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
    description: Optional[str] = None


class DeliveryChargeResponse(DeliveryChargeBase):
    id: str = Field(alias="_id")
    locationId: Optional[int] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


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

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


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

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# Coach Mark Schemas
class CoachMarkBase(BaseModel):
    anchorId: str
    title: str
    description: str
    screenName: Optional[str] = None
    sequenceOrder: int = 0
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
    createdAt: str
    updatedAt: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


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
    createdAt: str
    updatedAt: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# Collection Schemas
class CollectionBase(BaseModel):
    name: str
    description: Optional[str] = None
    imageUrl: Optional[str] = None
    isActive: bool = True
    displayOrder: int = 0
    productIds: List[str] = []
    visiblePages: List[str] = ["Home"]
    userSegments: List[str] = ["all"]
    visibilityRules: List[Dict[str, Any]] = []


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
    visibilityRules: Optional[List[Dict[str, Any]]] = None


class CollectionResponse(CollectionBase):
    id: str = Field(alias="_id")
    createdAt: str
    updatedAt: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


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
    items: List[Dict[str, Any]]  # populated items
    paymentMethod: str
    upiPaymentScreenshot: Optional[str] = None
    notes: Optional[str] = None
    status: ReturnRequestStatus
    valetId: Optional[str] = None
    valet: Optional[Dict[str, Any]] = None  # populated valet
    user: Optional[Dict[str, Any]] = None  # populated user
    deliveryCharge: float
    createdAt: str
    updatedAt: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
class ProductResponse(ProductBase):
    id: str = Field(alias="_id")
    productId: Optional[int] = None
    productIdFormatted: Optional[str] = None
    price: Optional[float] = None
    originalPrice: Optional[float] = None
    discountPercentage: Optional[float] = None
    defaultDiscountPercentage: Optional[float] = None
    applicableDiscounts: Optional[List[Dict[str, Any]]] = None
    variations: Optional[List[Dict[str, Any]]] = None
    searchTags: Optional[List[str]] = None
    gst: Optional[float] = 0  # Evaluated from category level
    createdAt: str
    updatedAt: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


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
    stock: int = 0
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

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


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


class CouponCreate(CouponBase):
    pass


class CouponUpdate(BaseModel):
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
    usedCount: int = 0
    createdAt: str
    updatedAt: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class CouponValidate(BaseModel):
    code: str
    amount: float
    category: Optional[str] = None


class CouponValidateCart(BaseModel):
    """Validate discount against cart: backend computes eligible subtotal from items."""

    code: str
    items: List[Dict[str, Any]]  # [{ productId, quantity, sellAsCase? }]
    shippingAddress: Optional[Dict[str, Any]] = None


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

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# Banner Schemas
class BannerBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    imageUrl: str
    displayOrder: int = 0
    startDate: str
    endDate: Optional[str] = None
    isActive: bool = True
    isPublished: bool = False
    visibilityRules: List[Dict[str, Any]] = []
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
    visibilityRules: Optional[List[Dict[str, Any]]] = None
    userSegments: Optional[List[str]] = None
    linkUrl: Optional[str] = None


class BannerResponse(BannerBase):
    id: str = Field(alias="_id")
    createdAt: str
    updatedAt: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# Brand Schemas
class BrandCreate(BaseModel):
    name: str
    logoUrl: Optional[str] = ""
    showInMobileHomepage: bool = False


class BrandUpdate(BaseModel):
    name: Optional[str] = None
    logoUrl: Optional[str] = None
    showInMobileHomepage: Optional[bool] = None


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
    address: Optional[Dict[str, Any]] = None
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
    displayOrder: int = 0
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
    createdAt: str
    updatedAt: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


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

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


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
    description: Optional[str] = None


class DeliveryChargeResponse(DeliveryChargeBase):
    id: str = Field(alias="_id")
    locationId: Optional[int] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


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

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


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

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# Coach Mark Schemas
class CoachMarkBase(BaseModel):
    anchorId: str
    title: str
    description: str
    screenName: Optional[str] = None
    sequenceOrder: int = 0
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
    createdAt: str
    updatedAt: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


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
    createdAt: str
    updatedAt: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# Collection Schemas
class CollectionBase(BaseModel):
    name: str
    description: Optional[str] = None
    imageUrl: Optional[str] = None
    isActive: bool = True
    displayOrder: int = 0
    productIds: List[str] = []
    visiblePages: List[str] = ["Home"]
    userSegments: List[str] = ["all"]
    visibilityRules: List[Dict[str, Any]] = []


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
    visibilityRules: Optional[List[Dict[str, Any]]] = None


class CollectionResponse(CollectionBase):
    id: str = Field(alias="_id")
    createdAt: str
    updatedAt: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# Referral Schemas
class ReferralSegmentSetting(BaseModel):
    segment: str  # "retail" or "business"
    discountType: DiscountType = DiscountType.PERCENTAGE
    discountValue: float = 0
    isActive: bool = False


class ReferralSettingsResponse(BaseModel):
    retail: ReferralSegmentSetting
    business: ReferralSegmentSetting


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
    items: List[Dict[str, Any]]  # populated items
    paymentMethod: str
    upiPaymentScreenshot: Optional[str] = None
    notes: Optional[str] = None
    status: ReturnRequestStatus
    valetId: Optional[str] = None
    valet: Optional[Dict[str, Any]] = None  # populated valet
    user: Optional[Dict[str, Any]] = None  # populated user
    deliveryCharge: float
    createdAt: str
    updatedAt: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
