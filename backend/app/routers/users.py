import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.models.schemas import UserResponse, UserUpdate
from app.repositories.user_repository import user_repository
from app.utils.auth import get_current_user, require_super_admin
from app.utils.limiter import limiter

router = APIRouter()


@router.get("", response_model=List[UserResponse])
@router.get("/", response_model=List[UserResponse])
async def get_users(
    role: Optional[str] = None,
    approvalStatus: Optional[str] = None,
    isActive: Optional[bool] = None,
    current_user: dict = Depends(require_super_admin),
):
    query = {}
    if role:
        query["role"] = role
    if approvalStatus:
        query["approvalStatus"] = approvalStatus
    if isActive is not None:
        query["isActive"] = isActive

    users = await user_repository.findAll(query)

    # Remove passwords
    users_without_passwords = [{k: v for k, v in user.items() if k != "password"} for user in users]

    return [UserResponse(**user) for user in users_without_passwords]


@router.get("/pending-approvals", response_model=List[UserResponse])
async def get_pending_approvals(current_user: dict = Depends(require_super_admin)):
    users = await user_repository.findAll({"approvalStatus": "pending"})
    users_without_passwords = [{k: v for k, v in user.items() if k != "password"} for user in users]
    return [UserResponse(**user) for user in users_without_passwords]


@router.get("/me", response_model=UserResponse)
@router.get("/profile", response_model=UserResponse)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user's profile"""
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Could not identify current user")

    user = await user_repository.findById(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(**user)


@router.put("/me/deactivate", response_model=UserResponse)
async def deactivate_own_account(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Could not identify current user")

    user = await user_repository.findById(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("role") == "super_admin":
        raise HTTPException(status_code=400, detail="Super admin accounts cannot self-deactivate")

    update_data = {"isActive": False}
    if user.get("role") == "wholesaler":
        update_data["isDeactivated"] = True

    updated_user = await user_repository.update(user_id, update_data)
    return UserResponse(**updated_user)


class DutyStatusRequest(BaseModel):
    isOnDuty: bool


@router.put("/me/duty-status")
async def update_duty_status(
    data: DutyStatusRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user.get("_id")
    if current_user.get("role") != "valet":
        raise HTTPException(status_code=403, detail="Only valets can update duty status")
    
    await user_repository.update(user_id, {"isOnDuty": data.isOnDuty})
    return {"isOnDuty": data.isOnDuty, "message": f"You are now {'on duty' if data.isOnDuty else 'off duty'}"}


@router.get("/valets/available", response_model=List[UserResponse])
async def get_available_valets(
    pincode: str,
    slotId: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    # 1. Get on-duty valets
    all_valets = await user_repository.findAll({"role": "valet"})
    on_duty = [v for v in all_valets if v.get("isOnDuty")]
    
    # 2. Filter by service area
    in_area = [v for v in on_duty if pincode in v.get("serviceAreaPincodes", [])]
    if not in_area:
        return []
        
    # 3. Filter by availability (full_day or slotId match for today)
    from datetime import datetime
    from app.db.storage_factory import get_storage
    today = datetime.now().strftime("%Y-%m-%d")
    avail_store = get_storage("valetAvailability")
    today_avails = await avail_store.findAll({"date": today})
    
    avail_map = {str(a.get("userId", "")): a for a in today_avails}
    available_valets = []
    for v in in_area:
        vid = str(v.get("_id", ""))
        a = avail_map.get(vid)
        if not a:
            continue
        if a.get("availabilityType") == "full_day":
            available_valets.append(v)
        elif slotId and slotId in a.get("slots", []):
            available_valets.append(v)
            
    if not available_valets:
        return []
        
    # 4. Sort by active load
    from app.repositories.order_repository import order_repository
    active_orders = await order_repository.findAll({
        "status": {"$in": ["pending_valet", "shipped", "return_pickup"]}
    })
    
    load_map = {str(v.get("_id", "")): 0 for v in available_valets}
    for o in active_orders:
        av_id = o.get("assignedValet") or o.get("pendingValetId")
        if type(av_id) == dict:
            av_id = av_id.get("_id")
        av_id = str(av_id) if av_id else ""
        if av_id in load_map:
            load_map[av_id] += 1
            
    # Check max capacity & add load count
    final_valets = []
    for v in available_valets:
        load = load_map[str(v.get("_id", ""))]
        v["activeOrderCount"] = load
        max_cap = v.get("maxConcurrentOrders", 3)
        if load < max_cap:
            final_valets.append(v)
            
    # Sort least busy first
    final_valets.sort(key=lambda v: v.get("activeOrderCount", 0))
    
    users_without_passwords = [{k: v for k, v in user.items() if k != "password"} for user in final_valets]
    return [UserResponse(**user) for user in users_without_passwords]


@router.put("/{user_id}/approve", response_model=UserResponse)
async def approve_user(user_id: str, current_user: dict = Depends(require_super_admin)):
    user = await user_repository.findById(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("role") != "wholesaler":
        raise HTTPException(status_code=400, detail="Only business customers require approval")

    updated_user = await user_repository.update(user_id, {"approvalStatus": "approved", "isActive": True})

    return UserResponse(**updated_user)


@router.put("/{user_id}/reject", response_model=UserResponse)
async def reject_user(user_id: str, current_user: dict = Depends(require_super_admin)):
    user = await user_repository.findById(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user = await user_repository.update(user_id, {"approvalStatus": "rejected", "isActive": False})

    return UserResponse(**updated_user)


class RoleUpdateRequest(BaseModel):
    role: str
    approvalStatus: Optional[str] = None


@router.put("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: str, role_data: RoleUpdateRequest, current_user: dict = Depends(require_super_admin)
):
    if role_data.role not in ["customer", "wholesaler", "valet"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = await user_repository.findById(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("role") == "super_admin":
        raise HTTPException(status_code=400, detail="Cannot change super admin role")

    # Validate Company Name and Address when changing to wholesaler (Business Customer)
    if role_data.role == "wholesaler":
        company_name = user.get("companyName") or ""
        address = user.get("address") or {}

        if not company_name or not company_name.strip():
            raise HTTPException(
                status_code=400,
                detail="Company name is required for Business customer. Please update the user's profile with Company Name before changing the role.",
            )
        if not address.get("street") or not str(address.get("street")).strip():
            raise HTTPException(
                status_code=400,
                detail="Address is required for Business customer. Please update the user's profile with Address before changing the role.",
            )

    update_data = {"role": role_data.role}

    if role_data.role in ["wholesaler", "valet"]:
        update_data["approvalStatus"] = role_data.approvalStatus or "approved"
    else:
        update_data["approvalStatus"] = "approved"

    updated_user = await user_repository.update(user_id, update_data)

    return UserResponse(**updated_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, current_user: dict = Depends(get_current_user)):
    # Convert both IDs to strings for proper comparison
    current_user_id = str(current_user.get("_id", ""))
    requested_user_id = str(user_id)
    if current_user.get("role") != "super_admin" and current_user_id != requested_user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    user = await user_repository.findById(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(**user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_data: UserUpdate, current_user: dict = Depends(get_current_user)):
    # Convert both IDs to strings for proper comparison
    current_user_id = str(current_user.get("_id", ""))
    requested_user_id = str(user_id)
    if current_user.get("role") != "super_admin" and current_user_id != requested_user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    if current_user.get("role") != "super_admin":
        # Non-super admins cannot change certain fields
        update_dict = user_data.dict(exclude_unset=True)
        for key in ["role", "approvalStatus", "isActive", "creditLimit"]:
            update_dict.pop(key, None)
    else:
        update_dict = user_data.dict(exclude_unset=True)

    # Get existing user for validation
    existing_user = await user_repository.findById(user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check email uniqueness if email is being updated
    if "email" in update_dict and update_dict["email"]:
        new_email = update_dict["email"].lower()
        existing_with_email = await user_repository.findByEmail(new_email)
        if existing_with_email and str(existing_with_email.get("_id")) != user_id:
            raise HTTPException(status_code=400, detail="Email already in use by another account.")
        if not existing_user or existing_user.get("email") != new_email:
            update_dict["isEmailVerified"] = False

    # If super admin is changing role to wholesaler, validate Company Name and Address
    if current_user.get("role") == "super_admin" and "role" in update_dict and update_dict["role"] == "wholesaler":
        final_company_name = (
            update_dict.get("companyName") if "companyName" in update_dict else existing_user.get("companyName")
        )
        final_address = update_dict.get("address") if "address" in update_dict else existing_user.get("address")
        final_address = final_address or {}

        if not final_company_name or not final_company_name.strip():
            raise HTTPException(
                status_code=400,
                detail="Company name is required for Business customer. Please update the user's profile with Company Name before changing the role.",
            )
        if not final_address.get("street") or not str(final_address.get("street")).strip():
            raise HTTPException(
                status_code=400,
                detail="Address is required for Business customer. Please update the user's profile with Address before changing the role.",
            )

    if "role" not in update_dict and existing_user.get("role") == "wholesaler":
        final_company_name = (
            update_dict.get("companyName") if "companyName" in update_dict else existing_user.get("companyName")
        )
        final_address = update_dict.get("address") if "address" in update_dict else existing_user.get("address")
        final_address = final_address or {}

        if not final_company_name or not final_company_name.strip():
            raise HTTPException(status_code=400, detail="Company name is required for Business customer")
        if not final_address.get("street") or not str(final_address.get("street")).strip():
            raise HTTPException(status_code=400, detail="Address is required for Business customer")

    user = await user_repository.update(user_id, update_dict)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(**user)


@router.put("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(user_id: str, current_user: dict = Depends(require_super_admin)):
    user = await user_repository.findById(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("role") != "wholesaler":
        raise HTTPException(status_code=400, detail="Only business customers can be deactivated")

    updated_user = await user_repository.update(user_id, {"isDeactivated": True})
    return UserResponse(**updated_user)


@router.put("/{user_id}/activate", response_model=UserResponse)
async def activate_user(user_id: str, current_user: dict = Depends(require_super_admin)):
    user = await user_repository.findById(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user = await user_repository.update(user_id, {"isDeactivated": False})
    return UserResponse(**updated_user)


@router.put("/{user_id}/mark-valet", response_model=UserResponse)
async def mark_user_as_valet(user_id: str, current_user: dict = Depends(require_super_admin)):
    user = await user_repository.findById(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("role") == "super_admin":
        raise HTTPException(status_code=400, detail="Cannot mark super admin as valet")

    updated_user = await user_repository.update(user_id, {"role": "valet"})
    return UserResponse(**updated_user)


class PasswordChangeRequest(BaseModel):
    newPassword: str
    currentPassword: Optional[str] = None


@router.put("/{user_id}/password")
async def change_password(
    user_id: str, password_data: PasswordChangeRequest, current_user: dict = Depends(get_current_user)
):
    # Convert both IDs to strings for proper comparison
    current_user_id = str(current_user.get("_id", ""))
    requested_user_id = str(user_id)
    is_admin = current_user.get("role") == "super_admin"
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

        stored_hash = user.get("password", "")
        if not stored_hash or not verify_password(password_data.currentPassword, stored_hash):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

    await user_repository.update(user_id, {"password": password_data.newPassword})
    return {"message": "Password changed successfully"}


@router.delete("/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(require_super_admin)):
    user = await user_repository.findById(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("role") == "super_admin":
        raise HTTPException(status_code=400, detail="Cannot delete super admin")

    await user_repository.delete(user_id)
    return {"message": "User deleted successfully"}


# ─── Email Verification Endpoints ───
class VerifyEmailRequest(BaseModel):
    code: str


@router.post("/request-email-verification")
@limiter.limit("5/minute")
async def request_email_verification(request: Request, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("_id")
    user = await user_repository.findById(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    email = user.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="No email address associated with your profile.")

    from app.utils.email_otp import request_email_otp_async

    ok, payload = await request_email_otp_async(email)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=payload.get("message", "Too many verification requests. Please try again later."),
            headers={"Retry-After": str(int(payload.get("retry_after_seconds") or 0))},
        )

    response_data = {"message": "Verification code sent to your email."}
    if os.getenv("ENVIRONMENT") == "development" or os.getenv("TESTING") == "true":
        response_data["code"] = payload.get("otp")

    return response_data


@router.post("/verify-email")
@limiter.limit("5/minute")
async def verify_email(data: VerifyEmailRequest, request: Request, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("_id")
    user = await user_repository.findById(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    email = user.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="No email address associated with your profile.")

    from app.utils.email_otp import verify_email_otp_async

    result = await verify_email_otp_async(email, data.code)
    if not result.get("valid"):
        raise HTTPException(status_code=400, detail=result.get("message", "Invalid or expired verification code."))

    await user_repository.update(user_id, {"isEmailVerified": True})
    return {"message": "Email verified successfully."}
