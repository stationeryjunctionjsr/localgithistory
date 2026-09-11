from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class SystemSettings(DictCompatibleModel):
    id: str = Field(default=None, alias='_id')
    external_id: Optional[str] = Field(default=None, alias='external_id')
    maintenance_mode: Optional[str] = Field(default=None, alias='maintenanceMode')
    allow_signups: Optional[str] = Field(default=None, alias='allowSignups')
    max_upload_size_mb: int = Field(default=0, alias='maxUploadSizeMb')
    default_currency: Optional[str] = Field(default=None, alias='defaultCurrency')
    timezone: Optional[str] = Field(default=None, alias='timezone')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    eid: Optional[str] = Field(default=None, alias='eid')
    c: Optional[str] = Field(default=None, alias='c')
    u: Optional[str] = Field(default=None, alias='u')
