from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import CouponResponse
from app.repositories.coupon_repository import coupon_repository
from app.utils.auth import check_roles, get_current_user

router = APIRouter()


def require_wholesaler(current_user: dict = Depends(get_current_user)):
    """Only Business Segment (wholesaler) users can access schemes."""
    return check_roles(current_user, "wholesaler")


@router.get("", response_model=List[CouponResponse])
@router.get("/", response_model=List[CouponResponse])
async def get_schemes(current_user: dict = Depends(require_wholesaler)):
    """
    List all active discount schemes for the Business Segment (wholesaler).
    These are essentially coupons where applicableRoles includes 'wholesaler'.
    Returns them sorted by creation date descending.
    """
    coupons = await coupon_repository.findAll({"isActive": True})

    # Filter for wholesaler and expiration
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    business_coupons = []
    
    for c in coupons:
        if "wholesaler" not in (c.applicable_roles or []):
            continue
        valid_until = c.valid_until
        if valid_until:
            try:
                end_dt = datetime.fromisoformat(valid_until.replace("Z", "+00:00")).replace(tzinfo=timezone.utc)
                if now > end_dt:
                    continue
            except Exception:
                pass
        business_coupons.append(c)

    # Sort by createdAt descending
    business_coupons.sort(key=lambda x: (x.created_at or ""), reverse=True)

    # We will return the full coupon objects so the frontend has all fields it needs
    # to display "Buy X Get Y" and "Amount off products" details.
    out = []
    for c in business_coupons:
        # We need to map _id to id if returning as dict, or just return as CouponResponse
        out.append(CouponResponse(**c))
    return out


@router.get("/applicable/{product_id}", response_model=List[dict])
async def get_applicable_schemes(product_id: str, current_user: dict = Depends(require_wholesaler)):
    """
    Get all active schemes applicable to a given product.
    Calculates the final effective unit price for each.
    """
    from app.repositories.product_repository import product_repository

    product = await product_repository.findById(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    coupons = await coupon_repository.findAll({"isActive": True})
    
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    business_coupons = []
    
    for c in coupons:
        if "wholesaler" not in (c.applicable_roles or []):
            continue
        valid_until = c.valid_until
        if valid_until:
            try:
                end_dt = datetime.fromisoformat(valid_until.replace("Z", "+00:00")).replace(tzinfo=timezone.utc)
                if now > end_dt:
                    continue
            except Exception:
                pass
        business_coupons.append(c)

    applicable_offers = []
    for c in business_coupons:
        # Check if product is eligible
        applies_to_type = c.applies_to_type or "all"
        applies_to_ids = c.applies_to_value_ids or []
        is_eligible = await coupon_repository._product_eligible_async(
            product, applies_to_type, applies_to_ids, c.excluded_product_ids
        )

        if is_eligible:
            applicable_offers.append(c)

    # Return raw dicts for frontend flexibility. Exclude internal DB specific logic if needed,
    # but returning CouponResponse data format is fine.

    out = []
    for c in applicable_offers:
        cr = CouponResponse(**c).model_dump(by_alias=True)
        out.append(cr)

    return out


@router.get("/applicable/bundle/{bundle_id}", response_model=List[dict])
async def get_applicable_bundle_schemes(bundle_id: str, current_user: dict = Depends(require_wholesaler)):
    """
    Get all active schemes applicable to a given bundle.
    """
    from app.repositories.bundle_repository import bundle_repository

    bundle = await bundle_repository.findById(bundle_id)
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")

    coupons = await coupon_repository.findAll({"isActive": True})
    
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    business_coupons = []
    
    for c in coupons:
        if "wholesaler" not in (c.applicable_roles or []):
            continue
        valid_until = c.valid_until
        if valid_until:
            try:
                end_dt = datetime.fromisoformat(valid_until.replace("Z", "+00:00")).replace(tzinfo=timezone.utc)
                if now > end_dt:
                    continue
            except Exception:
                pass
        business_coupons.append(c)

    applicable_offers = []
    for c in business_coupons:
        applies_to_type = c.applies_to_type or "all"
        applies_to_ids = c.applies_to_value_ids or []
        is_eligible = await coupon_repository._bundle_eligible_async(
            bundle, applies_to_type, applies_to_ids, c.excluded_product_ids
        )

        if is_eligible:
            applicable_offers.append(c)

    out = []
    for c in applicable_offers:
        cr = CouponResponse(**c).model_dump(by_alias=True)
        out.append(cr)

    return out
