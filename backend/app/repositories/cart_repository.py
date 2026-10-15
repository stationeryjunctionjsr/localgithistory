from app.models.saved_for_later import SavedForLater, SavedForLaterItem
from typing import TYPE_CHECKING, Optional, List
from app.models.cart import Cart
from app.models.daos import CartInternalCreate, CartInternalUpdate, CartItemInternal

from app.db.storage_factory import get_storage


class CartRepository:
    def __init__(self) -> None:
        self.storage = get_storage("carts")

    async def findByUser(self, user_id: int) -> Optional[Cart]:
        return await self.storage.findOne(user=user_id)

    async def create(self, cart_data: 'CartInternalCreate') -> Cart:
        return await self.storage.create(cart_data)

    async def update(self, id: int, update_data: 'CartInternalUpdate') -> Optional[Cart]:
        return await self.storage.update(id, update_data)

    async def clearCart(self, user_id: int) -> Optional[Cart]:
        """Atomically clear all items from the user's cart."""
        return await self.storage.update_items_atomic(user_id, lambda _: [])

    async def createOrUpdate(self, user_id: int, items: list) -> Optional[Cart]:
        existing = await self.findByUser(user_id)
        cart_data = CartInternalUpdate(user=user_id, items=items or [])
        if existing:
            return await self.update(existing.id, cart_data)
        else:
            create_data = CartInternalCreate(user=user_id, items=items or [])
            return await self.create(create_data)

    async def addItem(self, user_id: int, item: 'CartItemInternal') -> Optional[Cart]:
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

    async def removeItem(self, user_id: int, item_id: str) -> Optional[Cart]:
        """Atomically remove a specific item from the cart.

        Uses a DB-level FOR UPDATE lock so concurrent removals cannot race.
        """
        def _merge(current_items):
            return [it for it in current_items if it.id != item_id and it.product != item_id]

        return await self.storage.update_items_atomic(user_id, _merge)

    async def saveForLater(self, user_id: int, product_id: int) -> Optional[SavedForLater]:
        """Save item for later via atomic single-row SQL."""
        saved_storage = get_storage("savedForLater")
        await saved_storage.add_item(user_id, product_id)
        return await saved_storage.findOne(user=user_id)

    async def getSavedForLater(self, user_id: int) -> SavedForLater:
        """Get saved for later items"""
        saved_storage = get_storage("savedForLater")
        return await saved_storage.findOne(user=user_id) or SavedForLater(user=user_id, items=[])


from datetime import datetime, timezone

if TYPE_CHECKING:
    from app.models.daos import CartInternalCreate, CartInternalUpdate
    

cart_repository = CartRepository()
