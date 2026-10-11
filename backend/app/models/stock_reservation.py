from datetime import datetime
from typing import List, Optional
from pydantic import Field, ConfigDict
from pydantic import BaseModel

class StockReservation(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')

    id: int
    external_id: str
    product_id: str = Field(alias="productId")
    user_id: Optional[str] = Field(default=None, alias="userId")
    quantity: int
    status: str
    expires_at: Optional[datetime] = Field(default=None, alias="expiresAt")
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")


class ProductReservedStock(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    product_id: str
    reserved_quantity: int


class StockReservationBatch(BaseModel):
    model_config = ConfigDict(extra='forbid')
    items: List[ProductReservedStock] = Field(default_factory=list)

    def get_reserved_for_product(self, product_id: str) -> int:
        pid_str = str(product_id)
        for item in self.items:
            if item.product_id == pid_str:
                return item.reserved_quantity
        return 0

