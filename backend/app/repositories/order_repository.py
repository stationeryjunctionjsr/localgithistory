from datetime import datetime, timezone
from typing import Dict, Optional, Any
from app.models.order import Order, OrderInternalCreate, OrderInternalUpdate, Any
from app.models.order import Order, OrderInternalCreate, OrderInternalUpdate, Any
from app.models.order import Order, OrderInternalCreate, OrderInternalUpdate

from app.db.storage_factory import get_storage
from app.utils.logger import logger


class OrderRepository:
    def __init__(self):
        self.storage = get_storage("orders")

    async def generateOrderNumber(self, user_role: str) -> str:
        # Determine prefix based on user role
        prefix = "ORDER-RT-"  # Retail customer orders
        if user_role == "wholesaler":
            prefix = "ORDER-WH-"  # Business (wholesaler) orders

        if hasattr(self.storage, "get_max_order_number_suffix"):
            max_id = await self.storage.get_max_order_number_suffix(prefix)
        else:
            # Generate incremental ID for each type
            all_orders = await self.storage.findAll()
            orders_of_type = [
                order for order in all_orders if order.orderNumber and order.orderNumber.startswith(prefix)
            ]

            max_id = 0
            import re

            for order in orders_of_type:
                match = re.match(f"{re.escape(prefix)}(\\d+)", order.orderNumber)
                if match:
                    max_id = max(max_id, int(match.group(1)))

        next_id = max(1, max_id + 1)  # ORDER-RT-1, ORDER-WH-1, etc. (never 0)
        return f"{prefix}{next_id}"

    async def findAll(self, query: Optional[Dict] = None, skip: Optional[int] = None, limit: Optional[int] = None):
        # Delegate all filtering to storage (DAO)
        try:
            return await self.storage.findAll(query, skip=skip, limit=limit)
        except TypeError:
            docs = await self.storage.findAll(query)
            if skip is not None or limit is not None:
                start = skip or 0
                end = (start + limit) if limit is not None else None
                return docs[start:end]
            return docs

    async def count(self, query: Optional[Dict] = None) -> int:
        if hasattr(self.storage, "count"):
            return await self.storage.count(query)
        orders = await self.storage.findAll(query)
        return len(orders)

    async def countByUser(self, user_id: str) -> int:
        return await self.count({"user": user_id})

    async def findById(self, id: str):
        return await self.storage.findById(id)

    async def create(self, order_data: OrderInternalCreate):
        if not order_data.createdAt:
            order_data.createdAt = datetime.now(timezone.utc).isoformat()
            
        order_data.orderNumber = await self.generateOrderNumber(order_data.userRole or "")
        return await self.storage.create(order_data)

    async def update(self, id: str, update_data: OrderInternalUpdate):
        if update_data.status == "out_for_delivery" and update_data.shippedAt is None:
            update_data.shippedAt = datetime.now(timezone.utc).isoformat()

        if update_data.status == "delivered":
            if update_data.deliveredAt is None:
                update_data.deliveredAt = datetime.now(timezone.utc).isoformat()
            order = await self.findById(id)
            if order and order.paymentMethod == "cod":
                if update_data.paymentStatus is None:
                    update_data.paymentStatus = "paid"
                if update_data.codPaymentReceived is None:
                    update_data.codPaymentReceived = True
                if update_data.codPaymentReceivedAt is None:
                    update_data.codPaymentReceivedAt = datetime.now(timezone.utc).isoformat()
            try:
                created_at_str = order.createdAt if order else None
                if created_at_str and update_data.deliveredAt:
                    created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                    delivered_at = datetime.fromisoformat(update_data.deliveredAt.replace("Z", "+00:00"))
                    hours = (delivered_at - created_at).total_seconds() / 3600.0
                    update_data.turnaroundHours = round(hours, 2)
            except Exception:
                pass

        if update_data.status == "shipped" and update_data.shippedAt is None:
            update_data.shippedAt = datetime.now(timezone.utc).isoformat()

        if update_data.status == "cancelled" and update_data.cancelledAt is None:
            update_data.cancelledAt = datetime.now(timezone.utc).isoformat()

        fields = {f: getattr(update_data, f) for f in update_data.model_fields_set}
        return await self.storage.update(id, fields)

    async def delete(self, id: str):
        return await self.storage.delete(id)


order_repository = OrderRepository()

