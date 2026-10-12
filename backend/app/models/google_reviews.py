from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel

class Google_reviews(BaseModel):
    id: Optional[str] = None
    rating: Optional[str] = Field(default=None, alias='rating')
    review_count: int = Field(default=0, alias='reviewCount')
    last_updated: Optional[str] = Field(default=None, alias='lastUpdated')
    method: Optional[str] = Field(default=None, alias='method')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    c: Optional[str] = Field(default=None, alias='c')
    u: Optional[str] = Field(default=None, alias='u')
