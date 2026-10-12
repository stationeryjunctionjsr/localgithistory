from datetime import datetime
from typing import Optional
from pydantic import Field
from app.models.base import CamelBaseModel

class ValetPayoutSettings(CamelBaseModel):
    id: Optional[int] = None
    delivery_charge_per_order: float = 0.0
    return_pickup_charge_per_order: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
