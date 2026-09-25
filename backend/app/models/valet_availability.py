from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel
from app.models.base import CamelBaseModel

class ValetAvailability(CamelBaseModel):
    id: str = None
    external_id: Optional[str] = None
    valet_id: Optional[str] = None
    date: Optional[datetime] = None
    availability_type: Optional[str] = None
    slots: Optional[List[str]] = None
    zones: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    vid: Optional[str] = None
    s: Optional[str] = None
    z: Optional[str] = None
    eid: Optional[str] = None
    atype: Optional[str] = None
    up: Optional[str] = None
