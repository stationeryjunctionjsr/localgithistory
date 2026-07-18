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
    effective_role = user.get("effectiveRole") or user.get("role", "customer")
    return effective_role


def get_min_quantity_for_role(product: dict, role: str) -> int:
    if role == "wholesaler":
        qty_per_case = product.get("quantityPerCase") or 0
        if qty_per_case > 0:
            return qty_per_case
        return 1
    return 1


@router.get("")
@router.get("/")
async def get_wishlist(current_user: dict = Depends(get_current_user)):
    """Get user's wishlist"""
    try:
        wishlist = await wishlist_repository.findByUser(current_user.get("_id"))
        if not wishlist or not wishlist.get("items"):
            return {"items": [], "itemCount": 0}

        role_for_pricing = get_role_for_pricing(current_user)
        populated_items = []

        product_ids = [item.get("product") for item in wishlist.get("items", []) if item.get("product")]
        products_map = {}
        if product_ids:
            products = await product_repository.findAll({"allowed_ids": product_ids})
            products_map = {str(p["_id"]): p for p in products}

        for item in wishlist.get("items", []):
            product = products_map.get(str(item.get("product")))
            if not product or product.get("isActive") is False:
                continue

            quantity = item.get("quantity", 1)
            price = product_repository.getPriceForRole(product, role_for_pricing, quantity)

            populated_items.append(
                {
                    **item,
                    "product": {
                        "_id": product.get("_id"),
                        "name": product.get("name"),
                        "sku": product.get("sku"),
                        "images": product.get("images", []),
                        "mrp": product.get("mrp"),
                        "mrpPerCase": product.get("mrpPerCase"),
                        "quantityPerCase": product.get("quantityPerCase"),
                        "price": price,
                    },
                }
            )

        return {"items": populated_items, "itemCount": len(populated_items)}
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.post("")
@router.post("/")
async def add_to_wishlist(item: WishlistItemRequest, current_user: dict = Depends(get_current_user)):
    """Add item to wishlist"""
    try:
        product = await product_repository.findById(item.productId)
        if not product or product.get("isActive") is False:
            raise HTTPException(status_code=404, detail="Product not found")

        role_for_pricing = get_role_for_pricing(current_user)
        min_qty = get_min_quantity_for_role(product, role_for_pricing)

        await wishlist_repository.addItem(current_user.get("_id"), {"product": item.productId, "quantity": min_qty})

        # Track the addition
        from app.repositories.tracking_repository import tracking_repository

        await tracking_repository.trackWishlistAdd(
            current_user.get("_id"), item.productId, getattr(item, "sessionId", None)
        )

        return {"message": "Added to wishlist"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.delete("/{product_id}")
async def remove_from_wishlist(product_id: str, current_user: dict = Depends(get_current_user)):
    """Remove item from wishlist"""
    try:
        removed = await wishlist_repository.removeItem(current_user.get("_id"), product_id)
        if not removed:
            raise HTTPException(status_code=404, detail="Wishlist item not found")
        return {"message": "Removed from wishlist"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.delete("")
@router.delete("/")
async def clear_wishlist(current_user: dict = Depends(get_current_user)):
    """Clear wishlist"""
    try:
        await wishlist_repository.clear(current_user.get("_id"))
        return {"message": "Wishlist cleared"}
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")
