import os

filepath = 'tests/test_router_pydantic_refactor.py'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# Import CamelBaseModel
if 'CamelBaseModel' not in text:
    text = text.replace('from pydantic import BaseModel, Field, ValidationError', 'from pydantic import BaseModel, Field, ValidationError\nfrom app.models.base import CamelBaseModel')

replacements = {
    'class AdEventPayloadSchema(BaseModel):': 'class AdEventPayloadSchema(CamelBaseModel):',
    'class NotifyPincodePayloadSchema(BaseModel):': 'class NotifyPincodePayloadSchema(CamelBaseModel):\n    product_id: str\n    product_name: str\n    pincode: str\n    email: Optional[str] = None',
    'class Msg91WebhookPayloadSchema(BaseModel):': 'class Msg91WebhookPayloadSchema(CamelBaseModel):\n    status: Optional[str] = None\n    type: Optional[str] = None\n\n    @property\n    def resolved_status(self) -> Optional[str]:\n        return self.status or self.type',
    'class RefreshTokenRequestSchema(BaseModel):': 'class RefreshTokenRequestSchema(CamelBaseModel):\n    user_id: str\n    session_id: str\n    refresh_id: str',
    'class DeliverySlotSchema(BaseModel):': 'class DeliverySlotSchema(CamelBaseModel):\n    id: Optional[str] = None\n    start_time: str\n    end_time: str\n    capacity: int = 10\n    booked_count: int = 0\n    is_full_day: bool = False\n    is_urgent: bool = False\n    is_active: bool = True\n    cutoff_hours: Optional[int] = None\n    urgent_cutoff_hours: Optional[int] = None',
    'class DeliverySlotConfigCreateSchema(BaseModel):': 'class DeliverySlotConfigCreateSchema(CamelBaseModel):\n    zone_id: str\n    slots: List[DeliverySlotSchema] = Field(default_factory=list)\n    zone_default_capacity: int = 10',
    'class ShippingAddressSchema(BaseModel):': 'class ShippingAddressSchema(CamelBaseModel):\n    street: Optional[str] = None\n    city: str\n    state: str\n    zip_code: str\n    phone: Optional[str] = None',
    'class OrderItemCreateSchema(BaseModel):': 'class OrderItemCreateSchema(CamelBaseModel):\n    product_id: str\n    quantity: int = Field(gt=0)\n    price: float = Field(ge=0.0)',
    'class CommissionTierSchema(BaseModel):': 'class CommissionTierSchema(CamelBaseModel):\n    id: Optional[str] = None\n    min_order_value: float = 0.0\n    max_order_value: Optional[float] = None\n    commission_pct: float = Field(ge=0.0, le=100.0)',
    'class ReturnRequestCreateSchema(BaseModel):': 'class ReturnRequestCreateSchema(CamelBaseModel):\n    order_id: str\n    reason: str\n    items: List[Dict[str, Any]] = Field(default_factory=list)',
}

import re

for old, new in replacements.items():
    if old in text:
        # We need to replace the class and its block
        pattern = re.escape(old) + r'.+?(?=\n\nclass|\n\n\n|\Z)'
        text = re.sub(pattern, new, text, flags=re.DOTALL)

# Let's write the text back
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)

