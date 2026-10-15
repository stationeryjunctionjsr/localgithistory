from __future__ import annotations
from pydantic import ConfigDict
from datetime import datetime
from typing import Optional, List
from pydantic import Field
from pydantic import BaseModel
from app.models.base import CamelBaseModel

class Product(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    id: int 
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

    def has_seller(self, seller_id: Optional[int]) -> bool:
        if seller_id is None:
            return True
        for s in self.sellers:
            if s.seller_id == seller_id:
                return True
        return False


class ApplicableDiscountSnippet(CamelBaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None


class WeightedSearchResult(CamelBaseModel):
    products: List[Product] = Field(default_factory=list)
    used_fuzzy: bool = False
    suggested_query: Optional[str] = None


class ProductFacets(CamelBaseModel):
    brands: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    sub_categories: List[str] = Field(default_factory=list)
    collections: List[str] = Field(default_factory=list)


class VariantCombinationItem(CamelBaseModel):
    attributes: dict[str, str] = Field(default_factory=dict)
    quantity: int = 1


class ProductFilter(CamelBaseModel):
    id: Optional[int] = None
    search: Optional[str] = None
    category: Optional[str] = None
    categories: Optional[str] = None
    sub_category: Optional[str] = None
    brand: Optional[str] = None
    brands: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    popularity: Optional[str] = None
    collection: Optional[str] = None
    category_tag: Optional[str] = None
    min_discount: Optional[float] = None
    allowed_seller_ids: Optional[List[int]] = None
    my_seller_id: Optional[int] = None
    seller_ids: Optional[List[int]] = None
    allowed_ids: Optional[List[int]] = None
    role: str = "customer"
    user_id: Optional[str] = None
    sort: Optional[str] = None
    sort_by: Optional[str] = None
    is_active: Optional[bool] = None
    include_inactive: bool = False
    availability: Optional[str] = None
    sku: Optional[str] = None
    name: Optional[str] = None
    limit: Optional[int] = None


ProductCatalogQuery = ProductFilter


from app.models.schemas import VariantOption, ProductSellerEntry, ProductDetails, QuantityTier
Product.model_rebuild()
WeightedSearchResult.model_rebuild()
ProductCatalogQuery.model_rebuild()


