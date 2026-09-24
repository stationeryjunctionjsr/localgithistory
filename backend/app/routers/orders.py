from app.models.daos import NotificationInternalCreate
from app.models.payment import PaymentEntry
import uuid
from app.models.schemas import UserSnippet, ValetSnippet, UserInternalUpdate
import logging
from app.models.schemas import UserSnippet, ValetSnippet, PopulatedOrderResponse, PopulatedOrderItemResponse
from app.db.storage_factory import get_storage
from app.models.user import User
from app.models.order import Order, OrderInternalCreate, OrderInternalUpdate
from app.models.daos import BundleInternalUpdate
from app.models.sub_order import SubOrder, SubOrderInternalCreate, SubOrderInternalUpdate, SubOrderItem
from app.models.product import Product
from pydantic import BaseModel, ConfigDict, Field
class GenerateInvoiceResponse(BaseModel):
    success: bool
    invoiceUrl: str
from fastapi.responses import FileResponse
from app.schemas.orders import PaginatedOrdersResponse, PaginatedSubOrdersResponse, DeliveryChargeUpdateResponse
from app.models.schemas import UserSnippet, ValetSnippet, Address, OrderItemCreate, SellerDeliveryOption, ItemSnippet as OrderItem
from typing import Dict, Any
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Header, status
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


def _resolve_product_seller_id(product: Product, serviceable_seller_ids: list[str] = None) -> str:
    if product.sellers:
        return product.sellers[0].sellerId
    # Product has no seller_id field — sellers list is the sole source
    return None


# Helper function to create order notification
async def create_order_notification(order):
    order_zone_id = None
    try:
        super_admin = await user_repository.findOne({"role": "super_admin"})
        if not super_admin:
            return

        import uuid
        await notification_repository.create(
            NotificationInternalCreate(**{
                "_id": str(uuid.uuid4()),
                "userId": super_admin.id,
                "type": "new_order",
                "title": "New Order Received",
                "message": f'New order "{(order.order_number if order.order_number is not None else order.id)}" worth ₹{(order.total if order.total is not None else 0):.2f} received',
                "metadata": {
                    "orderId": order.id,
                    "orderNumber": (order.order_number if order.order_number is not None else order.id),
                    "amount": (order.total if order.total is not None else 0),
                    "userId": order.user,
                    "createdAt": order.created_at.isoformat() if order.created_at else None,
                }
            })
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
        import uuid
        await notification_repository.create(
            NotificationInternalCreate(**{
                "_id": str(uuid.uuid4()),
                "userId": super_admin.id,
                "type": "new_payment",
                "title": "New Payment Received",
                "message": f'New payment "{payment_id}" worth ₹{(payment.total_amount if payment.total_amount is not None else 0):.2f} received',
                "metadata": {
                    "paymentId": payment.id,
                    "paymentIdFormatted": payment_id,
                    "orderId": payment.order_id,
                    "amount": (payment.total_amount if payment.total_amount is not None else 0),
                    "paymentMethod": payment.payment_method,
                    "createdAt": payment.created_at or datetime.now(__import__("datetime").timezone.utc).isoformat() + "Z",
                }
            })
        )
    except Exception as e:
        logger.error(
            "Error creating payment notification for payment %s: %s", payment.id, str(e), exc_info=True
        )


# Helper schemas for order creation
class OrderCreateRequest(BaseModel):
    shippingAddress: Address
    billingAddress: Optional[Address] = None
    paymentMethod: str = "cod"  # 'cod', 'upi', or 'credit'
    upiPaymentScreenshot: Optional[str] = None
    notes: Optional[str] = None
    couponCode: Optional[str] = None  # Coupon code to apply
    referralCode: Optional[str] = None  # Referral code to apply
    discount: Optional[float] = 0
    printedBill: Optional[bool] = False
    items: Optional[List[OrderItemCreate]] = None  # [{productId, quantity}] - optional, if not provided uses user's cart
    isUrgentDelivery: Optional[bool] = False
    deliverySlotId: Optional[str] = None  # slot.id within a slot config
    deliverySlotConfigId: Optional[str] = None  # _id of the DeliverySlotConfig doc
    deliverySlotDate: Optional[str] = None  # ISO date string e.g. "2026-07-15"
    # Per-seller delivery options for split-cart orders
    # [{sellerId, isUrgentDelivery, deliverySlotId, deliverySlotConfigId, deliverySlotDate}]
    sellerDeliveryOptions: Optional[List[SellerDeliveryOption]] = None


from app.models.schemas import VariantAttributes, CouponResponse


class CalculatedOrderItem(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    product: Optional[str] = None
    sellerId: Optional[str] = None
    productName: Optional[str] = None
    quantity: int = 1
    sellAsCase: Optional[bool] = False
    price: float = 0.0
    priceBeforeCoupon: float = 0.0
    couponDiscount: float = 0.0
    referralDiscount: float = 0.0
    coupon_discount: float = 0.0
    referral_discount: float = 0.0
    subtotal: float = 0.0
    singleUnitPrice: float = 0.0
    singleUnitTaxableValue: float = 0.0
    singleUnitCGST: float = 0.0
    singleUnitSGST: float = 0.0
    numberOfSingleUnits: int = 1
    gst: float = 0.0
    taxableValue: float = 0.0
    cgst: float = 0.0
    sgst: float = 0.0
    variantAttributes: Optional[VariantAttributes] = None
    variant_attributes: Optional[VariantAttributes] = None


class OrderStatusUpdate(BaseModel):
        status: str


class AssignValetRequest(BaseModel):
    valetId: str


class ConfirmPickupRequest(BaseModel):
    """Sent by valet when physically collecting items from a seller's location."""

    notes: Optional[str] = None


class LocationDeliveryCharge(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    charge: float = 0.0
    minCartValue: float = 0.0
    isApplicableToRole: bool = True
    urgentDeliveryCharge: Optional[float] = None
    urgentDeliveryAvailable: Optional[bool] = False


class CouponDetailModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: Optional[str] = Field(None, alias="_id")
    code: Optional[str] = None
    discountType: Optional[str] = Field(None, alias="discount_type")
    discountValue: Optional[float] = Field(0.0, alias="discount_value")
    typeOfDiscount: Optional[str] = Field(None, alias="type_of_discount")
    method: Optional[str] = None
    couponMode: Optional[str] = Field(None, alias="coupon_mode")

    @property
    def discount_type(self) -> Optional[str]:
        return self.discountType

    @property
    def discount_value(self) -> Optional[float]:
        return self.discountValue

    @property
    def type_of_discount(self) -> Optional[str]:
        return self.typeOfDiscount


class ItemDiscountEntry(BaseModel):
    """Maps a cart item index to its coupon discount amount."""
    model_config = ConfigDict(extra="forbid")
    itemIndex: int
    discountAmount: float


class CouponValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    valid: bool = False
    message: Optional[str] = None
    coupon: Optional[CouponDetailModel] = None
    discount: float = 0.0
    eligibleItemIndices: Optional[List[int]] = None
    itemDiscounts: Optional[List[ItemDiscountEntry]] = None
    bxgyItemIndices: Optional[List[int]] = None


class ReferralProgramSegmentSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    segment: str = "retail"
    discountType: str = Field("percentage", alias="discount_type")
    discountValue: float = Field(0.0, alias="discount_value")
    isActive: bool = Field(False, alias="is_active")

    @property
    def is_active(self) -> bool:
        return self.isActive

    @property
    def discount_type(self) -> str:
        return self.discountType

    @property
    def discount_value(self) -> float:
        return self.discountValue


class ReferralSettingsModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    retail: ReferralProgramSegmentSettings = Field(default_factory=ReferralProgramSegmentSettings)
    business: Optional[ReferralProgramSegmentSettings] = None


async def populate_orders(orders: list[Any]) -> list[PopulatedOrderResponse]:
    """
    Bulk populates references (user, assignedValet, products, and payment) for a list of orders.
    Optimized to minimize DB queries by fetching all needed references in bulk.
    Returns strongly-typed Pydantic PopulatedOrderResponse models.
    """
    if not orders:
        return []

    user_ids = set()
    valet_ids = set()
    product_ids = set()
    order_ids = set()

    # 1. Collect all unique IDs across all orders
    for order in orders:
        if order.user:
            user_ids.add(str(order.user))

        # Order.assigned_valet is the snake_case Pydantic field (alias: assignedValet)
        if order.assigned_valet:
            valet_ids.add(str(order.assigned_valet))

        if order.id:
            order_ids.add(str(order.id))

        for item in order.items if order.items else []:
                # ItemSnippet.product holds the product ID reference
                pid = item.productId or item.product
                if pid and str(pid).isdigit():
                    product_ids.add(str(pid))

    # 2. Fetch all required users, valets, products, and payments in parallel
    users_task = get_storage("users").findAll({"allowed_ids": list(user_ids.union(valet_ids))}) if user_ids.union(valet_ids) else None
    products_task = get_storage("products").findAll({"allowed_ids": list(product_ids)}) if product_ids else None
    payments_task = get_storage("payments").findAll({"allowed_order_ids": list(order_ids)}) if order_ids else None

    # Execute DB queries concurrently (if any)
    users_list = await users_task if users_task else []
    products_list = await products_task if products_task else []
    payments_list = await payments_task if payments_task else []

    # 3. Build lookup maps — u.id and p.id are declared Pydantic fields
    users_map = {str(u.id): u for u in users_list if u.id}
    products_map = {str(p.id): p for p in products_list if p.id}
    payments_map: dict = {}
    for p in payments_list:
        # Payment.order_id is the declared Pydantic field (alias: orderId)
        oid = str(p.order_id) if p.order_id else None
        if oid:
            if oid not in payments_map:
                payments_map[oid] = []
            payments_map[oid].append(p)

    # 4. Construct fully populated responses
    populated = []
    for order in orders:
        o_user = str(order.user) if order.user else None
        user = users_map[o_user] if o_user and o_user in users_map else None

        # assigned_valet is the snake_case Pydantic field on Order
        o_valet = str(order.assigned_valet) if order.assigned_valet else None
        valet = users_map[o_valet] if o_valet and o_valet in users_map else None

        o_id = str(order.id) if order.id else None
        payment_entries = payments_map[o_id] if o_id and o_id in payments_map else []

        o_items = order.items if order.items else []
        populated_items = []

        for i_dict in o_items:
            # i_dict is a Pydantic ItemSnippet (OrderItem)
            # .product holds the product ID reference; .productId is the alternate field
            pid = str(i_dict.product) if i_dict.product else (str(i_dict.productId) if i_dict.productId else None)
            product = products_map[pid] if pid and pid in products_map else None

            # stockStatus, taxRate, taxAmount are not stored in sj_order_items (DB has
            # only product_id, quantity, price) — they are None until the DB schema
            # is extended and ItemSnippet gains those columns.
            p_item = PopulatedOrderItemResponse(
                product=product,
                quantity=i_dict.quantity,
                price=i_dict.price,
                stockStatus=None,
                taxRate=None,
                taxAmount=None,
            )
            populated_items.append(p_item)

        from app.models.order import Order
        order_resp = Order.model_validate(order, from_attributes=True)
        order_resp.items = populated_items

        # couponCode, zoneId, adminNotes, valetNotes are not yet stored in sj_orders
        # (no DB columns) — declared on PopulatedOrderResponse as Optional[str] = None
        pop_order = PopulatedOrderResponse(
            id=order_resp.id,
            user=UserSnippet.model_validate(user, from_attributes=True) if user else None,
            assignedValet=ValetSnippet.model_validate(valet, from_attributes=True) if valet else None,
            paymentEntries=[entry for payment in payment_entries for entry in (payment.payment_entries or [])] if payment_entries else [],
            items=populated_items,
            sub_orders=order_resp.sub_orders,
            orderStatus=order_resp.status,
            totalAmount=order_resp.total,
            deliveryFee=order_resp.shipping,
            discount=order_resp.discount,
            couponCode=None,
            paymentMethod=order_resp.payment_method,
            paymentStatus=order_resp.payment_status,
            address=Address.model_validate(order_resp.shipping_address, from_attributes=True) if order_resp.shipping_address else None,
            createdAt=order_resp.created_at,
            updatedAt=order_resp.updated_at,
            zoneId=None,
            orderNotes=order_resp.notes,
            adminNotes=None,
            valetNotes=None,
        )
        populated.append(pop_order)

    return populated
async def populate_order(order: Any) -> Optional[PopulatedOrderResponse]:
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
        query["user"] = str(current_user.id)
    elif current_user.role == "valet":
        query["assignedValet"] = str(current_user.id)
    elif current_user.role == "seller":
        query["subOrders.sellerId"] = str(current_user.id)
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
        is_seller = any(str(sub.seller_id) == str(current_user.id) for sub in (order.sub_orders or []))
        if not is_seller:
            raise HTTPException(status_code=403, detail="Access denied")

    populated_order = await populate_order(order)
    return populated_order


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
    order_zone_id = None
    # User must be logged in to place an order
    if not current_user:
        raise HTTPException(status_code=401, detail="Please log in to place an order")

    # Check for existing order with the same idempotency key for this user
    if idempotency_key:
        existing_orders = await order_repository.findAll({"user": current_user.id, "idempotencyKey": idempotency_key})
        if existing_orders:
            # Return the existing order to prevent duplicate creation
            populated_existing = await populate_order(existing_orders[0])
            return populated_existing

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
                    float(entry.amount or 0.0)
                    for entry in (p.payment_entries or [])
                    if (entry.verified)
                )
                effective_due = (p.total_amount if p.total_amount is not None else 0.0) - verified_paid

                if effective_due > 0:
                    order_date_raw = p.order_date or p.created_at
                    if order_date_raw:
                        try:
                            from datetime import timedelta
                            
                            if isinstance(order_date_raw, str):
                                order_date = (
                                    datetime.fromisoformat(order_date_raw.replace("Z", "+00:00"))
                                    .astimezone(__import__("datetime").timezone.utc)
                                    .replace(tzinfo=None)
                                )
                            else:
                                order_date = order_date_raw.replace(tzinfo=None)

                            due_date = order_date + timedelta(days=terms_days)
                            if now > due_date:
                                has_overdue = True
                                break
                        except Exception as e:
                            logging.warning("Background task failed", exc_info=e)
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
        p = (_cart_products_map[str(item.product or item.product_id)] if str(item.product or item.product_id) in _cart_products_map else None)
        if p:
            qty = (item.quantity if item.quantity is not None else 0)
            sell_as_case = (item.sell_as_case if item.sell_as_case is not None else False)
            temp_subtotal += product_repository.calculateTotalPrice(
                p, effective_role, qty, sell_as_case=sell_as_case, user_id=current_user.id
            )

    base_shipping = 0.0
    if order_data.shippingAddress:
        try:
            state = order_data.shippingAddress.state or ""
            city = order_data.shippingAddress.city or ""
            district = order_data.shippingAddress.district or ""
            zip_code = order_data.shippingAddress.effective_pincode

            from app.repositories.delivery_charge_repository import delivery_charge_repository

            delivery_charge_data_raw = await delivery_charge_repository.getChargeForLocation(
                state, city, district, zip_code, effective_role, temp_subtotal
            )
            delivery_charge_data = (
                delivery_charge_data_raw
            )
            if delivery_charge_data:
                charge_amount = float(delivery_charge_data.charge if delivery_charge_data.charge is not None else 0.0)
                min_cart_value_for_free = float(delivery_charge_data.minCartValue if delivery_charge_data.minCartValue is not None else 0.0)
                is_applicable = (
                    delivery_charge_data.isApplicableToRole
                    if delivery_charge_data.isApplicableToRole is not None
                    else True
                )
                if is_applicable:
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

    if order_data.couponCode:
        from app.repositories.coupon_repository import coupon_repository

        role_for_coupon = effective_role
        validation_raw = await coupon_repository.validateCoupon(
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
        validation = (
            validation_raw
        )
        is_val_valid = validation.valid
        if not is_val_valid:
            val_msg = validation.message
            raise HTTPException(status_code=400, detail=val_msg)
        val_c_raw = validation.coupon
        val_c = (
            val_c_raw
        )
        applied_coupon_id = val_c.id
        val_code = val_c.code
        coupon_code = val_code or ("AUTO-" + (applied_coupon_id or "")[:8])
        coupon_discount = validation.discount
        eligible_item_indices = validation.eligibleItemIndices
        item_discounts = validation.itemDiscounts
        bxgy_item_indices = validation.bxgyItemIndices

        c_obj = val_c
        c_method = c_obj.method
        c_mode = c_obj.couponMode
        if c_method == "discount_code" and c_mode == "override":
            is_override = True

        val_disc_type = val_c.discountType
        val_disc_val = val_c.discountValue
        val_type_of_disc = val_c.typeOfDiscount
        coupon_info = {
            "code": coupon_code,
            "discountType": val_disc_type,
            "discountValue": val_disc_val,
            "discountAmount": coupon_discount,
            "typeOfDiscount": val_type_of_disc,
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
            best_raw = max(
                auto_list,
                key=lambda x: (
                    (x.discount if x.discount is not None else 0.0)
                ),
            )
            best = (
                best_raw
            )
            coupon_discount = best.discount if best.discount is not None else 0.0
            eligible_item_indices = best.eligibleItemIndices
            item_discounts = best.itemDiscounts
            bxgy_item_indices = best.bxgyItemIndices
            c_raw = best.coupon
            c = (
                c_raw
            )
            applied_coupon_id = c.id
            coupon_code = c.code or ("AUTO-" + (applied_coupon_id or "")[:8])
            coupon_info = {
                "code": coupon_code,
                "discountType": c.discountType,
                "discountValue": c.discountValue,
                "discountAmount": coupon_discount,
                "typeOfDiscount": c.typeOfDiscount,
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
        product = (_cart_products_map[str(item.product or item.product_id)] if str(item.product or item.product_id) in _cart_products_map else None)
        if not product:
            raise HTTPException(
                status_code=400, detail=f"Product not found: {item.product or item.product_id}"
            )
        quantity = (item.quantity if item.quantity is not None else 0)
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
    c_type_of_disc = coupon_info["typeOfDiscount"] if coupon_info is not None else None
    is_shipping_discount = coupon_info is not None and c_type_of_disc == "shipping_discount"

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

    if order_data.referralCode:
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

        ref_settings_raw = await referral_repository.get_settings()
        ref_settings = (
            ref_settings_raw
        )
        retail_settings = ref_settings.retail
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
        (order_data.shippingAddress.effective_pincode or order_data.shippingAddress.zipCode or order_data.shippingAddress.pincode or "")
        if order_data.shippingAddress
        else ""
    )
    _pincode_seller_ids = set()
    if _customer_pincode:
        try:
            from app.repositories.zone_seller_cache import get_seller_ids_for_pincode

            _pincode_seller_ids = await get_seller_ids_for_pincode(_customer_pincode)
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

        effective_price = ((item_total_before_coupon or 0) / quantity) if quantity else 0

        order_items.append(
            CalculatedOrderItem(
                product=str(product.id),
                sellerId=_resolve_product_seller_id(product, _pincode_seller_ids),
                productName=product.name,
                quantity=quantity,
                sellAsCase=sell_as_case,
                price=effective_price,
                priceBeforeCoupon=round(item_total_before_coupon, 2),
                couponDiscount=round(item_coupon_discount, 2),
                coupon_discount=round(item_coupon_discount, 2),
                referralDiscount=round(item_referral_discount, 2),
                referral_discount=round(item_referral_discount, 2),
                subtotal=round(final_item_total, 2),
                singleUnitPrice=round(single_unit_price, 2),
                singleUnitTaxableValue=round(single_unit_taxable_value, 2),
                singleUnitCGST=round(single_unit_cgst, 2),
                singleUnitSGST=round(single_unit_sgst, 2),
                numberOfSingleUnits=total_single_units,
                gst=gst_percent,
                taxableValue=round(taxable_value, 2),
                cgst=round(cgst, 2),
                sgst=round(sgst, 2),
                # variantAttributes is not stored on ItemSnippet / sj_order_items
                # (DB only has product_id, quantity, price). Pass None until extended.
                variantAttributes=None,
            )
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
        zip_code = order_data.shippingAddress.effective_pincode if order_data.shippingAddress else ""

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
                order_zone_id = str(_zone_doc.id)
                zone_urgent_available = bool(_zone_doc.urgentDeliveryAvailable)

        # ── Resolve slot config: zone-specific first, then "default" fallback ─
        # New design: one config record per zone per date (zoneId field).
        # "default" config serves as a fallback for zones with no specific config.
        _slot_config_raw = None
        if order_zone_id:
            _zone_configs = await slot_storage.findAll(
                {"date": target_date, "segment": seg, "zoneId": order_zone_id, "isActive": True}
            )
            if _zone_configs:
                _slot_config_raw = _zone_configs[0]
        if not _slot_config_raw:
            _default_configs = await slot_storage.findAll(
                {"date": target_date, "segment": seg, "zoneId": "default", "isActive": True}
            )
            if _default_configs:
                _slot_config_raw = _default_configs[0]

        from app.routers.delivery_slots import DeliverySlotConfigModel
        _slot_config = (
            _slot_config_raw
        )

        slot_configs = [_slot_config] if _slot_config else []

        matched_config = None
        matched_slot = None

        for sc in slot_configs:
            sc_slots = sc.slots or []
            for sl in sc_slots:
                sl_is_active = sl.isActive
                if not (sl_is_active if sl_is_active is not None else True):
                    continue

                # ── Flat capacity check (new per-zone record design) ─────────
                # Each config record is already scoped to a zone, so capacity
                # and bookedCount are flat fields on the slot — no sub-dict needed.
                _cap = sl.capacity
                if _cap is None:
                    _cap = sc.zoneDefaultCapacity
                _booked = (sl.bookedCount) or 0
                if _cap is not None and _booked >= int(_cap):
                    continue  # Slot full

                sl_is_urgent = bool(sl.isUrgent)
                # Match by explicit ID or match by Urgent condition
                if order_data.isUrgentDelivery and not order_data.deliverySlotId:
                    if sl_is_urgent:
                        # Check cutoff
                        cutoff = (
                            sl.urgentCutoffHours
                        )
                        if cutoff is None:
                            cutoff = sl.cutoffHours
                        if cutoff is not None:
                            ist = pytz.timezone("Asia/Kolkata")
                            now_ist = _dt.datetime.now(ist)
                            anchor_time_str = sl.endTime or sl.end_time or ""  # urgent → end time
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
                    sl_id = sl.id
                    sl_start = sl.startTime
                    sl_end = sl.endTime
                    if (sl_id or f"{sl_start}-{sl_end}") == order_data.deliverySlotId:
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
            is_full_day = bool(matched_slot.isFullDay)
            if not is_full_day:
                # Flat capacity re-check (per-zone record, no zoneCapacities sub-dict)
                _cap = matched_slot.capacity
                if _cap is None:
                    _cap = matched_config.zoneDefaultCapacity
                _booked = (matched_slot.bookedCount) or 0
                if _cap is not None and _booked >= int(_cap):
                    raise HTTPException(status_code=400, detail="Selected delivery slot is fully booked.")

                ms_is_urgent = bool(matched_slot.isUrgent)
                ms_urgent_cutoff = matched_slot.urgentCutoffHours
                ms_cutoff = matched_slot.cutoffHours
                cutoff_hours = (ms_urgent_cutoff if ms_is_urgent and ms_urgent_cutoff is not None else ms_cutoff)
                if cutoff_hours is not None:
                    ist = pytz.timezone("Asia/Kolkata")
                    now_ist = _dt.datetime.now(ist)
                    ms_end = matched_slot.endTime
                    ms_start = matched_slot.startTime
                    anchor_time_str = (ms_end if ms_is_urgent else ms_start)
                    try:
                        anchor_ist = ist.localize(
                            _dt.datetime.strptime(f"{target_date} {anchor_time_str}", "%Y-%m-%d %H:%M")
                        )
                        if now_ist >= (anchor_ist - _dt.timedelta(hours=cutoff_hours)):
                            raise HTTPException(status_code=400, detail="Booking time for this slot has passed.")
                    except ValueError:
                        pass

        mc_id = str(matched_config.id)
        ms_id = str(matched_slot.id)
        ms_start = matched_slot.startTime
        ms_end = matched_slot.endTime
        ms_is_urgent = bool(matched_slot.isUrgent)

        selected_slot_info = {
            "configId": mc_id,
            "slotId": ms_id,
            "zoneId": order_zone_id,
            "date": matched_config.date,
            "startTime": ms_start,
            "endTime": ms_end,
            "isUrgent": ms_is_urgent,
        }

        if selected_slot_info["isUrgent"]:
            order_data.isUrgentDelivery = True

    # Check pincode serviceability before proceeding
    if order_data.shippingAddress and (order_data.shippingAddress.effective_pincode or order_data.shippingAddress.zipCode):
        shipping_zip = str(order_data.shippingAddress.effective_pincode or order_data.shippingAddress.zipCode).strip()
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
            seller_ids_in_order = {item.sellerId for item in order_items if item.sellerId}
            for sid in seller_ids_in_order:
                sdoc = await user_repository.findById(sid)
                if sdoc:
                    seller_zone_ids = sdoc.service_area_zones or []
                    # Empty list = seller hasn't configured zones yet; allow during migration
                    if seller_zone_ids and order_zone_id not in seller_zone_ids:
                        s_name = sdoc.companyName or sdoc.name or "Seller"
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
            state = order_data.shippingAddress.state if order_data.shippingAddress.state is not None else ""
            city = order_data.shippingAddress.city if order_data.shippingAddress.city is not None else ""
            district = order_data.shippingAddress.district if order_data.shippingAddress.district is not None else ""
            zip_code = order_data.shippingAddress.zipCode if order_data.shippingAddress.zipCode is not None else ""

            # Calculate total before shipping for tiered charge calculation
            total_before_shipping = subtotal  # Use subtotal (after coupon, includes GST)

            # Get delivery charge with role and amount consideration (now includes pincode)
            delivery_charge_data_raw = await delivery_charge_repository.getChargeForLocation(
                state, city, district, zip_code, effective_role, total_before_shipping
            )
            delivery_charge_data = (
                delivery_charge_data_raw
            )

            if delivery_charge_data:
                charge_amount = delivery_charge_data.charge if delivery_charge_data.charge is not None else 0
                min_cart_value_for_free = delivery_charge_data.minCartValue if delivery_charge_data.minCartValue is not None else 0

                # Apply delivery charge only if:
                # 1. It's applicable to the user's role
                # 2. Total before shipping is less than minimum for free delivery
                if delivery_charge_data.isApplicableToRole if delivery_charge_data.isApplicableToRole is not None else True:
                    if order_data.isUrgentDelivery and effective_role in ("customer", "wholesaler"):
                        if zone_urgent_available:
                            # Urgent delivery is determined by the zone's urgentDeliveryAvailable flag.
                            # The cart is treated as a single unit — all items are either
                            # urgent or standard. No per-seller validation needed here.
                            urgent_charge = delivery_charge_data.urgentDeliveryCharge
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
    c_tod = coupon_info["typeOfDiscount"] if coupon_info is not None else None
    is_shipping_discount = coupon_info is not None and c_tod == "shipping_discount"
    
    shipping_net_to_charge = base_shipping
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
            await user_repository.update(current_user.id, UserInternalUpdate(creditUsed=0))
            user.credit_used = 0
        if user.credit_limit is None:
            await user_repository.update(current_user.id, UserInternalUpdate(creditLimit=0))
            user.credit_limit = 0

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

    # Deduct credit BEFORE writing the order record.
    # The pre-check above (L1313-1325) is an optimistic read; two concurrent requests
    # can both pass it if they read the same credit_used value simultaneously.
    # add_credit_used_atomic uses a conditional UPDATE (credit_used + amount <= limit)
    # so the second of two concurrent requests will get rowcount == 0 and be rejected
    # cleanly — before an order record has been written.
    _credit_deducted = False
    if order_data.paymentMethod == "credit":
        success = await user_repository.add_credit_used_atomic(current_user.id, total)
        if not success:
            ORDER_FAILURES.labels(reason="credit_limit_exceeded").inc()
            raise HTTPException(status_code=400, detail="Insufficient credit limit or user not found.")
        _credit_deducted = True

    # ── MULTI-VM CREDIT DEDUCTION (commented out — already atomic at DB level) ───
    #
    # The active add_credit_used_atomic() above is a single conditional UPDATE:
    #   UPDATE sj_users SET credit_used = credit_used + amount
    #   WHERE id = :id AND credit_used + amount <= credit_limit
    # This is atomic in MySQL — safe across all 4 workers on this VM and across
    # all VMs sharing the same DB.  No distributed lock is needed.
    #
    # HOW SINGLE-VM WORKS (active):
    #   uvicorn --workers 4 means 4 independent processes.  If two orders for the
    #   same user arrive simultaneously, both call add_credit_used_atomic().
    #   MySQL serialises them at the row level; only the one that keeps credit_used
    #   within the limit will succeed (rowcount == 1).  The other gets rowcount == 0
    #   and is rejected before an order record is written.
    #
    # IF A REDIS PRE-LOCK IS EVER NEEDED (e.g. to provide user-facing queue feedback):
    #
    # # _credit_deducted = False
    # # if order_data.paymentMethod == "credit":
    # #     import aioredis, os
    # #     redis = aioredis.from_url(os.environ["REDIS_URL"])
    # #     lock_key = f"sj:credit:{current_user.id}"
    # #     async with redis.lock(lock_key, timeout=5, blocking_timeout=4):
    # #         success = await user_repository.add_credit_used_atomic(current_user.id, total)
    # #         if not success:
    # #             ORDER_FAILURES.labels(reason="credit_limit_exceeded").inc()
    # #             raise HTTPException(status_code=400, detail="Credit limit exceeded.")
    # #         _credit_deducted = True
    #
    # TO ACTIVATE:
    #   1. pip install aioredis
    #   2. Add REDIS_URL to .env
    #   3. Replace the active block above with the commented block above.
    #
    # ─────────────────────────────────────────────────────────────────────────────


    # Create order

    order = await order_repository.create(
        OrderInternalCreate(
            user= current_user.id,
            sessionId= current_user.session_id,
            items= [
                OrderItem(
                    productId=str(i.product),
                    product=str(i.product),
                    quantity=i.quantity,
                    price=i.price,
                    name=i.productName,
                    sellAsCase=i.sellAsCase,
                )
                for i in order_items
            ],
            subtotalBeforeCoupon= round(subtotal_before_coupon, 2),
            subtotal= round(subtotal, 2),
            tax= tax,
            shipping= shipping,
            deliveryGst= delivery_gst,
            discount= discount,
            couponCode= coupon_code,
            couponInfo= coupon_info,
            total= total,
            orderType= order_type,
            isUrgentDelivery= order_data.isUrgentDelivery if effective_role in ("customer", "wholesaler") else False,
            deliverySlot= selected_slot_info,
            shippingAddress= order_data.shippingAddress,
            billingAddress= order_data.billingAddress or order_data.shippingAddress,
            paymentMethod= order_data.paymentMethod,
            upiPaymentScreenshot= screenshot_path if order_data.paymentMethod == "upi" else None,
            notes= f"Referral Code Applied: {applied_referral_code} | {order_data.notes or ''}".strip(" |")
            if applied_referral_code
            else (order_data.notes or ""),
            printedBill= order_data.printedBill,
            idempotencyKey= idempotency_key,
        )
    )

    # ── Post-creation compensation block ─────────────────────────────────────────
    # Order record is now persisted. If any step below fails unexpectedly (e.g.
    # the stock decrement or payment creation raises), we mark the order as
    # "failed" and restore credit so the record is never silently broken.
    try:
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
                        db_id = slot_config.id if slot_config.id is not None else config_id
                        async with factory() as session:
                            child_table = slot_storage.CHILD_TABLE
                            parent_table = slot_storage.TABLE
                            
                            # --- BEGIN OLD COMMENTED CODE ---
                            # result = await session.execute(
                            #     text(f"SELECT booked_count, capacity FROM {child_table} WHERE parent_id = :id AND slot_uuid = :slot_id FOR UPDATE"),
                            #     {"id": int(db_id) if str(db_id).isdigit() else None, "slot_id": slot_id},
                            # )
                            # row = result.fetchone()
                            # if row:
                            #     await session.execute(
                            #         text(f"UPDATE {child_table} SET booked_count = booked_count + 1 WHERE parent_id = :id AND slot_uuid = :slot_id"),
                            #         {"id": int(db_id) if str(db_id).isdigit() else None, "slot_id": slot_id},
                            #     )
                            #     await session.execute(
                            #         text(f"UPDATE {parent_table} SET updated_at = UTC_TIMESTAMP() WHERE id = :id"),
                            #         {"id": int(db_id) if str(db_id).isdigit() else None},
                            #     )
                            #     await session.commit()
                            # --- END OLD COMMENTED CODE ---

                            # --- NEW ATOMIC CODE ---
                            # Atomic increment that strictly enforces capacity at the database level.
                            # capacity is a varchar in DB, so we cast to UNSIGNED for safe numeric comparison.
                            update_result = await session.execute(
                                text(f"""
                                    UPDATE {child_table} 
                                    SET booked_count = booked_count + 1 
                                    WHERE parent_id = :id 
                                      AND slot_uuid = :slot_id 
                                      AND (capacity IS NULL OR capacity = '' OR booked_count < CAST(capacity AS UNSIGNED))
                                """),
                                {"id": int(db_id) if str(db_id).isdigit() else None, "slot_id": slot_id},
                            )
                            
                            if update_result.rowcount == 0:
                                # Rowcount 0 means either the slot doesn't exist OR it's fully booked.
                                # Raising an exception triggers the order compensation block, refunding credit and marking order as failed.
                                raise ValueError("Delivery slot is fully booked or unavailable.")
                                
                            await session.execute(
                                text(f"UPDATE {parent_table} SET updated_at = UTC_TIMESTAMP() WHERE id = :id"),
                                {"id": int(db_id) if str(db_id).isdigit() else None},
                            )
                            await session.commit()
                            # --- END NEW ATOMIC CODE ---
            except Exception as e:
                _cfg_id = selected_slot_info["configId"] if selected_slot_info and "configId" in selected_slot_info else selected_slot_info.configId
                _s_id = selected_slot_info["slotId"] if selected_slot_info and "slotId" in selected_slot_info else selected_slot_info.slotId
                logger.error(
                    "Failed to increment slot bookedCount for config %s slot %s: %s",
                    _cfg_id,
                    _s_id,
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
                        spec_qty = max(1, spec.quantity if spec.quantity is not None else 1)
                        spec_pid = str(spec.productId or "")
                        ref_item = next(
                            (
                                i
                                for i in bundle_items_in_order
                                # ItemSnippet has .product and .productId (camelCase), not product_id
                                if str((i.product or "")) == spec_pid or str(i.productId or "") == spec_pid
                            ),
                            bundle_items_in_order[0],
                        )
                        copies = max(1, (ref_item.quantity if ref_item.quantity is not None else spec_qty) // spec_qty)
                    # Bundle.salesCount is a declared Pydantic field
                    sales_c = bundle.salesCount if bundle.salesCount is not None else 0
                    new_sales = sales_c + copies
                    await bundle_repository.update(b_id, BundleInternalUpdate(salesCount=new_sales))
        except Exception as e:
            logger.error("Failed to increment bundle salesCount: %s", str(e), exc_info=True)

        # Atomically decrement stock and fulfil the reservation in one shot per item.
        # Uses SELECT … FOR UPDATE so concurrent orders for the same product serialize
        # at the DB level — no two orders can read the same stock value and both succeed.
        for item in order_items:
            product = await product_repository.findById(item.product)

            # Build variant_combinations arg expected by decrement_stock_atomic
            variant_combos = None
            if item.variant_attributes or item.variantAttributes:
                variant_combos = [{"attributes": item.variant_attributes or item.variantAttributes, "quantity": item.quantity}]

            new_stock = await product_repository.decrement_stock_atomic(
                str(item.product),
                item.quantity,
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
                new_stock = max(0, product.stock - item.quantity) if product.stock is not None else None

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
                        import uuid
                        from app.models.daos import NotificationInternalCreate
                        await notification_repository.create(
                            NotificationInternalCreate(
                                _id=str(uuid.uuid4()),
                                userId=super_admin.id,
                                type="low_stock",
                                title="Low Stock Alert",
                                message=f'Product "{product.sku}" - "{product.name}" has {new_stock} pieces left',
                                metadata={
                                    "productId": product.id,
                                    "sku": product.sku,
                                    "productName": product.name,
                                    "quantity": new_stock,
                                    "category": product.category,
                                    "threshold": threshold if threshold is not None else None,
                                },
                            )
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

        # Credit was already deducted atomically BEFORE the order was created (see above).

        # Update discount usage count if discount was used
        if applied_coupon_id:
            from app.repositories.coupon_repository import coupon_repository

            await coupon_repository.incrementUsage(applied_coupon_id, current_user.id)

        # Create payment record
        user_for_payment = await user_repository.findById(current_user.id)
        payment_data = {
            "orderId": order.id,
            "userId": str(user_for_payment.user_id),  # Use userId instead of customerId
            "customerName": user_for_payment.name,
            "orderDate": order.created_at if isinstance(order.created_at, str) else str(order.created_at),
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
                    "createdAt": order.created_at.isoformat() if order.created_at else None,
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

    except Exception as _post_order_exc:
        # ── Compensation ──────────────────────────────────────────────────────────
        # Something failed after the order was written. Mark it as failed so it is
        # visible to ops instead of silently lingering as a ghost record.
        logger.error(
            "[OrderCreate] Post-creation step failed for order %s — marking as failed. Error: %s",
            order.id,
            str(_post_order_exc),
            exc_info=True,
        )
        try:
            await order_repository.update(str(order.id), OrderInternalUpdate(status="failed"))
        except Exception:
            logger.error("[OrderCreate] Could not mark order %s as failed.", order.id, exc_info=True)

        # Restore credit that was pre-deducted if this was a credit order.
        if _credit_deducted:
            try:
                await user_repository.add_credit_used_atomic(current_user.id, -total)
            except Exception:
                logger.error(
                    "[OrderCreate] Could not restore credit for user %s after order %s failure.",
                    current_user.id,
                    order.id,
                    exc_info=True,
                )

        raise HTTPException(status_code=500, detail="Order could not be completed. Please try again.")

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
    await user_repository.update(current_user.id, UserInternalUpdate(address=order_data.shippingAddress))

    populated_order = await populate_order(order)
    email = populated_order.user.email if (populated_order.user and populated_order.user.email) else None
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
            if not oi.sellerId and super_admin_id:
                oi.sellerId = super_admin_id

        # Build a lookup of sellerId -> seller user doc (for name)
        seller_ids_in_order = {item.sellerId for item in order_items if item.sellerId}
        seller_docs = {}
        for sid in seller_ids_in_order:
            sdoc = await user_repository.findById(sid)
            if sdoc:
                seller_docs[sid] = sdoc

        # Group order_items by sellerId
        from collections import defaultdict

        groups = defaultdict(list)
        for oi in order_items:
            sid = oi.sellerId
            groups[sid].append(oi)

        # Only split if multiple seller groups exist
        if len(groups) > 1:
            parent_order_number = (order.order_number if order.order_number is not None else str(order.id))
            sub_order_ids = []

            # Build per-seller delivery option lookup from request
            seller_delivery_map = {}
            if order_data.sellerDeliveryOptions:
                for sdo in order_data.sellerDeliveryOptions:
                    seller_delivery_map[sdo.sellerId] = sdo

            # Fetch delivery charge data once (same pincode for all sub-orders)
            try:
                await delivery_charge_repository.getChargeForLocation(
                    order_data.shippingAddress.state if order_data.shippingAddress.state is not None else "",
                    order_data.shippingAddress.city if order_data.shippingAddress.city is not None else "",
                    order_data.shippingAddress.district if order_data.shippingAddress.district is not None else "",
                    order_data.shippingAddress.zipCode if order_data.shippingAddress.zipCode is not None else "",
                    effective_role,
                    subtotal,
                )
            except Exception as e:
                logging.warning("Background task failed", exc_info=e)

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

                sdo = (seller_delivery_map[str(seller_id)] if seller_id and str(seller_id) in seller_delivery_map else None)

                # Record the delivery slot on the sub-order (informational, no charge)
                if sdo and sdo.deliverySlotId and sdo.deliverySlotDate:
                    grp_slot_info = {
                        "configId": sdo.deliverySlotConfigId,
                        "slotId": sdo.deliverySlotId,
                        "date": sdo.deliverySlotDate,
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
                    sdoc = (seller_docs[str(seller_id)] if str(seller_id) in seller_docs else None)
                    if sdoc:
                        seller_name = sdoc.companyName if sdoc.companyName else (sdoc.name if sdoc.name else "")
                else:
                    seller_name = "Platform"

                sub_order_data = {
                    "subOrderNumber": sub_number,
                    "parentOrderId": str(order.id),
                    "parentOrderNumber": parent_order_number,
                    "sellerId": str(seller_id) if seller_id else None,
                    "sellerName": seller_name,
                    "user": current_user.id,
                    "items": [
                        SubOrderItem(
                            productId=str(i.product),
                            name=i.productName,
                            qty=i.quantity,
                            price=i.price,
                        )
                        for i in items_group
                    ],
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
                    "notes": order_data.notes or "",
                    "couponCode": coupon_code,
                    "couponInfo": coupon_info,
                    "createdAt": order.created_at.isoformat() if order.created_at else None,
                }
                sub = await sub_order_repository.create(SubOrderInternalCreate(**sub_order_data))
                sub_order_ids.append(str(sub.id))

                # Notify the seller about their new sub-order (if it's a seller admin, not platform)
                if seller_id:
                    try:
                        import uuid
                        await notification_repository.create(
                            NotificationInternalCreate(**{
                                "_id": str(uuid.uuid4()),
                                "userId": seller_id,
                                "type": "new_sub_order",
                                "title": "New Order Received",
                                "message": f'New sub-order "{sub_number}" worth ₹{grp_total:.2f} received',
                                "metadata": {
                                    "subOrderId": str(sub.id),
                                    "subOrderNumber": sub_number,
                                    "parentOrderId": str(order.id),
                                    "amount": grp_total,
                                }
            })
        )
                    except Exception as notif_err:
                        logger.error("Error notifying seller %s: %s", seller_id, str(notif_err), exc_info=True)

            # Store sub-order references on the parent order
            await order_repository.update(
                str(order.id),
                OrderInternalUpdate(hasSubOrders=True,
                    subOrderIds=sub_order_ids,),
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
            raise HTTPException(status_code=403, detail="You do not have a sub-order in this order")

    await order_repository.update(order_id, OrderInternalUpdate(
        trackingId=data.trackingId,
        courierPartner=data.courierPartner,
        trackingUpdatedAt=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat() + "Z"
    ))

    # Push notification to customer
    try:
        from app.services.push_notification_service import push_notification_service

        await push_notification_service.send_to_user(
            str(order.user),
            PushNotifications(
                title="Order Shipped",
                message=f"Your order #{(order.order_number if order.order_number is not None else order_id)} has been shipped. Tracking ID: {data.trackingId}"
            ),
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

    await order_repository.update(order_id, OrderInternalUpdate(shipping=new_delivery_charge, total=new_total))

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
                        payment.payment_entries[0].entryId,
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
                            "paymentId": updated_payment_with_entry.paymentId,
                            "orderId": updated_payment_with_entry.orderId,
                            "totalAmount": (order.total if order.total is not None else payment.totalAmount),
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
                        "orderId": new_payment.orderId,
                        "totalAmount": new_payment.totalAmount,
                        "paymentMethod": "cod",
                        "createdAt": datetime.now(__import__("datetime").timezone.utc).isoformat() + "Z",
                    }
                )
    elif status_data.status == "cancelled":
        # Guard: prevent re-cancelling a terminal order which would double-restore stock/credit.
        _TERMINAL_STATUSES = {"cancelled", "declined", "delivered", "returned", "failed"}
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
                    raise ValueError("Cannot calculate credit usage: credit_used or total is None")
                new_credit_used = max(0, user.credit_used - order.total)
                await user_repository.update(order.user, UserInternalUpdate(creditUsed=new_credit_used))

        # Restore stock atomically — uses SELECT … FOR UPDATE so a concurrent new order
        # cannot race against this restoration and produce a wrong stock count.
        for item in (order.items or []):
            if item.product and item.quantity:
                await product_repository.increment_stock_atomic(str(item.product), int((item.quantity if item.quantity is not None else 0)))

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

    updated_order = await order_repository.update(order_id, OrderInternalUpdate(**update_data))
    populated_order = await populate_order(updated_order)

    # ── C5: Cascade terminal status from parent to sub-orders ─────────────────
    if status_data.status in ("cancelled", "delivered"):
        from datetime import datetime as _dt

        sub_ids = updated_order.subOrderIds if updated_order.subOrderIds else []
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
                    logger.warning("Commission stamp failed for sub-order %s: %s", _so_id, _ce)
                await sub_order_repository.update(_so_id, SubOrderInternalUpdate(**_cascade))

    # Recompute parent fulfillmentStatus from all sub-orders
    sub_ids = updated_order.subOrderIds if updated_order.subOrderIds else []

    # Recompute overall fulfillment status based on sub-orders
    _f_status = await _compute_fulfillment_status(sub_ids)
    if _f_status and _f_status != updated_order.status:
        updated_order = await order_repository.update(order_id, OrderInternalUpdate(status=_f_status))
        sub_ids = updated_order.subOrderIds if updated_order.subOrderIds else []

    # Send status change email notification
    populated_order = await populate_order(updated_order)
    if populated_order:
        email = populated_order.user.email if (populated_order.user and populated_order.user.email) else None
        if email:
            background_tasks.add_task(email_service.send_order_status_email, email, populated_order)

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
                        OrderInternalUpdate(invoicePath=invoice_path, invoiceGeneratedAt=_dt.utcnow().isoformat() + "Z"),
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
        raise HTTPException(status_code=400, detail="Only pending orders can be accepted")

    # UPI orders must have a verified payment entry before acceptance
    if order.payment_method == "upi":
        payments = await payment_repository.findByOrderId(order_id)
        payment = payments[0] if payments else None
        entries = (payment.payment_entries or []) if payment else []
        any_verified = any(entry.verified for entry in entries)
        if not any_verified:
            raise HTTPException(status_code=400, detail="UPI payment must be verified before accepting the order")

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
        raise HTTPException(status_code=400, detail="UPI orders cannot be declined")

    if order.payment_method not in ["cod", "credit"]:
        raise HTTPException(status_code=400, detail="Only COD and Credit orders can be declined")

    if order.status != "pending":
        raise HTTPException(status_code=400, detail="Only pending orders can be declined")

    # For credit orders, refund credit used
    if order.payment_method == "credit":
        user = await user_repository.findById(order.user)
        if user and user.credit_used:
            if user.credit_used is None or order.total is None:
                raise ValueError("Cannot calculate credit usage: credit_used or total is None")
            new_credit_used = max(0, user.credit_used - order.total)
            await user_repository.update(order.user, UserInternalUpdate(creditUsed=new_credit_used))

    # Restore stock atomically — uses SELECT … FOR UPDATE so a concurrent new order
    # cannot race against this restoration and produce a wrong stock count.
    for item in (order.items or []):
        if item.product and item.quantity:
            await product_repository.increment_stock_atomic(str(item.product), int((item.quantity if item.quantity is not None else 0)))

    updated_order = await order_repository.update(
        order_id, OrderInternalUpdate(status="declined", declineReason=decline_data.reason)
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
        OrderInternalUpdate(status="pending_valet",
            pendingValetId=valet_data.valetId,
            valetAssignedAt=now_iso,
            valetDeclineHistory=[],
            valetCascadeCount=0,),
    )

    # Push notification to the valet
    try:
        from app.services.push_notification_service import push_notification_service

        timeout_label = "5 minutes" if is_urgent else "20 minutes"
        await push_notification_service.send_to_user(valet_data.valetId, PushNotifications(
                title= "New Delivery Request",
                message= (
                    f"You have a new delivery order #{(order.order_number if order.order_number is not None else order_id)}. "
                    f"Please respond within {timeout_label}."
                ),
                link= f"/valet/orders/{order_id}",
            ))
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
#))
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
#))
#         order.valetDeclineHistory = history
#         order.pendingValetId = None
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
        raise HTTPException(status_code=400, detail="Only COD and Credit orders can be cancelled")

    # Orders can only be cancelled before they are Accepted (status is still 'pending')
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="Orders can only be cancelled before they are accepted")

    # For credit orders, refund credit used
    if order.payment_method == "credit":
        user = await user_repository.findById(order.user)
        if user and user.credit_used:
            if user.credit_used is None or order.total is None:
                raise ValueError("Cannot calculate credit usage: credit_used or total is None")
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
        OrderInternalUpdate(status="cancelled", cancelledAt=datetime.now(__import__("datetime").timezone.utc).isoformat(), cancelledBy=current_user.id),
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

    valet = await user_repository.findById(valet_data.valetId)
    if not valet or valet.role != "valet":
        raise HTTPException(status_code=400, detail="Invalid valet")

    updated_order = await order_repository.update(order_id, OrderInternalUpdate(assignedValet=valet_data.valetId))

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
        except Exception as e:
            logging.warning("Background task failed", exc_info=e)

    now_iso = datetime.now(__import__("datetime").timezone.utc).isoformat() + "Z"
    valet_id = str(current_user.id) if current_user.role == "valet" else str((order.pending_valet_id or ""))
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
                    _so_id, SubOrderInternalUpdate(assignedValet=valet_id,
                        pickupStatus="pending_pickup",),
                )
                _seller_id = _so.sellerId
                if _seller_id and _seller_id not in notified_sellers:
                    notified_sellers.add(_seller_id)
                    try:
                        from app.services.push_notification_service import push_notification_service

                        await push_notification_service.send_to_user(_seller_id, PushNotifications(
                                title= "Valet is Coming to Pick Up",
                                message= (
                                    f"{valet_name} accepted order #{(order.order_number if order.order_number is not None else order_id)} "
                                    "and will collect your items soon."
                                ),
                                link= f"/seller/orders/{order_id}",
                            ))
                    except Exception as e:
                        logger.warning("[ValetResponse] Push to seller %s failed: %s", _seller_id, e)
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
                        OrderInternalUpdate(invoicePath=invoice_path, invoiceGeneratedAt=now_iso),
                    )
            except Exception as invoice_err:
                logger.error("[ValetResponse] Invoice generation failed: %s", invoice_err)

        populated_order = await populate_order(updated_order)
        return populated_order

    # ── DECLINE ───────────────────────────────────────────────────────────────
    decline_history = list(order.valet_decline_history or [])
    if valet_id and not any(d.valetId == valet_id for d in decline_history):
        from app.models.order import ValetDeclineHistoryEntry
        decline_history.append(ValetDeclineHistoryEntry(valetId=valet_id, reason="declined"))

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
                    title= "New Delivery Request",
                    message= (
                        f"You have a new delivery order #{(order.order_number if order.order_number is not None else order_id)}. "
                        f"Please respond within {timeout_label}."
                    ),
                    link= f"/valet/orders/{order_id}",
                ))
        except Exception as e:
            logger.warning("[ValetResponse] Push to next valet failed: %s", e)
    else:
        # No more valets — revert to processing
        updated_order = await order_repository.update(
            order_id,
            OrderInternalUpdate(status="processing", pendingValetId=None, valetAssignedAt=None),
        )
        # Notify seller
        if seller_id:
            try:
                from app.services.push_notification_service import push_notification_service

                await push_notification_service.send_to_user(seller_id, PushNotifications(
                        title= "No Valets Available — Reassign Required",
                        message= (
                            f"All valets declined order #{(order.order_number if order.order_number is not None else order_id)}. "
                            "Please assign a valet manually."
                        ),
                        link= f"/seller/orders/{order_id}",
                    ))
            except Exception as e:
                logger.warning("[ValetResponse] Push to seller (all declined) failed: %s", e)

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
        # Notify the customer
        try:
            from app.services.push_notification_service import push_notification_service

            await push_notification_service.send_to_user(order.user, PushNotifications(
                    title= "Your Order is On the Way! 🚴",
                    message= (
                        f"Your order #{(order.order_number if order.order_number is not None else order_id)} has been collected "
                        "from all sellers and is now heading to you."
                    ),
                    link= f"/orders/{order_id}",
                ))
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
        raise HTTPException(status_code=400, detail="This order is not a credit order")

    user = await user_repository.findById(current_user.id)
    if user.role != "wholesaler":
        raise HTTPException(status_code=403, detail="Only business customers can settle credit")

    # Reject zero or negative settlement amounts
    settle_amount = float(settle_data.amount)
    if settle_amount <= 0:
        raise HTTPException(status_code=400, detail="Settlement amount must be greater than zero")

    # Find payment record
    payments = await payment_repository.findByOrderId(order_id)
    if not payments or len(payments) == 0:
        raise HTTPException(status_code=404, detail="Payment record not found")
    payment = payments[0]

    if payment.amount_paid is None:
        raise ValueError("Cannot calculate remaining amount: amount_paid is None")
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
    payment_image = settle_data.paymentImage or settle_data.upiPaymentScreenshot
    await payment_repository.addPaymentEntry(
        payment.id, {"amount": settle_amount, "image": payment_image, "verified": False}
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
        order_id, OrderInternalUpdate(invoicePath=invoice_path, invoiceGeneratedAt=datetime.now(__import__("datetime").timezone.utc).isoformat() + "Z")
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
        query["status"] = status  # was query.status = status (dict has no .status attribute)
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

    allowed_statuses = ["pending", "confirmed", "processing", "shipped", "out_for_delivery", "delivered", "cancelled"]
    if status_data.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {', '.join(allowed_statuses)}")

    from datetime import datetime as _dt

    internal_update = SubOrderInternalUpdate(status=status_data.status)
    if status_data.status == "delivered":
        internal_update.deliveredAt = _dt.utcnow().isoformat() + "Z"
        try:
            from app.routers.commission import stamp_commission_on_delivery

            _comm = await stamp_commission_on_delivery(sub_order)
            if "commissionPct" in _comm: internal_update.commissionPct = _comm["commissionPct"]
            if "commissionAmount" in _comm: internal_update.commissionAmount = _comm["commissionAmount"]
            if "commissionStatus" in _comm: internal_update.commissionStatus = _comm["commissionStatus"]
        except Exception as _ce:
            logger.warning("Commission stamp failed for sub-order %s: %s", sub_order_id, _ce)
    elif status_data.status == "cancelled":
        internal_update.cancelledAt = _dt.utcnow().isoformat() + "Z"
    elif status_data.status == "shipped":
        internal_update.shippedAt = _dt.utcnow().isoformat() + "Z"

    updated = await sub_order_repository.update(sub_order_id, internal_update)

    # Bubble up: recalculate parent fulfillmentStatus
    parent_id = sub_order.parent_order_id
    if parent_id:
        parent = await order_repository.findById(parent_id)
        if parent and parent.subOrderIds:
            _f_status = await _compute_fulfillment_status(parent.subOrderIds)
            if _f_status:
                await order_repository.update(parent_id, OrderInternalUpdate(status=_f_status))

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
        query["status"] = status  # was query.status = status (dict has no .status attribute)
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








