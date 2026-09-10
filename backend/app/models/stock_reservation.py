from datetime import datetime
from typing import Optional
from pydantic import Field, ConfigDict
from app.models.core import DictCompatibleModel

class StockReservation(DictCompatibleModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    external_id: str
    product_id: str = Field(alias="productId")
    user_id: Optional[str] = Field(default=None, alias="userId")
    quantity: int
    status: str
    expires_at: Optional[datetime] = Field(default=None, alias="expiresAt")
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")
