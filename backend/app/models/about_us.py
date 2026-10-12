from datetime import datetime
from typing import Optional
from pydantic import Field
from app.models.base import CamelBaseModel

class AboutUs(CamelBaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    version: Optional[str] = None
    is_published: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
