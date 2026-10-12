from datetime import datetime
from typing import Optional
from app.models.base import CamelBaseModel

class ReviewClassifications(CamelBaseModel):
    id: Optional[int] = None
    review_id: Optional[str] = None
    category: Optional[str] = None
    confidence_score: Optional[float] = None
    sentiment: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
