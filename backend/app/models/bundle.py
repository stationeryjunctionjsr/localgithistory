from typing import List, Optional, Any, Dict
from pydantic import Field, BaseModel

from app.models.base import CamelBaseModel
class BundleItem(CamelBaseModel):
    product_id: Optional[str] = None
    quantity: Optional[int] = 1

class Bundle(CamelBaseModel):
    id: str = Field(default="", alias="_id")
    name: str = ""
    description: Optional[str] = None
    price: float = 0.0
    discount_percentage: Optional[float] = None
    is_active: bool = True
    sales_count: Optional[int] = 0
    items: List[BundleItem] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    external_id: Optional[str] = None

class EmailOtp(BaseModel):
    pass

class FaqSection(BaseModel):
    pass

class Otp(BaseModel):
    pass
