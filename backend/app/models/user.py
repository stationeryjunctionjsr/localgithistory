from app.models.schemas import AddressSnippet as Address, CartItem, OrderItem, VisibilityRule
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict, Field
from app.models.base import CamelBaseModel

class UserFilter(CamelBaseModel):
    model_config = ConfigDict(extra="forbid")
    id: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    referral_code: Optional[str] = None
    is_seller_admin: Optional[bool] = None
    is_on_duty: Optional[bool] = None
    approval_status: Optional[str] = None
    is_active: Optional[bool] = None
    allowed_ids: Optional[List[int]] = None

UserFilter.model_rebuild()


class User(CamelBaseModel):
    id: int
    user_id_formatted: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = ""
    company_name: Optional[str] = None
    gst_number: Optional[str] = None
    address: Optional['Address'] = None
    saved_addresses: List['Address'] = Field(default=[])
    is_active: bool = Field(default=True)
    approval_status: Optional[str] = None
    is_deactivated: bool = Field(default=False)
    credit_limit: Optional[float] = None
    credit_used: Optional[float] = None
    payment_terms: Optional[int] = None
    assigned_salesperson: Optional[str] = None
    is_email_verified: bool = Field(default=False)
    referral_code: Optional[str] = None
    is_seller_admin: bool = Field(default=False)
    service_area_zones: Optional[List[int]] = Field(default=[])
    is_on_duty: bool = Field(default=False)
    commission_override_pct: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    session_id: Optional[int] = None
    effective_role: Optional[str] = None
    upi_id: Optional[str] = None
    qr_code_url: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_ifsc_code: Optional[str] = None
    bank_account_holder: Optional[str] = None
    bank_name: Optional[str] = None
    max_concurrent_orders: Optional[int] = None

User.model_rebuild()



