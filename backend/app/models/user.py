from app.models.schemas import AddressSnippet as Address, CartItem, OrderItem, VisibilityRule
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel
from app.models.base import CamelBaseModel

class User(CamelBaseModel):
    id: str 
    user_id: int 
    user_id_formatted: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    phone: str = ""
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
    service_area_zones: Optional[List[str]] = Field(default=[])
    is_on_duty: bool = Field(default=False)
    commission_override_pct: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    session_id: Optional[str] = None
    effective_role: Optional[str] = None
    upi_id: Optional[str] = None
    qr_code_url: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_ifsc_code: Optional[str] = None
    bank_account_holder: Optional[str] = None
    bank_name: Optional[str] = None
    max_concurrent_orders: Optional[int] = None

User.model_rebuild()

