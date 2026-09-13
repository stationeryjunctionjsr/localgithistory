from app.models.user import User
from typing import Dict, Any, List
from app.models.schemas import MessageResponse
from app.models.product import Product
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.repositories.product_repository import product_repository
from app.repositories.wishlist_repository import wishlist_repository
from app.utils.auth import get_current_user
from app.utils.logger import logger

router = APIRouter()


class WishlistItemRequest(BaseModel):
    productId: str
    sessionId: Optional[str] = None


def get_role_for_pricing(user: dict) -> str:
    effective_role = user.effective_role or (user.role if user.role is not None else "customer")
    return effective_role


def get_min_quantity_for_role(product: dict, role: str) -> int:
    if role == "wholesaler":
        qty_per_case = product.quantity_per_case or 0
        if qty_per_case > 0:
            return qty_per_case
        return 1
    return 1


@router.get("", response_model=List[Product])
@router.get("/", response_model=List[Product])
async def get_wishlist(current_user: User = Depends(get_current_user)):
    """Get user's wishlist"""
    try:
        wishlist = await wishlist_repository.findByUser(current_user.id)
        if not wishlist or not wishlist.items:
            return {"items": [], "itemCount": 0}

        role_for_pricing = get_role_for_pricing(current_user)
        populated_items = []

        raw_items = (wishlist.items if wishlist.items is not None else [])
        norm_items = []
        for it in raw_items:
            if isinstance(it, dict):
                norm_items.append(it)
            elif isinstance(it, str):
                norm_items.append({"product": it, "quantity": 1})

        product_ids = [item.product for item in norm_items if item.product]
        products_map = {}
        if product_ids:
            products = await product_repository.findAll({"allowed_ids": product_ids})
            products_map = {str(p.id): p for p in products}

        for item in norm_items:
            product = products_map.get(str(item.product))
            if not product or product.is_active is False:
                continue

            quantity = (item.quantity if item.quantity is not None else 1)
            price = product_repository.getPriceForRole(product, role_for_pricing, quantity)

            populated_items.append(
                {
                    **item,
                    "product": {
                        "_id": product.id,
                        "name": product.name,
                        "sku": product.sku,
                        "images": (product.images or []),
                        "mrp": product.mrp,
                        "mrpPerCase": product.mrp_per_case,
                        "quantityPerCase": product.quantity_per_case,
                        "price": price,
                    },
                }
            )

        return {"items": populated_items, "itemCount": len(populated_items)}
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.post("", response_model=MessageResponse)
@router.post("/", response_model=MessageResponse)
async def add_to_wishlist(item: WishlistItemRequest, current_user: User = Depends(get_current_user)):
    """Add item to wishlist"""
    try:
        product = await product_repository.findById(item.productId)
        if not product or product.is_active is False:
            raise HTTPException(status_code=404, detail="Product not found")

        role_for_pricing = get_role_for_pricing(current_user)
        min_qty = get_min_quantity_for_role(product, role_for_pricing)

        await wishlist_repository.addItem(current_user.id, {"product": item.productId, "quantity": min_qty})

        # Track the addition
        from app.repositories.tracking_repository import tracking_repository

        await tracking_repository.trackWishlistAdd(
            current_user.id, item.productId, item.sessionId
        )

        return {"message": "Added to wishlist"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.delete("/{product_id}", response_model=MessageResponse)
async def remove_from_wishlist(product_id: str, current_user: User = Depends(get_current_user)):
    """Remove item from wishlist"""
    try:
        removed = await wishlist_repository.removeItem(current_user.id, product_id)
        if not removed:
            raise HTTPException(status_code=404, detail="Wishlist item not found")
        return {"message": "Removed from wishlist"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.delete("", response_model=MessageResponse)
@router.delete("/", response_model=MessageResponse)
async def clear_wishlist(current_user: User = Depends(get_current_user)):
    """Clear wishlist"""
    try:
        await wishlist_repository.clear(current_user.id)
        return {"message": "Wishlist cleared"}
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")
