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

    # Filter for wholesaler
    business_coupons = [c for c in coupons if "wholesaler" in (c.get("applicableRoles") or [])]

    # Sort by createdAt descending
    business_coupons.sort(key=lambda x: x.get("createdAt", ""), reverse=True)

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
    business_coupons = [c for c in coupons if "wholesaler" in (c.get("applicableRoles") or [])]

    applicable_offers = []
    for c in business_coupons:
        # Check if product is eligible
        applies_to_type = c.get("appliesToType") or "all"
        applies_to_ids = c.get("appliesToValueIds") or []
        is_eligible = await coupon_repository._product_eligible_async(
            product, applies_to_type, applies_to_ids, c.get("excludedProductIds")
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
