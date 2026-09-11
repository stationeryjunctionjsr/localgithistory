from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class OrderFeedback(DictCompatibleModel):
    id: str = Field(default=None, alias='_id')
    external_id: Optional[Any] = Field(default=None, alias='external_id')
    order_id: Optional[Any] = Field(default=None, alias='orderId')
    user_id: Optional[Any] = Field(default=None, alias='userId')
    rating: Optional[Any] = Field(default=None, alias='rating')
    comment: Optional[Any] = Field(default=None, alias='comment')
    delivery_rating: Optional[Any] = Field(default=None, alias='deliveryRating')
    delivery_comment: Optional[Any] = Field(default=None, alias='deliveryComment')
    feedback_type: Optional[Any] = Field(default=None, alias='feedbackType')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    eid: Optional[Any] = Field(default=None, alias='eid')
    c: Optional[Any] = Field(default=None, alias='c')
    u: Optional[Any] = Field(default=None, alias='u')
