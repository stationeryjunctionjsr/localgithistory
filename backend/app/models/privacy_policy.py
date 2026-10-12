from datetime import datetime
from typing import Optional
from pydantic import Field
from app.models.base import CamelBaseModel

class PrivacyPolicy(CamelBaseModel):
    id: Optional[int] = None
    version: Optional[str] = None
    content: Optional[str] = None
    effective_date: Optional[datetime] = None
    is_active: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
