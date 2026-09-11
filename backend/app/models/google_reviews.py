from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class Google_reviews(DictCompatibleModel):
    id: str = Field(default=None, alias='_id')
    external_id: Optional[Any] = Field(default=None, alias='external_id')
    rating: Optional[Any] = Field(default=None, alias='rating')
    review_count: Optional[Any] = Field(default=None, alias='reviewCount')
    last_updated: Optional[Any] = Field(default=None, alias='lastUpdated')
    method: Optional[Any] = Field(default=None, alias='method')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    eid: Optional[Any] = Field(default=None, alias='eid')
    c: Optional[Any] = Field(default=None, alias='c')
    u: Optional[Any] = Field(default=None, alias='u')
