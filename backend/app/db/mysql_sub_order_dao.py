import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.models.sub_order import (
    SubOrder,
    SubOrderFilter,
    SubOrderItem,
    SubOrderInternalCreate,
    SubOrderInternalUpdate,
)

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(v) -> float:
    try:
        return float(v) if v is not None else 0.0
    except (ValueError, TypeError):
        logger.warning("_safe_float: cannot convert %r to float, defaulting to 0.0", v, exc_info=True)
        return 0.0


class MySQLSubOrderDAO:
    """
    Fully normalized DAO for sj_sub_orders.
    Implements same interface as MySQLDocStore for drop-in compatibility.
    """

    @property
    def table_name(self) -> str:
        return "sj_sub_orders"

    @property
    def items_table_name(self) -> str:
        return "sj_sub_order_items"

    def _get_session_factory(self):
        return get_async_session_factory()

    def _map_to_schema(self, row, items_rows=None) -> SubOrder:
        sub = SubOrder.model_validate(row)
        if items_rows:
            sub.items = [
                SubOrderItem(
                    product_id=it.product_id,
                    name=it.name,
                    qty=it.qty,
                    price=float(it.price) if it.price is not None else 0.0,
                )
                for it in items_rows
                if it.sub_order_id == row.id
            ]
        else:
            sub.items = []
        return sub

    async def findAll(self, filter_params: Optional[SubOrderFilter] = None, skip: int = 0, limit: int = 0) -> List[SubOrder]:
        factory = self._get_session_factory()
        if not factory:
            return []

        where_clauses = []
        params = {}
        if filter_params:
            if filter_params.id:
                where_clauses.append("id = :q_id")
                params["q_id"] = filter_params.id
            if filter_params.seller_id:
                where_clauses.append("seller_id = :seller_id")
                params["seller_id"] = filter_params.seller_id
            if filter_params.parent_order_id:
                where_clauses.append("parent_order_id = :parent_order_id")
                params["parent_order_id"] = filter_params.parent_order_id
            if filter_params.status:
                where_clauses.append("status = :status")
                params["status"] = filter_params.status
            if filter_params.commission_status:
                where_clauses.append("commission_status = :commission_status")
                params["commission_status"] = filter_params.commission_status
            if filter_params.payment_status:
                where_clauses.append("payment_status = :payment_status")
                params["payment_status"] = filter_params.payment_status
            if filter_params.start_date:
                where_clauses.append("created_at >= :start_date")
                params["start_date"] = filter_params.start_date
            if filter_params.end_date:
                where_clauses.append("created_at <= :end_date")
                params["end_date"] = filter_params.end_date

        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        limit_sql = f" LIMIT {limit} OFFSET {skip}" if limit else (f" OFFSET {skip}" if skip else "")
        async with factory() as session:
            result = await session.execute(text(f"SELECT * FROM {self.table_name}{where_sql} ORDER BY id DESC{limit_sql}"), params)
            rows = result.fetchall()
            if not rows:
                return []
            sub_order_ids = [r.id for r in rows]
            in_clause = ", ".join(str(i) for i in sub_order_ids)
            items_res = await session.execute(text(f"SELECT * FROM {self.items_table_name} WHERE sub_order_id IN ({in_clause})"))
            items_rows = items_res.fetchall()
            return [self._map_to_schema(r, items_rows) for r in rows]

    async def findById(self, id: int) -> Optional[SubOrder]:
        factory = self._get_session_factory()
        if not factory or not id:
            return None
        async with factory() as session:
            q = text(f"SELECT * FROM {self.table_name} WHERE id = :id")
            result = await session.execute(q, {"id": id})
            row = result.fetchone()
            if not row:
                return None
            items_res = await session.execute(
                text(f"SELECT * FROM {self.items_table_name} WHERE sub_order_id = :so_id"),
                {"so_id": row.id},
            )
            items_rows = items_res.fetchall()
            return self._map_to_schema(row, items_rows)

    async def findByParentOrder(self, parent_order_id: int) -> List[SubOrder]:
        factory = self._get_session_factory()
        if not factory or not parent_order_id:
            return []
        async with factory() as session:
            q = text(f"SELECT * FROM {self.table_name} WHERE parent_order_id = :pid ORDER BY id ASC")
            params = {"pid": parent_order_id}
            result = await session.execute(q, params)
            rows = result.fetchall()
            if not rows:
                return []
            sub_order_ids = [r.id for r in rows]
            in_clause = ", ".join(str(i) for i in sub_order_ids)
            items_res = await session.execute(text(f"SELECT * FROM {self.items_table_name} WHERE sub_order_id IN ({in_clause})"))
            items_rows = items_res.fetchall()
            return [self._map_to_schema(r, items_rows) for r in rows]

    async def findBySeller(self, seller_id: str, filter_params: Optional[SubOrderFilter] = None, skip: int = 0, limit: int = 0) -> List[SubOrder]:
        f = filter_params.model_copy() if filter_params else SubOrderFilter()
        f.seller_id = seller_id
        return await self.findAll(f, skip=skip, limit=limit)

    async def count(self, filter_params: Optional[SubOrderFilter] = None) -> int:
        factory = self._get_session_factory()
        if not factory:
            return 0
        where_clauses = []
        params = {}
        if filter_params:
            if filter_params.id:
                where_clauses.append("id = :q_id")
                params["q_id"] = filter_params.id
            if filter_params.seller_id:
                where_clauses.append("seller_id = :seller_id")
                params["seller_id"] = filter_params.seller_id
            if filter_params.parent_order_id:
                where_clauses.append("parent_order_id = :parent_order_id")
                params["parent_order_id"] = filter_params.parent_order_id
            if filter_params.status:
                where_clauses.append("status = :status")
                params["status"] = filter_params.status
            if filter_params.commission_status:
                where_clauses.append("commission_status = :commission_status")
                params["commission_status"] = filter_params.commission_status
            if filter_params.payment_status:
                where_clauses.append("payment_status = :payment_status")
                params["payment_status"] = filter_params.payment_status
            if filter_params.start_date:
                where_clauses.append("created_at >= :start_date")
                params["start_date"] = filter_params.start_date
            if filter_params.end_date:
                where_clauses.append("created_at <= :end_date")
                params["end_date"] = filter_params.end_date
        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        async with factory() as session:
            result = await session.execute(text(f"SELECT COUNT(*) FROM {self.table_name}{where_sql}"), params)
            return result.scalar() or 0

    async def create(self, data: SubOrderInternalCreate) -> SubOrder:
        factory = self._get_session_factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        now = datetime.now(timezone.utc)

        slot_id = data.delivery_slot.slot_id if data.delivery_slot else None
        slot_date = data.delivery_slot.date if data.delivery_slot else None

        ship_name = data.shipping_address.name if data.shipping_address else None
        ship_phone = data.shipping_address.phone if data.shipping_address else None
        ship_line1 = (data.shipping_address.address or data.shipping_address.street) if data.shipping_address else None
        ship_city = data.shipping_address.city if data.shipping_address else None
        ship_state = data.shipping_address.state if data.shipping_address else None
        ship_pincode = (data.shipping_address.pincode or data.shipping_address.zip_code) if data.shipping_address else None

        bill_name = data.billing_address.name if data.billing_address else None
        bill_phone = data.billing_address.phone if data.billing_address else None
        bill_line1 = (data.billing_address.address or data.billing_address.street) if data.billing_address else None
        bill_city = data.billing_address.city if data.billing_address else None
        bill_state = data.billing_address.state if data.billing_address else None
        bill_pincode = (data.billing_address.pincode or data.billing_address.zip_code) if data.billing_address else None

        coupon_code = data.coupon_code or (data.coupon_info.code if data.coupon_info else None)
        coupon_type = data.coupon_info.discount_type if data.coupon_info else None
        coupon_val = data.coupon_info.discount_value if data.coupon_info else None

        params = {
            "sub_order_number": data.sub_order_number,
            "parent_order_id": data.parent_order_id,
            "parent_order_number": data.parent_order_number,
            "seller_id": data.seller_id,
            "seller_name": data.seller_name,
            "user_id": data.user,
            "subtotal": float(data.subtotal),
            "tax": float(data.tax),
            "shipping": float(data.shipping),
            "delivery_gst": float(data.delivery_gst),
            "discount": float(data.discount),
            "total": float(data.total),
            "order_type": data.order_type,
            "status": data.status,
            "payment_method": data.payment_method,
            "payment_status": data.payment_status,
            "is_urgent_delivery": data.is_urgent_delivery,
            "delivery_slot_config_id": None,
            "delivery_slot_id": slot_id,
            "delivery_slot_date": slot_date,
            "notes": data.notes,
            "coupon_code": coupon_code,
            "coupon_info_type": coupon_type,
            "coupon_info_value": coupon_val,
            "commission_status": data.commission_status if data.commission_status else "unrealized",
            "shipping_name": ship_name,
            "shipping_phone": ship_phone,
            "shipping_line1": ship_line1,
            "shipping_city": ship_city,
            "shipping_state": ship_state,
            "shipping_pincode": ship_pincode,
            "billing_name": bill_name,
            "billing_phone": bill_phone,
            "billing_line1": bill_line1,
            "billing_city": bill_city,
            "billing_state": bill_state,
            "billing_pincode": bill_pincode,
            "pickup_status": (data.pickup_status if data.pickup_status is not None else "pending_pickup"),
            "assigned_valet": data.assigned_valet,
            "fulfillment_type": data.fulfillment_type or "hyperlocal",
            "courier_partner": data.courier_partner,
            "tracking_id": data.tracking_id,
            "awb_code": data.awb_code,
            "created_at": now,
            "updated_at": now,
        }

        sql = text(f"""
            INSERT INTO {self.table_name}
                (sub_order_number, parent_order_id, parent_order_number,
                 seller_id, seller_name, user_id, subtotal, tax, shipping, delivery_gst,
                 discount, total, order_type, status, payment_method, payment_status,
                 is_urgent_delivery, delivery_slot_config_id, delivery_slot_id, delivery_slot_date,
                 notes, coupon_code, coupon_info_type, coupon_info_value, commission_status,
                 shipping_name, shipping_phone, shipping_line1, shipping_city, shipping_state, shipping_pincode,
                 billing_name, billing_phone, billing_line1, billing_city, billing_state, billing_pincode,
                 pickup_status, assigned_valet,
                 fulfillment_type, courier_partner, tracking_id, awb_code,
                 created_at, updated_at)
            VALUES
                (:sub_order_number, :parent_order_id, :parent_order_number,
                 :seller_id, :seller_name, :user_id, :subtotal, :tax, :shipping, :delivery_gst,
                 :discount, :total, :order_type, :status, :payment_method, :payment_status,
                 :is_urgent_delivery, :delivery_slot_config_id, :delivery_slot_id, :delivery_slot_date,
                 :notes, :coupon_code, :coupon_info_type, :coupon_info_value, :commission_status,
                 :shipping_name, :shipping_phone, :shipping_line1, :shipping_city, :shipping_state, :shipping_pincode,
                 :billing_name, :billing_phone, :billing_line1, :billing_city, :billing_state, :billing_pincode,
                 :pickup_status, :assigned_valet,
                 :fulfillment_type, :courier_partner, :tracking_id, :awb_code,
                 :created_at, :updated_at)
        """)

        item_sql = text(f"""
            INSERT INTO {self.items_table_name}
                (sub_order_id, product_id, name, qty, price)
            VALUES
                (:sub_order_id, :product_id, :name, :qty, :price)
        """)

        async with factory() as session:
            result = await session.execute(sql, params)
            new_id = result.lastrowid

            items = data.items if data.items is not None else []
            for item in items:
                await session.execute(
                    item_sql,
                    {
                        "sub_order_id": new_id,
                        "product_id": item.product_id if item.product_id is not None else "",
                        "name": item.name if item.name is not None else "",
                        "qty": int(item.qty or 0),
                        "price": _safe_float(item.price),
                    },
                )

            await session.commit()

        return await self.findById(str(new_id))

    def _parse_dt(self, dt_val):
        if not dt_val:
            return None
        try:
            return datetime.fromisoformat(dt_val.replace('Z', '+00:00'))
        except AttributeError:
            return dt_val
        except (ValueError, TypeError):
            return None

    async def update(self, id: int, update_data: SubOrderInternalUpdate) -> Optional[SubOrder]:
        factory = self._get_session_factory()
        if not factory or not id:
            return None
        row_id = id
        now = datetime.now(timezone.utc)
        set_clauses = ["updated_at = :updated_at"]
        params = {"updated_at": now, "row_id": row_id}
        data = update_data

        if data.status is not None:
            set_clauses.append("status = :status")
            params["status"] = data.status
        if data.shipped_at is not None:
            set_clauses.append("dispatched_at = :dispatched_at")
            params["dispatched_at"] = self._parse_dt(data.shipped_at)
        if data.delivered_at is not None:
            set_clauses.append("delivered_at = :delivered_at")
            params["delivered_at"] = self._parse_dt(data.delivered_at)
        if data.cancelled_at is not None:
            set_clauses.append("cancelled_at = :cancelled_at")
            params["cancelled_at"] = self._parse_dt(data.cancelled_at)
        if data.pickup_status is not None:
            set_clauses.append("pickup_status = :pickup_status")
            params["pickup_status"] = data.pickup_status
        if data.picked_up_at is not None:
            set_clauses.append("picked_up_at = :picked_up_at")
            params["picked_up_at"] = self._parse_dt(data.picked_up_at)
        if data.commission_pct is not None:
            set_clauses.append("commission_pct = :commission_pct")
            params["commission_pct"] = data.commission_pct
        if data.commission_amount is not None:
            set_clauses.append("commission_amount = :commission_amount")
            params["commission_amount"] = data.commission_amount
        if data.commission_status is not None:
            set_clauses.append("commission_status = :commission_status")
            params["commission_status"] = data.commission_status
        if data.assigned_valet is not None:
            set_clauses.append("assigned_valet = :assigned_valet")
            params["assigned_valet"] = data.assigned_valet
        if data.fulfillment_type is not None:
            set_clauses.append("fulfillment_type = :fulfillment_type")
            params["fulfillment_type"] = data.fulfillment_type
        if data.courier_partner is not None:
            set_clauses.append("courier_partner = :courier_partner")
            params["courier_partner"] = data.courier_partner
        if data.tracking_id is not None:
            set_clauses.append("tracking_id = :tracking_id")
            params["tracking_id"] = data.tracking_id
        if data.awb_code is not None:
            set_clauses.append("awb_code = :awb_code")
            params["awb_code"] = data.awb_code

        if len(set_clauses) > 1:
            sql = text(f"UPDATE {self.table_name} SET {', '.join(set_clauses)} WHERE id = :row_id")
            async with factory() as session:
                await session.execute(sql, params)
                await session.commit()

        return await self.findById(id)

    async def delete(self, id: int) -> bool:
        factory = self._get_session_factory()
        if not factory or not id:
            return False
        async with factory() as session:
            sql = f"DELETE FROM {self.table_name} WHERE id = :id"
            result = await session.execute(text(sql), {"id": id})
            await session.commit()
            return result.rowcount > 0
