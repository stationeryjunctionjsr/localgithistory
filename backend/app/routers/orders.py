from app.models.user import User
from app.models.order import Order
from app.models.sub_order import SubOrder
from pydantic import BaseModel
class GenerateInvoiceResponse(BaseModel):
    success: bool
    invoiceUrl: str
from fastapi.responses import FileResponse
from app.schemas.orders import PaginatedOrdersResponse, PaginatedSubOrdersResponse, DeliveryChargeUpdateResponse
from typing import Dict, Any
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.repositories.cart_repository import cart_repository
from app.repositories.category_repository import category_repository
from app.repositories.notification_repository import notification_repository
from app.repositories.order_repository import order_repository
from app.repositories.payment_repository import payment_repository
from app.repositories.product_repository import product_repository
from app.repositories.sub_order_repository import sub_order_repository
from app.repositories.user_repository import user_repository
from app.services.email_service import email_service
from app.utils.auth import (
    get_current_user,
    is_seller_admin,
    require_seller_admin,
    require_super_admin,
    require_super_admin_or_seller,
    require_super_admin_or_valet,
)
from app.utils.invoice_generator import generate_invoice_pdf, save_invoice_pdf
from app.utils.limiter import limiter
from app.utils.logger import logger
from app.utils.metrics import ORDER_FAILURES

router = APIRouter()


def _resolve_product_seller_id(product: dict | Product, serviceable_seller_ids: list[str] = None) -> str:
    # product can be dict or Product
    if isinstance(product, dict):
        sellers = product.get("sellers", [])
        if sellers:
            return sellers[0].get("id") or sellers[0].get("_id")
        return product.get("sellerId") or product.get("seller_id")
    else:
        if getattr(product, "sellers", None):
            return product.sellers[0].id if getattr(product.sellers[0], "id", None) else getattr(product.sellers[0], "seller_id", None)
        return getattr(product, "seller_id", None)


# Helper function to create order notification
async def create_order_notification(order):
    try:
        super_admin = await user_repository.findOne({"role": "super_admin"})
        if not super_admin:
            return

        await notification_repository.create(
            {
                "userId": super_admin.id,
                "type": "new_order",
                "title": "New Order Received",
                "message": f'New order "{(order.order_number if order.order_number is not None else order.id)}" worth ₹{(order.total if order.total is not None else 0):.2f} received',
                "data": {
                    "orderId": order.id,
                    "orderNumber": (order.order_number if order.order_number is not None else order.id),
                    "amount": (order.total if order.total is not None else 0),
                    "userId": order.user,
                    "createdAt": order.created_at,
                },
            }
        )
    except Exception as e:
        logger.error("Error creating order notification for order %s: %s", order.id, str(e), exc_info=True)


# Helper function to create payment notification
async def create_payment_notification(payment):
    try:
        super_admin = await user_repository.findOne({"role": "super_admin"})
        if not super_admin:
            return

        payment_id = payment.payment_id or payment.id
        await notification_repository.create(
            {
                "userId": super_admin.id,
                "type": "new_payment",
                "title": "New Payment Received",
                "message": f'New payment "{payment_id}" worth ₹{(payment.total_amount if payment.total_amount is not None else 0):.2f} received',
                "data": {
                    "paymentId": payment.id,
                    "paymentIdFormatted": payment_id,
                    "orderId": payment.order_id,
                    "amount": (payment.total_amount if payment.total_amount is not None else 0),
                    "paymentMethod": payment.payment_method,
                    "createdAt": payment.created_at or datetime.now(__import__("datetime").timezone.utc).isoformat() + "Z",
                },
            }
        )
    except Exception as e:
        logger.error(
            "Error creating payment notification for payment %s: %s", payment.id, str(e), exc_info=True
        )


# Helper schemas for order creation
class OrderCreateRequest(BaseModel):
    shippingAddress: dict
    billingAddress: Optional[dict] = None
    paymentMethod: str = "cod"  # 'cod', 'upi', or 'credit'
    upiPaymentScreenshot: Optional[str] = None
    notes: Optional[str] = None
    couponCode: Optional[str] = None  # Coupon code to apply
    referralCode: Optional[str] = None  # Referral code to apply
    discount: Optional[float] = 0
    printedBill: Optional[bool] = False
    items: Optional[List[dict]] = None  # [{productId, quantity}] - optional, if not provided uses user's cart
    isUrgentDelivery: Optional[bool] = False
    deliverySlotId: Optional[str] = None  # slot.id within a slot config
    deliverySlotConfigId: Optional[str] = None  # _id of the DeliverySlotConfig doc
    deliverySlotDate: Optional[str] = None  # ISO date string e.g. "2026-07-15"
    # Per-seller delivery options for split-cart orders
    # [{sellerId, isUrgentDelivery, deliverySlotId, deliverySlotConfigId, deliverySlotDate}]
    sellerDeliveryOptions: Optional[List[dict]] = None


class OrderStatusUpdate(BaseModel):
        status: str


class AssignValetRequest(BaseModel):
    valetId: str


class ConfirmPickupRequest(BaseModel):
    """Sent by valet when physically collecting items from a seller's location."""

    notes: Optional[str] = None


async def populate_orders(orders: list[Any]) -> list[Any]:
    """
    Bulk populates references (user, assignedValet, products, and payment) for a list of orders.
    Optimized to minimize DB queries by fetching all needed references in bulk.
    Handles both Pydantic objects and dictionaries.
    """
    user_ids = set()
    valet_ids = set()
    product_ids = set()
    order_ids = set()

    # 1. Collect all unique IDs across all orders
    for order in orders:
        if isinstance(order, dict):
            if order.get("user"):
                user_ids.add(str(order["user"]))
            if order.get("assignedValet"):
                valet_ids.add(str(order["assignedValet"]))
            if order.get("_id") or order.get("id"):
                order_ids.add(str(order.get("_id") or order.get("id")))
            for item in order.get("items") or []:
                prod = item.get("product")
                if isinstance(prod, dict):
                    pid = prod.get("_id") or prod.get("id")
                    if pid: product_ids.add(str(pid))
                elif hasattr(prod, "id"):
                    product_ids.add(str(prod.id))
                elif prod:
                    product_ids.add(str(prod))
        else:
            if getattr(order, "user", None):
                user_ids.add(str(order.user))
            if getattr(order, "assigned_valet", None):
                valet_ids.add(str(order.assigned_valet))
            elif getattr(order, "assignedValet", None):
                valet_ids.add(str(order.assignedValet))
            if getattr(order, "id", None):
                order_ids.add(str(order.id))
            for item in getattr(order, "items", []) or []:
                if isinstance(item, dict):
                    prod = item.get("product")
                else:
                    prod = getattr(item, "product", None)
                if isinstance(prod, dict):
                    pid = prod.get("_id") or prod.get("id")
                    if pid: product_ids.add(str(pid))
                elif hasattr(prod, "id"):
                    product_ids.add(str(prod.id))
                elif prod:
                    product_ids.add(str(prod))

    # 2. Bulk fetch users, valets, payments, and products with smart database-level queries
    all_users_to_fetch = list(user_ids.union(valet_ids))
    users_map = {}
    if all_users_to_fetch:
        users = await user_repository.findAll({"allowed_ids": all_users_to_fetch})
        users_map = {str(u.id): u for u in users}

    # For products:
    products_map = {}
    if product_ids:
        products = await product_repository.findAll({"allowed_ids": list(product_ids)})
        products_map = {str(p.id): p for p in products}

    # For payments:
    payments_map = {}
    if order_ids:
        payments = await payment_repository.findAll({"allowed_order_ids": list(order_ids)})
        for p in payments:
            oid = p.order_id
            if oid:
                payments_map[str(oid)] = p.payment_entries or []

    
    # 3. Populate each order using the maps
    populated_orders = []
    for order in orders:
        o_user_id = str(order.get("user") if isinstance(order, dict) else getattr(order, "user", ""))
        user = users_map.get(o_user_id)
        
        o_valet_id = str(order.get("assignedValet") or order.get("assigned_valet") if isinstance(order, dict) else getattr(order, "assigned_valet", ""))
        valet = users_map.get(o_valet_id) if o_valet_id else None
        
        o_id = str(order.get("_id") or order.get("id") if isinstance(order, dict) else getattr(order, "id", ""))
        payment_entries = payments_map.get(o_id, [])

        o_items = order.get("items") if isinstance(order, dict) else getattr(order, "items", [])
        populated_items = []
        for item in (o_items or []):
            item_dict = item if isinstance(item, dict) else (item if hasattr(item, "model_dump") else item)
            prod = item_dict.get("product")
            if isinstance(prod, dict):
                prod_id = str(prod.get("_id") or prod.get("id"))
            elif hasattr(prod, "id"):
                prod_id = str(prod.id)
            else:
                prod_id = str(prod)
            
            product = products_map.get(prod_id)
            populated_items.append(
                {**item_dict, "product": product if product else {"_id": prod_id, "name": "Product not found"}}
            )

        order_dict = order if isinstance(order, dict) else (order if hasattr(order, "model_dump") else order)
        
        user_dict = None
        if user:
            u_id = user.get("_id") or user.get("id") if isinstance(user, dict) else getattr(user, "id", "")
            u_user_id = user.get("userId") or user.get("user_id") if isinstance(user, dict) else getattr(user, "user_id", "")
            u_user_id_fmt = user.get("userIdFormatted") or user.get("user_id_formatted") if isinstance(user, dict) else getattr(user, "user_id_formatted", "")
            u_name = user.get("name") if isinstance(user, dict) else getattr(user, "name", "")
            u_email = user.get("email") if isinstance(user, dict) else getattr(user, "email", "")
            u_company = user.get("companyName") or user.get("company_name") if isinstance(user, dict) else getattr(user, "company_name", "")
            u_gstin = user.get("gstin") if isinstance(user, dict) else getattr(user, "gstin", "")
            u_loc = user.get("locationLink") or user.get("location_link") if isinstance(user, dict) else getattr(user, "location_link", "")
            
            user_dict = {
                "_id": u_id,
                "userId": u_user_id,
                "userIdFormatted": u_user_id_fmt,
                "name": u_name,
                "email": u_email,
                "companyName": u_company,
                "gstin": u_gstin,
                "locationLink": u_loc,
            }

        valet_dict = None
        if valet:
            v_id = valet.get("_id") or valet.get("id") if isinstance(valet, dict) else getattr(valet, "id", "")
            v_name = valet.get("name") if isinstance(valet, dict) else getattr(valet, "name", "")
            v_phone = valet.get("phone") if isinstance(valet, dict) else getattr(valet, "phone", "")
            valet_dict = {
                "_id": v_id,
                "name": v_name,
                "phone": v_phone,
            }

        populated_order = {
            **order_dict,
            "user": user_dict,
            "assignedValet": valet_dict,
            "items": populated_items,
            "paymentEntries": payment_entries,
        }
        populated_orders.append(populated_order)

    return populated_orders



async def populate_order(order: dict) -> Optional[dict]:
    """Populate a single order by reusing populate_orders"""
    if not order:
        return None
    res = await populate_orders([order])
    return res[0] if res else None


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
        query.user = current_user.id
    elif current_user.role == "valet":
        query["assignedValet"] = current_user.id
    # Super admin sees all orders; optionally filter by assignedValet
    elif current_user.role == "super_admin" and assignedValet:
        query["assignedValet"] = assignedValet

    if status:
        query.status = status
    if paymentMethod:
        query["paymentMethod"] = paymentMethod
    if startDate:
        query["startDate"] = startDate
    if endDate:
        query["endDate"] = endDate

    total = await order_repository.count(query)

    # Apply pagination when page + limit are provided
    if page is not None and limit is not None and limit > 0:
        page = max(1, page)
        start = (page - 1) * limit
        orders = await order_repository.findAll(query, skip=start, limit=limit)
        has_more = (start + limit) < total

        populated_orders = await populate_orders(orders)

        return {
            "orders": populated_orders,
            "total": total,
            "page": page,
            "limit": limit,
            "hasMore": has_more,
        }

    # No pagination -- return all (backwards compatible), capped at 1000 rows to protect memory
    orders = await order_repository.findAll(query, limit=1000)
    populated_orders = await populate_orders(orders)
    return populated_orders


@router.get("/{order_id}", response_model=Order)
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

    populated_order = await populate_order(order)
    return populated_order


@router.post("", response_model=Order, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=Order, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_order(
    request: Request,
    order_data: OrderCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    # User must be logged in to place an order
    if not current_user:
        raise HTTPException(status_code=401, detail="Please log in to place an order")

    # Valets cannot place orders
    if current_user.role == "valet":
        raise HTTPException(status_code=403, detail="Valets cannot place orders")

    # Get user to check deactivation status
    user = await user_repository.findById(current_user.id)

    from app.repositories.coupon_repository import coupon_repository

    await coupon_repository.get_active_automatic_product_discounts()

    # Determine effective role (if deactivated wholesaler, treat as customer)
    effective_role = "customer"
    if user.is_deactivated and user.role == "wholesaler":
        effective_role = "customer"
    else:
        effective_role = (user.role if user.role is not None else "customer")

    # Block wholesaler if they have overdue credit dues (unverified payments do not count)
    if effective_role == "wholesaler":
        terms_days = user.payment_terms
        if terms_days is None:
            terms_days = 30
        else:
            try:
                terms_days = int(terms_days)
            except Exception:
                terms_days = 30

        user_id_val = user.user_id if user.user_id else str(user.id)
        user_payments = await payment_repository.findAll({"userId": user_id_val})
        import datetime as dt
        now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
        has_overdue = False

        for p in user_payments:
            if p.payment_method == "credit":
                verified_paid = sum(
                    entry.get("amount", 0.0) for entry in (p.payment_entries or []) if entry.get("verified")
                )
                effective_due = (p.total_amount if p.total_amount is not None else 0.0) - verified_paid

                if effective_due > 0:
                    order_date_str = p.order_date or p.created_at
                    if order_date_str:
                        try:
                            from datetime import timedelta

                            order_date = (
                                datetime.fromisoformat(order_date_str.replace("Z", "+00:00"))
                                .astimezone(__import__("datetime").timezone.utc)
                                .replace(tzinfo=None)
                            )
                            due_date = order_date + timedelta(days=terms_days)
                            if now > due_date:
                                has_overdue = True
                                break
                        except Exception:
                            pass
        if has_overdue:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have overdue bills. Please clear your pending dues to continue placing orders.",
            )

    order_type = "b2b" if effective_role == "wholesaler" else "b2c"
    await order_repository.countByUser(current_user.id)

    # Validate payment method against segment feature flags
    is_wholesale = effective_role == "wholesaler"
    segment_prefix = "wholesale" if is_wholesale else "retail"
    payment_method = order_data.paymentMethod

    if payment_method not in ["cod", "upi", "credit"]:
        raise HTTPException(status_code=400, detail="Invalid payment method")

    payment_flag_id = f"{segment_prefix}_enable_{payment_method}"
    gst_flag_id = f"{segment_prefix}_enable_gst"

    from app.repositories.feature_flag_repository import FeatureFlagRepository

    ff_repo = FeatureFlagRepository()
    is_method_enabled = await ff_repo.is_enabled(payment_flag_id)
    gst_enabled = await ff_repo.is_enabled(gst_flag_id)

    if not is_method_enabled:
        method_label = (
            "Cash on Delivery" if payment_method == "cod" else ("UPI" if payment_method == "upi" else "Credit")
        )
        segment_label = "business" if is_wholesale else "retail"
        raise HTTPException(status_code=400, detail=f"{method_label} is not enabled for {segment_label} customers")

    # Get cart items from user's cart (or from request if provided)
    if order_data.items:
        cart_items = order_data.items
    else:
        cart = await cart_repository.findByUser(current_user.id)
        if not cart or not cart.items:
            ORDER_FAILURES.labels(reason="empty_cart").inc()
            raise HTTPException(status_code=400, detail="Your cart is empty")
        cart_items = (cart.items or [])
    # Pre-load all products referenced in cart items in a single batch query (eliminates N+1)
    _cart_product_ids = list(
        {
            str(item.product or item.product_id)
            for item in cart_items
            if item.product or item.product_id
        }
    )
    _cart_products_list = (
        await product_repository.findAll({"allowed_ids": _cart_product_ids}) if _cart_product_ids else []
    )
    _cart_products_map = {str(p.id): p for p in _cart_products_list}

    # Calculate initial subtotal and base shipping before coupon application
    temp_subtotal = 0.0
    for item in cart_items:
        p = _cart_products_map.get(str(item.product or item.product_id))
        if p:
            qty = ((item.get("quantity") if isinstance(item, dict) else item.quantity) if (item.get("quantity") if isinstance(item, dict) else item.quantity) is not None else 0)
            sell_as_case = (item.sell_as_case if item.sell_as_case is not None else False)
            temp_subtotal += product_repository.calculateTotalPrice(
                p, effective_role, qty, sell_as_case=sell_as_case, user_id=current_user.id
            )

    base_shipping = 0.0
    if order_data.shippingAddress:
        try:
            state = order_data.shippingAddress.get("state", "")
            city = order_data.shippingAddress.get("city", "")
            district = order_data.shippingAddress.get("district", "")
            zip_code = order_data.shippingAddress.get("zipCode", "")

            from app.repositories.delivery_charge_repository import delivery_charge_repository

            delivery_charge_data = await delivery_charge_repository.getChargeForLocation(
                state, city, district, zip_code, effective_role, temp_subtotal
            )
            if delivery_charge_data:
                charge_amount = delivery_charge_data.get("charge", 0)
                min_cart_value_for_free = delivery_charge_data.get("minCartValue", 0)
                if delivery_charge_data.get("isApplicableToRole", True):
                    if min_cart_value_for_free > 0 and temp_subtotal < min_cart_value_for_free:
                        base_shipping = float(charge_amount)
                    elif min_cart_value_for_free == 0 or min_cart_value_for_free == float("inf"):
                        base_shipping = float(charge_amount)
        except Exception as e:
            logger.warning("Error calculating base shipping before coupon: %s", str(e))

    # Validate and apply discount (coupon) if provided. When discount has "Applies to" (categories/brands/etc.),
    # only eligible cart items count toward minimum and discount amount.
    coupon_discount = 0.0
    coupon_code = None
    coupon_info = None
    applied_coupon_id = None  # coupon _id for incrementUsage
    eligible_item_indices = None
    item_discounts = None
    is_override = False

    if hasattr(order_data, "couponCode") and order_data.couponCode:
        from app.repositories.coupon_repository import coupon_repository

        role_for_coupon = effective_role
        validation = await coupon_repository.validateCoupon(
            order_data.couponCode,
            role_for_coupon,
            0.0,
            current_user.id,
            None,
            order_data.paymentMethod,
            cart_items=cart_items,
            product_repository=product_repository,
            shipping_address=order_data.shippingAddress,
            shipping_charge=base_shipping,
        )
        if not validation.get("valid"):
            raise HTTPException(status_code=400, detail=validation.get("message"))
        applied_coupon_id = validation["coupon"].id
        coupon_code = validation["coupon"].get("code") or ("AUTO-" + (applied_coupon_id or "")[:8])
        coupon_discount = validation["discount"]
        eligible_item_indices = validation.get("eligibleItemIndices")
        item_discounts = validation.get("itemDiscounts")
        validation.get("bxgyItemIndices")

        c_obj = validation.get("coupon") or {}
        if c_obj.get("method") == "discount_code" and c_obj.get("couponMode") == "override":
            is_override = True

        coupon_info = {
            "code": coupon_code,
            "discountType": validation["coupon"]["discountType"],
            "discountValue": validation["coupon"]["discountValue"],
            "discountAmount": coupon_discount,
            "typeOfDiscount": validation["coupon"].get("typeOfDiscount"),
        }
    else:
        # Apply best automatic discount if any
        from app.repositories.coupon_repository import coupon_repository

        auto_list = await coupon_repository.find_applicable_automatic_discounts(
            current_user.id,
            effective_role,
            cart_items,
            product_repository,
            order_data.paymentMethod,
            shipping_address=order_data.shippingAddress,
            shipping_charge=base_shipping,
        )
        if auto_list:
            best = max(auto_list, key=lambda x: x["discount"])
            coupon_discount = best["discount"]
            eligible_item_indices = best.get("eligibleItemIndices")
            item_discounts = best.get("itemDiscounts")
            best.get("bxgyItemIndices")
            c = best["coupon"]
            applied_coupon_id = c.id
            coupon_code = c.code or ("AUTO-" + (applied_coupon_id or "")[:8])
            coupon_info = {
                "code": coupon_code,
                "discountType": c.discount_type,
                "discountValue": c.discount_value,
                "discountAmount": coupon_discount,
                "typeOfDiscount": c.type_of_discount,
            }

    # Calculate totals with GST (after coupon discount)
    subtotal = 0.0
    subtotal_before_coupon = 0.0
    total_cgst = 0.0
    total_sgst = 0.0
    order_items = []

    # Build item totals for discount distribution (eligible-only vs all)
    initial_subtotal = 0.0
    eligible_subtotal_for_discount = None
    item_totals = []
    for idx, item in enumerate(cart_items):
        product = _cart_products_map.get(str(item.product or item.product_id))
        if not product:
            raise HTTPException(
                status_code=400, detail=f"Product not found: {item.product or item.product_id}"
            )
        quantity = ((item.get("quantity") if isinstance(item, dict) else item.quantity) if (item.get("quantity") if isinstance(item, dict) else item.quantity) is not None else 0)
        sell_as_case = (item.sell_as_case if item.sell_as_case is not None else False)

        ignore_auto = False
        if is_override and eligible_item_indices is not None and idx in eligible_item_indices:
            ignore_auto = True

        item_total = product_repository.calculateTotalPrice(
            product,
            effective_role,
            quantity,
            sell_as_case=sell_as_case,
            user_id=current_user.id,
            ignore_auto_discount=ignore_auto,
        )
        item_totals.append((product, item_total, quantity, sell_as_case, item))
        initial_subtotal += item_total
    if eligible_item_indices is not None and len(eligible_item_indices) > 0 and coupon_discount > 0:
        eligible_subtotal_for_discount = sum(item_totals[i][1] for i in eligible_item_indices if i < len(item_totals))

    # --- Phase 1: Apply Coupon Discount ---
    is_shipping_discount = coupon_info is not None and coupon_info.get("typeOfDiscount") == "shipping_discount"

    for idx, (product, item_total_before_coupon, quantity, sell_as_case, item) in enumerate(item_totals):
        # Apply discount: exact mapping if available, else proportional
        if is_shipping_discount:
            item_coupon_discount = 0.0
        elif item_discounts is not None and idx in item_discounts:
            item_coupon_discount = item_discounts[idx]
            item_discounts[idx] = 0.0  # Prevent double application if any logic loops
        elif (
            coupon_discount > 0
            and eligible_subtotal_for_discount
            and eligible_subtotal_for_discount > 0
            and idx in (eligible_item_indices or [])
        ):
            if eligible_subtotal_for_discount is None:
                raise ValueError("Data Integrity Error: Missing eligible subtotal for coupon discount allocation")
            coupon_discount_ratio = coupon_discount / eligible_subtotal_for_discount
            item_coupon_discount = item_total_before_coupon * coupon_discount_ratio
        elif coupon_discount > 0 and initial_subtotal > 0:
            coupon_discount_ratio = coupon_discount / initial_subtotal
            item_coupon_discount = item_total_before_coupon * coupon_discount_ratio
        else:
            item_coupon_discount = 0.0

        item_total_after_coupon = max(0.0, item_total_before_coupon - item_coupon_discount)

        # Store temporary values back in the tuple (re-constructing the tuple)
        item_totals[idx] = (
            product,
            item_total_before_coupon,
            quantity,
            sell_as_case,
            item,
            item_coupon_discount,
            item_total_after_coupon,
        )

    # --- Phase 2: Compute global referral discount ---
    subtotal_after_coupon = sum(t[6] for t in item_totals)

    referral_discount = 0.0
    applied_referral_code = None

    if hasattr(order_data, "referralCode") and order_data.referralCode:
        ref_code = order_data.referralCode.strip().upper()

        # 1. User must be customer role (Retail)
        if effective_role != "customer":
            raise HTTPException(status_code=400, detail="Referral discount is only available for retail customers")

        # 2. Must be first order (0 orders)
        order_count = await order_repository.countByUser(current_user.id)
        if order_count > 0:
            raise HTTPException(status_code=400, detail="Referral discount is only available on your first order")

        # 3. Settings must be active globally
        from app.repositories.referral_repository import referral_repository

        ref_settings = await referral_repository.get_settings()
        retail_settings = ref_settings.get("retail", {})
        if not (retail_settings.is_active if retail_settings.is_active is not None else False) or (retail_settings.discount_value if retail_settings.discount_value is not None else 0) <= 0:
            raise HTTPException(status_code=400, detail="Referral program is not active at the moment")

        # 4. Valid referrer user
        referrer = await user_repository.findOne({"referralCode": ref_code})
        if not referrer:
            raise HTTPException(status_code=400, detail="Invalid referral code")

        # 5. Cannot refer self
        if str(referrer.id) == str(current_user.id):
            raise HTTPException(status_code=400, detail="You cannot use your own referral code")

        # If all valid, calculate discount using latest settings
        discount_type = retail_settings.discount_type
        discount_value = (retail_settings.discount_value if retail_settings.discount_value is not None else 0)

        if discount_type == "percentage":
            if subtotal_after_coupon is None or discount_value is None:
                raise ValueError("Data Integrity Error: Missing values for referral discount calculation")
            referral_discount = subtotal_after_coupon * (discount_value / 100)
        else:  # fixed
            referral_discount = min(discount_value, subtotal_after_coupon)

        applied_referral_code = ref_code
    # -------------------------------

    # --- Phase 3: Distribute referral discount, calculate single unit price & GST ---
    subtotal = 0.0
    total_cgst = 0.0
    total_sgst = 0.0
    order_items = []

    # Resolve customer delivery pincode for seller routing
    _customer_pincode = (
        (order_data.shippingAddress.get("zipCode") or order_data.shippingAddress.get("pincode") or "")
        if order_data.shippingAddress
        else ""
    )
    _pincode_seller_ids = set()
    if _customer_pincode:
        try:
            from app.routers.delivery_charges import get_serviceable_seller_ids_for_pincode

            _, _pincode_seller_ids = await get_serviceable_seller_ids_for_pincode(_customer_pincode, "customer")
            _pincode_seller_ids = set(_pincode_seller_ids or [])
        except Exception as _pse:
            logger.warning("Could not resolve serviceable sellers for pincode %s: %s", _customer_pincode, _pse)

    for idx, (
        product,
        item_total_before_coupon,
        quantity,
        sell_as_case,
        item,
        item_coupon_discount,
        item_total_after_coupon,
    ) in enumerate(item_totals):
        # Distribute referral discount proportionally
        if referral_discount > 0 and subtotal_after_coupon > 0:
            item_referral_discount = item_total_after_coupon * (referral_discount / subtotal_after_coupon)
        else:
            item_referral_discount = 0.0

        final_item_total = max(0.0, item_total_after_coupon - item_referral_discount)

        # Calculate total single physical units
        qty_per_case = int(product.quantity_per_case or 1)
        total_single_units = (quantity * qty_per_case) if sell_as_case else quantity

        single_unit_price = final_item_total / total_single_units if total_single_units > 0 else 0.0

        # GST Calculation per single unit
        gst_percent = (product.gst if product.gst is not None else 0) if gst_enabled else 0
        gst_multiplier = 1 + (gst_percent / 100)
        single_unit_taxable_value = single_unit_price / gst_multiplier if gst_multiplier > 0 else single_unit_price
        single_unit_cgst = single_unit_taxable_value * (gst_percent / 200) if gst_percent > 0 else 0
        single_unit_sgst = single_unit_taxable_value * (gst_percent / 200) if gst_percent > 0 else 0

        # Aggregate totals for the item
        taxable_value = single_unit_taxable_value * total_single_units
        cgst = single_unit_cgst * total_single_units
        sgst = single_unit_sgst * total_single_units

        subtotal += final_item_total
        total_cgst += cgst
        total_sgst += sgst

        effective_price = (item_total_before_coupon / quantity) if quantity else 0

        order_items.append(
            {
                "product": product.id,
                "sellerId": _resolve_product_seller_id(product, _pincode_seller_ids),
                "productName": product.name,
                "quantity": quantity,
                "sellAsCase": sell_as_case,
                "price": effective_price,
                "priceBeforeCoupon": round(item_total_before_coupon, 2),
                "couponDiscount": round(item_coupon_discount, 2),
                "referralDiscount": round(item_referral_discount, 2),
                "subtotal": round(final_item_total, 2),
                "singleUnitPrice": round(single_unit_price, 2),
                "singleUnitTaxableValue": round(single_unit_taxable_value, 2),
                "singleUnitCGST": round(single_unit_cgst, 2),
                "singleUnitSGST": round(single_unit_sgst, 2),
                "numberOfSingleUnits": total_single_units,
                "gst": gst_percent,
                "taxableValue": round(taxable_value, 2),
                "cgst": round(cgst, 2),
                "sgst": round(sgst, 2),
            }
        )

        # Check stock (considering reservations)
        from app.repositories.stock_reservation_repository import stock_reservation_repository

        user_res = await stock_reservation_repository.get_user_reservations(current_user.id)
        prod_res = next((r for r in user_res if r.product_id == str(product.id)), None)

        has_valid_reservation = False
        if prod_res and int(prod_res.quantity) >= quantity:
            has_valid_reservation = True

        if not has_valid_reservation:
            # Check if stock is available in the pool
            available_pool = await product_repository.get_available_stock(
                product.id, exclude_user_id=current_user.id
            )
            if available_pool < quantity:
                ORDER_FAILURES.labels(reason="insufficient_stock").inc()
                raise HTTPException(
                    status_code=400,
                    detail=f"Stock is no longer reserved or available for {product.name}. Please check your cart.",
                )

    tax = round(total_cgst + total_sgst, 2)  # Total GST = CGST + SGST

    # ------------------------------------------------------------------
    # Slot booking validation
    # ----------------------------------------------------------------
    selected_slot_info = None
    zone_urgent_available = False  # set from zone if urgent delivery is requested
    if (order_data.deliverySlotId and order_data.deliverySlotDate) or order_data.isUrgentDelivery:
        import datetime as _dt

        import pytz

        from app.db.storage_factory import get_storage as _get_storage

        slot_storage = _get_storage("deliverySlots")
        seg = "wholesale" if effective_role == "wholesaler" else "retail"
        zip_code = order_data.shippingAddress.get("zipCode", "") if order_data.shippingAddress else ""

        target_date = order_data.deliverySlotDate
        if order_data.isUrgentDelivery and not target_date:
            ist = pytz.timezone("Asia/Kolkata")
            target_date = _dt.datetime.now(ist).date().isoformat()
            order_data.deliverySlotDate = target_date

        # ── Resolve zone for the shipping pincode ────────────────────────────
        order_zone_id = None
        if zip_code:
            from app.repositories.zone_seller_cache import get_zone_for_pincode as _get_zone
            _zone_doc = await _get_zone(zip_code)
            if _zone_doc:
                # Use MySQL _id (as string) — consistent with zone_seller_cache key
                order_zone_id = str(_zone_doc.get("_id", _zone_doc.get("id")))
                zone_urgent_available = bool(_zone_doc.get("urgentDeliveryAvailable", False))

        # ── Resolve slot config: zone-specific first, then "default" fallback ─
        # New design: one config record per zone per date (zoneId field).
        # "default" config serves as a fallback for zones with no specific config.
        _slot_config = None
        if order_zone_id:
            _zone_configs = await slot_storage.findAll(
                {"date": target_date, "segment": seg, "zoneId": order_zone_id, "isActive": True}
            )
            if _zone_configs:
                _slot_config = _zone_configs[0]
        if not _slot_config:
            _default_configs = await slot_storage.findAll(
                {"date": target_date, "segment": seg, "zoneId": "default", "isActive": True}
            )
            if _default_configs:
                _slot_config = _default_configs[0]

        slot_configs = [_slot_config] if _slot_config else []

        matched_config = None
        matched_slot = None

        for sc in slot_configs:
            for sl in sc.get("slots", []):
                if not (sl.get("isActive") if sl.get("isActive") is not None else True):
                    continue

                # ── Flat capacity check (new per-zone record design) ─────────
                # Each config record is already scoped to a zone, so capacity
                # and bookedCount are flat fields on the slot — no sub-dict needed.
                _cap = sl.get("capacity")
                if _cap is None:
                    _cap = sc.get("zoneDefaultCapacity")
                _booked = (sl.get("bookedCount") if sl.get("bookedCount") is not None else 0)
                if _cap is not None and _booked >= int(_cap):
                    continue  # Slot full

                # Match by explicit ID or match by Urgent condition
                if order_data.isUrgentDelivery and not order_data.deliverySlotId:
                    if (sl.get("isUrgent") if sl.get("isUrgent") is not None else False):
                        # Check cutoff
                        cutoff = (
                            sl.get("urgentCutoffHours")
                            if sl.get("urgentCutoffHours") is not None
                            else sl.get("cutoffHours")
                        )
                        if cutoff is not None:
                            ist = pytz.timezone("Asia/Kolkata")
                            now_ist = _dt.datetime.now(ist)
                            anchor_time_str = (sl.end_time or "")  # urgent → end time
                            try:
                                anchor_ist = ist.localize(
                                    _dt.datetime.strptime(f"{target_date} {anchor_time_str}", "%Y-%m-%d %H:%M")
                                )
                                if now_ist >= (anchor_ist - _dt.timedelta(hours=cutoff)):
                                    continue
                            except ValueError:
                                pass

                        matched_config = sc
                        matched_slot = sl
                        break
                else:
                    if (sl.get("id") or f"{sl.get('startTime')}-{sl.get('endTime')}") == order_data.deliverySlotId:
                        matched_config = sc
                        matched_slot = sl
                        break
            if matched_slot:
                break

        if not matched_slot:
            if order_data.isUrgentDelivery and not order_data.deliverySlotId:
                raise HTTPException(
                    status_code=400, detail="Urgent delivery is currently unavailable for your location."
                )
            else:
                raise HTTPException(status_code=400, detail="Selected delivery slot is no longer available.")

        # Re-check capacity & cutoffs for standard slot selection
        if not order_data.isUrgentDelivery or order_data.deliverySlotId:
            is_full_day = (matched_slot.get("isFullDay") if matched_slot.get("isFullDay") is not None else False)
            if not is_full_day:
                # Flat capacity re-check (per-zone record, no zoneCapacities sub-dict)
                _cap = matched_slot.get("capacity")
                if _cap is None:
                    _cap = matched_config.get("zoneDefaultCapacity")
                _booked = (matched_slot.get("bookedCount") if matched_slot.get("bookedCount") is not None else 0)
                if _cap is not None and _booked >= int(_cap):
                    raise HTTPException(status_code=400, detail="Selected delivery slot is fully booked.")

                cutoff_hours = (
                    matched_slot.get("urgentCutoffHours")
                    if matched_slot.get("isUrgent") and matched_slot.get("urgentCutoffHours") is not None
                    else matched_slot.get("cutoffHours")
                )
                if cutoff_hours is not None:
                    ist = pytz.timezone("Asia/Kolkata")
                    now_ist = _dt.datetime.now(ist)
                    is_urgent = (matched_slot.get("isUrgent") if matched_slot.get("isUrgent") is not None else False)
                    anchor_time_str = (
                        (matched_slot.get("endTime") or "") if is_urgent else (matched_slot.get("startTime") or "")
                    )
                    try:
                        anchor_ist = ist.localize(
                            _dt.datetime.strptime(f"{target_date} {anchor_time_str}", "%Y-%m-%d %H:%M")
                        )
                        if now_ist >= (anchor_ist - _dt.timedelta(hours=cutoff_hours)):
                            raise HTTPException(status_code=400, detail="Booking time for this slot has passed.")
                    except ValueError:
                        pass

        selected_slot_info = {
            "configId": str(matched_config.get("_id", matched_config.get("id"))),
            "slotId": matched_slot.get("_id", matched_slot.get("id")),
            "zoneId": order_zone_id,
            "date": matched_config["date"],
            "startTime": matched_slot["startTime"],
            "endTime": matched_slot["endTime"],
            "isUrgent": (matched_slot.get("isUrgent") if matched_slot.get("isUrgent") is not None else False),
        }

        if selected_slot_info["isUrgent"]:
            order_data.isUrgentDelivery = True

    # Check pincode serviceability before proceeding
    if order_data.shippingAddress and order_data.shippingAddress.get("zipCode"):
        shipping_zip = str(order_data.shippingAddress.get("zipCode")).strip()
        is_serviceable = await delivery_charge_repository.isPincodeServiceable(shipping_zip, effective_role)

        if not is_serviceable:
            ORDER_FAILURES.labels(reason="pincode_not_serviceable").inc()
            raise HTTPException(
                status_code=400, detail="Your pincode is not serviceable. Please contact support for assistance."
            )

        # Zone-based seller serviceability check
        # Resolve zone_id if not already set (e.g. non-slot standard orders)
        if not order_zone_id and shipping_zip:
            from app.repositories.zone_seller_cache import get_zone_for_pincode as _gz2
            _z2 = await _gz2(shipping_zip)
            if _z2:
                order_zone_id = str(_z2.id or "")

        if order_zone_id:
            seller_ids_in_order = {item.get("sellerId", item.get("seller_id")) for item in order_items if item.get("sellerId", item.get("seller_id"))}
            for sid in seller_ids_in_order:
                sdoc = await user_repository.findById(sid)
                if sdoc:
                    seller_zone_ids = (sdoc.get("sellerPermissions") or {}).get("serviceableZoneIds", [])
                    # Empty list = seller hasn't configured zones yet; allow during migration
                    if seller_zone_ids and order_zone_id not in seller_zone_ids:
                        s_name = sdoc.get("companyName") or sdoc.get("name") or "Seller"
                        ORDER_FAILURES.labels(reason="seller_zone_not_serviceable").inc()
                        raise HTTPException(
                            status_code=400,
                            detail=f"Products from '{s_name}' are not available for delivery to your area.",
                        )


    # Calculate delivery charge based on location, user role, and order amount
    # Enhanced logic to handle all scenarios:
    # a) If no delivery charge added by super admin overall, then consider it as 0
    # b) If delivery charge added for some locations and not for others, and no default delivery charge present:
    #    i) For locations with delivery charge, calculate as per the value entered
    #    ii) For locations without delivery charge, the delivery charge will be zero
    # c) If delivery charge added for some locations and not for others, and a default delivery charge present:
    #    i) For locations with delivery charge, calculate as per the value entered
    #    ii) For locations without delivery charge, use the default delivery charge (with tiered support)
    # d) The delivery charge should be added only if total (before delivery charge) is less than minimum for free delivery
    # e) Role-based applicability: Check if delivery charge applies to wholesaler
    # f) Tiered charges: For default charges, apply tier based on order amount
    shipping = 0.0
    min_cart_value_for_free = 0.0

    if order_data.shippingAddress:
        try:
            state = order_data.shippingAddress.get("state", "")
            city = order_data.shippingAddress.get("city", "")
            district = order_data.shippingAddress.get("district", "")
            zip_code = order_data.shippingAddress.get("zipCode", "")

            # Calculate total before shipping for tiered charge calculation
            total_before_shipping = subtotal  # Use subtotal (after coupon, includes GST)

            # Get delivery charge with role and amount consideration (now includes pincode)
            delivery_charge_data = await delivery_charge_repository.getChargeForLocation(
                state, city, district, zip_code, effective_role, total_before_shipping
            )

            if delivery_charge_data:
                charge_amount = delivery_charge_data.get("charge", 0)
                min_cart_value_for_free = delivery_charge_data.get("minCartValue", 0)

                # Apply delivery charge only if:
                # 1. It's applicable to the user's role
                # 2. Total before shipping is less than minimum for free delivery
                if delivery_charge_data.get("isApplicableToRole", True):
                    if order_data.isUrgentDelivery and effective_role in ("customer", "wholesaler"):
                        if zone_urgent_available:
                            # Urgent delivery is determined by the zone's urgentDeliveryAvailable flag.
                            # The cart is treated as a single unit — all items are either
                            # urgent or standard. No per-seller validation needed here.
                            urgent_charge = delivery_charge_data.get("urgentDeliveryCharge")
                            shipping = float(urgent_charge) if urgent_charge is not None else 0.0
                        else:
                            raise HTTPException(
                                status_code=400, detail="Urgent delivery is not available for this location"
                            )
                    else:
                        if min_cart_value_for_free > 0 and total_before_shipping < min_cart_value_for_free:
                            shipping = float(charge_amount)
                        elif min_cart_value_for_free == 0 or min_cart_value_for_free == float("inf"):
                            # If no minimum for free delivery, always apply charge
                            shipping = float(charge_amount)
                        # else shipping remains 0 (free delivery)
                elif order_data.isUrgentDelivery:
                    raise HTTPException(
                        status_code=400, detail="Urgent delivery is not available for your customer type"
                    )
            elif order_data.isUrgentDelivery:
                raise HTTPException(status_code=400, detail="Urgent delivery is not available for this location")
        except (KeyError, ValueError, TypeError) as e:
            logger.warning("Data error fetching delivery charge: %s", str(e))
            shipping = 0.0
        except Exception as e:
            logger.error("Unexpected error fetching delivery charge: %s", str(e), exc_info=True)
            shipping = 0.0

    # Apply shipping discount calculation and compute net shipping to charge
    base_shipping = shipping
    shipping_net_to_charge = base_shipping
    is_shipping_discount = coupon_info is not None and coupon_info.get("typeOfDiscount") == "shipping_discount"

    if is_shipping_discount:
        shipping_discount_amount = coupon_discount
        shipping_net_to_charge = max(0.0, base_shipping - shipping_discount_amount)

    # Delivery GST calculation on the net shipping charge (Inclusive of tax)
    delivery_gst = 0.0
    if shipping_net_to_charge > 0:
        default_charge = await delivery_charge_repository.getDefaultCharge()
        if default_charge and default_charge.delivery_charge_gst:
            gst_percentage = float((default_charge.delivery_charge_gst_percentage if default_charge.delivery_charge_gst_percentage is not None else 18.0))
            gst_multiplier = 1 + (gst_percentage / 100)

            # Shipping is inclusive of taxes. Extract base charge and tax.
            base_shipping_charge = shipping_net_to_charge / gst_multiplier
            delivery_gst = round(shipping_net_to_charge - base_shipping_charge, 2)

            # The system treats the base amount as the actual delivery charge
            shipping_net_to_charge = round(base_shipping_charge, 2)

            # If there was no shipping discount, update the main `shipping` variable to the base amount
            if not is_shipping_discount:
                shipping = shipping_net_to_charge

    # In case of shipping discount, store base shipping (exclusive of tax) in shipping field so PDF invoices sum up correctly
    if is_shipping_discount:
        # Since base_shipping was inclusive, we must also extract its base value
        if default_charge and default_charge.delivery_charge_gst:
            gst_percentage = float((default_charge.delivery_charge_gst_percentage if default_charge.delivery_charge_gst_percentage is not None else 18.0))
            gst_multiplier = 1 + (gst_percentage / 100)
            shipping = round(base_shipping / gst_multiplier, 2)
        else:
            shipping = base_shipping

    discount = coupon_discount + referral_discount  # Coupon + Referral discount
    # Round off the total amount based on standard rounding rules
    total = round(
        subtotal + shipping_net_to_charge + delivery_gst
    )  # subtotal already has coupon and referral discount applied, just add shipping and delivery_gst

    # For UPI, require payment screenshot
    if order_data.paymentMethod == "upi":
        if not order_data.upiPaymentScreenshot:
            raise HTTPException(status_code=400, detail="UPI payment screenshot is required")

    # Check credit limit for credit payment method
    if order_data.paymentMethod == "credit":
        # Initialize credit if not set
        if user.credit_used is None:
            await user_repository.update(current_user.id, {"creditUsed": 0})
            user["creditUsed"] = 0
        if user.credit_limit is None:
            await user_repository.update(current_user.id, {"creditLimit": 0})
            user["creditLimit"] = 0

        if ((user.credit_used if user.credit_used is not None else 0) + total) > (user.credit_limit if user.credit_limit is not None else 0):
            ORDER_FAILURES.labels(reason="credit_limit_exceeded").inc()
            raise HTTPException(status_code=400, detail="Credit limit exceeded")

    # Upload UPI screenshot to OCI if present
    screenshot_path = None
    if order_data.paymentMethod == "upi" and order_data.upiPaymentScreenshot:
        from app.services.oci_storage import upload_base64_image_and_return_path

        screenshot_path = await upload_base64_image_and_return_path(
            order_data.upiPaymentScreenshot, "payments", filename_prefix="upi-screenshot"
        )

    # Create order
    order = await order_repository.create(
        {
            "user": current_user.id,
            "sessionId": current_user.session_id,
            "items": order_items,
            "subtotalBeforeCoupon": round(subtotal_before_coupon, 2),
            "subtotal": round(subtotal, 2),
            "tax": tax,
            "shipping": shipping,
            "deliveryGst": delivery_gst,
            "discount": discount,
            "couponCode": coupon_code,
            "couponInfo": coupon_info,
            "total": total,
            "orderType": order_type,
            "isUrgentDelivery": order_data.isUrgentDelivery if effective_role in ("customer", "wholesaler") else False,
            "deliverySlot": selected_slot_info,
            "shippingAddress": order_data.shippingAddress,
            "billingAddress": order_data.billingAddress or order_data.shippingAddress,
            "paymentMethod": order_data.paymentMethod,
            "upiPaymentScreenshot": screenshot_path if order_data.paymentMethod == "upi" else None,
            "notes": f"Referral Code Applied: {applied_referral_code} | {order_data.notes or ''}".strip(" |")
            if applied_referral_code
            else order_data.notes,
            "printedBill": order_data.printedBill if hasattr(order_data, "printedBill") else False,
            "status": "pending",  # New orders start as pending
            "paymentStatus": "paid" if order_data.paymentMethod == "upi" else "pending",  # UPI=Paid, COD/Credit=Pending
        }
    )

    # Increment delivery slot bookedCount if a slot was booked
    if selected_slot_info:
        try:
            from app.db.storage_factory import get_storage as _get_storage
            import json
            from sqlalchemy import text
            from app.config.database import get_async_session_factory

            slot_storage = _get_storage("deliverySlots")
            config_id = selected_slot_info["configId"]
            slot_id = selected_slot_info["slotId"]
            slot_config = await slot_storage.findById(config_id)
            if slot_config:
                factory = get_async_session_factory()
                if factory:
                    db_id = slot_config.get("_db_id") or config_id
                    async with factory() as session:
                        result = await session.execute(
                            text(f"SELECT doc FROM {slot_storage.table_name} WHERE id = :id FOR UPDATE"),
                            {"id": int(db_id) if str(db_id).isdigit() else 0},
                        )
                        row = result.fetchone()
                        if row and row.doc:
                            doc = json.loads(row.doc)
                            updated_slots = (doc.slots or [])
                            for sl in updated_slots:
                                if sl.id == slot_id:
                                    # Flat bookedCount increment — per-zone config records
                                    # each have their own bookedCount directly on the slot.
                                    sl["bookedCount"] = (sl.get("bookedCount") if sl.get("bookedCount") is not None else 0) + 1
                                    break
                            doc["slots"] = updated_slots
                            doc["updatedAt"] = datetime.now(__import__("datetime").timezone.utc).isoformat()
                            await session.execute(
                                text(
                                    f"UPDATE {slot_storage.table_name} SET doc = :doc, updated_at = UTC_TIMESTAMP() WHERE id = :id"
                                ),
                                {"doc": json.dumps(doc, default=str), "id": int(db_id) if str(db_id).isdigit() else 0},
                            )
                            await session.commit()
        except Exception as e:
            logger.error(
                "Failed to increment slot bookedCount for config %s slot %s: %s",
                selected_slot_info.get("configId"),
                selected_slot_info.get("slotId"),
                str(e),
                exc_info=True,
            )

    # Increment sales volume for product bundles included in this order.
    # Increment by the actual number of bundle copies purchased (not always +1).
    try:
        unique_bundle_ids = {item.bundle_id for item in cart_items if item.bundle_id}
        for b_id in unique_bundle_ids:
            from app.repositories.bundle_repository import bundle_repository

            bundle = await bundle_repository.findById(b_id)
            if bundle:
                # Determine how many full copies of this bundle were in the order.
                # Use the first bundle item spec as the reference: copies = cart_qty / spec_qty.
                bundle_items_in_order = [i for i in cart_items if i.bundle_id == b_id]
                bundle_specs = bundle.items or []
                copies = 1  # default
                if bundle_specs and bundle_items_in_order:
                    spec = bundle_specs[0]
                    spec_qty = max(1, spec.get("quantity", 1) or 1)
                    spec_pid = str(spec.get("productId", ""))
                    ref_item = next(
                        (
                            i
                            for i in bundle_items_in_order
                            if str((i.product or "")) == spec_pid or str((i.product_id or "")) == spec_pid
                        ),
                        bundle_items_in_order[0],
                    )
                    copies = max(1, ref_item.get("quantity", spec_qty) // spec_qty)
                new_sales = (bundle.sales_count if bundle.sales_count is not None else 0) + copies
                await bundle_repository.update(b_id, {"salesCount": new_sales})
    except Exception as e:
        logger.error("Failed to increment bundle salesCount: %s", str(e), exc_info=True)

    # Atomically decrement stock and fulfil the reservation in one shot per item.
    # Uses SELECT … FOR UPDATE so concurrent orders for the same product serialize
    # at the DB level — no two orders can read the same stock value and both succeed.
    for item in order_items:
        product = await product_repository.findById(item.product)

        # Build variant_combinations arg expected by decrement_stock_atomic
        variant_combos = None
        if getattr(item, "variant_attributes", None) or (isinstance(item, dict) and item.get("variantAttributes")):
            variant_combos = [{"attributes": item.get("variantAttributes", item.get("variant_attributes")) if isinstance(item, dict) else item.variant_attributes, "quantity": item.get("quantity") if isinstance(item, dict) else (item.get("quantity") if isinstance(item, dict) else item.quantity)}]

        new_stock = await product_repository.decrement_stock_atomic(
            str(item.product),
            (item.get("quantity") if isinstance(item, dict) else item.quantity),
            variant_combinations=variant_combos,
            role=effective_role,
        )
        if new_stock is None:
            # Should not happen in production (factory always set), but guard anyway
            logger.error(
                "[OrderCreate] decrement_stock_atomic returned None for product %s — "
                "order %s may have incorrect stock. Investigate factory availability.",
                item.product,
                order.id,
            )
            new_stock = max(0, ((product.stock if product.stock is not None else 0) or 0) - (item.get("quantity") if isinstance(item, dict) else item.quantity))

        # Fulfil the stock reservation for this user + product
        from app.repositories.stock_reservation_repository import stock_reservation_repository

        await stock_reservation_repository.fulfill_user_reservations(current_user.id, item.product)

        # Check if stock is below category minimum quantity
        should_notify = False
        threshold = None

        if product.category:
            cat = await category_repository.findByName(product.category)
            if cat and cat.minimum_quantity:
                threshold = cat.minimum_quantity
                if new_stock < threshold:
                    should_notify = True

        if should_notify and threshold is not None:
            try:
                super_admin = await user_repository.findOne({"role": "super_admin"})
                if super_admin:
                    await notification_repository.create(
                        {
                            "userId": super_admin.id,
                            "type": "low_stock",
                            "title": "Low Stock Alert",
                            "message": f'Product "{product.sku}" - "{product.name}" has {new_stock} pieces left',
                            "data": {
                                "productId": product.id,
                                "sku": product.sku,
                                "productName": product.name,
                                "quantity": new_stock,
                                "category": product.category,
                                "threshold": threshold if threshold is not None else None,
                            },
                        }
                    )
            except Exception as e:
                logger.error(
                    "Error creating low stock notification for product %s: %s",
                    product.id,
                    str(e),
                    exc_info=True,
                )

    # Clean up any leftover active reservations of the user
    from app.repositories.stock_reservation_repository import stock_reservation_repository

    await stock_reservation_repository.release_user_reservations(current_user.id)

    # Update credit used for credit payment method
    if order_data.paymentMethod == "credit":
        success = await user_repository.add_credit_used_atomic(current_user.id, total)
        if not success:
            raise HTTPException(status_code=400, detail="Insufficient credit limit or user not found.")

    # Update discount usage count if discount was used
    if applied_coupon_id:
        from app.repositories.coupon_repository import coupon_repository

        await coupon_repository.incrementUsage(applied_coupon_id, current_user.id)

    # Create payment record
    user_for_payment = await user_repository.findById(current_user.id)
    payment_data = {
        "orderId": order.id,
        "userId": user_for_payment.user_id,  # Use userId instead of customerId
        "customerName": user_for_payment.name,
        "orderDate": order.created_at,
        "paymentMethod": order_data.paymentMethod,
        "totalAmount": total,
    }

    # Set payment amounts and entries based on payment method
    if order_data.paymentMethod == "upi":
        # UPI: Paid upfront, amount remaining is 0
        payment_data["amountPaid"] = total
        payment_data["amountRemaining"] = 0
        payment_data["paymentEntries"] = [
            {
                "entryId": 1,
                "amount": total,
                "image": screenshot_path,
                "verified": False,
                "createdAt": order.created_at,
            }
        ]
    elif order_data.paymentMethod == "credit":
        # Credit: Not paid yet, full amount remaining, no entry until settlement
        payment_data["amountPaid"] = 0
        payment_data["amountRemaining"] = total
        payment_data["paymentEntries"] = []
    else:
        # COD: Not paid yet, full amount remaining, no entry until delivery
        payment_data["amountPaid"] = 0
        payment_data["amountRemaining"] = total
        payment_data["paymentEntries"] = []

    payment = await payment_repository.create(payment_data)

    # Create notification for new order
    await create_order_notification(order)

    # Create notification for new payment (if payment method is UPI)
    if order_data.paymentMethod == "upi":
        await create_payment_notification(payment)

    # Invoice for retail customers is auto-generated on delivery (not at order placement)

    # Clear cart
    await cart_repository.clearCart(current_user.id)

    # Save address to user's profile
    await user_repository.addSavedAddress(current_user.id, order_data.shippingAddress)
    # Update current address to the one just used
    await user_repository.update(current_user.id, {"address": order_data.shippingAddress})

    populated_order = await populate_order(order)
    email = populated_order.get("user", {}).email if populated_order.user else None
    if email:
        background_tasks.add_task(email_service.send_order_placed_email, email, populated_order)

    # ────────────────────────────────────────────────────────────────
    # Sub-order creation: split by seller
    # Only create sub-orders when the cart contains products from
    # more than one seller (including the platform / super-admin as
    # a seller bucket with sellerId=None).
    # ────────────────────────────────────────────────────────────────
    try:
        super_admin_doc = await user_repository.findOne({"role": "super_admin"})
        super_admin_id = str(super_admin_doc.id) if super_admin_doc else None

        # Fallback to super_admin for legacy products (H6)
        for oi in order_items:
            if not oi.get("sellerId") and super_admin_id:
                oi["sellerId"] = super_admin_id

        # Build a lookup of sellerId -> seller user doc (for name)
        seller_ids_in_order = {item.get("sellerId", item.get("seller_id")) for item in order_items if item.get("sellerId", item.get("seller_id"))}
        seller_docs = {}
        for sid in seller_ids_in_order:
            sdoc = await user_repository.findById(sid)
            if sdoc:
                seller_docs[sid] = sdoc

        # Group order_items by sellerId
        from collections import defaultdict

        groups: dict = defaultdict(list)
        for oi in order_items:
            sid = oi.get("sellerId")
            groups[sid].append(oi)

        # Only split if multiple seller groups exist
        if len(groups) > 1:
            parent_order_number = (order.order_number if order.order_number is not None else str(order.id))
            sub_order_ids = []

            # Build per-seller delivery option lookup from request
            seller_delivery_map = {}
            if order_data.sellerDeliveryOptions:
                for sdo in order_data.sellerDeliveryOptions:
                    seller_delivery_map[sdo.get("sellerId")] = sdo

            # Fetch delivery charge data once (same pincode for all sub-orders)
            try:
                await delivery_charge_repository.getChargeForLocation(
                    order_data.shippingAddress.get("state", ""),
                    order_data.shippingAddress.get("city", ""),
                    order_data.shippingAddress.get("district", ""),
                    order_data.shippingAddress.get("zipCode", ""),
                    effective_role,
                    subtotal,
                )
            except Exception:
                pass

            for idx, (seller_id, items_group) in enumerate(groups.items()):
                sub_number = sub_order_repository._generate_sub_order_number(parent_order_number, idx)

                # Per-group subtotal / tax
                grp_subtotal = sum((i.subtotal if i.subtotal is not None else 0) for i in items_group)
                grp_tax = sum((i.cgst if i.cgst is not None else 0) + (i.sgst if i.sgst is not None else 0) for i in items_group)
                grp_discount = sum((i.coupon_discount if i.coupon_discount is not None else 0) + (i.referral_discount if i.referral_discount is not None else 0) for i in items_group)

                # ── Delivery charge: always 0 on sub-orders ──────────────────
                # Delivery is charged once on the parent order based on the
                # customer's pincode. Sub-orders carry only item-level amounts.
                grp_shipping = 0.0
                grp_delivery_gst = 0.0
                grp_slot_info = None
                # Inherit urgent flag from the parent order request
                grp_is_urgent = bool(order_data.isUrgentDelivery)

                sdo = seller_delivery_map.get(str(seller_id) if seller_id else None)

                # Record the delivery slot on the sub-order (informational, no charge)
                if sdo and sdo.get("deliverySlotId") and sdo.get("deliverySlotDate"):
                    grp_slot_info = {
                        "configId": sdo.get("deliverySlotConfigId"),
                        "slotId": sdo.get("deliverySlotId"),
                        "date": sdo.get("deliverySlotDate"),
                    }
                elif order_data.deliverySlotId and order_data.deliverySlotDate:
                    # Single slot chosen for whole order — apply to all sub-orders
                    grp_slot_info = {
                        "configId": order_data.deliverySlotConfigId,
                        "slotId": order_data.deliverySlotId,
                        "date": order_data.deliverySlotDate,
                    }

                grp_total = round(grp_subtotal - grp_discount, 2)

                seller_name = ""
                if seller_id:
                    sdoc = seller_docs.get(str(seller_id))
                    if sdoc:
                        seller_name = sdoc.get("companyName") or sdoc.get("name") or ""
                else:
                    seller_name = "Platform"

                sub_order_data = {
                    "subOrderNumber": sub_number,
                    "parentOrderId": str(order.id),
                    "parentOrderNumber": parent_order_number,
                    "sellerId": str(seller_id) if seller_id else None,
                    "sellerName": seller_name,
                    "user": current_user.id,
                    "items": items_group,
                    "subtotal": round(grp_subtotal, 2),
                    "tax": round(grp_tax, 2),
                    "shipping": round(grp_shipping, 2),
                    "deliveryGst": round(grp_delivery_gst, 2),
                    "discount": round(grp_discount, 2),
                    "total": grp_total,
                    "orderType": order_type,
                    "status": "pending",
                    "paymentMethod": order_data.paymentMethod,
                    "paymentStatus": "paid" if order_data.paymentMethod == "upi" else "pending",
                    "isUrgentDelivery": grp_is_urgent,
                    "deliverySlot": grp_slot_info,
                    "shippingAddress": order_data.shippingAddress,
                    "billingAddress": order_data.billingAddress or order_data.shippingAddress,
                    "notes": order_data.notes,
                    "couponCode": coupon_code,
                    "couponInfo": coupon_info,
                    "createdAt": order.created_at,
                }
                sub = await sub_order_repository.create(sub_order_data)
                sub_order_ids.append(str(sub.id))

                # Notify the seller about their new sub-order (if it's a seller admin, not platform)
                if seller_id:
                    try:
                        await notification_repository.create(
                            {
                                "userId": seller_id,
                                "type": "new_sub_order",
                                "title": "New Order Received",
                                "message": f'New sub-order "{sub_number}" worth ₹{grp_total:.2f} received',
                                "data": {
                                    "subOrderId": str(sub.id),
                                    "subOrderNumber": sub_number,
                                    "parentOrderId": str(order.id),
                                    "amount": grp_total,
                                },
                            }
                        )
                    except Exception as notif_err:
                        logger.error("Error notifying seller %s: %s", seller_id, str(notif_err), exc_info=True)

            # Store sub-order references on the parent order
            await order_repository.update(
                str(order.id),
                {
                    "hasSubOrders": True,
                    "subOrderIds": sub_order_ids,
                },
            )
            # Refresh populated_order to include subOrderIds
            updated_parent = await order_repository.findById(str(order.id))
            populated_order = await populate_order(updated_parent)
    except Exception as sub_err:
        logger.error(
            "Sub-order creation failed (parent order %s still valid): %s", order.id, str(sub_err), exc_info=True
        )

    return populated_order


class TrackingUpdateRequest(BaseModel):
    trackingId: str
    courierPartner: Optional[str] = None


@router.put("/{order_id}/tracking", response_model=Order)
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
            raise HTTPException(status_code=403, detail="You do not have a sub-order in this order")

    update_payload = {
        "trackingId": data.trackingId,
        "courierPartner": data.courierPartner,
        "trackingUpdatedAt": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat() + "Z",
    }
    await order_repository.update(order_id, update_payload)

    # Push notification to customer
    try:
        from app.services.push_notification_service import push_notification_service

        await push_notification_service.send_to_user(
            str(order.user),
            {
                "title": "Order Shipped",
                "message": f"Your order #{(order.order_number if order.order_number is not None else order_id)} has been shipped. Tracking ID: {data.trackingId}",
                "data": {"orderId": order_id, "trackingId": data.trackingId, "type": "order_shipped"},
            },
        )
    except Exception as _ne:
        logger.warning("Tracking notification failed for order %s: %s", order_id, _ne)

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
        raise HTTPException(status_code=403, detail="Can only update delivery charge for business customer orders")

    # Only allow before dispatch
    if order.status not in ["pending", "confirmed", "processing"]:
        raise HTTPException(status_code=400, detail="Can only update delivery charge before order is dispatched")

    new_delivery_charge = request.newDeliveryCharge
    old_delivery_charge = (order.shipping if order.shipping is not None else 0)
    difference = new_delivery_charge - old_delivery_charge

    if difference == 0:
        raise HTTPException(status_code=400, detail="New delivery charge is same as current charge")

    # Update order totals
    new_total = (order.total if order.total is not None else 0) + difference

    await order_repository.update(order_id, {"shipping": new_delivery_charge, "total": new_total})

    # Update payment record based on payment method
    payments = await payment_repository.findByOrderId(order_id)
    if payments and len(payments) > 0:
        payment = payments[0]
        payment_method = (order.payment_method if order.payment_method is not None else "cod")

        if payment_method == "upi":
            # For UPI: Update amount remaining (to be settled during delivery as COD)
            new_amount_remaining = (payment.amount_remaining if payment.amount_remaining is not None else 0) + difference
            await payment_repository.update(
                payment.id, {"totalAmount": new_total, "amountRemaining": new_amount_remaining}
            )
        elif payment_method in ["credit", "cod"]:
            # For Credit/COD: Update amount remaining
            new_amount_remaining = (payment.amount_remaining if payment.amount_remaining is not None else 0) + difference
            await payment_repository.update(
                payment.id, {"totalAmount": new_total, "amountRemaining": new_amount_remaining}
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


async def _compute_fulfillment_status(sub_order_ids: list) -> Optional[str]:
    """
    Derive parent order fulfillmentStatus from sub-order states.
    Returns None if there are no sub-orders (single-seller, legacy flow).
    """
    if not sub_order_ids:
        return None

    statuses = []
    for so_id in sub_order_ids:
        so = await sub_order_repository.findById(so_id)
        if so:
            statuses.append((so.status if so.status is not None else "pending"))

    if not statuses:
        return None

    terminal_delivered = {"delivered", "returned"}
    terminal_cancelled = {"cancelled"}
    terminal = terminal_delivered | terminal_cancelled

    if all(s in terminal_delivered for s in statuses):
        return "fulfilled"
    if all(s in terminal_cancelled for s in statuses):
        return "failed"
    if any(s in terminal_delivered for s in statuses):
        return "partial"
    if all(s in terminal for s in statuses):
        return "failed"  # all cancelled/returned mix
    return "unfulfilled"


@router.put("/{order_id}/status", response_model=Order)
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
            raise HTTPException(status_code=403, detail="Valet can only mark orders as delivered")
        if order.assigned_valet != current_user.id:
            raise HTTPException(status_code=403, detail="Order not assigned to you")

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

            update_data.paymentStatus = "paid"
            update_data.codPaymentReceived = True
            update_data.codPaymentReceivedAt = datetime.now(__import__("datetime").timezone.utc).isoformat()

    if status_data.status == "out_for_delivery":
        update_data.shippedAt = None  # Will be set by repository
    elif status_data.status == "delivered":
        from datetime import datetime

        # Increment deliveredCount on the slot
        try:
            config_id = order.delivery_slot_config_id
            slot_id = order.delivery_slot_id
            if config_id and slot_id:
                from app.db.storage_factory import get_storage as _get_storage
                slot_storage = _get_storage("deliverySlots")
                slot_config = await slot_storage.findById(config_id)
                if slot_config:
                    slots_list = slot_config.get("slots", [])
                    for sl in slots_list:
                        if sl.id == slot_id:
                            sl["deliveredCount"] = (sl.delivered_count if sl.delivered_count is not None else 0) + 1
                            break
                    await slot_storage.update(config_id, {"slots": slots_list})
        except Exception as e:
            logger.error("Failed to increment deliveredCount for config %s slot %s: %s", order.delivery_slot_config_id, order.delivery_slot_id, str(e), exc_info=True)

        if order.payment_method == "cod" and "paymentStatus" not in update_data:
            update_data.paymentStatus = "paid"
            update_data.codPaymentReceived = True
            update_data.codPaymentReceivedAt = datetime.now(__import__("datetime").timezone.utc).isoformat()

            # Create or update payment record for COD
            existing_payment = await payment_repository.findByOrderId(order.id)
            if existing_payment and len(existing_payment) > 0:
                payment = existing_payment[0]
                # Check if payment entry exists, if not add one
                if payment.payment_entries and len((payment.payment_entries or [])) > 0:
                    # Update existing payment entry
                    await payment_repository.updatePaymentEntry(
                        payment.id,
                        payment["paymentEntries"][0].get("entryId"),
                        {"amount": order.total or payment.total_amount, "verified": False},
                    )
                    updated_payment = await payment_repository.update(
                        payment.id,
                        {"amountPaid": order.total or payment.total_amount, "amountRemaining": 0},
                    )
                    # Create notification for COD payment
                    await create_payment_notification(updated_payment)
                else:
                    # Add new payment entry for COD payment received
                    updated_payment_with_entry = await payment_repository.addPaymentEntry(
                        payment.id,
                        {"amount": order.total or payment.total_amount, "image": None, "verified": False},
                    )
                    # Create notification for COD payment
                    await create_payment_notification(
                        {
                            "_id": updated_payment_with_entry.id,
                            "paymentId": updated_payment_with_entry.get("paymentId")
                            or updated_payment_with_entry.id,
                            "orderId": updated_payment_with_entry.get("orderId"),
                            "totalAmount": (order.total if order.total is not None else payment.get("totalAmount", 0)),
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
                        "orderDate": order.created_at,
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
                        "paymentId": new_payment.get("paymentId") or new_payment.id,
                        "orderId": new_payment.get("orderId"),
                        "totalAmount": new_payment.get("totalAmount", 0),
                        "paymentMethod": "cod",
                        "createdAt": datetime.now(__import__("datetime").timezone.utc).isoformat() + "Z",
                    }
                )
    elif status_data.status == "cancelled":
        # For cancelled orders, restore stock and refund credit if credit payment
        if order.payment_method == "credit":
            user = await user_repository.findById(order.user)
            if user and user.credit_used:
                new_credit_used = max(0, ((user.credit_used if user.credit_used is not None else 0) or 0) - ((order.total if order.total is not None else 0) or 0))
                await user_repository.update(order.user, {"creditUsed": new_credit_used})

        # Restore stock atomically — uses SELECT … FOR UPDATE so a concurrent new order
        # cannot race against this restoration and produce a wrong stock count.
        for item in (order.items or []):
            if item.product and (item.get("quantity") if isinstance(item, dict) else item.quantity):
                await product_repository.increment_stock_atomic(str(item.product), int(((item.get("quantity") if isinstance(item, dict) else item.quantity) if (item.get("quantity") if isinstance(item, dict) else item.quantity) is not None else 0)))

        from datetime import datetime

        update_data.cancelledAt = datetime.now(__import__("datetime").timezone.utc).isoformat()
        update_data.cancelledBy = current_user.id

        # Mark existing payment as cancelled (do NOT create new records or mark as paid)
        existing_payments_cancel = await payment_repository.findByOrderId(order_id)
        if existing_payments_cancel:
            pay = existing_payments_cancel[0]
            await payment_repository.update(
                pay.id,
                {"paymentStatus": "cancelled", "amountRemaining": 0},
            )

    updated_order = await order_repository.update(order_id, update_data)
    populated_order = await populate_order(updated_order)

    # ── C5: Cascade terminal status from parent to sub-orders ─────────────────
    if status_data.status in ("cancelled", "delivered"):
        from datetime import datetime as _dt

        sub_ids = updated_order.get("subOrderIds") or []
        for _so_id in sub_ids:
            _so = await sub_order_repository.findById(_so_id)
            if not _so:
                continue
            # Skip sub-orders already in a terminal state
            if _so.status in ("delivered", "cancelled", "returned"):
                continue
            if status_data.status == "cancelled":
                await sub_order_repository.update(
                    _so_id,
                    {
                        "status": "cancelled",
                        "cancelledAt": _dt.utcnow().isoformat() + "Z",
                    },
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
                    logger.warning("Commission stamp failed for sub-order %s: %s", _so_id, _ce)
                await sub_order_repository.update(_so_id, _cascade)

    # Recompute parent fulfillmentStatus from all sub-orders
    _f_status = await _compute_fulfillment_status(updated_order.get("subOrderIds") or [])
    if _f_status:
        await order_repository.update(order_id, {"fulfillmentStatus": _f_status})
        updated_order["fulfillmentStatus"] = _f_status

    if status_data.status == "delivered":
        email = populated_order.get("user", {}).email if populated_order.user else None
        if email:
            background_tasks.add_task(email_service.send_order_delivered_email, email, populated_order)

        # Auto-generate invoice for retail customers on delivery
        order_user = await user_repository.findById(order.user)
        if order_user and order_user.role == "customer" and not updated_order.get("invoicePath"):
            try:
                from datetime import datetime as _dt

                payments_for_invoice = await payment_repository.findByOrderId(order_id)
                payment_for_invoice = payments_for_invoice[0] if payments_for_invoice else None
                super_admin = await user_repository.findOne({"role": "super_admin"})
                if payment_for_invoice:
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
                        {"invoicePath": invoice_path, "invoiceGeneratedAt": _dt.utcnow().isoformat() + "Z"},
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


@router.put("/{order_id}/accept", response_model=Order)
async def accept_order(order_id: str, current_user: User = Depends(require_super_admin)):
    """Accept order (Pending -> Processing)"""
    order = await order_repository.findById(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "pending":
        raise HTTPException(status_code=400, detail="Only pending orders can be accepted")

    # UPI orders must have a verified payment entry before acceptance
    if order.payment_method == "upi":
        payments = await payment_repository.findByOrderId(order_id)
        payment = payments[0] if payments else None
        entries = (payment.payment_entries or []) if payment else []
        any_verified = any(entry.get("verified") for entry in entries)
        if not any_verified:
            raise HTTPException(status_code=400, detail="UPI payment must be verified before accepting the order")

    updated_order = await order_repository.update(order_id, {"status": "processing"})

    populated_order = await populate_order(updated_order)
    return populated_order


class DeclineOrderRequest(BaseModel):
        reason: str


@router.put("/{order_id}/decline", response_model=Order)
async def decline_order(
    order_id: str, decline_data: DeclineOrderRequest, current_user: User = Depends(require_super_admin)
):
    """Decline order (with reason, only COD/Credit)"""
    order = await order_repository.findById(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.payment_method == "upi":
        raise HTTPException(status_code=400, detail="UPI orders cannot be declined")

    if order.payment_method not in ["cod", "credit"]:
        raise HTTPException(status_code=400, detail="Only COD and Credit orders can be declined")

    if order.status != "pending":
        raise HTTPException(status_code=400, detail="Only pending orders can be declined")

    # For credit orders, refund credit used
    if order.payment_method == "credit":
        user = await user_repository.findById(order.user)
        if user and user.credit_used:
            new_credit_used = max(0, ((user.credit_used if user.credit_used is not None else 0) or 0) - ((order.total if order.total is not None else 0) or 0))
            await user_repository.update(order.user, {"creditUsed": new_credit_used})

    # Restore stock atomically — uses SELECT … FOR UPDATE so a concurrent new order
    # cannot race against this restoration and produce a wrong stock count.
    for item in (order.items or []):
        if item.product and (item.get("quantity") if isinstance(item, dict) else item.quantity):
            await product_repository.increment_stock_atomic(str(item.product), int(((item.get("quantity") if isinstance(item, dict) else item.quantity) if (item.get("quantity") if isinstance(item, dict) else item.quantity) is not None else 0)))

    updated_order = await order_repository.update(
        order_id, {"status": "declined", "declineReason": decline_data.reason}
    )

    populated_order = await populate_order(updated_order)
    return populated_order


@router.put("/{order_id}/dispatch", response_model=Order)
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
            raise HTTPException(status_code=403, detail="You can only dispatch your own orders")

    if order.status != "processing":
        raise HTTPException(status_code=400, detail="Only processing orders can be dispatched")

    valet = await user_repository.findById(valet_data.valetId)
    if not valet or valet.role != "valet":
        raise HTTPException(status_code=400, detail="Invalid valet")

    from datetime import datetime

    now_iso = datetime.now(__import__("datetime").timezone.utc).isoformat() + "Z"
    is_urgent = (order.is_urgent_delivery if order.is_urgent_delivery is not None else False)
    timeout_minutes = 5 if is_urgent else 20

    updated_order = await order_repository.update(
        order_id,
        {
            "status": "pending_valet",
            "pendingValetId": valet_data.valetId,
            "valetAssignedAt": now_iso,
            "valetDeclineHistory": [],
            "valetCascadeCount": 0,
        },
    )

    # Push notification to the valet
    try:
        from app.services.push_notification_service import push_notification_service

        timeout_label = "5 minutes" if is_urgent else "20 minutes"
        await push_notification_service.send_to_user(
            valet_data.valetId,
            {
                "title": "New Delivery Request",
                "message": (
                    f"You have a new delivery order #{(order.order_number if order.order_number is not None else order_id)}. "
                    f"Please respond within {timeout_label}."
                ),
                "link": f"/valet/orders/{order_id}",
                "data": {
                    "orderId": order_id,
                    "type": "valet_assignment",
                    "isUrgent": is_urgent,
                    "timeoutMinutes": timeout_minutes,
                },
            },
        )
    except Exception as push_err:
        logger.warning("[Dispatch] Push notification to valet failed: %s", push_err)
        # Non-fatal — order is already in pending_valet state

    populated_order = await populate_order(updated_order)
    return populated_order


@router.get("/valet/pending", response_model=List[Order])
async def get_valet_pending_orders(current_user: User = Depends(get_current_user)):
    if current_user.role != "valet":
        raise HTTPException(status_code=403, detail="Only valets can view pending assignments")
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
# @router.put("/{order_id}/valet-response", response_model=Order)
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
#         updated_order = await order_repository.update(order_id, {
#             "status": "shipped",
#             "assignedValet": str(current_user.id),
#             "pendingValetId": None,
#             "shippedAt": now_iso,
#             "invoiceUrl": invoice.get("url") if invoice else None
#         })
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
#         await order_repository.update(order_id, {
#             "valetDeclineHistory": history,
#             "pendingValetId": None
#         })
#         order["valetDeclineHistory"] = history
#         order["pendingValetId"] = None
#
#         from app.jobs.valet_timeout_job import _cascade_or_revert
#         await _cascade_or_revert(order)
#         return await populate_order(await order_repository.findById(order_id))
# ── END DUPLICATE ROUTE ───────────────────────────────────────────────────────


@router.put("/{order_id}/cancel", response_model=Order)
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
        raise HTTPException(status_code=400, detail="Only COD and Credit orders can be cancelled")

    # Orders can only be cancelled before they are Accepted (status is still 'pending')
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="Orders can only be cancelled before they are accepted")

    # For credit orders, refund credit used
    if order.payment_method == "credit":
        user = await user_repository.findById(order.user)
        if user and user.credit_used:
            new_credit_used = max(0, ((user.credit_used if user.credit_used is not None else 0) or 0) - ((order.total if order.total is not None else 0) or 0))
            await user_repository.update(order.user, {"creditUsed": new_credit_used})

    # Restore stock atomically — uses SELECT … FOR UPDATE so a concurrent new order
    # cannot race against this restoration and produce a wrong stock count.
    for item in (order.items or []):
        if item.product and (item.get("quantity") if isinstance(item, dict) else item.quantity):
            await product_repository.increment_stock_atomic(str(item.product), int(((item.get("quantity") if isinstance(item, dict) else item.quantity) if (item.get("quantity") if isinstance(item, dict) else item.quantity) is not None else 0)))

    from datetime import datetime

    updated_order = await order_repository.update(
        order_id,
        {"status": "cancelled", "cancelledAt": datetime.now(__import__("datetime").timezone.utc).isoformat(), "cancelledBy": current_user.id},
    )

    populated_order = await populate_order(updated_order)
    return populated_order


@router.put("/{order_id}/assign-valet", response_model=Order)
async def assign_valet(
    order_id: str, valet_data: AssignValetRequest, current_user: User = Depends(require_super_admin)
):
    order = await order_repository.findById(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    valet = await user_repository.findById(valet_data.valetId)
    if not valet or valet.role != "valet":
        raise HTTPException(status_code=400, detail="Invalid valet")

    updated_order = await order_repository.update(order_id, {"assignedValet": valet_data.valetId})

    populated_order = await populate_order(updated_order)
    return populated_order


# ─── Valet Response (Accept / Decline) ───────────────────────────────────────


class ValetResponseRequest(BaseModel):
    action: str  # "accept" | "decline"
    declineReason: Optional[str] = None


@router.put("/{order_id}/valet-response", response_model=Order)
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
        raise HTTPException(status_code=400, detail="action must be 'accept' or 'decline'")

    order = await order_repository.findById(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "pending_valet":
        raise HTTPException(status_code=400, detail="Order is not awaiting valet confirmation")

    # Valets can only respond to orders assigned to them
    if current_user.role == "valet":
        if str((order.pending_valet_id or "")) != str(current_user.id):
            raise HTTPException(status_code=403, detail="This order is not assigned to you")

    # Check if the offer window has expired
    assigned_at_str = (order.valet_assigned_at or "")
    is_urgent = (order.is_urgent_delivery if order.is_urgent_delivery is not None else False)
    timeout_minutes = 5 if is_urgent else 20
    if assigned_at_str:
        try:
            assigned_at = datetime.fromisoformat(assigned_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
            if datetime.now(__import__("datetime").timezone.utc) >= assigned_at + timedelta(minutes=timeout_minutes):
                raise HTTPException(
                    status_code=400,
                    detail="The acceptance window for this order has expired",
                )
        except HTTPException:
            raise
        except Exception:
            pass

    now_iso = datetime.now(__import__("datetime").timezone.utc).isoformat() + "Z"
    valet_id = str(current_user.id) if current_user.role == "valet" else str((order.pending_valet_id or ""))
    seller_id = order.seller_id

    # ── ACCEPT ────────────────────────────────────────────────────────────────
    if response_data.action == "accept":
        updated_order = await order_repository.update(
            order_id,
            {
                "status": "shipped",
                "assignedValet": valet_id,
                "pendingValetId": None,
                "valetAcceptedAt": now_iso,
                "shippedAt": now_iso,
            },
        )

        # Fetch valet details once for notifications
        valet = await user_repository.findById(valet_id)
        valet_name = (valet.name if valet.name is not None else "The valet") if valet else "The valet"

        # ── Multi-seller: propagate assignedValet to all sub-orders, notify each seller ──
        # NOTE: hasSubOrders/subOrderIds not in relational DB — query sub-orders directly.
        sub_orders_for_order = await sub_order_repository.findByParentOrder(order_id)
        if sub_orders_for_order:
            notified_sellers: set = set()
            for _so in sub_orders_for_order:
                _so_id = str(_so.id)
                # Set assignedValet on each sub-order so sellers can see who's picking up
                await sub_order_repository.update(
                    _so_id,
                    {
                        "assignedValet": valet_id,
                        "pickupStatus": "pending_pickup",
                    },
                )
                _seller_id = _so.get("sellerId")
                if _seller_id and _seller_id not in notified_sellers:
                    notified_sellers.add(_seller_id)
                    try:
                        from app.services.push_notification_service import push_notification_service

                        await push_notification_service.send_to_user(
                            _seller_id,
                            {
                                "title": "Valet is Coming to Pick Up",
                                "message": (
                                    f"{valet_name} accepted order #{(order.order_number if order.order_number is not None else order_id)} "
                                    "and will collect your items soon."
                                ),
                                "link": f"/seller/orders/{order_id}",
                                "data": {
                                    "orderId": order_id,
                                    "subOrderId": _so_id,
                                    "type": "valet_accepted",
                                },
                            },
                        )
                    except Exception as e:
                        logger.warning("[ValetResponse] Push to seller %s failed: %s", _seller_id, e)
        else:
            # Single-seller: notify the order's seller as before
            if seller_id:
                try:
                    from app.services.push_notification_service import push_notification_service

                    await push_notification_service.send_to_user(
                        seller_id,
                        {
                            "title": "Order Dispatched",
                            "message": f"{valet_name} accepted order #{(order.order_number if order.order_number is not None else order_id)} and is on the way.",
                            "link": f"/seller/orders/{order_id}",
                            "data": {"orderId": order_id, "type": "valet_accepted"},
                        },
                    )
                except Exception as e:
                    logger.warning("[ValetResponse] Push to seller failed: %s", e)

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
                        {"invoicePath": invoice_path, "invoiceGeneratedAt": now_iso},
                    )
            except Exception as invoice_err:
                logger.error("[ValetResponse] Invoice generation failed: %s", invoice_err)

        populated_order = await populate_order(updated_order)
        return populated_order

    # ── DECLINE ───────────────────────────────────────────────────────────────
    decline_history = list(order.valet_decline_history or [])
    if valet_id and not any(isinstance(d, dict) and d.get("valetId") == valet_id for d in decline_history) and valet_id not in decline_history:
        decline_history.append({"valetId": valet_id, "reason": "declined"})

    await order_repository.update(
        order_id,
        {
            "valetDeclinedAt": now_iso,
            "valetDeclineReason": response_data.declineReason or "",
            "valetDeclineHistory": decline_history,
            "pendingValetId": None,
            "valetCascadeCount": (order.valet_cascade_count or 0) + 1,
        },
    )

    # Try to find the next available valet (cascade)
    from app.jobs.valet_timeout_job import _find_next_available_valet

    order_fresh = await order_repository.findById(order_id)
    next_valet = await _find_next_available_valet(order_fresh, decline_history)

    if next_valet:
        next_valet_id = str(next_valet.id)
        updated_order = await order_repository.update(
            order_id,
            {
                "pendingValetId": next_valet_id,
                "valetAssignedAt": now_iso,
            },
        )
        # Notify next valet
        try:
            from app.services.push_notification_service import push_notification_service

            timeout_label = "5 minutes" if is_urgent else "20 minutes"
            await push_notification_service.send_to_user(
                next_valet_id,
                {
                    "title": "New Delivery Request",
                    "message": (
                        f"You have a new delivery order #{(order.order_number if order.order_number is not None else order_id)}. "
                        f"Please respond within {timeout_label}."
                    ),
                    "link": f"/valet/orders/{order_id}",
                    "data": {"orderId": order_id, "type": "valet_assignment", "isUrgent": is_urgent},
                },
            )
        except Exception as e:
            logger.warning("[ValetResponse] Push to next valet failed: %s", e)
    else:
        # No more valets — revert to processing
        updated_order = await order_repository.update(
            order_id,
            {"status": "processing", "pendingValetId": None, "valetAssignedAt": None},
        )
        # Notify seller
        if seller_id:
            try:
                from app.services.push_notification_service import push_notification_service

                await push_notification_service.send_to_user(
                    seller_id,
                    {
                        "title": "No Valets Available — Reassign Required",
                        "message": (
                            f"All valets declined order #{(order.order_number if order.order_number is not None else order_id)}. "
                            "Please assign a valet manually."
                        ),
                        "link": f"/seller/orders/{order_id}",
                        "data": {"orderId": order_id, "type": "valet_all_declined"},
                    },
                )
            except Exception as e:
                logger.warning("[ValetResponse] Push to seller (all declined) failed: %s", e)

    populated_order = await populate_order(updated_order)
    return populated_order


# ─── Valet Confirms Pickup from a Seller (multi-seller orders) ────────────────


@router.put("/{order_id}/sub-orders/{sub_order_id}/confirm-pickup", response_model=Order)
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
            raise HTTPException(status_code=403, detail="This order is not assigned to you")

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
        raise HTTPException(status_code=400, detail="Sub-order does not belong to this order")

    # Idempotency: already picked up
    if sub_order.pickup_status == "picked_up":
        raise HTTPException(status_code=400, detail="Pickup already confirmed for this seller")

    # Mark this sub-order as picked up (pickedUpAt is auto-stamped by the repository)
    await sub_order_repository.update(sub_order_id, {"pickupStatus": "picked_up"})

    # Re-fetch all sibling sub-orders to check if ALL pickups are done
    all_sub_orders = await sub_order_repository.findByParentOrder(order_id)
    remaining = [s for s in all_sub_orders if s.pickup_status != "picked_up"]

    # now_iso = datetime.now(__import__("datetime").timezone.utc).isoformat() + "Z"  # was a dangling no-op after find-and-replace stripped the assignment; unused in this block

    if not remaining:
        # ── All sellers picked up — transition parent to 'out_for_delivery' ──
        await order_repository.update(order_id, {"status": "out_for_delivery"})
        logger.info(
            "[ConfirmPickup] All %d sub-orders picked up for order %s — moving to out_for_delivery",
            len(all_sub_orders),
            order_id,
        )
        # Notify the customer
        try:
            from app.services.push_notification_service import push_notification_service

            await push_notification_service.send_to_user(
                order.user,
                {
                    "title": "Your Order is On the Way! 🚴",
                    "message": (
                        f"Your order #{(order.order_number if order.order_number is not None else order_id)} has been collected "
                        "from all sellers and is now heading to you."
                    ),
                    "link": f"/orders/{order_id}",
                    "data": {"orderId": order_id, "type": "order_out_for_delivery"},
                },
            )
        except Exception as e:
            logger.warning("[ConfirmPickup] Customer notification failed: %s", e)

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


@router.post("/{order_id}/settle-credit", response_model=Order)
async def settle_credit(
    order_id: str, settle_data: SettleCreditRequest, current_user: User = Depends(get_current_user)
):
    """Settle credit for an order (wholesaler only)"""

    order = await order_repository.findById(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Check access
    if order.user != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Check if order payment method is credit
    if order.payment_method != "credit":
        raise HTTPException(status_code=400, detail="This order is not a credit order")

    user = await user_repository.findById(current_user.id)
    if user.role != "wholesaler":
        raise HTTPException(status_code=403, detail="Only business customers can settle credit")

    # Find payment record
    payments = await payment_repository.findByOrderId(order_id)
    if not payments or len(payments) == 0:
        raise HTTPException(status_code=404, detail="Payment record not found")
    payment = payments[0]

    settle_amount = float(settle_data.amount)
    remaining_amount = (payment.amount_remaining if payment.amount_remaining is not None else payment.get("totalAmount", 0) - ((payment.amount_paid if payment.amount_paid is not None else 0) or 0)
    )

    if settle_amount > remaining_amount:
        raise HTTPException(status_code=400, detail=f"Amount cannot exceed remaining amount: ₹{remaining_amount:.2f}")

    # Add payment entry
    payment_image = settle_data.paymentImage or settle_data.upiPaymentScreenshot
    await payment_repository.addPaymentEntry(
        payment.id, {"amount": settle_amount, "image": payment_image, "verified": False}
    )

    # Update user credit
    new_credit_used = max(0, ((user.credit_used if user.credit_used is not None else 0) or 0) - settle_amount)
    await user_repository.update(current_user.id, {"creditUsed": new_credit_used})

    # Update payment record
    updated_payment = await payment_repository.findById(payment.id)

    # If fully paid, update order payment status
    if updated_payment.get("amountRemaining", 0) <= 0:
        await order_repository.update(order_id, {"paymentStatus": "paid"})

    return {"message": "Credit settled successfully", "payment": updated_payment, "remainingCredit": new_credit_used}


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
        raise HTTPException(status_code=400, detail="Payment record not found for this order")

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
        order_id, {"invoicePath": invoice_path, "invoiceGeneratedAt": datetime.now(__import__("datetime").timezone.utc).isoformat() + "Z"}
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
        raise HTTPException(status_code=404, detail="Invoice not generated yet")

    file_path = Path(DATA_DIR).parent / order["invoicePath"].lstrip("/")

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
        query.status = status
    skip = (page - 1) * limit
    sub_orders = await sub_order_repository.findBySeller(seller_id, query, skip=skip, limit=limit)
    total = await sub_order_repository.count({"sellerId": seller_id, **query})
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

    allowed_statuses = ["pending", "confirmed", "processing", "shipped", "out_for_delivery", "cancelled"]
    if status_data.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {', '.join(allowed_statuses)}")

    from datetime import datetime as _dt

    update_fields = {"status": status_data.status}
    if status_data.status == "delivered":
        update_fields["deliveredAt"] = _dt.utcnow().isoformat() + "Z"
        # Stamp commission on sub-order delivery
        try:
            from app.routers.commission import stamp_commission_on_delivery

            _comm = await stamp_commission_on_delivery(sub_order)
            update_fields.update(_comm)
        except Exception as _ce:
            logger.warning("Commission stamp failed for sub-order %s: %s", sub_order_id, _ce)
    elif status_data.status == "cancelled":
        update_fields["cancelledAt"] = _dt.utcnow().isoformat() + "Z"
    elif status_data.status == "shipped":
        update_fields["shippedAt"] = _dt.utcnow().isoformat() + "Z"

    updated = await sub_order_repository.update(sub_order_id, update_fields)

    # Bubble up: recalculate parent fulfillmentStatus
    parent_id = sub_order.parent_order_id
    if parent_id:
        parent = await order_repository.findById(parent_id)
        if parent and parent.get("subOrderIds"):
            _f_status = await _compute_fulfillment_status(parent["subOrderIds"])
            if _f_status:
                await order_repository.update(parent_id, {"fulfillmentStatus": _f_status})

    return updated


@router.get("/admin/sub-orders", response_model=PaginatedSubOrdersResponse)
async def get_all_sub_orders(
    sellerId: Optional[str] = None,
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
        query.status = status
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
        logging.getLogger(__name__).warning("Commission promotion failed: %s", e)

    return {
        "subOrders": sub_orders,
        "totalCount": total,
        "page": page,
        "limit": limit,
    }







