from app.models.daos import WishlistItemInternal
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel
from app.models.base import CamelBaseModel

class Wishlist(CamelBaseModel):
    id: Optional[int] = None
    user: Optional[int] = None
    items: List[WishlistItemInternal] = Field(default=[])
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
