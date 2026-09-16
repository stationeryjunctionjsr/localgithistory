from typing import List, Optional, Any, Dict
from pydantic import Field, BaseModel

class BundleItem(BaseModel):
    productId: Optional[str] = Field(default=None, alias="product_id")
    quantity: Optional[int] = 1

class Bundle(BaseModel):
    id: str = Field(default="", alias="_id")
    name: str = ""
    description: Optional[str] = None
    price: float = 0.0
    discountPercentage: Optional[float] = None
    isActive: bool = True
    salesCount: Optional[int] = 0
    items: List[BundleItem] = []
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    external_id: Optional[str] = None

class EmailOtp(BaseModel):
    pass

class FaqSection(BaseModel):
    pass

class Otp(BaseModel):
    pass
