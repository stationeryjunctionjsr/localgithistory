from app.models.base import CamelBaseModel
from datetime import datetime
from typing import Optional, List, Any
from pydantic import Field
from pydantic import BaseModel

class CartItem(CamelBaseModel):
    id: Optional[str] = Field(default=None)
    product: str
    quantity: int
    sell_as_case: bool = Field(default=False)
    bundle_id: Optional[str] = Field(default=None)
    bundle_name: Optional[str] = Field(default=None)

class Cart(CamelBaseModel):
    id: Optional[str] = Field(default=None)
    user: str = Field(alias="user_id")
    items: List[CartItem] = []
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)
