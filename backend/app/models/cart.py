from datetime import datetime
from typing import Optional, List, Any
from pydantic import Field
from app.models.core import DictCompatibleModel

class CartItem(DictCompatibleModel):
    id: Optional[str] = Field(default=None, alias="_id")
    product: str
    quantity: int
    sell_as_case: bool = Field(default=False, alias="sellAsCase")
    bundle_id: Optional[str] = Field(default=None, alias="bundleId")
    bundle_name: Optional[str] = Field(default=None, alias="bundleName")

class Cart(DictCompatibleModel):
    user: str
    items: List[CartItem] = []
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")
