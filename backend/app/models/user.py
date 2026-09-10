from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class User(DictCompatibleModel):
    id: str = Field(alias="_id")
    user_id: int = Field(alias="userId")
    user_id_formatted: Optional[str] = Field(default=None, alias="userIdFormatted")
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    phone: str = ""
    company_name: Optional[str] = Field(default=None, alias="companyName")
    address: Dict[str, Any] = {}
    saved_addresses: List[Dict[str, Any]] = Field(default=[], alias="savedAddresses")
    is_active: bool = Field(default=True, alias="isActive")
    approval_status: Optional[str] = Field(default=None, alias="approvalStatus")
    is_deactivated: bool = Field(default=False, alias="isDeactivated")
    credit_limit: float = Field(default=0.0, alias="creditLimit")
    credit_used: float = Field(default=0.0, alias="creditUsed")
    payment_terms: Optional[int] = Field(default=None, alias="paymentTerms")
    assigned_salesperson: Optional[str] = Field(default=None, alias="assignedSalesperson")
    is_email_verified: bool = Field(default=False, alias="isEmailVerified")
    referral_code: Optional[str] = Field(default=None, alias="referralCode")
    is_seller_admin: bool = Field(default=False, alias="isSellerAdmin")
    seller_permissions: Dict[str, Any] = Field(default={}, alias="sellerPermissions")
    service_area_zones: List[str] = Field(default=[], alias="serviceAreaZones")
    is_on_duty: bool = Field(default=False, alias="isOnDuty")
    commission_override_pct: Optional[float] = Field(default=None, alias="commissionOverridePct")
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")
