from datetime import datetime
from typing import Optional, List
from pydantic import Field
from app.models.base import CamelBaseModel

class SavedForLaterItem(CamelBaseModel):
    user: Optional[str] = None
    product_id: Optional[str] = None
    product: Optional[str] = None
    saved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

class SavedForLater(CamelBaseModel):
    id: Optional[str] = None
    user: Optional[str] = None
    items: List[SavedForLaterItem] = Field(default_factory=list)
    updated_at: Optional[datetime] = None
