from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel
from app.models.base import CamelBaseModel

class ReferralSegment(CamelBaseModel):
    segment: str
    discount_type: str = Field(default="percentage")
    discount_value: Optional[float] = None
    is_active: bool = Field(default=False)

class ReferralSettings(CamelBaseModel):
    id: str = Field(default="1")
    retail: Optional[ReferralSegment] = None
    business: Optional[ReferralSegment] = None
