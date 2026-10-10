from datetime import datetime
from typing import Optional, List
from pydantic import Field, AliasChoices
from app.models.base import CamelBaseModel

class SavedForLaterItem(CamelBaseModel):
    product: Optional[str] = Field(default=None, validation_alias=AliasChoices("product", "product_id", "productId"))
    product_id: Optional[str] = Field(default=None, validation_alias=AliasChoices("product_id", "product", "productId"))
    created_at: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("created_at", "saved_at", "savedAt"))
    saved_at: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("saved_at", "created_at", "savedAt"))

class SavedForLater(CamelBaseModel):
    id: Optional[str] = Field(default=None, validation_alias=AliasChoices("id", "_id"))
    user: Optional[str] = None
    items: List[SavedForLaterItem] = Field(default_factory=list)
    updated_at: Optional[datetime] = None
