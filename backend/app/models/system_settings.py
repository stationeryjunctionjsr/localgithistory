from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class SystemSettings(DictCompatibleModel):
    id: str = Field(default=None, alias='_id')
    external_id: Optional[Any] = Field(default=None, alias='external_id')
    maintenance_mode: Optional[Any] = Field(default=None, alias='maintenanceMode')
    allow_signups: Optional[Any] = Field(default=None, alias='allowSignups')
    max_upload_size_mb: Optional[Any] = Field(default=None, alias='maxUploadSizeMb')
    default_currency: Optional[Any] = Field(default=None, alias='defaultCurrency')
    timezone: Optional[Any] = Field(default=None, alias='timezone')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    eid: Optional[Any] = Field(default=None, alias='eid')
    c: Optional[Any] = Field(default=None, alias='c')
    u: Optional[Any] = Field(default=None, alias='u')
