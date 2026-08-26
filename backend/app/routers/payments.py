from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.repositories.notification_repository import notification_repository
from app.repositories.payment_repository import payment_repository
from app.repositories.user_repository import user_repository
from app.utils.auth import require_roles, require_super_admin
from app.utils.logger import logger
from app.utils.metrics import PAYMENT_ERRORS

router = APIRouter()
require_wholesaler = require_roles("wholesaler")


@router.get("/dues")
async def get_wholesaler_dues(current_user: dict = Depends(require_wholesaler)):
    """Retrieve credit dues information for the logged-in wholesaler"""
    from datetime import datetime, timezone, timedelta
    from app.repositories.payment_repository import payment_repository
    from app.repositories.order_repository import order_repository

    # 1. Get user credit terms (default to 30 days)
    terms_days = current_user.get("paymentTerms")
    if terms_days is None:
        terms_days = 30
    else:
        try:
            terms_days = int(terms_days)
        except Exception:
            terms_days = 30

    # 2. Get all payments for this user
    user_payments = await payment_repository.findAll({"userId": current_user.get("userId")})
    unpaid_credit_bills = []

    for p in user_payments:
        # Check if it is a credit payment
        if p.get("paymentMethod") == "credit":
            # Calculate verified amount paid
            verified_paid = sum(
                entry.get("amount", 0.0) for entry in (p.get("paymentEntries") or []) if entry.get("verified")
            )
            # Calculate effective remaining due amount
            effective_due = p.get("totalAmount", 0.0) - verified_paid
            if effective_due > 0:
                unpaid_credit_bills.append((p, effective_due))

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    total_dues = 0.0
    total_overdue = 0.0
    has_overdue_bills = False
    bills_info = []

    for bill, effective_due in unpaid_credit_bills:
        total_dues += effective_due

        # Retrieve order details to get orderNumber or fallback to orderId
        order_number = bill.get("orderId")
        try:
            order = await order_repository.findById(bill.get("orderId"))
            if order:
                order_number = order.get("orderNumber", bill.get("orderId"))
        except Exception:
            pass

        # Parse orderDate as naive UTC datetime
        order_date_str = bill.get("orderDate") or bill.get("createdAt")
        if order_date_str:
            try:
                order_date = (
                    datetime.fromisoformat(order_date_str.replace("Z", "+00:00"))
                    .astimezone(timezone.utc)
                    .replace(tzinfo=None)
                )
            except Exception:
                order_date = now
        else:
            order_date = now

        due_date = order_date + timedelta(days=terms_days)
        is_overdue = now > due_date

        if is_overdue:
            has_overdue_bills = True
            total_overdue += effective_due

        # Construct time remaining string
        if is_overdue:
            days_overdue = (now - due_date).days
            if days_overdue == 0:
                time_remaining_str = "Overdue today"
            else:
                time_remaining_str = f"Overdue by {days_overdue} day{'s' if days_overdue > 1 else ''}"
        else:
            days_left = (due_date - now).days
            if days_left == 0:
                time_remaining_str = "Due today"
            else:
                time_remaining_str = f"{days_left} day{'s' if days_left > 1 else ''} remaining"

        bills_info.append(
            {
                "orderId": bill.get("orderId"),
                "orderNumber": order_number,
                "amountRemaining": effective_due,
                "totalAmount": bill.get("totalAmount", 0.0),
                "orderDate": order_date_str,
                "dueDate": due_date.isoformat() + "Z",
                "timeRemaining": time_remaining_str,
                "overdue": is_overdue,
                "paymentId": bill.get("_id"),
            }
        )

    # Sort bills by due date (earliest first)
    bills_info.sort(key=lambda b: b["dueDate"])

    nearest_due_amount = 0.0
    nearest_due_date = None

    if bills_info:
        nearest_due = bills_info[0]
        nearest_due_amount = nearest_due["amountRemaining"]
        nearest_due_date = nearest_due["dueDate"]

    minimum_overdue = total_overdue if has_overdue_bills else nearest_due_amount

    return {
        "hasOverdueBills": has_overdue_bills,
        "totalDues": total_dues,
        "currentOverdue": total_overdue,
        "minimumOverdue": minimum_overdue,
        "nearestDueAmount": nearest_due_amount,
        "nearestDueDate": nearest_due_date,
        "bills": bills_info,
        "paymentTerms": terms_days,
    }


class VerifyEntryRequest(BaseModel):
    verified: bool


class CreditSettlementRequest(BaseModel):
    orderId: str
    amount: float
    upiPaymentScreenshot: str


@router.get("")
@router.get("/")
async def get_payments(
    orderId: Optional[str] = Query(None),
    userId: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    current_user: dict = Depends(require_super_admin),
):
    """Get all payments (Super Admin only)"""
    from app.repositories.order_repository import order_repository

    query = {}
    if orderId:
        query["orderId"] = orderId
    if userId:
        query["userId"] = userId
    if startDate:
        query["startDate"] = startDate
    if endDate:
        query["endDate"] = endDate

    payments = await payment_repository.findAll(query or None)

    # Bulk-fetch all referenced orders in one query to avoid N+1 DB calls
    order_ids = list({p.get("orderId") for p in payments if p.get("orderId")})
    orders_list = await order_repository.findAll({"_id": {"$in": order_ids}}) if order_ids else []
    order_map = {str(o.get("_id")): o for o in orders_list}

    enhanced_payments = []
    for payment in payments:
        order = order_map.get(str(payment.get("orderId")))
        enhanced_payments.append({
            **payment,
            "orderNumber": order.get("orderNumber") if order else payment.get("orderId"),
        })

    return enhanced_payments


@router.get("/{payment_id}")
async def get_payment(payment_id: str, current_user: dict = Depends(require_super_admin)):
    """Get single payment (Super Admin only)"""
    payment = await payment_repository.findById(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.put("/{payment_id}/verify-entry/{entry_id}")
async def verify_payment_entry(
    payment_id: str, entry_id: int, verify_data: VerifyEntryRequest, current_user: dict = Depends(require_super_admin)
):
    """Verify a payment entry (Super Admin only)"""
    try:
        payment = await payment_repository.updatePaymentEntry(payment_id, entry_id, {"verified": verify_data.verified})
        return payment
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        PAYMENT_ERRORS.labels(gateway="internal", error_type="verify_entry_failed").inc()
        logger.error("verify_payment_entry failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Server error")


@router.post("/credit-settlement")
async def submit_credit_settlement(
    settlement_data: CreditSettlementRequest, current_user: dict = Depends(require_wholesaler)
):
    """Submit a credit settlement payment (Wholesaler only)"""
    from app.repositories.order_repository import order_repository

    try:
        # Find the order
        order = await order_repository.findById(settlement_data.orderId)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Verify the order belongs to the user — use str() on both sides to
        # guard against type mismatches (int vs str IDs across storage backends).
        if str(order.get("user")) != str(current_user.get("_id")):
            raise HTTPException(status_code=403, detail="Not authorized to settle this order")

        # Verify the order is a credit order
        if order.get("paymentMethod") != "credit":
            raise HTTPException(status_code=400, detail="This order is not a credit order")

        # Find the payment record
        payments = await payment_repository.findByOrderId(settlement_data.orderId)
        if not payments or len(payments) == 0:
            raise HTTPException(status_code=404, detail="Payment record not found")

        payment = payments[0]

        # Re-fetch the payment record immediately before the guard to avoid a
        # race condition where two concurrent requests both read the same stale
        # amountRemaining and both pass the check before either is deducted.
        fresh_payments = await payment_repository.findByOrderId(settlement_data.orderId)
        if not fresh_payments:
            raise HTTPException(status_code=404, detail="Payment record not found")
        payment = fresh_payments[0]

        if settlement_data.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be strictly positive")

        # Verify amount doesn't exceed remaining amount (using freshly-read value)
        if settlement_data.amount > payment.get("amountRemaining", 0):
            raise HTTPException(
                status_code=400,
                detail=f"Settlement amount ({settlement_data.amount}) exceeds remaining amount ({payment.get('amountRemaining', 0)})",
            )

        # Upload screenshot to OCI
        from app.services.oci_storage import upload_base64_image_and_return_path

        screenshot_path = await upload_base64_image_and_return_path(
            settlement_data.upiPaymentScreenshot, "payments", filename_prefix="settlement-screenshot"
        )

        # Add payment entry
        updated_payment = await payment_repository.addPaymentEntry(
            payment.get("_id"),
            {
                "amount": float(settlement_data.amount),
                "image": screenshot_path,
                "verified": False,
                "paymentMethod": "upi",
                "notes": "Credit settlement payment",
            },
        )

        # Create notification for new payment (credit settlement)
        try:
            super_admin = await user_repository.findOne({"role": "super_admin"})
            if super_admin:
                payment_id = updated_payment.get("paymentId") or updated_payment.get("_id")
                await notification_repository.create(
                    {
                        "userId": super_admin.get("_id"),
                        "type": "new_payment",
                        "title": "New Payment Received",
                        "message": f'New payment "{payment_id}" worth ₹{settlement_data.amount:.2f} received',
                        "data": {
                            "paymentId": updated_payment.get("_id"),
                            "paymentIdFormatted": payment_id,
                            "orderId": updated_payment.get("orderId"),
                            "amount": settlement_data.amount,
                            "paymentMethod": "upi",
                            "createdAt": datetime.now(timezone.utc).isoformat() + "Z",
                        },
                    }
                )
        except Exception as e:
            logger.error("Error creating payment notification: %s", str(e), exc_info=True)

        return {"message": "Settlement payment submitted successfully", "payment": updated_payment}
    except HTTPException:
        raise
    except Exception as e:
        PAYMENT_ERRORS.labels(gateway="credit", error_type="settlement_failed").inc()
        logger.error("Credit settlement error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Server error")
