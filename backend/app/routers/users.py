from app.models.user import User
import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.models.schemas import UserResponse, UserUpdate, SUPPORTED_LANGUAGES, PaginatedUsersResponse, PreferencesResponse, DutyStatusResponse, MessageResponse
from typing import Dict, Any
from app.repositories.user_repository import user_repository
from app.utils.auth import get_current_user, require_super_admin, require_super_admin_or_seller
from app.utils.limiter import limiter

router = APIRouter()


@router.get("", response_model=PaginatedUsersResponse)
@router.get("/", response_model=PaginatedUsersResponse)
async def get_users(
    role: Optional[str] = None,
    approvalStatus: Optional[str] = None,
    isActive: Optional[bool] = None,
    page: Optional[int] = None,
    limit: Optional[int] = None,
    current_user: User = Depends(require_super_admin),
):
    query = {}
    if role:
        query["role"] = role
    if approvalStatus:
        query["approvalStatus"] = approvalStatus
    if isActive is not None:
        query["isActive"] = isActive

    if page is not None and limit is not None and limit > 0:
        page = max(1, page)
        start = (page - 1) * limit

        users = await user_repository.findAll(query, skip=start, limit=limit)
        total = await user_repository.count(query)

        # Remove passwords
        users_without_passwords = users

        return {
            "users": users_without_passwords,
            "totalCount": total,
            "page": page,
            "limit": limit
        }
        
    # No pagination -- return all (backwards compatible), capped at 1000 rows to protect memory
    users = await user_repository.findAll(query, limit=1000)
    users_without_passwords = users
    return {
        "users": users_without_passwords,
        "totalCount": len(users_without_passwords),
        "page": 1,
        "limit": len(users_without_passwords) or 1
    }


@router.get("/pending-approvals", response_model=List[UserResponse])
async def get_pending_approvals(current_user: User = Depends(require_super_admin)):
    users = await user_repository.findAll({"approvalStatus": "pending"})
    users_without_passwords = users
    return [user for user in users_without_passwords]


@router.get("/me", response_model=UserResponse)
@router.get("/profile", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get current authenticated user's profile"""
    user_id = current_user.id
    if not user_id:
        raise HTTPException(status_code=400, detail="Could not identify current user")

    user = await user_repository.findById(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


class UserPreferencesUpdate(BaseModel):
    preferredLanguage: str


@router.patch("/me/preferences", response_model=PreferencesResponse)
async def update_my_preferences(
    data: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update current user's UI preferences (language, etc.).
    Lightweight endpoint so the frontend can sync language across devices without
    triggering the full profile-update validation.
    """
    if data.preferredLanguage not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language '{data.preferredLanguage}'. Supported: {sorted(SUPPORTED_LANGUAGES)}",
        )
    user_id = current_user.id
    await user_repository.update(user_id, UserUpdate(preferredLanguage=data.preferredLanguage))
    return {"preferredLanguage": data.preferredLanguage}



@router.put("/me/deactivate", response_model=UserResponse)
async def deactivate_own_account(current_user: User = Depends(get_current_user)):
    user_id = current_user.id
    if not user_id:
        raise HTTPException(status_code=400, detail="Could not identify current user")

    user = await user_repository.findById(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == "super_admin":
        raise HTTPException(status_code=400, detail="Super admin accounts cannot self-deactivate")

    update_data = UserUpdate(isActive=False)
    if user.role == "wholesaler":
        update_data.is_deactivated = True
        update_data.serviceAreaZones = []

    updated_user = await user_repository.update(user_id, update_data)
    return updated_user


class DutyStatusRequest(BaseModel):
    isOnDuty: bool


@router.put("/me/duty-status", response_model=DutyStatusResponse)
async def update_duty_status(
    data: DutyStatusRequest,
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.id
    if current_user.role != "valet":
        raise HTTPException(status_code=403, detail="Only valets can update duty status")
    
    await user_repository.update(user_id, UserUpdate(isOnDuty=data.is_on_duty))
    return {"isOnDuty": data.is_on_duty, "message": f"You are now {'on duty' if data.is_on_duty else 'off duty'}"}


@router.get("/valets/available", response_model=List[UserResponse])
async def get_available_valets(
    pincode: str,
    slotId: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    # 1. Get on-duty valets
    all_valets = await user_repository.findAll({"role": "valet"})
    on_duty = [v for v in all_valets if v.is_on_duty]
    
    # 2. Filter by service area
    in_area = [v for v in on_duty if pincode in (v.service_area_pincodes or [])]
    if not in_area:
        return []
        
    # 3. Filter by availability (full_day or slotId match for today)
    from datetime import datetime
    from app.db.storage_factory import get_storage
    today = datetime.now().strftime("%Y-%m-%d")
    avail_store = get_storage("valetAvailability")
    today_avails = await avail_store.findAll({"date": today})
    
    avail_map = {str((a.userId if a.userId is not None else "")): a for a in today_avails}
    available_valets = []
    for v in in_area:
        vid = str((v.id or ""))
        a = (avail_map[vid] if vid in avail_map else None)
        if not a:
            continue
        if a.availabilityType == "full_day":
            available_valets.append(v)
        elif slotId and slotId in (a.slots if a.slots is not None else []):
            available_valets.append(v)
            
    if not available_valets:
        return []
        
    # 4. Sort by active load
    from app.repositories.order_repository import order_repository
    active_orders = await order_repository.findAll({
        "status": {"$in": ["pending_valet", "shipped", "return_pickup"]}
    })
    
    load_map = {str((v.id or "")): 0 for v in available_valets}
    for o in active_orders:
        av_id = o.assigned_valet or o.pending_valet_id
        if type(av_id) is not str and type(av_id) is not type(None):
            av_id = av_id.id
        # Removed dictionary checking to enforce strict models
        av_id = str(av_id) if av_id else ""
        if av_id in load_map:
            load_map[av_id] += 1
            
    # Check max capacity & add load count
    final_valets = []
    for v in available_valets:
        load = load_map[str((v.id or ""))]
        v["activeOrderCount"] = load
        max_cap = (v.max_concurrent_orders if v.max_concurrent_orders is not None else 3)
        if load < max_cap:
            final_valets.append(v)
            
    # Sort least busy first
    final_valets.sort(key=lambda v: (v.active_order_count if v.active_order_count is not None else 0))
    
    users_without_passwords = final_valets
    return [user for user in users_without_passwords]


@router.put("/{user_id}/approve", response_model=UserResponse)
async def approve_user(user_id: str, current_user: User = Depends(require_super_admin)):
    user = await user_repository.findById(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role != "wholesaler":
        raise HTTPException(status_code=400, detail="Only business customers require approval")

    updated_user = await user_repository.update(user_id, UserUpdate(approvalStatus="approved", isActive=True))

    return updated_user


@router.put("/{user_id}/reject", response_model=UserResponse)
async def reject_user(user_id: str, current_user: User = Depends(require_super_admin)):
    user = await user_repository.findById(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user = await user_repository.update(user_id, UserUpdate(approvalStatus="rejected", isActive=False))

    return updated_user


class RoleUpdateRequest(BaseModel):
    role: str
    approvalStatus: Optional[str] = None


@router.put("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: str, role_data: RoleUpdateRequest, current_user: User = Depends(require_super_admin)
):
    if role_data.role not in ["customer", "wholesaler", "valet"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = await user_repository.findById(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == "super_admin":
        raise HTTPException(status_code=400, detail="Cannot change super admin role")

    # Validate Company Name and Address when changing to wholesaler (Business Customer)
    if role_data.role == "wholesaler":
        company_name = user.company_name or ""
        address = user.address or {}

        if not company_name or not company_name.strip():
            raise HTTPException(
                status_code=400,
                detail="Company name is required for Business customer. Please update the user's profile with Company Name before changing the role.",
            )
        if not address.street or not str(address.street).strip():
            raise HTTPException(
                status_code=400,
                detail="Address is required for Business customer. Please update the user's profile with Address before changing the role.",
            )

    update_data = UserUpdate(role=role_data.role)

    if role_data.role in ["wholesaler", "valet"]:
        update_data.approval_status = role_data.approval_status or "approved"
    else:
        update_data.approval_status = "approved"

    updated_user = await user_repository.update(user_id, update_data)

    return updated_user


class SellerZoneSettingsUpdate(BaseModel):
    serviceableZoneIds: List[str]


@router.get("/seller-delivery-settings", response_model=UserResponse)
async def get_seller_delivery_settings(
    current_user: User = Depends(require_super_admin_or_seller),
):
    """Return the seller's current zone selections and all available zones with their pincodes."""
    from app.db.storage_factory import get_storage

    zones_storage = get_storage("deliveryZones")
    all_zones = await zones_storage.findAll({"isActive": True})

    current_zone_ids = current_user.service_area_zones or []

    available_zones = []
    for z in all_zones:
        z_id = str(z.id)
        z_name = z.name or ""
        z_pincodes = z.pincodes or []
        z_capacity = z.default_capacity if z.default_capacity is not None else 10
        z_urgent = z.urgent_delivery_available if z.urgent_delivery_available is not None else False
        z_customer_type = z.customer_type or "retail"
        available_zones.append({
            "id": z_id,
            "name": z_name,
            "pincodes": z_pincodes,
            "defaultCapacity": z_capacity,
            "urgentDeliveryAvailable": bool(z_urgent),
            "customerType": z_customer_type,
        })

    return {
        "sellerId": str((current_user.id or "")),
        "sellerName": current_user.company_name or (current_user.name or ""),
        "serviceableZoneIds": current_zone_ids,
        "availableZones": available_zones,
    }


@router.put("/seller-delivery-settings", response_model=UserResponse)
async def update_seller_delivery_settings(
    data: SellerZoneSettingsUpdate,
    current_user: User = Depends(require_super_admin_or_seller),
):
    """Update the seller's zone selections."""
    from app.repositories.zone_seller_cache import invalidate_zone_cache

    seller_id = str((current_user.id or ""))
    updated_user = await user_repository.update(seller_id, UserUpdate(serviceAreaZones=data.serviceableZoneIds))
    # Invalidate the full seller-zone cache so changes take effect immediately
    invalidate_zone_cache()
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, current_user: User = Depends(get_current_user)):
    # Convert both IDs to strings for proper comparison
    current_user_id = str((current_user.id or ""))
    requested_user_id = str(user_id)
    if current_user.role != "super_admin" and current_user_id != requested_user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    user = await user_repository.findById(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_data: UserUpdate, current_user: User = Depends(get_current_user)):
    # Convert both IDs to strings for proper comparison
    current_user_id = str((current_user.id or ""))
    requested_user_id = str(user_id)
    if current_user.role != "super_admin" and current_user_id != requested_user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    if current_user.role != "super_admin":
        # Non-super admins cannot change certain fields
        user_data.role = None
        user_data.approval_status = None
        user_data.isActive = None
        user_data.credit_limit = None


    # Get existing user for validation
    existing_user = await user_repository.findById(user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check email uniqueness if email is being updated
    if user_data.email is not None and user_data.email:
        new_email = user_data.email.lower()
        existing_with_email = await user_repository.findByEmail(new_email)
        if existing_with_email and str(existing_with_email.id or existing_with_email._id) != user_id:
            raise HTTPException(status_code=400, detail="Email already in use by another account.")
        if not existing_user or existing_user.email != new_email:
            user_data.is_email_verified = False

    # If super admin is changing role to wholesaler, validate Company Name and Address
    if current_user.role == "super_admin" and user_data.role is not None and user_data.role == "wholesaler":
        final_company_name = (
            user_data.company_name if user_data.company_name is not None else existing_user.company_name
        )
        final_address = user_data.address if user_data.address is not None else existing_user.address

        if not final_company_name or not str(final_company_name).strip():
            raise HTTPException(
                status_code=400,
                detail="Company name is required for Business customer. Please update the user's profile with Company Name before changing the role.",
            )
        final_street = final_address.street
        
        if not final_street or not str(final_street).strip():
            raise HTTPException(
                status_code=400,
                detail="Address is required for Business customer. Please update the user's profile with Address before changing the role.",
            )

    if user_data.role is None and existing_user.role == "wholesaler":
        final_company_name = (
            user_data.company_name if user_data.company_name is not None else existing_user.company_name
        )
        final_address = user_data.address if user_data.address is not None else existing_user.address

        if not final_company_name or not str(final_company_name).strip():
            raise HTTPException(status_code=400, detail="Company name is required for Business customer")
        final_street = final_address.street
        
        if not final_street or not str(final_street).strip():
            raise HTTPException(status_code=400, detail="Address is required for Business customer")

    user = await user_repository.update(user_id, user_data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.put("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(user_id: str, current_user: User = Depends(require_super_admin)):
    user = await user_repository.findById(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role != "wholesaler":
        raise HTTPException(status_code=400, detail="Only business customers can be deactivated")

    updated_user = await user_repository.update(user_id, UserUpdate(isDeactivated=True, serviceAreaZones=[]))
    return updated_user


@router.put("/{user_id}/activate", response_model=UserResponse)
async def activate_user(user_id: str, current_user: User = Depends(require_super_admin)):
    user = await user_repository.findById(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user = await user_repository.update(user_id, UserUpdate(isDeactivated=False))
    return updated_user


@router.put("/{user_id}/mark-valet", response_model=UserResponse)
async def mark_user_as_valet(user_id: str, current_user: User = Depends(require_super_admin)):
    user = await user_repository.findById(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == "super_admin":
        raise HTTPException(status_code=400, detail="Cannot mark super admin as valet")

    updated_user = await user_repository.update(user_id, UserUpdate(role="valet"))
    return updated_user


class PasswordChangeRequest(BaseModel):
    newPassword: str
    currentPassword: Optional[str] = None


@router.put("/{user_id}/password", response_model=MessageResponse)
async def change_password(
    user_id: str, password_data: PasswordChangeRequest, current_user: User = Depends(get_current_user)
):
    # Convert both IDs to strings for proper comparison
    current_user_id = str((current_user.id or ""))
    requested_user_id = str(user_id)
    is_admin = current_user.role == "super_admin"
    if not is_admin and current_user_id != requested_user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    user = await user_repository.findById(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not password_data.newPassword or len(password_data.newPassword) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")

    # Non-admins must provide and verify their current password
    if not is_admin:
        if not password_data.currentPassword:
            raise HTTPException(status_code=400, detail="currentPassword is required")
        from app.utils.auth import verify_password

        stored_hash = (user.password or "")
        if not stored_hash or not verify_password(password_data.currentPassword, stored_hash):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

    await user_repository.update(user_id, UserUpdate(password=password_data.newPassword))
    return {"message": "Password changed successfully"}


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(user_id: str, current_user: User = Depends(require_super_admin)):
    user = await user_repository.findById(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == "super_admin":
        raise HTTPException(status_code=400, detail="Cannot delete super admin")

    await user_repository.delete(user_id)
    return {"message": "User deleted successfully"}


# ─── Email Verification Endpoints ───
class VerifyEmailRequest(BaseModel):
    code: str


@router.post("/request-email-verification", response_model=MessageResponse)
@limiter.limit("5/minute")
async def request_email_verification(request: Request, current_user: User = Depends(get_current_user)):
    user_id = current_user.id
    user = await user_repository.findById(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    email = user.email
    if not email:
        raise HTTPException(status_code=400, detail="No email address associated with your profile.")

    from app.utils.email_otp import request_email_otp_async

    ok, payload = await request_email_otp_async(email)
    if not ok:
        err_msg = payload.get("message")
        retry_secs = payload.get("retry_after_seconds")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=err_msg,
            headers={"Retry-After": str(int(retry_secs or 0))},
        )

    response_data = {"message": "Verification code sent to your email."}
    if os.getenv("ENVIRONMENT") == "development" or os.getenv("TESTING") == "true":
        otp_val = payload.get("otp")
        response_data["code"] = otp_val

    return response_data


@router.post("/verify-email", response_model=MessageResponse)
@limiter.limit("5/minute")
async def verify_email(data: VerifyEmailRequest, request: Request, current_user: User = Depends(get_current_user)):
    user_id = current_user.id
    user = await user_repository.findById(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    email = user.email
    if not email:
        raise HTTPException(status_code=400, detail="No email address associated with your profile.")

    from app.utils.email_otp import verify_email_otp_async

    result = await verify_email_otp_async(email, data.code)
    is_valid = result.get("valid")
    if not is_valid:
        err_msg = result.get("message")
        raise HTTPException(status_code=400, detail=err_msg)

    await user_repository.update(user_id, UserUpdate(isEmailVerified=True))
    return {"message": "Email verified successfully."}


# ── Seller Zone Settings ────────────────────────────────────────────────────────




class PaymentDetailsUpdate(BaseModel):
    upiId: Optional[str] = None
    qrCodeUrl: Optional[str] = None
    bankAccountNumber: Optional[str] = None
    bankIfscCode: Optional[str] = None
    bankAccountHolder: Optional[str] = None
    bankName: Optional[str] = None

@router.put('/me/payment-details', response_model=UserResponse)
async def update_my_payment_details(data: PaymentDetailsUpdate, current_user: User = Depends(get_current_user)):
    if current_user.role not in ('wholesaler', 'valet'):
        raise HTTPException(status_code=403, detail='Only sellers and valets can update payment details')
    updated = await user_repository.update(str(current_user.id), UserUpdate(
        upiId=data.upi_id,
        qrCodeUrl=data.qr_code_url,
        bankAccountNumber=data.bank_account_number,
        bankIfscCode=data.bank_ifsc_code,
        bankAccountHolder=data.bank_account_holder,
        bankName=data.bank_name,
    ))
    return updated

from app.models.schemas import PaymentDetailsResponse

@router.get('/{user_id}/payment-details', response_model=PaymentDetailsResponse)
async def get_user_payment_details(user_id: str, current_user: User = Depends(require_super_admin)):
    user = await user_repository.findById(user_id)
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    return PaymentDetailsResponse(
        upiId=user.upi_id,
        qrCodeUrl=user.qr_code_url,
        bankAccountNumber=user.bank_account_number,
        bankIfscCode=user.bank_ifsc_code,
        bankAccountHolder=user.bank_account_holder,
        bankName=user.bank_name,
    )
