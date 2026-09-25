from datetime import datetime, timezone
from typing import Dict, Optional, Any
from app.models.daos import PaymentInternalCreate, PaymentInternalUpdate, PaymentEntryInternal

from app.db.storage_factory import get_storage
from app.utils.logger import logger


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
                payment_date_str = payment.order_date or payment.created_at or ""
                if not payment_date_str:
                    continue

                try:
                    payment_date = datetime.fromisoformat(payment_date_str.replace("Z", "+00:00"))
                except Exception as e:
                    logger.warning(
                        "Skipping payment record with unparseable date %r: %s",
                        payment_date_str, e,
                    )
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
        payments.sort(key=lambda p: (p.order_date if p.order_date is not None else p.created_at if p.created_at is not None else ""), reverse=True)

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
                p.payment_id
                and isinstance(p.payment_id, str)
                and (p.payment_id if p.payment_id is not None else "").startswith("PYMT-")
            ):
                import re

                match = re.match(r"PYMT-(\d+)", (p.payment_id if p.payment_id is not None else ""))
                if match:
                    max_id = max(max_id, int(match.group(1)))
        payment["paymentId"] = f"PYMT-{max_id + 1}"

        payment_model = PaymentInternalCreate.model_validate(payment)
        return await self.storage.create(payment_model)

    async def update(self, id: str, update_data: Any):
        if not isinstance(update_data, PaymentInternalUpdate):
            if isinstance(update_data, dict):
                update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()
                update_data = PaymentInternalUpdate.model_validate(update_data)
            else:
                update_dict = {}
                try:
                    if update_data.order_id is not None: update_dict["orderId"] = update_data.order_id
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
                    if update_data.payment_method is not None: update_dict["paymentMethod"] = update_data.payment_method
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

        entries = payment.payment_entries or []
        entry = {
            "entryId": len(entries) + 1,
            "amount": entry_data["amount"] if "amount" in entry_data else 0,
            "paymentMethod": entry_data["paymentMethod"] if "paymentMethod" in entry_data else (payment.payment_method or "cod"),
            "paidAt": entry_data["paidAt"] if "paidAt" in entry_data else datetime.now(timezone.utc).isoformat(),
            "image": entry_data["image"] if "image" in entry_data else None,  # Payment screenshot (optional)
            "notes": entry_data["notes"] if "notes" in entry_data else "",
            "verified": entry_data["verified"] if "verified" in entry_data else False,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }

        entries.append(entry)
        payment.payment_entries = entries

        # Update amount paid and remaining
        if payment.amount_paid is None:
            raise ValueError("amountPaid is None")
        payment.amount_paid = payment.amount_paid + entry["amount"]
        if payment.total_amount is None:
            raise ValueError("totalAmount is None")
        payment.amount_remaining = max(0, payment.total_amount - payment.amount_paid)


        def _to_internal_entry(e):
            if isinstance(e, dict):
                return PaymentEntryInternal(
                    entryId=e.get("entryId"),
                    amount=e.get("amount", 0),
                    paymentMethod=e.get("paymentMethod"),
                    paidAt=e.get("paidAt"),
                    image=e.get("image"),
                    notes=e.get("notes"),
                    verified=e.get("verified", False),
                    createdAt=e.get("createdAt")
                )
            return PaymentEntryInternal(
                entryId=int(e.entry_id) if e.entry_id else None,
                amount=e.amount,
                paymentMethod=e.payment_method,
                paidAt=e.paid_at.isoformat() if e.paid_at else None,
                image=e.image,
                notes=e.notes,
                verified=e.verified,
                createdAt=e.created_at.isoformat() if e.created_at else None
            )

        internal_entries = [_to_internal_entry(e) for e in payment.payment_entries]

        update_payload = PaymentInternalUpdate(
            orderId=payment.order_id,
            userId=payment.user_id,
            userIdFormatted=payment.user_id_formatted,
            customerName=payment.customer_name,
            orderDate=payment.order_date.isoformat() if payment.order_date else None,
            paymentMethod=payment.payment_method,
            amountPaid=payment.amount_paid,
            amountRemaining=payment.amount_remaining,
            totalAmount=payment.total_amount,
            paymentId=payment.payment_id,
            paymentEntries=internal_entries
        )
        return await self.update(payment_id, update_payload)




    async def updatePaymentEntry(self, payment_id: str, entry_id: int, update_data: Any):
        payment = await self.findById(payment_id)
        if not payment:
            raise ValueError("Payment not found")

        entries = payment.payment_entries or []
        entry_index = next((i for i, e in enumerate(entries) if (e.entry_id == str(entry_id) or e.entry_id == entry_id)), None)
        if entry_index is None:
            raise ValueError("Payment entry not found")

        # Update the object fields based on update_data dict
        entry = entries[entry_index]
        if "verified" in update_data:
            entry.verified = update_data["verified"]
        if "amount" in update_data:
            entry.amount = update_data["amount"]
        if "image" in update_data:
            entry.image = update_data["image"]
        if "notes" in update_data:
            entry.notes = update_data["notes"]
            
        def _to_internal_entry(e):
            if isinstance(e, dict):
                return PaymentEntryInternal(
                    entryId=e.get("entryId"),
                    amount=e.get("amount", 0),
                    paymentMethod=e.get("paymentMethod"),
                    paidAt=e.get("paidAt"),
                    image=e.get("image"),
                    notes=e.get("notes"),
                    verified=e.get("verified", False),
                    createdAt=e.get("createdAt")
                )
            return PaymentEntryInternal(
                entryId=int(e.entry_id) if e.entry_id else None,
                amount=e.amount,
                paymentMethod=e.payment_method,
                paidAt=e.paid_at.isoformat() if e.paid_at else None,
                image=e.image,
                notes=e.notes,
                verified=e.verified,
                createdAt=e.created_at.isoformat() if e.created_at else None
            )

        internal_entries = [_to_internal_entry(e) for e in entries]

        verified_paid = sum(float(e.amount or 0) for e in internal_entries if e.verified)
        total_amount = float(payment.total_amount or 0.0)
        amount_remaining = max(0.0, total_amount - verified_paid)

        update_payload = PaymentInternalUpdate(
            orderId=payment.order_id,
            userId=payment.user_id,
            userIdFormatted=payment.user_id_formatted,
            customerName=payment.customer_name,
            orderDate=payment.order_date.isoformat() if payment.order_date else None,
            paymentMethod=payment.payment_method,
            amountPaid=verified_paid,
            amountRemaining=amount_remaining,
            totalAmount=total_amount,
            paymentId=payment.payment_id,
            paymentEntries=internal_entries
        )
        return await self.update(payment_id, update_payload)

    async def delete(self, id: str):
        return await self.storage.delete(id)


payment_repository = PaymentRepository()


