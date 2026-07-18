import uuid
from datetime import datetime

from app.db.storage_factory import get_storage


class WishlistRepository:
    def __init__(self):
        self.storage = get_storage("wishlists")

    async def findByUser(self, user_id: str):
        return await self.storage.findOne({"user": user_id})

    async def createOrUpdate(self, user_id: str, items: list):
        existing = await self.findByUser(user_id)
        wishlist_data = {"user": user_id, "items": items or [], "updatedAt": datetime.utcnow().isoformat()}
        if existing:
            return await self.storage.update(existing.get("_id"), wishlist_data)
        else:
            return await self.storage.create(wishlist_data)

    async def addItem(self, user_id: str, item: dict):
        wishlist = await self.findByUser(user_id)

        normalized = {
            "_id": item.get("_id") or str(uuid.uuid4()),
            "product": item.get("product"),
            "quantity": item.get("quantity", 1),
            "addedAt": item.get("addedAt") or datetime.utcnow().isoformat(),
        }

        if not wishlist:
            return await self.createOrUpdate(user_id, [normalized])

        # No duplicates per product
        items = wishlist.get("items", [])
        exists = any(i.get("product") == normalized["product"] for i in items)
        if exists:
            return wishlist

        items.append(normalized)
        return await self.createOrUpdate(user_id, items)

    async def removeItem(self, user_id: str, product_id: str):
        wishlist = await self.findByUser(user_id)
        if not wishlist:
            return False

        items = wishlist.get("items", [])
        items = [item for item in items if item.get("product") != product_id]
        await self.createOrUpdate(user_id, items)
        return True

    async def clear(self, user_id: str):
        return await self.createOrUpdate(user_id, [])


wishlist_repository = WishlistRepository()
