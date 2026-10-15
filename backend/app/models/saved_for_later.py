from datetime import datetime, timezone
from typing import Optional, List
from pydantic import Field, field_validator
from app.models.base import CamelBaseModel

class SavedForLaterItem(CamelBaseModel):
    user: Optional[int] = None
    product_id: Optional[int] = None
    product: Optional[int] = None
    saved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    @field_validator('saved_at', 'created_at', mode='after')
    @classmethod
    def clean_dt(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None and v.tzinfo is not None:
            return v.astimezone(timezone.utc).replace(tzinfo=None)
        return v

class SavedForLater(CamelBaseModel):
    id: Optional[int] = None
    user: Optional[int] = None
    items: List[SavedForLaterItem] = Field(default_factory=list)
    updated_at: Optional[datetime] = None

    @field_validator('updated_at', mode='after')
    @classmethod
    def clean_dt(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None and v.tzinfo is not None:
            return v.astimezone(timezone.utc).replace(tzinfo=None)
        return v
