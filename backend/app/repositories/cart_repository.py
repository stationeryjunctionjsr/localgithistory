from app.models.saved_for_later import SavedForLater, SavedForLaterItem
from typing import TYPE_CHECKING
from app.models.daos import CartInternalCreate, CartInternalUpdate, CartItemInternal

from app.db.storage_factory import get_storage


class CartRepository:
    def __init__(self):
        self.storage = get_storage("carts")

    async def findByUser(self, user_id: str):
        return await self.storage.findOne({"user": user_id})

    async def create(self, cart_data: 'CartInternalCreate'):
        return await self.storage.create(cart_data)

    async def update(self, id: str, update_data: 'CartInternalUpdate'):
        return await self.storage.update(id, update_data)

    async def clearCart(self, user_id: str):
        """Atomically clear all items from the user's cart."""
        return await self.storage.update_items_atomic(user_id, lambda _: [])

    async def createOrUpdate(self, user_id: str, items: list):
        existing = await self.findByUser(user_id)
        cart_data = CartInternalUpdate(user=user_id, items=items or [])
        if existing:
            return await self.update(existing.id, cart_data)
        else:
            create_data = CartInternalCreate(user=user_id, items=items or [])
            return await self.create(create_data)

    async def addItem(self, user_id: str, item: 'CartItemInternal'):
        """Atomically add an item to the cart.

        Uses a DB-level FOR UPDATE lock so concurrent add requests for the
        same user cannot overwrite each other (lost-update race).
        """
        def _merge(current_items):
            items = list(current_items)
            existing_index = next(
                (
                    i
                    for i, it in enumerate(items)
                    if it.product == item.product
                    and it.variant_attributes == item.variant_attributes
                    and it.sell_as_case == item.sell_as_case
                ),
                None,
            )

            if existing_index is not None:
                old = items[existing_index]
                items[existing_index] = CartItemInternal(
                    product=old.product,
                    quantity=(old.quantity if old.quantity is not None else 0) + (item.quantity if item.quantity is not None else 0),
                    price=item.price,
                    sellAsCase=old.sell_as_case,
                    bundleId=old.bundle_id,
                    bundleName=old.bundle_name,
                    variantAttributes=old.variant_attributes,
                )
            else:
                items.append(item)

            return items

        return await self.storage.update_items_atomic(user_id, _merge)

    async def removeItem(self, user_id: str, item_id: str):
        """Atomically remove a specific item from the cart.

        Uses a DB-level FOR UPDATE lock so concurrent removals cannot race.
        """
        def _merge(current_items):
            return [it for it in current_items if it._id != item_id]

        return await self.storage.update_items_atomic(user_id, _merge)

    async def saveForLater(self, user_id: str, product_id: str):
        """Save item for later"""
        saved_storage = get_storage("savedForLater")
        existing = await saved_storage.findOne({"user": user_id})
        saved_item = SavedForLaterItem(user=user_id, product_id=product_id, saved_at=datetime.now(timezone.utc).isoformat())

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

if TYPE_CHECKING:
    from app.models.daos import CartInternalCreate, CartInternalUpdate
    

cart_repository = CartRepository()
