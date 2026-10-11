from datetime import datetime
from typing import Optional
from pydantic import Field
from app.models.base import CamelBaseModel


class ValetAvailability(CamelBaseModel):
    id: Optional[str] = None
    external_id: Optional[str] = None
    valet_id: Optional[str] = None
    date: Optional[str] = None
    availability_type: Optional[str] = None
    slots: list[str] = Field(default_factory=list)
    zones: list[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class EnrichedValetAvailability(ValetAvailability):
    valet_name: Optional[str] = None
    valet_phone: Optional[str] = None
    service_area_zones: list[str] = Field(default_factory=list)
