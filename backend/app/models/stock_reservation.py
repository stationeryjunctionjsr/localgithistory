from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.base import CamelBaseModel


class StockReservation(CamelBaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    product_id: int
    user_id: Optional[str] = None
    quantity: int
    status: str
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProductReservedStock(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    product_id: int
    reserved_quantity: int


class StockReservationBatch(BaseModel):
    model_config = ConfigDict(extra='forbid')
    items: List[ProductReservedStock] = Field(default_factory=list)

    def get_reserved_for_product(self, product_id: int) -> int:
        for item in self.items:
            if item.product_id == product_id:
                return item.reserved_quantity
        return 0

