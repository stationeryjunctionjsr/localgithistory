from app.models.saved_for_later import SavedForLater, SavedForLaterItem
from typing import Dict, Any
from app.models.daos import CartInternalCreate, CartInternalUpdate, CartItemInternal

from app.db.storage_factory import get_storage


class CartRepository:
    def __init__(self):
        self.storage = get_storage("carts")

    async def findByUser(self, user_id: str):
        return await self.storage.findOne({"user": user_id})

    async def create(self, cart_data: Any):
        if not isinstance(cart_data, CartInternalCreate):
            cart = CartInternalCreate(user=cart_data.user, items=(cart_data.items if cart_data.items is not None else []))
        else:
            cart = cart_data
        return await self.storage.create(cart)

    async def update(self, id: str, update_data: Any):
        if not isinstance(update_data, CartInternalUpdate):
            update_data = CartInternalUpdate.model_validate(update_data)
        return await self.storage.update(id, update_data)

    async def clearCart(self, user_id: str):
        cart = await self.findByUser(user_id)
        if cart:
            return await self.update(cart.id, CartInternalUpdate(items=[]))
        return None

    async def createOrUpdate(self, user_id: str, items: list):
        existing = await self.findByUser(user_id)
        cart_data = CartInternalUpdate(user=user_id, items=items or [])
        if existing:
            return await self.update(existing.id, cart_data)
        else:
            create_data = CartInternalCreate(user=user_id, items=items or [])
            return await self.create(create_data)

    async def addItem(self, user_id: str, item: Any):
        cart = await self.findByUser(user_id)
        if not cart:
            return await self.createOrUpdate(user_id, [item])

        items = (cart.items if cart.items is not None else [])
        # Check for existing item with same product, variants, and sellAsCase
        existing_item_index = next(
            (
                i
                for i, it in enumerate(items)
                if it.product == item.product
                and it.variant_attributes == item.variant_attributes
                and it.sellAsCase == item.sellAsCase
            ),
            None,
        )

        if existing_item_index is not None:
            old = items[existing_item_index]
            items[existing_item_index] = CartItemInternal(
                product=old.product,
                quantity=(old.quantity if old.quantity is not None else 0) + (item.quantity if item.quantity is not None else 0),
                price=item.price,
                sellAsCase=old.sellAsCase,
                bundleId=old.bundleId,
                bundleName=old.bundleName,
                variantAttributes=old.variant_attributes,
            )
        else:
            items.append(item)

        return await self.createOrUpdate(user_id, items)

    async def removeItem(self, user_id: str, item_id: str):
        cart = await self.findByUser(user_id)
        if not cart:
            raise ValueError("Cart not found")

        items = (cart.items if cart.items is not None else [])
        items = [item for item in items if item._id != item_id]
        return await self.createOrUpdate(user_id, items)

    async def saveForLater(self, user_id: str, product_id: str):
        """Save item for later"""
        saved_storage = get_storage("savedForLater")
        existing = await saved_storage.findOne({"user": user_id})

        saved_item = SavedForLaterItem(user=user_id, productId=product_id, savedAt=datetime.now(timezone.utc).isoformat())

        if existing:
            # Check if already saved
            items = (existing.items if existing.items is not None else [])
            already_saved = any(item.product_id == product_id for item in items)
            if already_saved:
                return existing
            items.append(saved_item)
            return await saved_storage.update(existing.id, SavedForLater(user=user_id, items=items))
        else:
            return await saved_storage.create(SavedForLater(user=user_id, items=[saved_item]))

    async def getSavedForLater(self, user_id: str):
        """Get saved for later items"""
        saved_storage = get_storage("savedForLater")
        return await saved_storage.findOne({"user": user_id}) or SavedForLater(user=user_id, items=[])


from datetime import datetime, timezone

cart_repository = CartRepository()
