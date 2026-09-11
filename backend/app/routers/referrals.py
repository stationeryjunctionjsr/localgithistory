from fastapi import APIRouter, Depends, HTTPException
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
    update_data = {"retail": settings.retail.dict(), "business": settings.business.dict()}
    updated = await referral_repository.update_settings(update_data)
    return updated


@router.get("/check-eligibility", response_model=ReferralEligibilityResponse)
async def check_referral_eligibility(current_user: dict = Depends(get_current_user)):
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
        retail_settings = settings.get("retail", {})
        if not retail_settings.get("isActive", False) or retail_settings.get("discountValue", 0) <= 0:
            return {"eligible": False, "message": "Referral program is not active at the moment"}

        return {
            "eligible": True,
            "discountType": retail_settings.get("discountType"),
            "discountValue": retail_settings.get("discountValue"),
        }
    except Exception as e:
        from app.utils.logger import logger

        logger.error(f"Error checking referral eligibility: {e}", exc_info=True)
        return {"eligible": False, "message": "An error occurred while checking eligibility"}


@router.post("/verify", response_model=ReferralVerifyResponse)
async def verify_referral_code(payload: ReferralVerifyRequest, current_user: dict = Depends(get_current_user)):
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
    if str(referrer.get("_id")) == str(current_user.id):
        raise HTTPException(status_code=400, detail="You cannot use your own referral code")

    # Return details
    settings = await referral_repository.get_settings()
    retail_settings = settings.get("retail", {})

    return {
        "valid": True,
        "discountType": retail_settings.get("discountType"),
        "discountValue": retail_settings.get("discountValue"),
        "referrerName": referrer.get("name", "Another user"),
    }


@router.get("/scheme", response_model=ReferralPublicSchemeResponse)
async def get_public_scheme(current_user: dict = Depends(get_current_user)):
    settings = await referral_repository.get_settings()
    retail_settings = settings.get("retail", {})
    return {
        "isActive": retail_settings.get("isActive", False),
        "discountType": retail_settings.get("discountType", "percentage"),
        "discountValue": retail_settings.get("discountValue", 0.0),
    }
