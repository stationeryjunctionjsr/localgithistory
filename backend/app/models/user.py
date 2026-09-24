from app.models.schemas import AddressSnippet as Address, CartItem, OrderItem, VisibilityRule
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel

class User(BaseModel):
    id: str = Field(alias="_id")
    user_id: int = Field(alias="userId")
    user_id_formatted: Optional[str] = Field(default=None, alias="userIdFormatted")
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    phone: str = ""
    company_name: Optional[str] = Field(default=None, alias="companyName")
    gst_number: Optional[str] = Field(default=None, alias="gstin")
    address: Optional['Address'] = None
    saved_addresses: List['Address'] = Field(default=[], alias="savedAddresses")
    is_active: bool = Field(default=True, alias="isActive")
    approval_status: Optional[str] = Field(default=None, alias="approvalStatus")
    is_deactivated: bool = Field(default=False, alias="isDeactivated")
    credit_limit: Optional[float] = Field(default=None, alias="creditLimit")
    credit_used: Optional[float] = Field(default=None, alias="creditUsed")
    payment_terms: Optional[int] = Field(default=None, alias="paymentTerms")
    assigned_salesperson: Optional[str] = Field(default=None, alias="assignedSalesperson")
    is_email_verified: bool = Field(default=False, alias="isEmailVerified")
    referral_code: Optional[str] = Field(default=None, alias="referralCode")
    is_seller_admin: bool = Field(default=False, alias="isSellerAdmin")
    service_area_zones: Optional[List[str]] = Field(default=[], alias="serviceAreaZones")
    is_on_duty: bool = Field(default=False, alias="isOnDuty")
    commission_override_pct: Optional[float] = Field(default=None, alias="commissionOverridePct")
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")
    session_id: Optional[str] = Field(default=None, alias="sessionId")
    effective_role: Optional[str] = Field(default=None, alias="effectiveRole")
    upi_id: Optional[str] = Field(default=None, alias="upiId")
    qr_code_url: Optional[str] = Field(default=None, alias="qrCodeUrl")
    max_concurrent_orders: Optional[int] = Field(default=None, alias="maxConcurrentOrders")

User.model_rebuild()

