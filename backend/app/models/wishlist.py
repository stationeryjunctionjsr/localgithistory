from app.models.daos import WishlistItemInternal
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel
from app.models.base import CamelBaseModel

class Wishlist(CamelBaseModel):
    id: str = None
    user: Optional[str] = None
    items: List[WishlistItemInternal] = Field(default=[])
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    wid: Optional[str] = None
    pid: Optional[str] = None
    external_id: Optional[str] = None
    user_id: Optional[str] = None
    eid: Optional[str] = None
    u: Optional[str] = None
