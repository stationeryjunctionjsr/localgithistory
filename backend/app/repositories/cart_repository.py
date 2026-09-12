from typing import Dict, Any
from app.models.daos import CartInternalCreate, CartInternalUpdate, CartItemInternal

from app.db.storage_factory import get_storage


class CartRepository:
    def __init__(self):
        self.storage = get_storage("carts")

    async def findByUser(self, user_id: str):
        return await self.storage.findOne({"user": user_id})

    async def create(self, cart_data: Any):
        cart = CartInternalCreate(user=cart_data["user"], items=cart_data.get("items", []))
        return await self.storage.create(cart)

    async def update(self, id: str, update_data: Any):
        if not isinstance(update_data, CartInternalUpdate):
            update_data = CartInternalUpdate(**update_data)
        return await self.storage.update(id, update_data)

    async def clearCart(self, user_id: str):
        cart = await self.findByUser(user_id)
        if cart:
            return await self.update(cart.get("_id"), {"items": []})
        return None

    async def createOrUpdate(self, user_id: str, items: list):
        existing = await self.findByUser(user_id)
        cart_data = {"user": user_id, "items": items or []}
        if existing:
            return await self.update(existing.get("_id"), cart_data)
        else:
            return await self.create(cart_data)

    async def addItem(self, user_id: str, item: dict):
        cart = await self.findByUser(user_id)
        if not cart:
            return await self.createOrUpdate(user_id, [item])

        items = cart.get("items", [])
        # Check for existing item with same product, variants, and sellAsCase
        existing_item_index = next(
            (
                i
                for i, it in enumerate(items)
                if getattr(it, "product", None) == getattr(item, "product", None)
                and getattr(it, "variantAttributes", None) == getattr(item, "variantAttributes", None)
                and getattr(it, "sellAsCase", None) == getattr(item, "sellAsCase", None)
            ),
            None,
        )

        if existing_item_index is not None:
            items[existing_item_index]["quantity"] += getattr(item, 'quantity', 0)
            items[existing_item_index]["price"] = getattr(item, "price", None)
        else:
            items.append(item)

        return await self.createOrUpdate(user_id, items)

    async def removeItem(self, user_id: str, item_id: str):
        cart = await self.findByUser(user_id)
        if not cart:
            raise ValueError("Cart not found")

        items = cart.get("items", [])
        items = [item for item in items if getattr(item, "_id", None) != item_id]
        return await self.createOrUpdate(user_id, items)

    async def saveForLater(self, user_id: str, product_id: str):
        """Save item for later"""
        saved_storage = get_storage("savedForLater")
        existing = await saved_storage.findOne({"user": user_id})

        saved_item = {"user": user_id, "productId": product_id, "savedAt": datetime.now(timezone.utc).isoformat()}

        if existing:
            # Check if already saved
            items = existing.get("items", [])
            already_saved = any(getattr(item, "productId", None) == product_id for item in items)
            if already_saved:
                return existing
            items.append(saved_item)
            return await saved_storage.update(existing.get("_id"), {"items": items})
        else:
            return await saved_storage.create({"user": user_id, "items": [saved_item]})

    async def getSavedForLater(self, user_id: str):
        """Get saved for later items"""
        saved_storage = get_storage("savedForLater")
        return await saved_storage.findOne({"user": user_id}) or {"items": []}


from datetime import datetime, timezone

cart_repository = CartRepository()
