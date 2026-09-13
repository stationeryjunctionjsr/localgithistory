from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel

class ReferralSegment(BaseModel):
    segment: str
    discount_type: str = Field(default="percentage", alias="discountType")
    discount_value: Optional[float] = Field(default=None, alias="discountValue")
    is_active: bool = Field(default=False, alias="isActive")

class ReferralSettings(BaseModel):
    id: str = Field(default="1", alias="_id")
    retail: Optional[ReferralSegment] = None
    business: Optional[ReferralSegment] = None
