from datetime import datetime, timezone
from typing import Dict, Optional, Any
from app.models.daos import PaymentInternalCreate, PaymentInternalUpdate, PaymentEntryInternal

from app.db.storage_factory import get_storage


class PaymentRepository:
    def __init__(self):
        self.storage = get_storage("payments")

    async def findAll(self, query: Optional[Dict] = None):
        payments = await self.storage.findAll(query)

        query = query or {}

        # Date filtering (since CLOB/Date filters are handled post-query)
        if query.get("startDate") or query.get("endDate"):
            from datetime import datetime, timezone

            filtered_payments = []
            for payment in payments:
                payment_date_str = payment.get("orderDate") or payment.get("createdAt", "")
                if not payment_date_str:
                    continue

                try:
                    payment_date = datetime.fromisoformat(payment_date_str.replace("Z", "+00:00"))
                except Exception:
                    continue

                if query.get("startDate"):
                    start_date = datetime.fromisoformat(query["startDate"])
                    if payment_date < start_date:
                        continue

                if query.get("endDate"):
                    end_date = datetime.fromisoformat(query["endDate"])
                    end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                    if payment_date > end_date:
                        continue

                filtered_payments.append(payment)
            payments = filtered_payments

        # Sort by order date (newest first)
        payments.sort(key=lambda p: p.get("orderDate", p.get("createdAt", "")), reverse=True)

        return payments

    async def findById(self, id: str):
        return await self.storage.findById(id)

    async def findOne(self, query: Any):
        return await self.storage.findOne(query)

    async def findByOrderId(self, order_id: str):
        return await self.storage.findAll({"orderId": order_id})

    async def create(self, payment_data: Any):
        payment = {
            "orderId": payment_data["orderId"],
            "userId": payment_data.get("userId") or payment_data.get("customerId"),  # Use userId instead of customerId
            "userIdFormatted": payment_data.get("userIdFormatted"),
            "customerName": payment_data["customerName"],
            "orderDate": payment_data.get("orderDate", datetime.now(timezone.utc).isoformat()),
            "paymentMethod": payment_data["paymentMethod"],  # 'cod', 'upi', 'credit'
            "amountPaid": payment_data.get("amountPaid", 0),
            "amountRemaining": payment_data.get("amountRemaining", payment_data.get("totalAmount", 0)),
            "totalAmount": payment_data.get("totalAmount", 0),
            "paymentEntries": payment_data.get("paymentEntries", []),
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        }

        # Generate incremental payment ID in PYMT-X format
        all_payments = await self.storage.findAll()
        max_id = 0
        for p in all_payments:
            if (
                p.get("paymentId")
                and isinstance(p.get("paymentId"), str)
                and p.get("paymentId", "").startswith("PYMT-")
            ):
                import re

                match = re.match(r"PYMT-(\d+)", p.get("paymentId", ""))
                if match:
                    max_id = max(max_id, int(match.group(1)))
        payment["paymentId"] = f"PYMT-{max_id + 1}"

        payment_model = PaymentInternalCreate(**payment)
        return await self.storage.create(payment_model)

    async def update(self, id: str, update_data: Any):
        if not isinstance(update_data, PaymentInternalUpdate):
            if isinstance(update_data, dict):
                update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()
                update_data = PaymentInternalUpdate(**update_data)
            else:
                update_dict = {}
                for k in ["orderId", "userId", "userIdFormatted", "customerName", "orderDate", "paymentMethod", "amountPaid", "amountRemaining", "totalAmount", "paymentId", "paymentEntries"]:
                    val = getattr(update_data, k, None)
                    if val is not None:
                        update_dict[k] = val
                update_dict["updatedAt"] = datetime.now(timezone.utc).isoformat()
                update_data = PaymentInternalUpdate(**update_dict)
        else:
            update_data.updatedAt = datetime.now(timezone.utc).isoformat()

        return await self.storage.update(id, update_data)

    async def addPaymentEntry(self, payment_id: str, entry_data: Any):
        payment = await self.findById(payment_id)
        if not payment:
            raise ValueError("Payment not found")

        entries = payment.get("paymentEntries") or []
        entry = {
            "entryId": len(entries) + 1,
            "amount": entry_data.get("amount", 0),
            "paymentMethod": entry_data.get("paymentMethod", payment.get("paymentMethod", "cod")),
            "paidAt": entry_data.get("paidAt", datetime.now(timezone.utc).isoformat()),
            "image": entry_data.get("image"),  # Payment screenshot (optional)
            "notes": entry_data.get("notes", ""),
            "verified": entry_data.get("verified", False),
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }

        entries.append(entry)
        payment["paymentEntries"] = entries

        # Update amount paid and remaining
        payment["amountPaid"] = (payment.get("amountPaid", 0) or 0) + entry["amount"]
        payment["amountRemaining"] = max(0, (payment.get("totalAmount", 0) or 0) - payment["amountPaid"])

        return await self.update(payment_id, payment)

    async def updatePaymentEntry(self, payment_id: str, entry_id: int, update_data: Any):
        payment = await self.findById(payment_id)
        if not payment:
            raise ValueError("Payment not found")

        entries = payment.get("paymentEntries") or []
        entry_index = next((i for i, e in enumerate(entries) if e.get("entryId") == entry_id), None)
        if entry_index is None:
            raise ValueError("Payment entry not found")

        entries[entry_index].update(update_data)
        payment["paymentEntries"] = entries

        return await self.update(payment_id, payment)

    async def delete(self, id: str):
        return await self.storage.delete(id)


payment_repository = PaymentRepository()
