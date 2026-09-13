from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel

class OrderFeedback(BaseModel):
    id: str = Field(default=None, alias='_id')
    external_id: Optional[str] = Field(default=None, alias='external_id')
    order_id: Optional[str] = Field(default=None, alias='orderId')
    user_id: Optional[str] = Field(default=None, alias='userId')
    rating: Optional[str] = Field(default=None, alias='rating')
    comment: Optional[str] = Field(default=None, alias='comment')
    delivery_rating: Optional[str] = Field(default=None, alias='deliveryRating')
    delivery_comment: Optional[str] = Field(default=None, alias='deliveryComment')
    feedback_type: Optional[str] = Field(default=None, alias='feedbackType')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    eid: Optional[str] = Field(default=None, alias='eid')
    c: Optional[str] = Field(default=None, alias='c')
    u: Optional[str] = Field(default=None, alias='u')
