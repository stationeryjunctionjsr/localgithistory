from app.models.daos import WishlistItemInternal
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel
from app.models.base import CamelBaseModel

class Wishlist(CamelBaseModel):
    id: Optional[int] = None
    user: Optional[str] = None
    items: List[WishlistItemInternal] = Field(default=[])
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    wid: Optional[str] = None
    pid: Optional[str] = None
    user_id: Optional[str] = None
    u: Optional[str] = None

    @property
    def _id(self) -> Optional[int]:
        return self.id
