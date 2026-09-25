from app.models.daos import CartItemInternal
from app.models.user import User
from app.models.schemas import CartResponse, SavedForLaterResponse, MessageResponse
from app.models.daos import WishlistItemInternal
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.repositories.cart_repository import cart_repository
from app.repositories.product_repository import product_repository
from app.utils.auth import get_current_user
from app.utils.logger import logger

router = APIRouter()


class CartItemRequest(BaseModel):
    productId: str
    quantity: int  # Always in units (for cases: quantity = cases * quantityPerCase)
    sellAsCase: bool = False  # Business only: price by case (MRP per case)
    sessionId: Optional[str] = None
    variantAttributes: Optional[Dict[str, str]] = None


class SaveForLaterRequest(BaseModel):
    productId: str


class CartItemUpdateRequest(BaseModel):
    quantity: int


@router.get("", response_model=CartResponse)
@router.get("/", response_model=CartResponse)
async def get_cart(current_user: User = Depends(get_current_user)):
    """Get user's cart"""
    try:
        from app.repositories.coupon_repository import coupon_repository

        await coupon_repository.get_active_automatic_product_discounts()

        cart = await cart_repository.findByUser(current_user.id)
        if not cart:
            cart = await cart_repository.createOrUpdate(current_user.id, [])

        # Populate products and adjust pricing
        role = current_user.effective_role or (current_user.role if current_user.role is not None else "customer")
        user_id = current_user.id

        # Bulk load products
        product_ids = [item.product for item in cart.items if item.product]
        products_map = {}
        if product_ids:
            products = await product_repository.findAll({"allowed_ids": product_ids})
            products_map = {str(p.id): p for p in products}

        cart_items = []
        for item in cart.items:
            product = (products_map[str(item.product)] if str(item.product) in products_map else None)
            if not product:
                continue
            quantity = item.quantity
            sell_as_case = item.sell_as_case
            subtotal = product_repository.calculateTotalPrice(
                product, role, quantity, sell_as_case=sell_as_case, user_id=user_id
            )
            if subtotal is None:
                raise ValueError(f"Data Integrity Error: Subtotal calculation failed for product {product.id}")
            price = (subtotal / quantity) if quantity else 0  # effective price per unit for display

            from app.repositories.stock_reservation_repository import stock_reservation_repository

            reserved = await stock_reservation_repository.get_reserved_quantity(
                product.id, exclude_user_id=current_user.id
            )
            if product.stock is None:
                raise ValueError(f"Data Integrity Error: Product {product.id} is missing stock information")
            available_stock = max(0, int(product.stock) - reserved)
            is_out_of_stock = quantity > available_stock

            cart_items.append(
                {
                    "_id": item.id,
                    "productId": product.id,
                    "name": product.name,
                    "sku": product.sku,
                    "images": product.images,
                    "mrp": product.mrp,
                    "mrpPerCase": product.mrp_per_case,
                    "quantityPerCase": product.quantity_per_case,
                    "quantity": quantity,
                    "sellAsCase": sell_as_case,
                    "price": price,
                    "subtotal": subtotal,
                    "outOfStock": is_out_of_stock,
                    "bundleId": item.bundle_id,
                    "bundleName": item.bundle_name,
                    "variantAttributes": item.variant_attributes,
                }
            )

        subtotal = sum(item.subtotal for item in cart_items)

        # Get earliest expiry for active reservations to display countdown timer in frontend
        from app.repositories.stock_reservation_repository import stock_reservation_repository

        active_reservations = await stock_reservation_repository.get_user_reservations(current_user.id)
        earliest_expiry = None
        if active_reservations:
            expiry_times = [r.expires_at for r in active_reservations if r.expires_at]
            if expiry_times:
                earliest_expiry = min(expiry_times)

        return {"items": cart_items, "subtotal": subtotal, "itemCount": len(cart_items), "expiresAt": earliest_expiry}
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.post("", response_model=MessageResponse)
@router.post("/", response_model=MessageResponse)
async def add_to_cart(item: CartItemRequest, current_user: User = Depends(get_current_user)):
    """Add item to cart"""
    try:
        product = await product_repository.findById(item.product_id)
        if not product or not product.is_active:
            raise HTTPException(status_code=404, detail="Product not found")

        role = current_user.effective_role or (current_user.role if current_user.role is not None else "customer")

        # Get existing cart to calculate final quantity
        cart = await cart_repository.findByUser(current_user.id)
        existing_total_qty = 0
        if cart:
            existing_total_qty = sum(
                (i.quantity if i.quantity is not None else 0) for i in (cart.items or []) if i.product == item.product_id
            )

        final_qty = existing_total_qty + item.quantity

        from app.repositories.stock_reservation_repository import stock_reservation_repository

        ttl_minutes = 30 if role == "wholesaler" else 10
        try:
            await stock_reservation_repository.reserve_stock_checked(
                product_id=item.product_id, user_id=current_user.id, quantity=final_qty, ttl_minutes=ttl_minutes
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        sell_as_case = (item.sell_as_case if item.sell_as_case is not None else False)

        # Business ordering by case: quantity must be multiple of quantityPerCase
        if sell_as_case and role == "wholesaler":
            qty_per_case = product.quantity_per_case or 0
            if not qty_per_case or product.mrp_per_case is None:
                raise HTTPException(status_code=400, detail="Product does not support case pricing")
            if item.quantity % qty_per_case != 0:
                raise HTTPException(
                    status_code=400, detail=f"Quantity must be a multiple of {qty_per_case} (quantity per case)"
                )
        elif sell_as_case and role == "customer":
            sell_as_case = False  # Retail: ignore sellAsCase

        import uuid

        from app.models.daos import CartItemInternal
        new_item = CartItemInternal(
            id_=str(uuid.uuid4()),
            product=item.product_id,
            quantity=item.quantity,
            sellAsCase=sell_as_case,
            variantAttributes=item.variant_attributes,
        )

        if cart:
            existing_item = next(
                (
                    i
                    for i in (cart.items or [])
                    if i.product == item.product_id
                    and i.sell_as_case == sell_as_case
                    and i.variant_attributes == item.variant_attributes
                ),
                None,
            )
            if existing_item:
                new_quantity = (existing_item.quantity if existing_item.quantity is not None else 0) + item.quantity
                items = (cart.items or [])
                for i, it in enumerate(items):
                    if it.id == existing_item.id:
                        items[i] = CartItemInternal(
                            product=it.product,
                            quantity=new_quantity,
                            price=it.price,
                            sellAsCase=it.sell_as_case,
                            bundleId=it.bundle_id,
                            bundleName=it.bundle_name,
                            variantAttributes=it.variant_attributes,
                        )
                        break
                await cart_repository.createOrUpdate(current_user.id, items)
            else:
                await cart_repository.addItem(current_user.id, new_item)
        else:
            await cart_repository.addItem(current_user.id, new_item)

        # Automatically remove from wishlist
        from app.repositories.wishlist_repository import wishlist_repository

        await wishlist_repository.removeItem(current_user.id, item.product_id)

        # Track the addition
        from app.repositories.tracking_repository import tracking_repository

        await tracking_repository.trackCartAdd(
            current_user.id, item.product_id, item.quantity, item.session_id
        )

        return {"message": "Item added to cart"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.put("/{item_id}", response_model=MessageResponse)
async def update_cart_item(
    item_id: str, update_data: CartItemUpdateRequest, current_user: User = Depends(get_current_user)
):
    """Update cart item quantity - allows decreasing below minimum (price adjusts automatically)"""
    try:
        cart = await cart_repository.findByUser(current_user.id)
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")

        item = next((i for i in (cart.items or []) if i.id == item_id), None)
        if not item:
            raise HTTPException(status_code=404, detail="Cart item not found")

        quantity = update_data.quantity

        # Validate quantity is at least 1
        if quantity < 1:
            raise HTTPException(status_code=400, detail="Quantity must be at least 1")

        product = await product_repository.findById(item.product)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        role = current_user.effective_role or (current_user.role if current_user.role is not None else "customer")
        sell_as_case = (item.sell_as_case if item.sell_as_case is not None else False)
        if sell_as_case and role == "wholesaler":
            qty_per_case = product.quantity_per_case or 0
            if qty_per_case and quantity % qty_per_case != 0:
                raise HTTPException(
                    status_code=400, detail=f"Quantity must be a multiple of {qty_per_case} (quantity per case)"
                )

        # Calculate final_qty BEFORE updating cart
        items = (cart.items or [])
        final_qty = 0
        for it in items:
            if it.id == item_id:
                final_qty += quantity
            elif it.product == item.product:
                final_qty += (it.quantity if it.quantity is not None else 0)

        from app.repositories.stock_reservation_repository import stock_reservation_repository
        ttl_minutes = 30 if role == "wholesaler" else 10
        
        try:
            await stock_reservation_repository.reserve_stock_checked(
                product_id=item.product, user_id=current_user.id, quantity=final_qty, ttl_minutes=ttl_minutes
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Apply update
        for i, it in enumerate(items):
            if it.id == item_id:
                items[i] = CartItemInternal(
                    product=it.product,
                    quantity=quantity,
                    price=it.price,
                    sellAsCase=it.sell_as_case,
                    bundleId=it.bundle_id,
                    bundleName=it.bundle_name,
                    variantAttributes=it.variant_attributes,
                )
                break

        await cart_repository.createOrUpdate(current_user.id, items)

        return {"message": "Cart updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.delete("/{item_id}", response_model=MessageResponse)
async def remove_cart_item(item_id: str, current_user: User = Depends(get_current_user)):
    """Remove item from cart"""
    try:
        cart = await cart_repository.findByUser(current_user.id)
        if cart:
            item = next((i for i in (cart.items or []) if i.id == item_id), None)
            if item:
                product_id = item.product
                await cart_repository.removeItem(current_user.id, item_id)

                # Recalculate remaining qty of this product in cart (if any, e.g. other variants)
                updated_cart = await cart_repository.findByUser(current_user.id)
                final_qty = sum(
                    (i.quantity if i.quantity is not None else 0) for i in (updated_cart.items or []) if i.product == product_id
                )
                from app.repositories.stock_reservation_repository import stock_reservation_repository

                if final_qty > 0:
                    role = current_user.effective_role or (current_user.role if current_user.role is not None else "customer")
                    ttl_minutes = 30 if role == "wholesaler" else 10
                    await stock_reservation_repository.reserve_stock(
                        product_id=product_id,
                        user_id=current_user.id,
                        quantity=final_qty,
                        ttl_minutes=ttl_minutes,
                    )
                else:
                    await stock_reservation_repository.release_user_reservations(
                        user_id=current_user.id, product_id=product_id
                    )
        return {"message": "Item removed from cart"}
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.delete("", response_model=MessageResponse)
@router.delete("/", response_model=MessageResponse)
async def clear_cart(current_user: User = Depends(get_current_user)):
    """Clear cart"""
    try:
        await cart_repository.clearCart(current_user.id)
        from app.repositories.stock_reservation_repository import stock_reservation_repository

        await stock_reservation_repository.release_user_reservations(current_user.id)
        return {"message": "Cart cleared"}
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.post("/save-for-later", response_model=MessageResponse)
async def save_for_later(request: SaveForLaterRequest, current_user: User = Depends(get_current_user)):
    """Save item for later"""
    try:
        from app.repositories.wishlist_repository import wishlist_repository

        await wishlist_repository.addItem(current_user.id, WishlistItemInternal(product=request.product_id))
        return {"message": "Item saved for later"}
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/saved-for-later", response_model=SavedForLaterResponse)
async def get_saved_for_later(current_user: User = Depends(get_current_user)):
    """Get saved for later items"""
    try:
        saved = await cart_repository.getSavedForLater(current_user.id)
        return saved or SavedForLaterResponse(items=[])
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")
