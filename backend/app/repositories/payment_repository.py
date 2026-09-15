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
        if query["startDate"] if "startDate" in query else None or query["endDate"] if "endDate" in query else None:
            from datetime import datetime, timezone

            filtered_payments = []
            for payment in payments:
                payment_date_str = payment["orderDate"] if "orderDate" in payment else None or payment["createdAt"] if "createdAt" in payment else ""
                if not payment_date_str:
                    continue

                try:
                    payment_date = datetime.fromisoformat(payment_date_str.replace("Z", "+00:00"))
                except Exception:
                    continue

                if query["startDate"] if "startDate" in query else None:
                    start_date = datetime.fromisoformat(query["startDate"])
                    if payment_date < start_date:
                        continue

                if query["endDate"] if "endDate" in query else None:
                    end_date = datetime.fromisoformat(query["endDate"])
                    end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                    if payment_date > end_date:
                        continue

                filtered_payments.append(payment)
            payments = filtered_payments

        # Sort by order date (newest first)
        payments.sort(key=lambda p: (p.orderDate if p.orderDate is not None else p["createdAt"] if "createdAt" in p else ""), reverse=True)

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
            "userId": payment_data["userId"] if "userId" in payment_data else None or payment_data["customerId"] if "customerId" in payment_data else None,  # Use userId instead of customerId
            "userIdFormatted": payment_data["userIdFormatted"] if "userIdFormatted" in payment_data else None,
            "customerName": payment_data["customerName"],
            "orderDate": payment_data["orderDate"] if "orderDate" in payment_data else datetime.now(timezone.utc).isoformat(),
            "paymentMethod": payment_data["paymentMethod"],  # 'cod', 'upi', 'credit'
            "amountPaid": payment_data["amountPaid"] if "amountPaid" in payment_data else 0,
            "amountRemaining": payment_data["amountRemaining"] if "amountRemaining" in payment_data else (payment_data["totalAmount"] if "totalAmount" in payment_data else 0),
            "totalAmount": payment_data["totalAmount"] if "totalAmount" in payment_data else 0,
            "paymentEntries": payment_data["paymentEntries"] if "paymentEntries" in payment_data else [],
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        }

        # Generate incremental payment ID in PYMT-X format
        all_payments = await self.storage.findAll()
        max_id = 0
        for p in all_payments:
            if (
                p.paymentId
                and isinstance(p.paymentId, str)
                and (p.paymentId if p.paymentId is not None else "").startswith("PYMT-")
            ):
                import re

                match = re.match(r"PYMT-(\d+)", (p.paymentId if p.paymentId is not None else ""))
                if match:
                    max_id = max(max_id, int(match.group(1)))
        payment["paymentId"] = f"PYMT-{max_id + 1}"

        payment_model = PaymentInternalCreate.model_validate(payment)
        return await self.storage.create(payment_model)

    async def update(self, id: str, update_data: Any):
        if not isinstance(update_data, PaymentInternalUpdate):
            if isinstance(update_data, dict):
                update_data.updatedAt = datetime.now(timezone.utc).isoformat()
                update_data = PaymentInternalUpdate.model_validate(update_data)
            else:
                update_dict = {}
                try:
                    if update_data.orderId is not None: update_dict["orderId"] = update_data.orderId
                except AttributeError: pass
                try:
                    if update_data.userId is not None: update_dict["userId"] = update_data.userId
                except AttributeError: pass
                try:
                    if update_data.userIdFormatted is not None: update_dict["userIdFormatted"] = update_data.userIdFormatted
                except AttributeError: pass
                try:
                    if update_data.customerName is not None: update_dict["customerName"] = update_data.customerName
                except AttributeError: pass
                try:
                    if update_data.orderDate is not None: update_dict["orderDate"] = update_data.orderDate
                except AttributeError: pass
                try:
                    if update_data.paymentMethod is not None: update_dict["paymentMethod"] = update_data.paymentMethod
                except AttributeError: pass
                try:
                    if update_data.amountPaid is not None: update_dict["amountPaid"] = update_data.amountPaid
                except AttributeError: pass
                try:
                    if update_data.amountRemaining is not None: update_dict["amountRemaining"] = update_data.amountRemaining
                except AttributeError: pass
                try:
                    if update_data.totalAmount is not None: update_dict["totalAmount"] = update_data.totalAmount
                except AttributeError: pass
                try:
                    if update_data.paymentId is not None: update_dict["paymentId"] = update_data.paymentId
                except AttributeError: pass
                try:
                    if update_data.paymentEntries is not None: update_dict["paymentEntries"] = update_data.paymentEntries
                except AttributeError: pass
                update_dict["updatedAt"] = datetime.now(timezone.utc).isoformat()
                update_data = PaymentInternalUpdate.model_validate(update_dict)
        else:
            update_data.updatedAt = datetime.now(timezone.utc).isoformat()

        return await self.storage.update(id, update_data)

    async def addPaymentEntry(self, payment_id: str, entry_data: Any):
        payment = await self.findById(payment_id)
        if not payment:
            raise ValueError("Payment not found")

        entries = payment["paymentEntries"] if "paymentEntries" in payment else None or []
        entry = {
            "entryId": len(entries) + 1,
            "amount": entry_data["amount"] if "amount" in entry_data else 0,
            "paymentMethod": entry_data["paymentMethod"] if "paymentMethod" in entry_data else (payment["paymentMethod"] if "paymentMethod" in payment else "cod"),
            "paidAt": entry_data["paidAt"] if "paidAt" in entry_data else datetime.now(timezone.utc).isoformat(),
            "image": entry_data["image"] if "image" in entry_data else None,  # Payment screenshot (optional)
            "notes": entry_data["notes"] if "notes" in entry_data else "",
            "verified": entry_data["verified"] if "verified" in entry_data else False,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }

        entries.append(entry)
        payment["paymentEntries"] = entries

        # Update amount paid and remaining
        if payment["amountPaid"] if "amountPaid" in payment else None is None:
            raise ValueError("amountPaid is None")
        payment["amountPaid"] = payment["amountPaid"] + entry["amount"]
        if payment["totalAmount"] if "totalAmount" in payment else None is None:
            raise ValueError("totalAmount is None")
        payment["amountRemaining"] = max(0, payment["totalAmount"] - payment["amountPaid"])

        return await self.update(payment_id, payment)

    async def updatePaymentEntry(self, payment_id: str, entry_id: int, update_data: Any):
        payment = await self.findById(payment_id)
        if not payment:
            raise ValueError("Payment not found")

        entries = payment["paymentEntries"] if "paymentEntries" in payment else None or []
        entry_index = next((i for i, e in enumerate(entries) if ("entryId" in e and e["entryId"] == entry_id)), None)
        if entry_index is None:
            raise ValueError("Payment entry not found")

        entries[entry_index].update(update_data)
        payment["paymentEntries"] = entries

        return await self.update(payment_id, payment)

    async def delete(self, id: str):
        return await self.storage.delete(id)


payment_repository = PaymentRepository()


