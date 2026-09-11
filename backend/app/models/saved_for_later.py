from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class SavedForLaterItem(DictCompatibleModel):
    product: Optional[str] = None
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")

class SavedForLater(DictCompatibleModel):
    id: str = Field(alias="_id")
    user: Optional[str] = None
    items: List[SavedForLaterItem] = []
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")
