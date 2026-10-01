"""
order_service.py
================
Pure business-logic helpers extracted from app/routers/orders.py.
All functions are async and fully typed.  No FastAPI routing concerns here.
"""

from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.base import CamelBaseModel
from app.models.daos import NotificationInternalCreate
from app.models.order import Order
from app.models.product import Product
from app.models.schemas import (
    Address,
    UserSnippet,
    ValetSnippet,
    ItemSnippet as OrderItem,
    PopulatedOrderResponse,
    PopulatedOrderItemResponse,
    VariantAttributes,
)
from app.repositories.notification_repository import notification_repository
from app.repositories.user_repository import user_repository
from app.db.storage_factory import get_storage
from app.utils.logger import logger


# ---------------------------------------------------------------------------
# Helper models
# ---------------------------------------------------------------------------

class CalculatedOrderItem(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    product: Optional[str] = None
    seller_id: Optional[str] = None
    product_name: Optional[str] = None
    quantity: int = 1
    sell_as_case: Optional[bool] = False
    price: float = 0.0
    price_before_coupon: float = 0.0
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


class LocationDeliveryCharge(CamelBaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    charge: float = 0.0
    min_cart_value: float = 0.0
    is_applicable_to_role: bool = True
    urgent_delivery_charge: Optional[float] = None
    urgent_delivery_available: Optional[bool] = False


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
        return self.type_of_discount


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
        return self.is_active

    @property
    def discount_type(self) -> str:
        return self.discountType

    @property
    def discount_value(self) -> float:
        return self.discountValue


class ReferralSettingsModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    retail: ReferralProgramSegmentSettings = Field(
        default_factory=ReferralProgramSegmentSettings)
    business: Optional[ReferralProgramSegmentSettings] = None


# ---------------------------------------------------------------------------
# Helpers: resolve product seller
# ---------------------------------------------------------------------------

def _resolve_product_seller_id(product: Product, serviceable_seller_ids: list[str] = None) -> str:
    if product.sellers:
        return product.sellers[0].seller_id
    # Product has no seller_id field — sellers list is the sole source
    return None


# ---------------------------------------------------------------------------
# Notification helpers
# ---------------------------------------------------------------------------

# Helper function to create order notification
async def create_order_notification(order) -> None:
    order_zone_id = None
    try:
        super_admin = await user_repository.findOne({"role": "super_admin"})
        if not super_admin:
            return

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
        logger.error("Error creating order notification for order %s: %s",
                     order.id, str(e), exc_info=True)


# Helper function to create payment notification
async def create_payment_notification(payment) -> None:
    try:
        super_admin = await user_repository.findOne({"role": "super_admin"})
        if not super_admin:
            return

        payment_id = payment.payment_id or payment.id
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


# ---------------------------------------------------------------------------
# Populate helpers
# ---------------------------------------------------------------------------

async def populate_orders(orders: list[Order]) -> list[PopulatedOrderResponse]:
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
            if 'productId' in item.model_fields:
                pid = item.product_id
            else:
                pid = item.product.id if item.product else None

            if pid and str(pid).isdigit():
                product_ids.add(str(pid))

    # 2. Fetch all required users, valets, products, and payments in parallel
    users_task = get_storage("users").findAll({"allowed_ids": list(
        user_ids.union(valet_ids))}) if user_ids.union(valet_ids) else None
    products_task = get_storage("products").findAll(
        {"allowed_ids": list(product_ids)}) if product_ids else None
    payments_task = get_storage("payments").findAll(
        {"allowed_order_ids": list(order_ids)}) if order_ids else None

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
        payment_entries = payments_map[o_id] if o_id and o_id in payments_map else [
        ]

        o_items = order.items if order.items else []
        populated_items = []

        for i_dict in o_items:
            # i_dict is a Pydantic ItemSnippet (OrderItem)
            # .product holds the product ID reference; .product_id is the alternate field
            pid = str(i_dict.product) if i_dict.product else (
                str(i_dict.product_id) if i_dict.product_id else None)
            product = products_map[pid] if pid and pid in products_map else None

            # stockStatus, taxRate, taxAmount are not stored in sj_order_items (DB has
            # only product_id, quantity, price) — they are None until the DB schema
            # is extended and ItemSnippet gains those columns.
            p_item = PopulatedOrderItemResponse(
                product=product,
                quantity=i_dict.quantity,
                price=i_dict.price,
                stock_status=None,
                tax_rate=None,
                tax_amount=None,
            )
            populated_items.append(p_item)

        from app.models.order import Order
        order_resp = Order.model_validate(order, from_attributes=True)
        order_resp.items = populated_items

        # couponCode, zoneId, adminNotes, valetNotes are not yet stored in sj_orders
        # (no DB columns) — declared on PopulatedOrderResponse as Optional[str] = None
        pop_order = PopulatedOrderResponse(
            id=order_resp.id,
            user=UserSnippet.model_validate(
                user, from_attributes=True) if user else None,
            assigned_valet=ValetSnippet.model_validate(
                valet, from_attributes=True) if valet else None,
            payment_entries=[entry for payment in payment_entries for entry in (
                payment.payment_entries or [])] if payment_entries else [],
            items=populated_items,
            sub_orders=order_resp.sub_orders,
            order_status=order_resp.status,
            total=order_resp.total,
            total_amount=order_resp.total,
            delivery_fee=order_resp.shipping,
            discount=order_resp.discount,
            coupon_code=None,
            payment_method=order_resp.payment_method,
            payment_status=order_resp.payment_status,
            address=Address(
                name=order_resp.ship_name,
                street=order_resp.ship_street,
                city=order_resp.ship_city,
                state=order_resp.ship_state,
                pincode=order_resp.ship_pincode,
                phone=order_resp.ship_phone,
                district=order_resp.ship_district,
                country=order_resp.ship_country,
                google_location=order_resp.ship_google_location,
                latitude=order_resp.ship_latitude,
                longitude=order_resp.ship_longitude,
                address=order_resp.ship_address
            ) if order_resp.ship_city or order_resp.ship_street else None,
            created_at=order_resp.created_at,
            updated_at=order_resp.updated_at,
            zone_id=None,
            order_notes=order_resp.notes,
            admin_notes=None,
            valet_notes=None,
        )
        populated.append(pop_order)

    return populated


async def populate_order(order: Order) -> Optional[PopulatedOrderResponse]:
    """Populate a single order by reusing populate_orders"""
    if not order:
        return None
    res = await populate_orders([order])
    return res[0] if res else None


# ---------------------------------------------------------------------------
# Fulfillment status helper
# ---------------------------------------------------------------------------

async def _compute_fulfillment_status(sub_order_ids: list) -> Optional[str]:
    """
    Derive parent order fulfillmentStatus from sub-order states.
    Returns None if there are no sub-orders (single-seller, legacy flow).
    """
    from app.repositories.sub_order_repository import sub_order_repository

    if not sub_order_ids:
        return None

    statuses = []
    for so_id in sub_order_ids:
        so = await sub_order_repository.findById(so_id)
        if so:
            statuses.append(
                (so.status if so.status is not None else "pending"))

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
