from pydantic import ConfigDict
from datetime import datetime
from typing import Optional, List, Any
from pydantic import Field, AliasChoices
from pydantic import BaseModel
from app.models.base import CamelBaseModel
from app.models.schemas import VariantOption, ProductSellerEntry, ProductDetails

class Product(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    id: str 
    product_id: int 
    product_id_formatted: Optional[str] = None
    name: str
    description: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    brand: Optional[str] = None
    mrp: Optional[float] = None
    gst: Optional[float] = None
    mrp_per_case: Optional[float] = None
    quantity_per_case: Optional[int] = None
    stock: Optional[int] = None
    rating: Optional[float] = None
    reviews: Optional[int] = None
    weight_grams: Optional[int] = 200
    length_cm: Optional[float] = None
    width_cm: Optional[float] = None
    height_cm: Optional[float] = None
    hsn_code: Optional[str] = None
    images: List[str] = []
    videos: List[str] = []
    is_active: bool = Field(default=True)
    is_exclusive: bool = Field(default=False)
    collection: Optional[str] = None
    tags: List[str] = []
    variant_attributes: List[str] = Field(default=[])
    sellers: List[ProductSellerEntry] = []
    variants: List[VariantOption] = []
    details: Optional[ProductDetails] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    search_tags: Optional[List[str]] = None
    resolved_collection_names: Optional[List[str]] = None
    previously_bought: Optional[bool] = None
    
    # Discount fields added dynamically by populate_product_discounts
    original_price: Optional[float] = None
    price: Optional[float] = None
    default_discount_percentage: Optional[float] = None
    discount_percentage: Optional[float] = None
    applicable_discounts: Optional[List['ApplicableDiscountSnippet']] = None
    quantity_tiers: Optional[List['QuantityTier']] = None
    quantity_item_type: Optional[str] = None
    display_image: Optional[str] = None


class ApplicableDiscountSnippet(CamelBaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None

from app.models.schemas import QuantityTier
Product.model_rebuild()
