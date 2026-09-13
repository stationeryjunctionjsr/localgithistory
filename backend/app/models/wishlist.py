from app.models.daos import WishlistItemInternal
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel

class Wishlist(BaseModel):
    id: str = Field(default=None, alias='_id')
    user: Optional[str] = Field(default=None, alias='user')
    items: List[WishlistItemInternal] = Field(default=[], alias='items')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    wid: Optional[str] = Field(default=None, alias='wid')
    pid: Optional[str] = Field(default=None, alias='pid')
    external_id: Optional[str] = Field(default=None, alias='external_id')
    user_id: Optional[str] = Field(default=None, alias='user_id')
    eid: Optional[str] = Field(default=None, alias='eid')
    u: Optional[str] = Field(default=None, alias='u')
