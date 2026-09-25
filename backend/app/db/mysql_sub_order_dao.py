from app.models.sub_order import SubOrderInternalCreate, SubOrderInternalUpdate
import logging
"""
MySQL DAO for sub-orders.
Fully normalized storage: no doc JSON.
Table: sj_sub_orders and sj_sub_order_items
"""

import secrets
from datetime import datetime, timezone
from typing import Dict
from app.models.sub_order import SubOrder, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(v):
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

    _COLUMN_MAP = {
        "sellerId": "seller_id",
        "status": "status",
        "parentOrderId": "parent_order_id",
        "user": "user_id",
        "commissionStatus": "commission_status",
        "paymentStatus": "payment_status",
        "total": "total",
        "subOrderNumber": "sub_order_number",
        "parentOrderNumber": "parent_order_number",
        "sellerName": "seller_name",
        "subtotal": "subtotal",
        "tax": "tax",
        "shipping": "shipping",
        "deliveryGst": "delivery_gst",
        "discount": "discount",
        "orderType": "order_type",
        "paymentMethod": "payment_method",
        "isUrgentDelivery": "is_urgent_delivery",
        "notes": "notes",
        "couponCode": "coupon_code",
        # Valet pickup tracking
        "pickupStatus": "pickup_status",
        "assignedValet": "assigned_valet",
    }

    @property
    def table_name(self) -> str:
        return "sj_sub_orders"

    @property
    def items_table_name(self) -> str:
        return "sj_sub_order_items"

    def _get_session_factory(self):
        return get_async_session_factory()

    def _map_to_schema(self, row, items_rows=None) -> 'SubOrder':
        from app.models.sub_order import SubOrder
        sub = SubOrder.model_validate(row)
        items = []
        if items_rows:
            for it in items_rows:
                if getattr(it, "sub_order_id", None) == row.id:
                    items.append({
                        "product_id": it.product_id, 
                        "name": it.name, 
                        "qty": it.qty, 
                        "price": float(it.price)
                    })
        sub.items = items
        return sub

    def _build_where(self, query: Dict):
        where_clauses = []
        params = {}
        for k, v in query.items():
            if k in ("_id", "id"):
                where_clauses.append("id = :q_id")
                params["q_id"] = int(v) if str(v).isdigit() else v
                continue
            col = self._COLUMN_MAP[k] if k in self._COLUMN_MAP else None
            p_name = f"qp_{k.replace('.', '_')}"
            if col:
                if isinstance(v, dict):
                    for op, op_val in v.items():
                        if op == "$in":
                            placeholders = [f":{p_name}_{i}" for i, _ in enumerate(op_val)]
                            for i, item in enumerate(op_val):
                                params[f"{p_name}_{i}"] = str(item)
                            if placeholders:
                                where_clauses.append(f"{col} IN ({', '.join(placeholders)})")
                            else:
                                where_clauses.append("1=0")
                        elif op == "$ne":
                            where_clauses.append(f"{col} != :{p_name}_ne")
                            params[f"{p_name}_ne"] = str(op_val)
                else:
                    where_clauses.append(f"{col} = :{p_name}")
                    params[p_name] = str(v) if not isinstance(v, bool) else ("true" if v else "false")
            else:
                pass  # Ignoring unmapped query fields
        return where_clauses, params

    async def findAll(self, query: Optional[Dict] = None, skip: int = 0, limit: int = 0) -> List['SubOrder']:
        factory = self._get_session_factory()
        if not factory:
            return []
        where_clauses, params = self._build_where(query or {})
        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        limit_sql = f" LIMIT {limit} OFFSET {skip}" if limit else (f" OFFSET {skip}" if skip else "")
        async with factory() as session:
            # 1. Fetch sub-orders
            query_sql = f"SELECT * FROM {self.table_name}{where_sql} ORDER BY created_at DESC{limit_sql}"
            result = await session.execute(text(query_sql), params)
            rows = result.fetchall()

            if not rows:
                return []

            # 2. Fetch all items for these sub-orders
            sub_order_ids = [r.id for r in rows]
            in_clause = ", ".join(str(id) for id in sub_order_ids)
            items_sql = f"SELECT * FROM {self.items_table_name} WHERE sub_order_id IN ({in_clause})"
            items_result = await session.execute(text(items_sql))
            items_rows = items_result.fetchall()

            return [SubOrder.model_validate(self._map_to_schema(r, items_rows) ) for r in rows]

    async def findOne(self, query: dict) -> Optional['SubOrder']:
        docs = await self.findAll(query, limit=1)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional['SubOrder']:
        return await self.findOne({"_id": id})

    async def findByParentOrder(self, parent_order_id: str) -> List['SubOrder']:
        return await self.findAll({"parentOrderId": parent_order_id})

    async def findBySeller(self, seller_id: str, query: Dict = None, skip: int = 0, limit: int = 0) -> List['SubOrder']:
        q = {**(query or {})}
        q["sellerId"] = seller_id
        return await self.findAll(q, skip=skip, limit=limit)

    async def count(self, query: Optional[Dict] = None) -> int:
        factory = self._get_session_factory()
        if not factory:
            return 0
        where_clauses, params = self._build_where(query or {})
        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        async with factory() as session:
            result = await session.execute(text(f"SELECT COUNT(*) FROM {self.table_name}{where_sql}"), params)
            return result.scalar() or 0

    async def create(self, data: 'SubOrderInternalCreate') -> 'SubOrder':
        factory = self._get_session_factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        now = datetime.now(timezone.utc)

        params = {
            "external_id": getattr(data, "external_id", None),
            "sub_order_number": data.sub_order_number,
            "parent_order_id": int(data.parent_order_id) if str(data.parent_order_id).isdigit() else None,
            "parent_order_number": data.parent_order_number,
            "seller_id": int(data.seller_id) if data.seller_id and str(data.seller_id).isdigit() else None,
            "seller_name": data.seller_name,
            "user_id": int(data.user) if data.user and str(data.user).isdigit() else None,
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
            "delivery_slot_config_id": data.delivery_slot_config_id,
            "delivery_slot_id": data.delivery_slot_id,
            "delivery_slot_date": data.delivery_slot_date,
            "notes": getattr(data, "notes", None),
            "coupon_code": getattr(data, "coupon_code", None),
            "coupon_info_type": getattr(data, "coupon_info_type", None),
            "coupon_info_value": getattr(data, "coupon_info_value", None),
            "commission_status": data.commission_status if data.commission_status else "unrealized",
            "shipping_name": getattr(data, "shipping_name", None),
            "shipping_phone": getattr(data, "shipping_phone", None),
            "shipping_line1": getattr(data, "shipping_line1", None),
            "shipping_city": getattr(data, "shipping_city", None),
            "shipping_state": getattr(data, "shipping_state", None),
            "shipping_pincode": getattr(data, "shipping_pincode", None),
            "billing_name": getattr(data, "billing_name", None),
            "billing_phone": getattr(data, "billing_phone", None),
            "billing_line1": getattr(data, "billing_line1", None),
            "billing_city": getattr(data, "billing_city", None),
            "billing_state": getattr(data, "billing_state", None),
            "billing_pincode": getattr(data, "billing_pincode", None),
            "pickup_status": (data.pickup_status if data.pickup_status is not None else "pending_pickup"),
            "assigned_valet": getattr(data, "assigned_valet", None),
            "created_at": now,
            "updated_at": now,
        }

        sql = text(f"""
            INSERT INTO {self.table_name}
                (external_id, sub_order_number, parent_order_id, parent_order_number,
                 seller_id, seller_name, user_id, subtotal, tax, shipping, delivery_gst,
                 discount, total, order_type, status, payment_method, payment_status,
                 is_urgent_delivery, delivery_slot_config_id, delivery_slot_id, delivery_slot_date,
                 notes, coupon_code, coupon_info_type, coupon_info_value, commission_status,
                 shipping_name, shipping_phone, shipping_line1, shipping_city, shipping_state, shipping_pincode,
                 billing_name, billing_phone, billing_line1, billing_city, billing_state, billing_pincode,
                 pickup_status, assigned_valet,
                 created_at, updated_at)
            VALUES
                (:external_id, :sub_order_number, :parent_order_id, :parent_order_number,
                 :seller_id, :seller_name, :user_id, :subtotal, :tax, :shipping, :delivery_gst,
                 :discount, :total, :order_type, :status, :payment_method, :payment_status,
                 :is_urgent_delivery, :delivery_slot_config_id, :delivery_slot_id, :delivery_slot_date,
                 :notes, :coupon_code, :coupon_info_type, :coupon_info_value, :commission_status,
                 :shipping_name, :shipping_phone, :shipping_line1, :shipping_city, :shipping_state, :shipping_pincode,
                 :billing_name, :billing_phone, :billing_line1, :billing_city, :billing_state, :billing_pincode,
                 :pickup_status, :assigned_valet,
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

            items = (data.items if data.items is not None else [])
            for item in items:
                await session.execute(
                    item_sql,
                    {
                        "sub_order_id": new_id,
                        "product_id": (item.product_id if item.product_id is not None else ""),
                        "name": (item.name if item.name is not None else ""),
                        "qty": int(item.qty or 0),
                        "price": _safe_float(item.price),
                    },
                )

            await session.commit()

        return await self.findById(str(new_id))

    def _parse_dt(self, dt_val):
        if not dt_val: return None
        from datetime import datetime
        if isinstance(dt_val, datetime): return dt_val
        try:
            return datetime.fromisoformat(dt_val.replace('Z', '+00:00'))
        except:
            return None

    async def update(self, id: str, update_data: 'SubOrderInternalUpdate') -> Optional['SubOrder']:
        factory = self._get_session_factory()
        if not factory:
            return None
        now = datetime.now(timezone.utc)
        set_clauses = ["updated_at = :updated_at"]
        params: Dict = {"updated_at": now, "row_id": int(id) if str(id).isdigit() else id}

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

        if len(set_clauses) > 1:
            sql = text(f"UPDATE {self.table_name} SET {', '.join(set_clauses)} WHERE id = :row_id")
            async with factory() as session:
                await session.execute(sql, params)
                await session.commit()

        return await self.findById(str(id))

    async def delete(self, id: str) -> bool:
        factory = self._get_session_factory()
        if not factory:
            return False
        async with factory() as session:
            result = await session.execute(text(f"DELETE FROM {self.table_name} WHERE id = :id"), {"id": int(id)})
            await session.commit()
            return result.rowcount > 0






