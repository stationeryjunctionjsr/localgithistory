from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from app.models.daos import PaymentInternalCreate, PaymentInternalUpdate, PaymentEntryInternal

from app.db.storage_factory import get_storage
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.models.daos import PaymentInternalCreate, PaymentInternalUpdate, PaymentEntryInternal
    


class PaymentRepository:
    def __init__(self):
        self.storage = get_storage("payments")

    async def findAll(self, query: Optional[dict] = None):
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

    async def findOne(self, query: dict):
        return await self.storage.findOne(query)

    async def findByOrderId(self, order_id: str):
        return await self.storage.findAll({"order_id": order_id})

    async def create(self, payment_data: 'PaymentInternalCreate'):
        # Generate incremental payment ID in PYMT-X format
        all_payments = await self.storage.findAll()
        max_id = 0
        for p in all_payments:
            if (
                p.payment_id is not None
                
                and p.payment_id.startswith("PYMT-")
            ):
                try:
                    num = int(p.payment_id.split("-")[1])
                    max_id = max(max_id, num)
                except ValueError:
                    continue
        
        payment_data.payment_id = f"PYMT-{max_id + 1}"
        
        if payment_data.created_at is None:
            payment_data.created_at = datetime.now(timezone.utc)
        if payment_data.updated_at is None:
            payment_data.updated_at = datetime.now(timezone.utc)
            
        return await self.storage.create(payment_data)

    async def update(self, id: str, update_data: 'PaymentInternalUpdate'):
        update_data.updated_at = datetime.now(timezone.utc)
        return await self.storage.update(id, update_data)

    async def addPaymentEntry(self, payment_id: str, entry_data: 'PaymentEntryInternal'):
        payment = await self.findById(payment_id)
        if not payment:
            raise ValueError("Payment not found")

        entries = payment.payment_entries or []
        entry_data.entry_id = str(len(entries) + 1)
        if entry_data.payment_method is None:
            entry_data.payment_method = payment.payment_method or "cod"
        if entry_data.paid_at is None:
            entry_data.paid_at = datetime.now(timezone.utc)
        if entry_data.created_at is None:
            entry_data.created_at = datetime.now(timezone.utc)

        entries.append(entry_data)
        payment.payment_entries = entries

        # Update amount paid and remaining
        if payment.amount_paid is None:
            raise ValueError("amountPaid is None")
        payment.amount_paid = payment.amount_paid + (entry_data.amount or 0)
        if payment.total_amount is None:
            raise ValueError("totalAmount is None")
        payment.amount_remaining = max(0, payment.total_amount - payment.amount_paid)

        update_payload = PaymentInternalUpdate(
            payment_entries=entries,
            amount_paid=payment.amount_paid,
            amount_remaining=payment.amount_remaining
        )
        return await self.update(payment_id, update_payload)

    async def updatePaymentEntry(self, payment_id: str, entry_id: int, update_data: 'PaymentEntryInternal'):
        payment = await self.findById(payment_id)
        if not payment:
            raise ValueError("Payment not found")

        entries = payment.payment_entries or []
        entry_index = next((i for i, e in enumerate(entries) if (str(e.entry_id) == str(entry_id))), None)
        if entry_index is None:
            raise ValueError("Payment entry not found")

        entry = entries[entry_index]
        if update_data.verified is not None:
            entry.verified = update_data.verified
        if update_data.amount is not None:
            entry.amount = update_data.amount
        if update_data.image is not None:
            entry.image = update_data.image
        if update_data.notes is not None:
            entry.notes = update_data.notes
            
        verified_paid = sum(float(e.amount or 0) for e in entries if e.verified)
        total_amount = float(payment.total_amount or 0.0)
        amount_remaining = max(0.0, total_amount - verified_paid)
        
        update_model = PaymentInternalUpdate(
            payment_entries=entries, 
            updated_at=datetime.now(timezone.utc),
            amount_paid=verified_paid,
            amount_remaining=amount_remaining
        )
        return await self.storage.update(payment_id, update_model)

    async def delete(self, id: str):
        return await self.storage.delete(id)


payment_repository = PaymentRepository()


