from datetime import datetime
from typing import Optional
from pydantic import Field
from app.models.base import CamelBaseModel

class SystemSettings(CamelBaseModel):
    id: Optional[str] = Field(default=None, alias='_id')
    external_id: Optional[str] = None
    maintenance_mode: bool = False
    allow_signups: bool = False
    max_upload_size_mb: Optional[int] = 0
    max_concurrent_orders: Optional[int] = 1
    default_currency: Optional[str] = None
    timezone: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
