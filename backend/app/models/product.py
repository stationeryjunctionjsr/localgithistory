from pydantic import ConfigDict
from datetime import datetime
from typing import Optional, List, Any
from pydantic import Field
from pydantic import BaseModel
from app.models.schemas import VariantOption, ProductSellerEntry

class Product(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    id: str = Field(alias="_id")
    product_id: int = Field(alias="productId")
    product_id_formatted: Optional[str] = Field(default=None, alias="productIdFormatted")
    name: str
    description: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = Field(default=None, alias="subCategory")
    brand: Optional[str] = None
    mrp: Optional[float] = None
    gst: Optional[float] = None
    mrp_per_case: Optional[float] = Field(default=None, alias="mrpPerCase")
    quantity_per_case: Optional[int] = Field(default=None, alias="quantityPerCase")
    stock: Optional[int] = None
    rating: Optional[float] = None
    reviews: Optional[int] = None
    images: List[str] = []
    videos: List[str] = []
    is_active: bool = Field(default=True, alias="isActive")
    is_exclusive: bool = Field(default=False, alias="isExclusive")
    collection: Optional[str] = None
    tags: List[str] = []
    variant_attributes: List[str] = Field(default=[], alias="variantAttributes")
    sellers: List[ProductSellerEntry] = []
    variants: List[VariantOption] = []
    details: Any = {}
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")
    searchTags: Optional[List[str]] = None
    resolvedCollectionNames: Optional[List[str]] = None
    previouslyBought: Optional[bool] = None
    
    # Discount fields added dynamically by populate_product_discounts
    originalPrice: Optional[float] = None
    price: Optional[float] = None
    defaultDiscountPercentage: Optional[float] = None
    discountPercentage: Optional[float] = None
    applicableDiscounts: Optional[List[Any]] = None
    quantityTiers: Optional[List[Any]] = None
    quantityItemType: Optional[str] = None
    displayImage: Optional[str] = None

