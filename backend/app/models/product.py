from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class Product(DictCompatibleModel):
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
    mrp_per_case: Optional[float] = Field(default=None, alias="mrpPerCase")
    quantity_per_case: Optional[int] = Field(default=None, alias="quantityPerCase")
    stock: int = 0
    rating: float = 0.0
    reviews: int = 0
    images: List[str] = []
    videos: List[str] = []
    is_active: bool = Field(default=True, alias="isActive")
    tags: List[str] = []
    variant_attributes: List[Any] = Field(default=[], alias="variantAttributes")
    variants: List[Any] = []
    details: Dict[str, Any] = {}
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")
