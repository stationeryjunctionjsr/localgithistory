from app.models.daos import NotificationInternalCreate
from fastapi.responses import FileResponse
from app.models.schemas import VariantAttributes, CouponResponse
from app.utils.logger import logger
from app.utils.limiter import limiter
from app.utils.invoice_generator import generate_invoice_pdf, save_invoice_pdf
from app.utils.auth import (
    get_current_user,
    is_seller_admin,
    require_seller_admin,
    require_super_admin,
    require_super_admin_or_seller,
    require_super_admin_or_valet,
)
from app.services.email_service import email_service
from app.repositories.user_repository import user_repository
from app.repositories.sub_order_repository import sub_order_repository
from app.repositories.product_repository import product_repository
from app.repositories.payment_repository import payment_repository
from app.repositories.order_repository import order_repository
from app.repositories.notification_repository import notification_repository
from app.repositories.category_repository import category_repository
from app.repositories.cart_repository import cart_repository
from pydantic import BaseModel, ConfigDict, Field
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Header, status
from typing import List, Optional
from datetime import datetime, timezone
import logging
import uuid

from app.models.schemas import (
    UserSnippet,
    ValetSnippet,
    Address,
    OrderItemCreate,
    SellerDeliveryOption,
    ItemSnippet as OrderItem,
    UserInternalUpdate,
    PopulatedOrderResponse,
    PopulatedOrderItemResponse,
)
from app.schemas.orders import PaginatedOrdersResponse, PaginatedSubOrdersResponse, DeliveryChargeUpdateResponse
from app.models.payment import PaymentEntry
from app.db.storage_factory import get_storage
from app.models.user import User
from app.models.order import Order, OrderInternalCreate, OrderInternalUpdate
from app.models.daos import BundleInternalUpdate
from app.models.sub_order import SubOrder, SubOrderInternalCreate, SubOrderInternalUpdate, SubOrderItem
from app.models.product import Product
from app.models.base import CamelBaseModel

# Import business logic and helpers from order_service
from app.services.order_service import (
    CalculatedOrderItem,
    LocationDeliveryCharge,
    CouponDetailModel,
    ItemDiscountEntry,
    CouponValidationResult,
    ReferralProgramSegmentSettings,
    ReferralSettingsModel,
    _resolve_product_seller_id,
    create_order_notification,
    create_payment_notification,
    populate_orders,
    populate_order,
    _compute_fulfillment_status,
    create_order_service,
)


class GenerateInvoiceResponse(BaseModel):
    success: bool
    invoiceUrl: str


router = APIRouter()






# Helper schemas for order creation
class OrderCreateRequest(CamelBaseModel):
    shipping_address: Address
    billing_address: Optional[Address] = None
    payment_method: str = "cod"  # 'cod', 'upi', or 'credit'
    upi_payment_screenshot: Optional[str] = None
    notes: Optional[str] = None
    coupon_code: Optional[str] = None  # Coupon code to apply
    referral_code: Optional[str] = None  # Referral code to apply
    discount: Optional[float] = 0
    printed_bill: Optional[bool] = False
    # [{productId, quantity}] - optional, if not provided uses user's cart
    items: Optional[List[OrderItemCreate]] = None
    is_urgent_delivery: Optional[bool] = False
    delivery_slot_id: Optional[str] = None  # slot.id within a slot config
    # _id of the DeliverySlotConfig doc
    delivery_slot_config_id: Optional[str] = None
    delivery_slot_date: Optional[str] = None  # ISO date string e.g. "2026-07-15"
    # Per-seller delivery options for split-cart orders
    # [{sellerId, isUrgentDelivery, deliverySlotId, deliverySlotConfigId, deliverySlotDate}]
    seller_delivery_options: Optional[List[SellerDeliveryOption]] = None



class OrderStatusUpdate(BaseModel):
    status: str


class AssignValetRequest(BaseModel):
    valetId: str


class ConfirmPickupRequest(BaseModel):
    """Sent by valet when physically collecting items from a seller's location."""

    notes: Optional[str] = None








@router.get("", response_model=PaginatedOrdersResponse)
@router.get("/", response_model=PaginatedOrdersResponse)
async def get_orders(
    status: Optional[str] = None,
    paymentMethod: Optional[str] = None,
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    page: Optional[int] = None,
    limit: Optional[int] = None,
    assignedValet: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    query = {}

    # Role-based filtering
    if current_user.role in ["customer", "wholesaler"]:
        query["user"] = str(current_user.id)
    elif current_user.role == "valet":
        query["assignedValet"] = str(current_user.id)
    elif current_user.role == "seller":
        query["subOrders.seller_id"] = str(current_user.id)
    # Super admin sees all orders; optionally filter by assignedValet
    elif current_user.role == "super_admin" and assignedValet:
        query["assignedValet"] = assignedValet

    if status:
        query["status"] = status
    if paymentMethod:
        query["paymentMethod"] = paymentMethod
    if startDate:
        query["startDate"] = startDate
    if endDate:
        query["endDate"] = endDate

    total = await order_repository.count(query)

    page = max(1, page or 1)
    limit = limit or 50
    start = (page - 1) * limit
    orders = await order_repository.findAll(query, skip=start, limit=limit)
    has_more = (start + limit) < total

    populated_orders = await populate_orders(orders)

    return PaginatedOrdersResponse(
        orders=populated_orders,
        totalCount=total,
        page=page,
        limit=limit
    )


@router.post("", response_model=PopulatedOrderResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=PopulatedOrderResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_order(
    request: Request,
    order_data: OrderCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    return await create_order_service(
        order_data=order_data,
        current_user=current_user,
        idempotency_key=idempotency_key,
        background_tasks=background_tasks,
    )




class TrackingUpdateRequest(BaseModel):
    trackingId: str
    courierPartner: Optional[str] = None


@router.put("/{order_id}/tracking")
async def update_order_tracking(
    order_id: str,
    data: TrackingUpdateRequest,
    current_user: User = Depends(require_super_admin_or_seller),
):
    """Set tracking ID and courier partner on an order (admin or seller)."""
    order = await order_repository.findById(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Sellers can only update their own sub-orders' parent orders
    if is_seller_admin(current_user):
        seller_id = str(current_user.id)
        sub_order_ids = order.sub_order_ids or []
        seller_has_sub = False
        for so_id in sub_order_ids:
            so = await sub_order_repository.findById(so_id)
            if so and str((so.seller_id or "")) == seller_id:
                seller_has_sub = True
                break
        if not seller_has_sub:
            raise HTTPException(
                status_code=403, detail="You do not have a sub-order in this order")

    await order_repository.update(order_id, OrderInternalUpdate(
        trackingId=data.trackingId,
        courierPartner=data.courierPartner,
        trackingUpdatedAt=__import__("datetime").datetime.now(
            __import__("datetime").timezone.utc).isoformat() + "Z"
    ))

    # Notify customer — in-app notification + push
    try:
        from app.utils.notify import notify_user
        order_num = order.order_number if order.order_number is not None else order_id
        await notify_user(
            user_id    = str(order.user),
            notif_type = "order_shipped",
            title      = "Order Shipped 📦",
            message    = f"Your order #{order_num} has been shipped. Tracking ID: {data.trackingId}",
            link       = f"/customer/orders/{order_id}",
            metadata   = {"order_id": str(order_id), "status": "shipped"},
        )
    except Exception as _ne:
        logger.warning(
            "Tracking notification failed for order %s: %s", order_id, _ne)

    return {"message": "Tracking updated", "trackingId": data.trackingId, "courierPartner": data.courierPartner}


class UpdateDeliveryChargeRequest(BaseModel):
    newDeliveryCharge: float


@router.put("/{order_id}/delivery-charge", response_model=DeliveryChargeUpdateResponse)
async def update_delivery_charge(
    order_id: str, request: UpdateDeliveryChargeRequest, current_user: User = Depends(require_super_admin)
):
    """Update delivery charge for an order (wholesaler only, before dispatch)"""
    # Get order
    order = await order_repository.findById(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Only allow for wholesaler/retailer orders
    user = await user_repository.findById(order.user)
    if not user or user.role != "wholesaler":
        raise HTTPException(
            status_code=403, detail="Can only update delivery charge for business customer orders")

    # Only allow before dispatch
    if order.status not in ["pending", "confirmed", "processing"]:
        raise HTTPException(
            status_code=400, detail="Can only update delivery charge before order is dispatched")

    new_delivery_charge = request.newDeliveryCharge
    old_delivery_charge = (order.shipping if order.shipping is not None else 0)
    difference = new_delivery_charge - old_delivery_charge

    if difference == 0:
        raise HTTPException(
            status_code=400, detail="New delivery charge is same as current charge")

    # Update order totals
    new_total = (order.total if order.total is not None else 0) + difference

    await order_repository.update(order_id, OrderInternalUpdate(shipping=new_delivery_charge, total=new_total))

    # Update payment record based on payment method
    payments = await payment_repository.findByOrderId(order_id)
    if payments and len(payments) > 0:
        payment = payments[0]
        payment_method = (
            order.payment_method if order.payment_method is not None else "cod")

        if payment_method == "upi":
            # For UPI: Update amount remaining (to be settled during delivery as COD)
            new_amount_remaining = (
                payment.amount_remaining if payment.amount_remaining is not None else 0) + difference
            await payment_repository.update(
                payment.id, {"totalAmount": new_total,
                             "amountRemaining": new_amount_remaining}
            )
        elif payment_method in ["credit", "cod"]:
            # For Credit/COD: Update amount remaining
            new_amount_remaining = (
                payment.amount_remaining if payment.amount_remaining is not None else 0) + difference
            await payment_repository.update(
                payment.id, {"totalAmount": new_total,
                             "amountRemaining": new_amount_remaining}
            )

    # Get updated order
    updated_order = await order_repository.findById(order_id)
    populated_order = await populate_order(updated_order)

    return {
        "message": "Delivery charge updated successfully",
        "order": populated_order,
        "difference": difference,
        "oldDeliveryCharge": old_delivery_charge,
        "newDeliveryCharge": new_delivery_charge,
    }




@router.put("/{order_id}/status", response_model=PopulatedOrderResponse)
async def update_order_status(
    order_id: str,
    status_data: OrderStatusUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_super_admin_or_valet),
):
    order = await order_repository.findById(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    update_data = {"status": status_data.status}

    # Valet can only mark orders as delivered (any payment method)
    if current_user.role == "valet":
        if status_data.status != "delivered":
            raise HTTPException(
                status_code=403, detail="Valet can only mark orders as delivered")
        if order.assigned_valet != current_user.id:
            raise HTTPException(
                status_code=403, detail="Order not assigned to you")

        # ── Pickup gate: for multi-seller orders, ALL sub-orders must be picked up ──
        # NOTE: hasSubOrders/subOrderIds not in relational DB — query sub-orders directly.
        all_sub_orders = await sub_order_repository.findByParentOrder(order_id)
        if all_sub_orders:
            not_picked_up = [
                so.sub_order_number or so.id
                for so in all_sub_orders
                if so.pickup_status != "picked_up"
            ]
            if not_picked_up:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Cannot mark as delivered: pickup not yet confirmed for "
                        f"{len(not_picked_up)} seller(s): {', '.join(str(x) for x in not_picked_up)}"
                    ),
                )
        # For COD orders, payment status changes to paid when delivered
        if order.payment_method == "cod":
            from datetime import datetime

            update_data.payment_status = "paid"
            update_data.codPaymentReceived = True
            update_data.codPaymentReceivedAt = datetime.now(
                __import__("datetime").timezone.utc).isoformat()

    if status_data.status == "out_for_delivery":
        update_data.shippedAt = None  # Will be set by repository
    elif status_data.status == "delivered":
        from datetime import datetime

        # Increment deliveredCount on the slot

        if order.payment_method == "cod" and "paymentStatus" not in update_data:
            update_data.payment_status = "paid"
            update_data.codPaymentReceived = True
            update_data.codPaymentReceivedAt = datetime.now(
                __import__("datetime").timezone.utc).isoformat()

            # Create or update payment record for COD
            existing_payment = await payment_repository.findByOrderId(order.id)
            if existing_payment and len(existing_payment) > 0:
                payment = existing_payment[0]
                # Check if payment entry exists, if not add one
                if payment.payment_entries and len((payment.payment_entries or [])) > 0:
                    # Update existing payment entry
                    await payment_repository.updatePaymentEntry(
                        payment.id,
                        payment.payment_entries[0].entryId,
                        {"amount": order.total or payment.total_amount,
                            "verified": False},
                    )
                    updated_payment = await payment_repository.update(
                        payment.id,
                        {"amountPaid": order.total or payment.total_amount,
                            "amountRemaining": 0},
                    )
                    # Create notification for COD payment
                    await create_payment_notification(updated_payment)
                else:
                    # Add new payment entry for COD payment received
                    updated_payment_with_entry = await payment_repository.addPaymentEntry(
                        payment.id,
                        PaymentEntryInternal(amount=order.total or payment.total_amount, image=None, verified=False),
                    )
                    # Create notification for COD payment
                    await create_payment_notification(
                        {
                            "_id": updated_payment_with_entry.id,
                            "paymentId": updated_payment_with_entry.paymentId,
                            "orderId": updated_payment_with_entry.order_id,
                            "totalAmount": (order.total if order.total is not None else payment.total_amount),
                            "paymentMethod": "cod",
                            "createdAt": datetime.now(__import__("datetime").timezone.utc).isoformat() + "Z",
                        }
                    )
            else:
                # Create new payment record (should already exist, but handle edge case)
                user = await user_repository.findById(order.user)
                new_payment = await payment_repository.create(
                    {
                        "orderId": order.id,
                        "userId": user.user_id if user else None,  # Use userId instead of customerId
                        "customerName": user.name if user else "Unknown",
                        "orderDate": order.created_at if isinstance(order.created_at, str) else str(order.created_at),
                        "paymentMethod": "cod",
                        "totalAmount": (order.total if order.total is not None else 0),
                        "amountPaid": (order.total if order.total is not None else 0),
                        "amountRemaining": 0,
                        "paymentEntries": [
                            {
                                "entryId": 1,
                                "amount": (order.total if order.total is not None else 0),
                                "image": None,
                                "verified": False,
                                "createdAt": datetime.now(__import__("datetime").timezone.utc).isoformat(),
                            }
                        ],
                    }
                )
                # Create notification for COD payment
                await create_payment_notification(
                    {
                        "_id": new_payment.id,
                        "paymentId": new_payment.paymentId,
                        "orderId": new_payment.order_id,
                        "totalAmount": new_payment.total_amount,
                        "paymentMethod": "cod",
                        "createdAt": datetime.now(__import__("datetime").timezone.utc).isoformat() + "Z",
                    }
                )
    elif status_data.status == "cancelled":
        # Guard: prevent re-cancelling a terminal order which would double-restore stock/credit.
        _TERMINAL_STATUSES = {"cancelled", "declined",
                              "delivered", "returned", "failed"}
        if order.status in _TERMINAL_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel an order that is already in '{order.status}' state",
            )
        # For cancelled orders, restore stock and refund credit if credit payment
        if order.payment_method == "credit":
            user = await user_repository.findById(order.user)
            if user and user.credit_used:
                if user.credit_used is None or order.total is None:
                    raise ValueError(
                        "Cannot calculate credit usage: credit_used or total is None")
                new_credit_used = max(0, user.credit_used - order.total)
                await user_repository.update(order.user, UserInternalUpdate(creditUsed=new_credit_used))

        # Restore stock atomically — uses SELECT … FOR UPDATE so a concurrent new order
        # cannot race against this restoration and produce a wrong stock count.
        for item in (order.items or []):
            if item.product and item.quantity:
                await product_repository.increment_stock_atomic(str(item.product), int((item.quantity if item.quantity is not None else 0)))

        from datetime import datetime

        update_data.cancelledAt = datetime.now(
            __import__("datetime").timezone.utc).isoformat()
        update_data.cancelledBy = current_user.id

        # Mark existing payment as cancelled (do NOT create new records or mark as paid)
        existing_payments_cancel = await payment_repository.findByOrderId(order_id)
        if existing_payments_cancel:
            pay = existing_payments_cancel[0]
            await payment_repository.update(
                pay.id,
                {"paymentStatus": "cancelled", "amountRemaining": 0},
            )

    updated_order = await order_repository.update(order_id, OrderInternalUpdate.model_validate(update_data))
    populated_order = await populate_order(updated_order)

    # ── C5: Cascade terminal status from parent to sub-orders ─────────────────
    if status_data.status in ("cancelled", "delivered"):
        from datetime import datetime as _dt

        sub_ids = updated_order.sub_order_ids if updated_order.sub_order_ids else []
        for _so_id in sub_ids:
            _so = await sub_order_repository.findById(_so_id)
            if not _so:
                continue
            # Skip sub-orders already in a terminal state
            if _so.status in ("delivered", "cancelled", "returned"):
                continue
            if status_data.status == "cancelled":
                await sub_order_repository.update(
                    _so_id, SubOrderInternalUpdate(status="cancelled",
                                                   cancelledAt=_dt.utcnow().isoformat() + "Z",),
                )
            elif status_data.status == "delivered":
                _cascade = {
                    "status": "delivered",
                    "deliveredAt": _dt.utcnow().isoformat() + "Z",
                }
                # Stamp commission on delivery for each sub-order
                try:
                    from app.routers.commission import stamp_commission_on_delivery

                    _comm = await stamp_commission_on_delivery(_so)
                    _cascade.update(_comm)
                except Exception as _ce:
                    logger.warning(
                        "Commission stamp failed for sub-order %s: %s", _so_id, _ce)
                await sub_order_repository.update(_so_id, SubOrderInternalUpdate.model_validate(_cascade))

    # Recompute parent fulfillmentStatus from all sub-orders
    sub_ids = updated_order.sub_order_ids if updated_order.sub_order_ids else []

    # Recompute overall fulfillment status based on sub-orders
    _f_status = await _compute_fulfillment_status(sub_ids)
    if _f_status and _f_status != updated_order.status:
        updated_order = await order_repository.update(order_id, OrderInternalUpdate(status=_f_status))
        sub_ids = updated_order.sub_order_ids if updated_order.sub_order_ids else []

    # Send status change email notification
    populated_order = await populate_order(updated_order)
    if populated_order:
        email = populated_order.user.email if (
            populated_order.user and populated_order.user.email) else None
        if email:
            background_tasks.add_task(
                email_service.send_order_status_email, email, populated_order)

    # ────────────────────────────────────────────────────────────────
    # RETAIL INVOICE GENERATION
    # ────────────────────────────────────────────────────────────────
    # Automatically generate an invoice when a retail order is delivered.
    # (Wholesaler invoices are generated separately)
    if status_data.status == "delivered":
        order_user = await user_repository.findById(updated_order.user)
        # Check if it's retail and hasn't been generated yet
        if order_user and order_user.role == "customer" and not updated_order.invoicePath:
            try:
                payments_for_order = await payment_repository.findByOrderId(order_id)
                payment_for_invoice = payments_for_order[0] if payments_for_order else None
                super_admin = await user_repository.findOne({"role": "super_admin"})
                pdf_buffer = await generate_invoice_pdf(
                    populated_order,
                    payment_for_invoice,
                    {
                        "name": (super_admin.name if super_admin.name is not None else "Stationery Junction")
                        if super_admin
                        else "Stationery Junction",
                        "companyName": (super_admin.company_name or "") if super_admin else "",
                        "gstin": (super_admin.gstin or "") if super_admin else "",
                        "address": (super_admin.address or {}) if super_admin else {},
                    },
                )
                invoice_path = await save_invoice_pdf(pdf_buffer, order_id)
                await order_repository.update(
                    order_id,
                    OrderInternalUpdate(
                        invoicePath=invoice_path, invoiceGeneratedAt=_dt.utcnow().isoformat() + "Z"),
                )
                # Refresh populated_order so the returned object has the invoice path
                updated_order = await order_repository.findById(order_id)
                populated_order = await populate_order(updated_order)
            except Exception as invoice_error:
                logger.error(
                    "Error auto-generating invoice on delivery for order %s: %s",
                    order_id,
                    str(invoice_error),
                    exc_info=True,
                )
                # Don't fail delivery status update if invoice generation fails

    return populated_order


@router.put("/{order_id}/accept", response_model=PopulatedOrderResponse)
async def accept_order(order_id: str, current_user: User = Depends(require_super_admin)):
    """Accept order (Pending -> Processing)"""
    order = await order_repository.findById(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "pending":
        raise HTTPException(
            status_code=400, detail="Only pending orders can be accepted")

    # UPI orders must have a verified payment entry before acceptance
    if order.payment_method == "upi":
        payments = await payment_repository.findByOrderId(order_id)
        payment = payments[0] if payments else None
        entries = (payment.payment_entries or []) if payment else []
        any_verified = any(entry.verified for entry in entries)
        if not any_verified:
            raise HTTPException(
                status_code=400, detail="UPI payment must be verified before accepting the order")

    updated_order = await order_repository.update(order_id, OrderInternalUpdate(status="processing"))

    populated_order = await populate_order(updated_order)
    return populated_order


class DeclineOrderRequest(BaseModel):
    reason: str


@router.put("/{order_id}/decline", response_model=PopulatedOrderResponse)
async def decline_order(
    order_id: str, decline_data: DeclineOrderRequest, current_user: User = Depends(require_super_admin)
):
    """Decline order (with reason, only COD/Credit)"""
    order = await order_repository.findById(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.payment_method == "upi":
        raise HTTPException(
            status_code=400, detail="UPI orders cannot be declined")

    if order.payment_method not in ["cod", "credit"]:
        raise HTTPException(
            status_code=400, detail="Only COD and Credit orders can be declined")

    if order.status != "pending":
        raise HTTPException(
            status_code=400, detail="Only pending orders can be declined")

    # For credit orders, refund credit used
    if order.payment_method == "credit":
        user = await user_repository.findById(order.user)
        if user and user.credit_used:
            if user.credit_used is None or order.total is None:
                raise ValueError(
                    "Cannot calculate credit usage: credit_used or total is None")
            new_credit_used = max(0, user.credit_used - order.total)
            await user_repository.update(order.user, UserInternalUpdate(creditUsed=new_credit_used))

    # Restore stock atomically — uses SELECT … FOR UPDATE so a concurrent new order
    # cannot race against this restoration and produce a wrong stock count.
    for item in (order.items or []):
        if item.product and item.quantity:
            await product_repository.increment_stock_atomic(str(item.product), int((item.quantity if item.quantity is not None else 0)))

    updated_order = await order_repository.update(
        order_id, OrderInternalUpdate(
            status="declined", declineReason=decline_data.reason)
    )

    populated_order = await populate_order(updated_order)
    return populated_order


@router.put("/{order_id}/dispatch", response_model=PopulatedOrderResponse)
async def dispatch_order(
    order_id: str,
    valet_data: AssignValetRequest,
    current_user: User = Depends(require_super_admin_or_seller),
):
    """
    Dispatch order: moves status from 'processing' -> 'pending_valet'.
    Notifies the chosen valet via push notification.
    The order only moves to 'shipped' once the valet explicitly accepts.
    Accessible by Super Admin or Seller Admin (sellers can only dispatch their own orders).
    """
    order = await order_repository.findById(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Sellers can only dispatch orders that belong to them
    if is_seller_admin(current_user):
        if str((order.seller_id or "")) != str(current_user.id):
            raise HTTPException(
                status_code=403, detail="You can only dispatch your own orders")

    if order.status != "processing":
        raise HTTPException(
            status_code=400, detail="Only processing orders can be dispatched")

    valet = await user_repository.findById(valet_data.valet_id)
    if not valet or valet.role != "valet":
        raise HTTPException(status_code=400, detail="Invalid valet")

    from datetime import datetime

    now_iso = datetime.now(__import__(
        "datetime").timezone.utc).isoformat() + "Z"
    is_urgent = (
        order.is_urgent_delivery if order.is_urgent_delivery is not None else False)
    timeout_minutes = 5 if is_urgent else 20

    updated_order = await order_repository.update(
        order_id,
        OrderInternalUpdate(status="pending_valet",
                            pendingValetId=valet_data.valet_id,
                            valetAssignedAt=now_iso,
                            valetDeclineHistory=[],
                            valetCascadeCount=0,),
    )

    # Push notification to the valet
    try:
        from app.services.push_notification_service import push_notification_service

        timeout_label = "5 minutes" if is_urgent else "20 minutes"
        await push_notification_service.send_to_user(valet_data.valet_id, PushNotifications(
            title="New Delivery Request",
            message=(
                f"You have a new delivery order #{(order.order_number if order.order_number is not None else order_id)}. "
                f"Please respond within {timeout_label}."
            ),
            link=f"/valet/orders/{order_id}",
        ))
    except Exception as push_err:
        logger.warning(
            "[Dispatch] Push notification to valet failed: %s", push_err)
        # Non-fatal — order is already in pending_valet state

    populated_order = await populate_order(updated_order)
    return populated_order


@router.get("/valet/pending", response_model=List[Order])
async def get_valet_pending_orders(current_user: User = Depends(get_current_user)):
    if current_user.role != "valet":
        raise HTTPException(
            status_code=403, detail="Only valets can view pending assignments")
    orders = await order_repository.findAll({
        "status": "pending_valet",
        "pendingValetId": str(current_user.id)
    })
    return [await populate_order(o) for o in orders]


# ── DUPLICATE ROUTE — COMMENTED OUT ──────────────────────────────────────────
# This block was shadowing the correct multi-seller valet_response implementation
# below (line ~2266). FastAPI matches routes in registration order, so this
# simpler version (accept: bool) was intercepting every request and the full
# multi-seller propagation logic was never reached.
# The correct implementation uses { "action": "accept" | "decline" } and is
# defined further below with require_super_admin_or_valet and the full
# hasSubOrders sub-order propagation logic.
# DO NOT re-enable this block without removing the duplicate below.
#
# class ValetResponseRequest(BaseModel):
    #     accept: bool
#     declineReason: Optional[str] = None
#
#
# @router.put("/{order_id}/valet-response", response_model=PopulatedOrderResponse)
# async def valet_response(
#     order_id: str,
#     response_data: ValetResponseRequest,
#     current_user: User = Depends(get_current_user),
# ):
#     order = await order_repository.findById(order_id)
#     if not order:
#         raise HTTPException(status_code=404, detail="Order not found")
#
#     if current_user.role != "super_admin":
#         if current_user.role != "valet":
#             raise HTTPException(status_code=403, detail="Access denied")
#         if str((order.pending_valet_id or "")) != str(current_user.id):
#             raise HTTPException(status_code=403, detail="Order is not assigned to you")
#
#     if order.status != "pending_valet":
#         raise HTTPException(status_code=400, detail="Order is not pending valet acceptance")
#
#     from datetime import datetime, timezone
#     now_iso = datetime.now(__import__("datetime").timezone.utc).isoformat() + "Z"
#
#     if response_data.accept:
#         # Generate Invoice
#         from app.routers.invoices import _generate_b2b_invoice_pdf
#         try:
#             invoice = await _generate_b2b_invoice_pdf(order_id)
#         except Exception:
#             invoice = None
#
#         updated_order = await order_repository.update(order_id, OrderInternalUpdate(#             status="shipped",
#             assignedValet=str(current_user.id),
#             pendingValetId=None,
#             shippedAt=now_iso,
#             invoiceUrl=invoice.url if invoice else None
# ))
#         # Notify seller
#         seller_id = order.seller_id
#         if seller_id:
#             try:
#                 from app.services.push_notification_service import push_notification_service
#                 await push_notification_service.send_to_user(
#                     seller_id,
#                     {
#                         "title": "Valet Accepted",
#                         "message": f"Valet has accepted order #{(order.order_number if order.order_number is not None else order_id)} and it is now shipped.",
#                         "link": f"/seller/orders/{order_id}",
#                     }
#                 )
#             except Exception:
#                 pass
#         return await populate_order(updated_order)
#     else:
#         # Declined -> Cascade
#         history = list(order.valet_decline_history or [])
#         valet_id_str = str(current_user.id)
#         if valet_id_str not in history:
#             history.append(valet_id_str)
#
#         await order_repository.update(order_id, OrderInternalUpdate(#             valetDeclineHistory=history,
#             pendingValetId=None
# ))
#         order.valetDeclineHistory = history
#         order.pending_valet_id = None
#
#         from app.jobs.valet_timeout_job import _cascade_or_revert
#         await _cascade_or_revert(order)
#         return await populate_order(await order_repository.findById(order_id))
# ── END DUPLICATE ROUTE ───────────────────────────────────────────────────────


@router.put("/{order_id}/cancel", response_model=PopulatedOrderResponse)
async def cancel_order(order_id: str, current_user: User = Depends(get_current_user)):
    """Cancel order (Customer/Wholesaler only, before Accept)"""
    order = await order_repository.findById(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Check access - only order owner can cancel
    if order.user != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Only COD/Credit orders can be cancelled
    if order.payment_method not in ["cod", "credit"]:
        raise HTTPException(
            status_code=400, detail="Only COD and Credit orders can be cancelled")

    # Orders can only be cancelled before they are Accepted (status is still 'pending')
    if order.status != "pending":
        raise HTTPException(
            status_code=400, detail="Orders can only be cancelled before they are accepted")

    # For credit orders, refund credit used
    if order.payment_method == "credit":
        user = await user_repository.findById(order.user)
        if user and user.credit_used:
            if user.credit_used is None or order.total is None:
                raise ValueError(
                    "Cannot calculate credit usage: credit_used or total is None")
            new_credit_used = max(0, user.credit_used - order.total)
            await user_repository.update(order.user, UserInternalUpdate(creditUsed=new_credit_used))

    # Restore stock atomically — uses SELECT … FOR UPDATE so a concurrent new order
    # cannot race against this restoration and produce a wrong stock count.
    for item in (order.items or []):
        if item.product and item.quantity:
            await product_repository.increment_stock_atomic(str(item.product), int((item.quantity if item.quantity is not None else 0)))

    from datetime import datetime

    updated_order = await order_repository.update(
        order_id,
        OrderInternalUpdate(status="cancelled", cancelledAt=datetime.now(
            __import__("datetime").timezone.utc).isoformat(), cancelledBy=current_user.id),
    )

    populated_order = await populate_order(updated_order)
    return populated_order


@router.put("/{order_id}/assign-valet", response_model=PopulatedOrderResponse)
async def assign_valet(
    order_id: str, valet_data: AssignValetRequest, current_user: User = Depends(require_super_admin)
):
    order = await order_repository.findById(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    valet = await user_repository.findById(valet_data.valet_id)
    if not valet or valet.role != "valet":
        raise HTTPException(status_code=400, detail="Invalid valet")

    updated_order = await order_repository.update(order_id, OrderInternalUpdate(assignedValet=valet_data.valet_id))

    populated_order = await populate_order(updated_order)
    return populated_order


# ─── Valet Response (Accept / Decline) ───────────────────────────────────────


class ValetResponseRequest(BaseModel):
    action: str  # "accept" | "decline"
    declineReason: Optional[str] = None


@router.put("/{order_id}/valet-response", response_model=PopulatedOrderResponse)
async def valet_response(
    order_id: str,
    response_data: ValetResponseRequest,
    current_user: User = Depends(require_super_admin_or_valet),
):
    """
    Valet accepts or declines an assigned order.
    - Accept: moves order to 'shipped', notifies seller.
    - Decline: auto-cascades to next eligible valet (or reverts to 'processing').
    """
    from datetime import datetime, timedelta

    if response_data.action not in ("accept", "decline"):
        raise HTTPException(
            status_code=400, detail="action must be 'accept' or 'decline'")

    order = await order_repository.findById(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "pending_valet":
        raise HTTPException(
            status_code=400, detail="Order is not awaiting valet confirmation")

    # Valets can only respond to orders assigned to them
    if current_user.role == "valet":
        if str((order.pending_valet_id or "")) != str(current_user.id):
            raise HTTPException(
                status_code=403, detail="This order is not assigned to you")

    # Check if the offer window has expired
    assigned_at_str = (order.valet_assigned_at or "")
    is_urgent = (
        order.is_urgent_delivery if order.is_urgent_delivery is not None else False)
    timeout_minutes = 5 if is_urgent else 20
    if assigned_at_str:
        try:
            assigned_at = datetime.fromisoformat(
                assigned_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
            if datetime.now(__import__("datetime").timezone.utc) >= assigned_at + timedelta(minutes=timeout_minutes):
                raise HTTPException(
                    status_code=400,
                    detail="The acceptance window for this order has expired",
                )
        except HTTPException:
            raise
        except Exception as e:
            logging.warning("orders: could not parse assigned_at for acceptance window check on order %r; skipping timeout check: %s", getattr(order, 'id', '?'), e, exc_info=e)

    now_iso = datetime.now(__import__(
        "datetime").timezone.utc).isoformat() + "Z"
    valet_id = str(current_user.id) if current_user.role == "valet" else str(
        (order.pending_valet_id or ""))
    seller_id = order.seller_id

    # ── ACCEPT ────────────────────────────────────────────────────────────────
    if response_data.action == "accept":
        updated_order = await order_repository.update(
            order_id,
            OrderInternalUpdate(status="shipped",
                                assignedValet=valet_id,
                                pendingValetId=None,
                                valetAcceptedAt=now_iso,
                                shippedAt=now_iso,),
        )

        # Fetch valet details once for notifications
        valet = await user_repository.findById(valet_id)
        valet_name = (
            valet.name if valet.name is not None else "The valet") if valet else "The valet"

        # ── Multi-seller: propagate assignedValet to all sub-orders, notify each seller ──
        # NOTE: hasSubOrders/subOrderIds not in relational DB — query sub-orders directly.
        sub_orders_for_order = await sub_order_repository.findByParentOrder(order_id)
        if sub_orders_for_order:
            notified_sellers: set = set()
            for _so in sub_orders_for_order:
                _so_id = str(_so.id)
                # Set assignedValet on each sub-order so sellers can see who's picking up
                await sub_order_repository.update(
                    _so_id, SubOrderInternalUpdate(assignedValet=valet_id,
                                                   pickupStatus="pending_pickup",),
                )
                _seller_id = _so.seller_id
                if _seller_id and _seller_id not in notified_sellers:
                    notified_sellers.add(_seller_id)
                    try:
                        from app.services.push_notification_service import push_notification_service

                        await push_notification_service.send_to_user(_seller_id, PushNotifications(
                            title="Valet is Coming to Pick Up",
                            message=(
                                f"{valet_name} accepted order #{(order.order_number if order.order_number is not None else order_id)} "
                                "and will collect your items soon."
                            ),
                            link=f"/seller/orders/{order_id}",
                        ))
                    except Exception as e:
                        logger.warning(
                            "[ValetResponse] Push to seller %s failed: %s", _seller_id, e)
        else:
            # Single-seller: notify the order's seller as before
            if seller_id:
                try:
                    from app.services.push_notification_service import push_notification_service

                    await push_notification_service.send_to_user(
                        seller_id,
                        PushNotifications(
                            title="Order Dispatched",
                            message=f"{valet_name} accepted order #{(order.order_number if order.order_number is not None else order_id)} and is on the way.",
                            link=f"/seller/orders/{order_id}"
                        ),
                    )
                except Exception as e:
                    logger.warning(
                        "[ValetResponse] Push to seller failed: %s", e)

        # Auto-generate invoice for B2B orders on accept
        order_user = await user_repository.findById(updated_order.user)
        if order_user and order_user.role == "wholesaler":
            try:
                payments = await payment_repository.findByOrderId(updated_order.id)
                payment_record = payments[0] if payments else None
                if payment_record:
                    super_admin = await user_repository.findOne({"role": "super_admin"})
                    populated_for_invoice = await populate_order(updated_order)
                    pdf_buffer = await generate_invoice_pdf(
                        populated_for_invoice,
                        payment_record,
                        {
                            "name": (super_admin.name if super_admin.name is not None else "Stationery Junction")
                            if super_admin
                            else "Stationery Junction",
                            "companyName": (super_admin.company_name or "") if super_admin else "",
                            "gstin": (super_admin.gstin or "") if super_admin else "",
                            "address": (super_admin.address or {}) if super_admin else {},
                        },
                    )
                    invoice_path = await save_invoice_pdf(pdf_buffer, updated_order.id)
                    await order_repository.update(
                        updated_order.id,
                        OrderInternalUpdate(
                            invoicePath=invoice_path, invoiceGeneratedAt=now_iso),
                    )
            except Exception as invoice_err:
                logger.error(
                    "[ValetResponse] Invoice generation failed: %s", invoice_err)

        populated_order = await populate_order(updated_order)
        return populated_order

    # ── DECLINE ───────────────────────────────────────────────────────────────
    decline_history = list(order.valet_decline_history or [])
    if valet_id and not any(d.valet_id == valet_id for d in decline_history):
        from app.models.order import ValetDeclineHistoryEntry
        decline_history.append(ValetDeclineHistoryEntry(
            valetId=valet_id, reason="declined"))

    await order_repository.update(
        order_id,
        OrderInternalUpdate(valetDeclinedAt=now_iso,
                            valetDeclineReason=response_data.declineReason or "",
                            valetDeclineHistory=decline_history,
                            pendingValetId=None,
                            valetCascadeCount=(order.valet_cascade_count or 0) + 1,),
    )

    # Try to find the next available valet (cascade)
    from app.jobs.valet_timeout_job import _find_next_available_valet

    order_fresh = await order_repository.findById(order_id)
    next_valet = await _find_next_available_valet(order_fresh, decline_history)

    if next_valet:
        next_valet_id = str(next_valet.id)
        updated_order = await order_repository.update(
            order_id,
            OrderInternalUpdate(pendingValetId=next_valet_id,
                                valetAssignedAt=now_iso,),
        )
        # Notify next valet
        try:
            from app.services.push_notification_service import push_notification_service

            timeout_label = "5 minutes" if is_urgent else "20 minutes"
            await push_notification_service.send_to_user(next_valet_id, PushNotifications(
                title="New Delivery Request",
                message=(
                    f"You have a new delivery order #{(order.order_number if order.order_number is not None else order_id)}. "
                    f"Please respond within {timeout_label}."
                ),
                link=f"/valet/orders/{order_id}",
            ))
        except Exception as e:
            logger.warning("[ValetResponse] Push to next valet failed: %s", e)
    else:
        # No more valets — revert to processing
        updated_order = await order_repository.update(
            order_id,
            OrderInternalUpdate(status="processing",
                                pendingValetId=None, valetAssignedAt=None),
        )
        # Notify seller
        if seller_id:
            try:
                from app.services.push_notification_service import push_notification_service

                await push_notification_service.send_to_user(seller_id, PushNotifications(
                    title="No Valets Available — Reassign Required",
                    message=(
                        f"All valets declined order #{(order.order_number if order.order_number is not None else order_id)}. "
                        "Please assign a valet manually."
                    ),
                    link=f"/seller/orders/{order_id}",
                ))
            except Exception as e:
                logger.warning(
                    "[ValetResponse] Push to seller (all declined) failed: %s", e)

    populated_order = await populate_order(updated_order)
    return populated_order


# ─── Valet Confirms Pickup from a Seller (multi-seller orders) ────────────────


@router.put("/{order_id}/sub-orders/{sub_order_id}/confirm-pickup")
async def confirm_sub_order_pickup(
    order_id: str,
    sub_order_id: str,
    pickup_data: ConfirmPickupRequest,
    current_user: User = Depends(require_super_admin_or_valet),
):
    """
    Valet confirms physical collection of items from a single seller's location.
    When the last sub-order is picked up, the parent order automatically transitions
    to 'out_for_delivery' and the customer receives a push notification.
    Accessible by the assigned valet (or super admin).
    """
    order = await order_repository.findById(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Only the assigned valet (or super admin) may confirm pickups
    if current_user.role == "valet":
        if str((order.assigned_valet or "")) != str(current_user.id):
            raise HTTPException(
                status_code=403, detail="This order is not assigned to you")

    # Guard: order must be in 'shipped' state (valet accepted, pickups in progress)
    if order.status != "shipped":
        raise HTTPException(
            status_code=400,
            detail="Pickup can only be confirmed after the valet has accepted the order (status: shipped)",
        )

    # Verify the sub-order belongs to this parent
    sub_order = await sub_order_repository.findById(sub_order_id)
    if not sub_order:
        raise HTTPException(status_code=404, detail="Sub-order not found")
    if str((sub_order.parent_order_id or "")) != str(order_id):
        raise HTTPException(
            status_code=400, detail="Sub-order does not belong to this order")

    # Idempotency: already picked up
    if sub_order.pickup_status == "picked_up":
        raise HTTPException(
            status_code=400, detail="Pickup already confirmed for this seller")

    # Mark this sub-order as picked up (pickedUpAt is auto-stamped by the repository)
    await sub_order_repository.update(sub_order_id, SubOrderInternalUpdate(pickupStatus="picked_up"))

    # Re-fetch all sibling sub-orders to check if ALL pickups are done
    all_sub_orders = await sub_order_repository.findByParentOrder(order_id)
    remaining = [s for s in all_sub_orders if s.pickup_status != "picked_up"]

    # now_iso = datetime.now(__import__("datetime").timezone.utc).isoformat() + "Z"  # was a dangling no-op after find-and-replace stripped the assignment; unused in this block

    if not remaining:
        # ── All sellers picked up — transition parent to 'out_for_delivery' ──
        await order_repository.update(order_id, OrderInternalUpdate(status="out_for_delivery"))
        logger.info(
            "[ConfirmPickup] All %d sub-orders picked up for order %s — moving to out_for_delivery",
            len(all_sub_orders),
            order_id,
        )
        # Notify the customer — in-app notification + push
        try:
            from app.utils.notify import notify_user
            order_num = order.order_number if order.order_number is not None else order_id
            await notify_user(
                user_id    = str(order.user),
                notif_type = "order_out_for_delivery",
                title      = "Your Order is On the Way! 🚴",
                message    = (
                    f"Your order #{order_num} has been collected "
                    "from all sellers and is now heading to you."
                ),
                link       = f"/customer/orders/{order_id}",
                metadata   = {"order_id": str(order_id), "status": "out_for_delivery"},
            )
        except Exception as e:
            logger.warning(
                "[ConfirmPickup] Customer notification failed: %s", e)

        updated_order = await order_repository.findById(order_id)
    else:
        logger.info(
            "[ConfirmPickup] Sub-order %s picked up for order %s — %d seller(s) still pending",
            sub_order_id,
            order_id,
            len(remaining),
        )
        updated_order = order

    refreshed_sub = await sub_order_repository.findById(sub_order_id)
    return {
        "subOrder": refreshed_sub,
        "parentOrderStatus": updated_order.status,
        "pickupsRemaining": len(remaining),
        "allPickedUp": not remaining,
    }


class SettleCreditRequest(BaseModel):
    amount: float
    paymentImage: Optional[str] = None
    upiPaymentScreenshot: Optional[str] = None


@router.post("/{order_id}/settle-credit")
async def settle_credit(
    order_id: str, settle_data: SettleCreditRequest, current_user: User = Depends(get_current_user)
):
    """Submit a credit settlement for an order (wholesaler only).

    The payment entry is created as unverified.  creditUsed is NOT reduced here —
    it will only be reduced when a super-admin marks the entry as verified.
    This prevents wholesalers from restoring credit with fake/absent payment proofs.
    """

    order = await order_repository.findById(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Check access — order must belong to the requesting user
    if order.user != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Only credit orders can be settled this way
    if order.payment_method != "credit":
        raise HTTPException(
            status_code=400, detail="This order is not a credit order")

    user = await user_repository.findById(current_user.id)
    if user.role != "wholesaler":
        raise HTTPException(
            status_code=403, detail="Only business customers can settle credit")

    # Reject zero or negative settlement amounts
    settle_amount = float(settle_data.amount)
    if settle_amount <= 0:
        raise HTTPException(
            status_code=400, detail="Settlement amount must be greater than zero")

    # Find payment record
    payments = await payment_repository.findByOrderId(order_id)
    if not payments or len(payments) == 0:
        raise HTTPException(status_code=404, detail="Payment record not found")
    payment = payments[0]

    if payment.amount_paid is None:
        raise ValueError(
            "Cannot calculate remaining amount: amount_paid is None")
    remaining_amount = (
        payment.amount_remaining
        if payment.amount_remaining is not None
        else payment.total_amount - payment.amount_paid
    )

    if settle_amount > remaining_amount:
        raise HTTPException(
            status_code=400,
            detail=f"Amount cannot exceed remaining amount: ₹{remaining_amount:.2f}",
        )

    # Add payment entry as UNVERIFIED.
    # creditUsed is NOT reduced here — it will only be reduced when an admin
    # verifies this entry.  This is the critical security fix: previously the
    # credit balance was reduced immediately on an unverified submission.
    payment_image = settle_data.paymentImage or settle_data.upi_payment_screenshot
    await payment_repository.addPaymentEntry(
        payment.id, PaymentEntryInternal(amount=settle_amount, image=payment_image, verified=False)
    )

    updated_payment = await payment_repository.findById(payment.id)

    return {
        "message": "Settlement submitted successfully. Your credit balance will be updated once the payment is verified by our team.",
        "payment": updated_payment,
    }


@router.post("/{order_id}/generate-invoice", response_model=GenerateInvoiceResponse)
async def generate_invoice(order_id: str, current_user: User = Depends(require_super_admin)):
    """Generate invoice for an order (Super Admin only)"""
    from datetime import datetime

    order = await order_repository.findById(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Get payment information
    payments = await payment_repository.findByOrderId(order_id)
    payment = payments[0] if payments and len(payments) > 0 else None

    if not payment:
        raise HTTPException(
            status_code=400, detail="Payment record not found for this order")

    # Get seller (Super Admin) information
    super_admin = await user_repository.findOne({"role": "super_admin"})
    if not super_admin:
        raise HTTPException(status_code=500, detail="Super admin not found")

    # Populate order with user and product data
    populated_order = await populate_order(order)

    # Generate PDF
    pdf_buffer = await generate_invoice_pdf(
        populated_order,
        payment,
        {
            "name": (super_admin.name if super_admin.name is not None else "Stationery Junction"),
            "companyName": (super_admin.company_name or ""),
            "gstin": (super_admin.gstin or ""),
            "address": (super_admin.address or {}),
        },
    )

    # Save PDF
    invoice_path = await save_invoice_pdf(pdf_buffer, order_id)

    # Update order with invoice path
    await order_repository.update(
        order_id, OrderInternalUpdate(invoicePath=invoice_path, invoiceGeneratedAt=datetime.now(
            __import__("datetime").timezone.utc).isoformat() + "Z")
    )

    return {"message": "Invoice generated successfully", "invoicePath": invoice_path}


@router.get("/{order_id}/invoice", response_class=FileResponse)
async def download_invoice(order_id: str, current_user: User = Depends(get_current_user)):
    """Download invoice PDF for an order"""
    from pathlib import Path

    from fastapi.responses import FileResponse

    from app.utils.file_storage import DATA_DIR

    order = await order_repository.findById(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Check authorization - user must be order owner or super admin
    is_owner = order.user == current_user.id
    is_super_admin = current_user.role == "super_admin"

    if not is_owner and not is_super_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    if not order.invoice_path:
        raise HTTPException(
            status_code=404, detail="Invoice not generated yet")

    invoice_path_str = order.invoice_path
    if invoice_path_str.startswith("/uploads/"):
        # Legacy path: was stored as /uploads/{env}/invoices/filename.pdf
        # Resolve relative to the backend root (parent of DATA_DIR's parent)
        file_path = Path(DATA_DIR).parent / invoice_path_str.lstrip("/")
    else:
        # New private path: stored as invoices/{env}/filename.pdf
        file_path = Path(DATA_DIR) / invoice_path_str

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Invoice file not found")

    return FileResponse(
        str(file_path), media_type="application/pdf", filename=f"invoice-{(order.order_number if order.order_number is not None else order_id)}.pdf"
    )


# ─── Seller Admin Order Endpoints ───


@router.get("/seller-orders", response_model=PaginatedSubOrdersResponse)
async def get_seller_orders(
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(require_seller_admin),
):
    """List sub-orders for the calling seller admin (Seller Admin only)."""
    seller_id = str(current_user.id)
    query: dict = {}
    if status:
        # was query.status = status (dict has no .status attribute)
        query["status"] = status
    skip = (page - 1) * limit
    sub_orders = await sub_order_repository.findBySeller(seller_id, query, skip=skip, limit=limit)
    total = await sub_order_repository.count({"seller_id": seller_id, **query})
    return {
        "subOrders": sub_orders,
        "totalCount": total,
        "page": page,
        "limit": limit,
    }


@router.get("/seller-orders/{sub_order_id}", response_model=SubOrder)
async def get_seller_order(
    sub_order_id: str,
    current_user: User = Depends(require_seller_admin),
):
    """Get a single sub-order (Seller Admin only — must own the sub-order)."""
    sub_order = await sub_order_repository.findById(sub_order_id)
    if not sub_order:
        raise HTTPException(status_code=404, detail="Sub-order not found")
    if str(sub_order.seller_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied.")
    return sub_order


class SubOrderStatusUpdate(BaseModel):
    status: str


@router.put("/seller-orders/{sub_order_id}/status", response_model=SubOrder)
async def update_seller_order_status(
    sub_order_id: str,
    status_data: SubOrderStatusUpdate,
    current_user: User = Depends(require_seller_admin),
):
    """Update sub-order status (Seller Admin only — must own the sub-order)."""
    sub_order = await sub_order_repository.findById(sub_order_id)
    if not sub_order:
        raise HTTPException(status_code=404, detail="Sub-order not found")
    if str(sub_order.seller_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied.")

    allowed_statuses = ["pending", "confirmed", "processing",
                        "shipped", "out_for_delivery", "delivered", "cancelled"]
    if status_data.status not in allowed_statuses:
        raise HTTPException(
            status_code=400, detail=f"Invalid status. Allowed: {', '.join(allowed_statuses)}")

    from datetime import datetime as _dt

    internal_update = SubOrderInternalUpdate(status=status_data.status)
    if status_data.status == "delivered":
        internal_update.deliveredAt = _dt.utcnow().isoformat() + "Z"
        try:
            from app.routers.commission import stamp_commission_on_delivery

            _comm = await stamp_commission_on_delivery(sub_order)
            if "commissionPct" in _comm:
                internal_update.commissionPct = _comm["commissionPct"]
            if "commissionAmount" in _comm:
                internal_update.commissionAmount = _comm["commissionAmount"]
            if "commissionStatus" in _comm:
                internal_update.commissionStatus = _comm["commissionStatus"]
        except Exception as _ce:
            logger.warning(
                "Commission stamp failed for sub-order %s: %s", sub_order_id, _ce)
    elif status_data.status == "cancelled":
        internal_update.cancelledAt = _dt.utcnow().isoformat() + "Z"
    elif status_data.status == "shipped":
        internal_update.shippedAt = _dt.utcnow().isoformat() + "Z"

    updated = await sub_order_repository.update(sub_order_id, internal_update)

    # Bubble up: recalculate parent fulfillmentStatus
    parent_id = sub_order.parent_order_id
    if parent_id:
        parent = await order_repository.findById(parent_id)
        if parent:
            _sub_orders = await sub_order_repository.findByParentOrder(parent_id)
            if _sub_orders:
                _f_status = await _compute_fulfillment_status([so.id for so in _sub_orders])
            if _f_status:
                await order_repository.update(parent_id, OrderInternalUpdate(status=_f_status))

    return updated


@router.get("/admin/sub-orders", response_model=PaginatedSubOrdersResponse)
async def get_all_sub_orders(
    seller_id: Optional[str] = None,
    status: Optional[str] = None,
    commissionStatus: Optional[str] = None,
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    current_user: User = Depends(require_super_admin),
):
    """List all sub-orders from seller admins (Super Admin only)."""
    query: dict = {}
    if sellerId:
        if sellerId == "platform":
            query["sellerId"] = None
        else:
            query["sellerId"] = sellerId
    if status:
        # was query.status = status (dict has no .status attribute)
        query["status"] = status
    if commissionStatus:
        query["commissionStatus"] = commissionStatus
    if startDate:
        query["startDate"] = startDate
    if endDate:
        query["endDate"] = endDate
    skip = (page - 1) * limit
    sub_orders = await sub_order_repository.findAll(query, skip=skip, limit=limit)
    total = await sub_order_repository.count(query)

    # Promote unrealized → realized commissions whose return window has elapsed
    try:
        from app.routers.commission import maybe_realize_commission
        import asyncio
        sub_orders = list(await asyncio.gather(*[maybe_realize_commission(so) for so in sub_orders]))
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(
            "Commission promotion failed: %s", e)

    return {
        "subOrders": sub_orders,
        "totalCount": total,
        "page": page,
        "limit": limit,
    }
@router.get("/{order_id}", response_model=PopulatedOrderResponse)
async def get_order(order_id: str, current_user: User = Depends(get_current_user)):
    order = await order_repository.findById(order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Check access
    if current_user.role in ["customer", "wholesaler"]:
        if order.user != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role == "valet":
        if order.assigned_valet != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role == "seller":
        is_seller = any(str(sub.seller_id) == str(current_user.id)
                        for sub in (order.sub_orders or []))
        if not is_seller:
            raise HTTPException(status_code=403, detail="Access denied")

    populated_order = await populate_order(order)
    return populated_order









