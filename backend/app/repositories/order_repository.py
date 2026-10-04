import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from app.models.order import Order, OrderInternalCreate, OrderInternalUpdate

from app.db.storage_factory import get_storage
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.models.daos import OrderInternalCreate, OrderInternalUpdate
    


class OrderRepository:
    def __init__(self):
        self.storage = get_storage("orders")

    async def generateOrderNumber(self, user_role: str) -> str:
        # Determine prefix based on user role
        prefix = "ORDER-RT-"  # Retail customer orders
        if user_role == "wholesaler":
            prefix = "ORDER-WH-"  # Business (wholesaler) orders

        # Depends on storage layer implementing `get_max_order_number_suffix`
        # MySQL DAO already implements this efficiently.
        max_id = await self.storage.get_max_order_number_suffix(prefix)

        next_id = max(1, max_id + 1)  # ORDER-RT-1, ORDER-WH-1, etc. (never 0)
        return f"{prefix}{next_id}"

    async def findAll(self, query: Optional[dict] = None, skip: Optional[int] = None, limit: Optional[int] = None):
        return await self.storage.findAll(query, skip=skip, limit=limit)

    async def count(self, query: Optional[dict] = None) -> int:
        return await self.storage.count(query)

    async def countByUser(self, user_id: str) -> int:
        return await self.count({"user": user_id})

    async def findById(self, id: str):
        return await self.storage.findById(id)

    async def create(self, order_data: 'OrderInternalCreate'):
        if not order_data.created_at:
            order_data.created_at = datetime.now(timezone.utc).isoformat()
            
        order_data.order_number = await self.generateOrderNumber(order_data.user_role or "")
        return await self.storage.create(order_data)

    async def update(self, id: str, update_data: 'OrderInternalUpdate'):
        if update_data.status == "out_for_delivery" and update_data.shipped_at is None:
            update_data.shipped_at = datetime.now(timezone.utc).isoformat()

        if update_data.status == "delivered":
            if update_data.delivered_at is None:
                update_data.delivered_at = datetime.now(timezone.utc).isoformat()
            order = await self.findById(id)
            if order and order.payment_method == "cod":
                if update_data.payment_status is None:
                    update_data.payment_status = "paid"
                if update_data.cod_payment_received is None:
                    update_data.cod_payment_received = True
                if update_data.cod_payment_received_at is None:
                    update_data.cod_payment_received_at = datetime.now(timezone.utc).isoformat()
            try:
                created_at = order.created_at if order else None
                if created_at and created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                if created_at and update_data.delivered_at:
                    delivered_at = datetime.fromisoformat(update_data.delivered_at.replace("Z", "+00:00"))
                    if delivered_at.tzinfo is None:
                        delivered_at = delivered_at.replace(tzinfo=timezone.utc)
                    hours = (delivered_at - created_at).total_seconds() / 3600.0
                    update_data.turnaround_hours = round(hours, 2)
            except Exception as e:
                logging.warning("order_repository.update: could not calculate turnaround hours for order %r (delivered_at=%r): %s", id, update_data.delivered_at, e, exc_info=e)

        if update_data.status == "shipped" and update_data.shipped_at is None:
            update_data.shipped_at = datetime.now(timezone.utc).isoformat()

        if update_data.status == "cancelled" and update_data.cancelled_at is None:
            update_data.cancelled_at = datetime.now(timezone.utc).isoformat()

        return await self.storage.update(id, update_data)

    async def delete(self, id: str):
        return await self.storage.delete(id)


order_repository = OrderRepository()

