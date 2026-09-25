from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel
from app.models.base import CamelBaseModel

class SavedForLaterItem(CamelBaseModel):
    product: Optional[str] = None
    created_at: Optional[datetime] = None

class SavedForLater(CamelBaseModel):
    id: str 
    user: Optional[str] = None
    items: List[SavedForLaterItem] = []
    updated_at: Optional[datetime] = None
