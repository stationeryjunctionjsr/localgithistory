from datetime import datetime, timezone
from typing import Dict, Optional

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

    async def create(self, order_data: Dict):
        order = {
            "orderNumber": await self.generateOrderNumber(
                order_data.get("userRole") or "" if isinstance(order_data, dict) else ""
            ),
            "user": order_data["user"],
            "sessionId": order_data.get("sessionId"),  # session in which order was placed (for user engagement metrics)
            "items": order_data.get("items", []),
            "subtotal": float(order_data["subtotal"]),
            "tax": float(order_data.get("tax", 0)),
            "shipping": float(order_data.get("shipping", 0)),
            "discount": float(order_data.get("discount", 0)),
            "total": float(order_data["total"]),
            "orderType": order_data["orderType"],
            "status": order_data.get("status", "pending"),
            "paymentStatus": order_data.get("paymentStatus", "pending"),
            "paymentMethod": order_data.get("paymentMethod", "cod"),
            "upiPaymentScreenshot": order_data.get("upiPaymentScreenshot"),
            "shippingAddress": order_data.get("shippingAddress", {}),
            "billingAddress": order_data.get("billingAddress", {}),
            "notes": order_data.get("notes", ""),
            "printedBill": order_data.get("printedBill", False),
            "assignedValet": order_data.get("assignedValet"),
            "shippedAt": order_data.get("shippedAt"),
            "deliveredAt": order_data.get("deliveredAt"),
            "codPaymentReceived": order_data.get("codPaymentReceived", False),
            "codPaymentReceivedAt": order_data.get("codPaymentReceivedAt"),
            "declineReason": order_data.get("declineReason"),
            "cancelledAt": order_data.get("cancelledAt"),
            "cancelledBy": order_data.get("cancelledBy"),
            "createdAt": order_data.get("createdAt") or datetime.now(timezone.utc).isoformat(),
        }

        return await self.storage.create(order)

    async def update(self, id: str, update_data: Dict):
        # Handle status-specific updates (only if not already set)
        if update_data.get("status") == "out_for_delivery":
            if "shippedAt" not in update_data:
                update_data["shippedAt"] = datetime.now(timezone.utc).isoformat()

        if update_data.get("status") == "delivered":
            if "deliveredAt" not in update_data:
                update_data["deliveredAt"] = datetime.now(timezone.utc).isoformat()
            # Get order to check payment method
            order = await self.findById(id)
            if order and order.get("paymentMethod") == "cod":
                if "paymentStatus" not in update_data:
                    update_data["paymentStatus"] = "paid"
                if "codPaymentReceived" not in update_data:
                    update_data["codPaymentReceived"] = True
                if "codPaymentReceivedAt" not in update_data:
                    update_data["codPaymentReceivedAt"] = datetime.now(timezone.utc).isoformat()
            # Turnaround time (hours) between createdAt and deliveredAt
            try:
                created_at_str = order.get("createdAt") if order else None
                delivered_at_str = update_data.get("deliveredAt")
                if created_at_str and delivered_at_str:
                    created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                    delivered_at = datetime.fromisoformat(delivered_at_str.replace("Z", "+00:00"))
                    hours = (delivered_at - created_at).total_seconds() / 3600.0
                    update_data["turnaroundHours"] = round(hours, 2)
            except Exception:
                logger.exception("Error calculating turnaround time for order")

        if update_data.get("status") == "shipped" and "shippedAt" not in update_data:
            update_data["shippedAt"] = datetime.now(timezone.utc).isoformat()

        if update_data.get("status") == "cancelled" and "cancelledAt" not in update_data:
            update_data["cancelledAt"] = datetime.now(timezone.utc).isoformat()

        return await self.storage.update(id, update_data)

    async def delete(self, id: str):
        return await self.storage.delete(id)


order_repository = OrderRepository()
