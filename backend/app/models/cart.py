from app.models.base import CamelBaseModel
from datetime import datetime
from typing import Optional, List, Any
from pydantic import Field
from app.models.daos import CartItemInternal

class CartItem(CartItemInternal):
    pass

class Cart(CamelBaseModel):
    id: Optional[str] = Field(default=None)
    user: str = Field(alias="user_id")
    items: List[CartItemInternal] = []
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

    @property
    def _id(self) -> Optional[str]:
        return self.id
