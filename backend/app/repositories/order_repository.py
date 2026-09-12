from datetime import datetime, timezone
from typing import Dict, Optional, Any
from app.models.order import Order, Any
from app.models.order import Order, Any
from app.models.order import Order

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
                order for order in all_orders if order.get("orderNumber") and order["orderNumber"].startswith(prefix)
            ]

            max_id = 0
            import re

            for order in orders_of_type:
                match = re.match(f"{re.escape(prefix)}(\\d+)", order["orderNumber"])
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

    async def create(self, order_data: Any):
        order = {
            "orderNumber": await self.generateOrderNumber(
                getattr(order_data, "userRole", None) or "" if isinstance(order_data, dict) else ""
            ),
            "user": order_data.user,
            "sessionId": getattr(order_data, "sessionId", None),  # session in which order was placed (for user engagement metrics)
            "items": getattr(order_data, 'items', []),
            "subtotal": float(order_data.subtotal),
            "tax": float(getattr(order_data, 'tax') or 0),
            "shipping": float(getattr(order_data, 'shipping') or 0),
            "discount": float(getattr(order_data, 'discount') or 0),
            "total": float(order_data.total),
            "orderType": order_data.orderType,
            "status": getattr(order_data, 'status', "pending"),
            "paymentStatus": getattr(order_data, 'paymentStatus', "pending"),
            "paymentMethod": getattr(order_data, 'paymentMethod', "cod"),
            "upiPaymentScreenshot": getattr(order_data, "upiPaymentScreenshot", None),
            "shippingAddress": getattr(order_data, 'shippingAddress', {}),
            "billingAddress": getattr(order_data, 'billingAddress', {}),
            "notes": getattr(order_data, 'notes', ""),
            "printedBill": getattr(order_data, 'printedBill', False),
            "assignedValet": getattr(order_data, "assignedValet", None),
            "shippedAt": getattr(order_data, "shippedAt", None),
            "deliveredAt": getattr(order_data, "deliveredAt", None),
            "codPaymentReceived": getattr(order_data, 'codPaymentReceived', False),
            "codPaymentReceivedAt": getattr(order_data, "codPaymentReceivedAt", None),
            "declineReason": getattr(order_data, "declineReason", None),
            "cancelledAt": getattr(order_data, "cancelledAt", None),
            "cancelledBy": getattr(order_data, "cancelledBy", None),
            "createdAt": getattr(order_data, "createdAt", None) or datetime.now(timezone.utc).isoformat(),
        }

        return await self.storage.create(order)

    async def update(self, id: str, update_data: Any):
        # Handle status-specific updates (only if not already set)
        if getattr(update_data, "status", None) == "out_for_delivery":
            if "shippedAt" not in update_data:
                update_data.shippedAt = datetime.now(timezone.utc).isoformat()

        if getattr(update_data, "status", None) == "delivered":
            if "deliveredAt" not in update_data:
                update_data.deliveredAt = datetime.now(timezone.utc).isoformat()
            # Get order to check payment method
            order = await self.findById(id)
            if order and order.get("paymentMethod") == "cod":
                if "paymentStatus" not in update_data:
                    update_data.paymentStatus = "paid"
                if "codPaymentReceived" not in update_data:
                    update_data.codPaymentReceived = True
                if "codPaymentReceivedAt" not in update_data:
                    update_data.codPaymentReceivedAt = datetime.now(timezone.utc).isoformat()
            # Turnaround time (hours) between createdAt and deliveredAt
            try:
                created_at_str = order.get("createdAt") if order else None
                delivered_at_str = getattr(update_data, "deliveredAt", None)
                if created_at_str and delivered_at_str:
                    created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                    delivered_at = datetime.fromisoformat(delivered_at_str.replace("Z", "+00:00"))
                    hours = (delivered_at - created_at).total_seconds() / 3600.0
                    update_data.turnaroundHours = round(hours, 2)
            except Exception:
                logger.exception("Error calculating turnaround time for order")

        if getattr(update_data, "status", None) == "shipped" and "shippedAt" not in update_data:
            update_data.shippedAt = datetime.now(timezone.utc).isoformat()

        if getattr(update_data, "status", None) == "cancelled" and "cancelledAt" not in update_data:
            update_data.cancelledAt = datetime.now(timezone.utc).isoformat()

        return await self.storage.update(id, update_data)

    async def delete(self, id: str):
        return await self.storage.delete(id)


order_repository = OrderRepository()

