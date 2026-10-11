from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel
from app.models.base import CamelBaseModel

class SellerAvailability(CamelBaseModel):
    id: str = None
    external_id: Optional[str] = None
    seller_id: Optional[str] = None
    status: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    reason: Optional[str] = None
    created_by: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    row_id: Optional[str] = None

    @property
    def startAt(self) -> Optional[str]:
        return self.start_at.isoformat() if self.start_at else None

    @property
    def endAt(self) -> Optional[str]:
        return self.end_at.isoformat() if self.end_at else None

    @property
    def startDate(self) -> Optional[str]:
        return self.start_at.isoformat() if self.start_at else None

    @property
    def endDate(self) -> Optional[str]:
        return self.end_at.isoformat() if self.end_at else None

    @property
    def sellerId(self) -> Optional[str]:
        return self.seller_id
