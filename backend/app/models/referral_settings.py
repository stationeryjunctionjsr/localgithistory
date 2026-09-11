from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class ReferralSegment(DictCompatibleModel):
    segment: str
    discount_type: str = Field(default="percentage", alias="discountType")
    discount_value: float = Field(default=0.0, alias="discountValue")
    is_active: bool = Field(default=False, alias="isActive")

class ReferralSettings(DictCompatibleModel):
    id: str = Field(default="1", alias="_id")
    retail: Optional[ReferralSegment] = None
    business: Optional[ReferralSegment] = None
