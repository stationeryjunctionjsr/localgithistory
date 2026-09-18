from datetime import datetime
from typing import Optional
from pydantic import Field
from pydantic import BaseModel

class ValetPayoutSettings(BaseModel):
    id: str = Field(default=None, alias='_id')
    external_id: Optional[str] = Field(default=None, alias='external_id')
    delivery_charge_per_order: float = Field(default=0.0, alias='deliveryChargePerOrder')
    return_pickup_charge_per_order: float = Field(default=0.0, alias='returnPickupChargePerOrder')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
