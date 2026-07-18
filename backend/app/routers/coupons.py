from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.schemas import CouponCreate, CouponResponse, CouponUpdate, CouponValidateCart
from app.repositories.coupon_repository import coupon_repository
from app.repositories.product_repository import product_repository
from app.utils.auth import get_current_user, require_super_admin

router = APIRouter()


@router.get("", response_model=List[CouponResponse])

@router.get("/", response_model=List[CouponResponse])
async def get_coupons(isActive: Optional[bool] = None, current_user: dict = Depends(require_super_admin)):
    query = {}
    if isActive is not None:
        query["isActive"] = isActive

    coupons = await coupon_repository.findAll(query)
    return [CouponResponse(**coupon) for coupon in coupons]


@router.get("/validate/{code}")
async def validate_coupon(
    code: str,
    amount: float = Query(...),
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    user_role = current_user.get("role", "customer")
    validation = await coupon_repository.validateCoupon(
        code, user_role, amount, current_user.get("_id"), category, None
    )
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["message"])
    return {
        "valid": True,
        "coupon": {
            "code": validation["coupon"]["code"],
            "discountType": validation["coupon"]["discountType"],
            "discountValue": validation["coupon"]["discountValue"],
        },
        "discount": validation["discount"],
    }


@router.post("/validate")
async def validate_coupon_with_cart(body: CouponValidateCart, current_user: dict = Depends(get_current_user)):
    """Validate discount using cart items; eligible subtotal is computed from items matching Applies to."""
    user_role = current_user.get("role", "customer")
    cart_items = [
        {
            "product": it.get("productId"),
            "productId": it.get("productId"),
            "quantity": it.get("quantity", 0),
            "sellAsCase": it.get("sellAsCase", False),
        }
        for it in (body.items or [])
    ]
    validation = await coupon_repository.validateCoupon(
        body.code,
        user_role,
        0.0,
        current_user.get("_id"),
        None,
        None,
        cart_items=cart_items,
        product_repository=product_repository,
        shipping_address=body.shippingAddress,
    )
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["message"])
    return {
        "valid": True,
        "coupon": {
            "code": validation["coupon"]["code"],
            "discountType": validation["coupon"]["discountType"],
            "discountValue": validation["coupon"]["discountValue"],
        },
        "discount": validation["discount"],
    }


@router.get("/{coupon_id}", response_model=CouponResponse)
async def get_coupon(coupon_id: str, current_user: dict = Depends(require_super_admin)):
    coupon = await coupon_repository.findById(coupon_id)
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return CouponResponse(**coupon)


@router.post("", response_model=CouponResponse, status_code=status.HTTP_201_CREATED)

@router.post("/", response_model=CouponResponse, status_code=status.HTTP_201_CREATED)
async def create_coupon(
    coupon_data: CouponCreate,
    resolution: Optional[str] = Query(None),
    force: bool = Query(False),
    current_user: dict = Depends(require_super_admin),
):
    try:
        data = coupon_data.dict()
        data["resolution"] = resolution
        data["force"] = force
        coupon = await coupon_repository.create(data)
        return CouponResponse(**coupon)
    except ValueError as e:
        from app.repositories.coupon_repository import OverlapConflictError

        if isinstance(e, OverlapConflictError):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail={"message": str(e), "overlap": e.overlap_data}
            )
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{coupon_id}", response_model=CouponResponse)
async def update_coupon(
    coupon_id: str,
    coupon_data: CouponUpdate,
    resolution: Optional[str] = Query(None),
    force: bool = Query(False),
    current_user: dict = Depends(require_super_admin),
):
    try:
        data = coupon_data.dict(exclude_unset=True)
        data["resolution"] = resolution
        data["force"] = force
        coupon = await coupon_repository.update(coupon_id, data)
        if not coupon:
            raise HTTPException(status_code=404, detail="Coupon not found")
        return CouponResponse(**coupon)
    except ValueError as e:
        from app.repositories.coupon_repository import OverlapConflictError

        if isinstance(e, OverlapConflictError):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail={"message": str(e), "overlap": e.overlap_data}
            )
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{coupon_id}")
async def delete_coupon(coupon_id: str, current_user: dict = Depends(require_super_admin)):
    result = await coupon_repository.delete(coupon_id)
    if not result:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return {"message": "Coupon deleted successfully"}
