from datetime import datetime
from typing import Optional
from pydantic import Field
from app.models.base import CamelBaseModel

class PincodeSearches(CamelBaseModel):
    id: Optional[int] = None
    pincode: Optional[str] = None
    query: Optional[str] = None
    is_serviceable: bool = False
    timestamp: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def searched_at(self) -> Optional[str]:
        return self.timestamp
