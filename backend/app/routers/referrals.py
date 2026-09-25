from app.models.user import User
import logging
from fastapi import APIRouter, Depends, HTTPException

logger = logging.getLogger(__name__)
from typing import Optional

from app.models.schemas import (
    ReferralSettingsResponse,
    ReferralVerifyRequest,
    ReferralVerifyResponse,
    ReferralEligibilityResponse,
    ReferralPublicSchemeResponse,
)
from app.repositories.referral_repository import referral_repository
from app.utils.auth import require_super_admin, get_current_user

router = APIRouter()


@router.get("/settings", response_model=ReferralSettingsResponse)
async def get_referral_settings(admin=Depends(require_super_admin)):
    settings = await referral_repository.get_settings()
    # Pydantic response_model will handle the mapping
    return settings


@router.put("/settings", response_model=ReferralSettingsResponse)
async def update_referral_settings(settings: ReferralSettingsResponse, admin=Depends(require_super_admin)):
    # Convert Pydantic model to dict for storage
    update_data = {"retail": settings.retail, "business": settings.business}
    updated = await referral_repository.update_settings(update_data)
    return updated


@router.get("/check-eligibility", response_model=ReferralEligibilityResponse)
async def check_referral_eligibility(current_user: User = Depends(get_current_user)):
    try:
        from app.repositories.order_repository import order_repository

        # 1. Must be retail customer (customer role)
        role = current_user.effective_role or (current_user.role if current_user.role is not None else "customer")
        if role != "customer":
            return {"eligible": False, "message": "Referral discount is only available for retail customers"}

        # 2. Must be first order (0 orders)
        user_id = current_user.id
        order_count = await order_repository.countByUser(user_id)
        if order_count > 0:
            return {"eligible": False, "message": "Referral discount is only available on your first order"}

        # 3. Referral scheme must be active globally for retail
        settings = await referral_repository.get_settings()
        retail_settings = (settings.retail or {})
        if not (retail_settings.is_active if retail_settings.is_active is not None else False) or (retail_settings.discount_value if retail_settings.discount_value is not None else 0) <= 0:
            return {"eligible": False, "message": "Referral program is not active at the moment"}

        return {
            "eligible": True,
            "discountType": retail_settings.discount_type,
            "discountValue": retail_settings.discount_value,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error checking referral eligibility for user %s: %s", getattr(current_user, 'id', '?'), str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while checking referral eligibility")


@router.post("/verify", response_model=ReferralVerifyResponse)
async def verify_referral_code(payload: ReferralVerifyRequest, current_user: User = Depends(get_current_user)):
    code = payload.code.strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="Referral code is required")

    # Check eligibility first
    eligibility = await check_referral_eligibility(current_user)
    if not eligibility["eligible"]:
        raise HTTPException(status_code=400, detail=eligibility["message"])

    # Find referrer in user repository
    from app.repositories.user_repository import user_repository

    referrer = await user_repository.findOne({"referralCode": code})
    if not referrer:
        raise HTTPException(status_code=400, detail="Invalid referral code")

    # Cannot refer self
    referrer_id = str(referrer.id)
    if referrer_id == str(current_user.id):
        raise HTTPException(status_code=400, detail="You cannot use your own referral code")

    # Return details
    settings = await referral_repository.get_settings()
    retail_settings = (settings.retail or {})

    referrer_name = referrer.name or "Another user"
    

    return {
        "valid": True,
        "discountType": retail_settings.discount_type,
        "discountValue": retail_settings.discount_value,
        "referrerName": referrer_name,
    }


@router.get("/scheme", response_model=ReferralPublicSchemeResponse)
async def get_public_scheme(current_user: User = Depends(get_current_user)):
    settings = await referral_repository.get_settings()
    retail_settings = (settings.retail or {})
    return {
        "isActive": (retail_settings.is_active if retail_settings.is_active is not None else False),
        "discountType": (retail_settings.discount_type if retail_settings.discount_type is not None else "percentage"),
        "discountValue": (retail_settings.discount_value if retail_settings.discount_value is not None else 0.0),
    }
