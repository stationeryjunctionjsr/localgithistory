import uuid
from datetime import datetime, timezone

from app.db.storage_factory import get_storage


class WishlistRepository:
    def __init__(self):
        self.storage = get_storage("wishlists")

    async def findByUser(self, user_id: str):
        return await self.storage.findOne({"user": user_id})

    async def createOrUpdate(self, user_id: str, items: list):
        from app.models.daos import WishlistInternalCreate, WishlistInternalUpdate
        existing = await self.findByUser(user_id)
        if existing:
            wishlist_data = WishlistInternalUpdate(user=user_id, items=items or [], updatedAt=datetime.now(timezone.utc).isoformat())
            return await self.storage.update(existing.id, wishlist_data)
        else:
            wishlist_data = WishlistInternalCreate(user=user_id, items=items or [], updatedAt=datetime.now(timezone.utc).isoformat())
            return await self.storage.create(wishlist_data)

    async def addItem(self, user_id: str, item: dict):
        wishlist = await self.findByUser(user_id)

        normalized = {
            "_id": item._id or str(uuid.uuid4()),
            "product": item.product,
            "quantity": (item.quantity if item.quantity is not None else 1),
            "addedAt": item.addedAt or datetime.now(timezone.utc).isoformat(),
        }

        if not wishlist:
            return await self.createOrUpdate(user_id, [normalized])

        # No duplicates per product
        items = (wishlist.items if wishlist.items is not None else [])
        exists = any(i.product == normalized["product"] for i in items)
        if exists:
            return wishlist

        items.append(normalized)
        return await self.createOrUpdate(user_id, items)

    async def removeItem(self, user_id: str, product_id: str):
        wishlist = await self.findByUser(user_id)
        if not wishlist:
            return False

        items = (wishlist.items if wishlist.items is not None else [])
        items = [item for item in items if item.product != product_id]
        await self.createOrUpdate(user_id, items)
        return True

    async def clear(self, user_id: str):
        return await self.createOrUpdate(user_id, [])


wishlist_repository = WishlistRepository()
