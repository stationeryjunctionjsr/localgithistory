
# We will read schemas.py, and completely replace from 'class ProductResponse' down to 'class CouponValidateCart'
# with the correct content.

correct_middle = """class ProductResponse(ProductBase):
    id: str = Field(alias="_id")
    productId: Optional[int] = None
    productIdFormatted: Optional[str] = None
    price: Optional[float] = None
    discountPercentage: Optional[float] = None
    variations: Optional[List[Dict[str, Any]]] = None
    searchTags: Optional[List[str]] = None
    gst: Optional[float] = 0  # Evaluated from category level
    createdAt: str
    updatedAt: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class PaginatedProductResponse(BaseModel):
    products: List[ProductResponse]
    totalCount: int
    brands: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    subCategories: Optional[List[str]] = None
    collections: Optional[List[str]] = None


# Discount (Coupon) Schemas
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


class CouponCreate(CouponBase):
    pass


class CouponUpdate(BaseModel):
    typeOfDiscount: Optional[str] = None
    code: Optional[str] = None
    method: Optional[str] = None
    discountType: Optional[DiscountType] = None
    discountValue: Optional[float] = None
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


class CouponResponse(CouponBase):
    id: str = Field(alias="_id")
    usedCount: int
    createdAt: str
    updatedAt: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class CouponValidate(BaseModel):
    code: str
    amount: float
    category: Optional[str] = None


class CouponValidateCart(BaseModel):"""

with open(r"c:\\Ecommerce app\\backend\\app\\models\\schemas.py", "r", encoding="utf-8") as f:
    content = f.read()


# We will just split on 'class ProductResponse' and 'class CouponValidateCart'
# but since ProductResponse is already messed up, we'll split on 'class ProductUpdate'
# wait, 'class ProductUpdate(BaseModel):' is intact!
# And 'class CouponValidateCart(BaseModel):' is intact.

part1 = content.split("class ProductResponse")[0]
part2 = "class CouponValidateCart(BaseModel):" + content.split("class CouponValidateCart(BaseModel):")[1]

new_content = part1 + correct_middle + part2

with open(r"c:\\Ecommerce app\\backend\\app\\models\\schemas.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print("done")
