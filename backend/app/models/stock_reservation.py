from datetime import datetime
from typing import List, Optional, Union
from pydantic import Field, ConfigDict
from pydantic import BaseModel

class StockReservation(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')

    id: int
    product_id: int = Field(alias="productId")
    user_id: Optional[str] = Field(default=None, alias="userId")
    quantity: int
    status: str
    expires_at: Optional[datetime] = Field(default=None, alias="expiresAt")
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")


class ProductReservedStock(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    product_id: int
    reserved_quantity: int


class StockReservationBatch(BaseModel):
    model_config = ConfigDict(extra='forbid')
    items: List[ProductReservedStock] = Field(default_factory=list)

    def get_reserved_for_product(self, product_id: Union[int, str]) -> int:
        try:
            pid_int = int(str(product_id).replace("PDT-", ""))
        except (ValueError, TypeError):
            return 0
        for item in self.items:
            if item.product_id == pid_int:
                return item.reserved_quantity
        return 0

