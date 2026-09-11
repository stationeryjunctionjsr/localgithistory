from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class ValetAvailability(DictCompatibleModel):
    id: str = Field(default=None, alias='_id')
    external_id: Optional[Any] = Field(default=None, alias='externalId')
    valet_id: Optional[Any] = Field(default=None, alias='valetId')
    date: Optional[Any] = Field(default=None, alias='date')
    availability_type: Optional[Any] = Field(default=None, alias='availabilityType')
    slots: Optional[Any] = Field(default=None, alias='slots')
    zones: Optional[Any] = Field(default=None, alias='zones')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    vid: Optional[Any] = Field(default=None, alias='vid')
    s: Optional[Any] = Field(default=None, alias='s')
    z: Optional[Any] = Field(default=None, alias='z')
    eid: Optional[Any] = Field(default=None, alias='eid')
    atype: Optional[Any] = Field(default=None, alias='atype')
    up: Optional[Any] = Field(default=None, alias='up')
