from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel

class SavedForLaterItem(BaseModel):
    product: Optional[str] = None
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")

class SavedForLater(BaseModel):
    id: str = Field(alias="_id")
    user: Optional[str] = None
    items: List[SavedForLaterItem] = []
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")
