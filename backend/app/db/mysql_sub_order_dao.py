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


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(v):
    try:
        return float(v) if v is not None else 0.0
    except Exception:
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
        suffix = (settings.table_suffix if settings.table_suffix is not None else "")
        return f"sj_sub_orders{suffix}"

    @property
    def items_table_name(self) -> str:
        suffix = (settings.table_suffix if settings.table_suffix is not None else "")
        return f"sj_sub_order_items{suffix}"

    def _get_session_factory(self):
        return get_async_session_factory()

    def _map_to_schema(self, row, items_rows=None) -> 'SubOrder':
        """Construct the NoSQL-style dictionary from flattened SQL columns."""
        doc = {
            "_id": str(row.id),
            "_db_id": str(row.id),
        }

        # Scalars
        if row.sub_order_number is not None:
            doc["subOrderNumber"] = row.sub_order_number
        if row.parent_order_id is not None:
            doc["parentOrderId"] = row.parent_order_id
        if row.parent_order_number is not None:
            doc["parentOrderNumber"] = row.parent_order_number
        if row.seller_id is not None:
            doc["sellerId"] = row.seller_id
        if row.seller_name is not None:
            doc["sellerName"] = row.seller_name
        if row.user_id is not None:
            doc["user"] = row.user_id
        if row.subtotal is not None:
            doc["subtotal"] = float(row.subtotal)
        if row.tax is not None:
            doc["tax"] = float(row.tax)
        if row.shipping is not None:
            doc["shipping"] = float(row.shipping)
        if row.delivery_gst is not None:
            doc["deliveryGst"] = float(row.delivery_gst)
        if row.discount is not None:
            doc["discount"] = float(row.discount)
        if row.total is not None:
            doc["total"] = float(row.total)
        if row.order_type is not None:
            doc["orderType"] = row.order_type
        if row.status is not None:
            doc["status"] = row.status
        if row.payment_method is not None:
            doc["paymentMethod"] = row.payment_method
        if row.payment_status is not None:
            doc["paymentStatus"] = row.payment_status
        if row.is_urgent_delivery is not None:
            doc["isUrgentDelivery"] = bool(row.is_urgent_delivery)
        if row.notes is not None:
            doc["notes"] = row.notes
        if row.coupon_code is not None:
            doc["couponCode"] = row.coupon_code
        if row.commission_status is not None:
            doc["commissionStatus"] = row.commission_status

        # Nested Objects
        if row.delivery_slot_config_id or row.delivery_slot_id or row.delivery_slot_date:
            doc["deliverySlot"] = {
                "configId": row.delivery_slot_config_id,
                "slotId": row.delivery_slot_id,
                "date": row.delivery_slot_date,
            }

        if row.coupon_info_type or row.coupon_info_value is not None:
            doc["couponInfo"] = {
                "discountType": row.coupon_info_type,
                "discountValue": float(row.coupon_info_value) if row.coupon_info_value is not None else 0,
            }

        doc["shippingAddress"] = {
            "name": row.shipping_name,
            "phone": row.shipping_phone,
            "line1": row.shipping_line1,
            "city": row.shipping_city,
            "state": row.shipping_state,
            "pincode": row.shipping_pincode,
        }

        doc["billingAddress"] = {
            "name": row.billing_name,
            "phone": row.billing_phone,
            "line1": row.billing_line1,
            "city": row.billing_city,
            "state": row.billing_state,
            "pincode": row.billing_pincode,
        }

        # Arrays
        items = []
        if items_rows:
            for it in items_rows:
                if it.sub_order_id == row.id:
                    items.append({"productId": it.product_id, "name": it.name, "qty": it.qty, "price": float(it.price)})
        doc["items"] = items

        # Dates
        if row.delivered_at:
            doc["deliveredAt"] = row.delivered_at.isoformat()
        if row.dispatched_at:
            doc["dispatchedAt"] = row.dispatched_at.isoformat()
        if row.cancelled_at:
            doc["cancelledAt"] = row.cancelled_at.isoformat()

        # Valet pickup tracking
        doc["pickupStatus"] = row.pickup_status if row.pickup_status else "pending_pickup"
        doc["assignedValet"] = row.assigned_valet
        if row.picked_up_at:
            doc["pickedUpAt"] = row.picked_up_at.isoformat()

        doc["createdAt"] = row.created_at.isoformat() if row.created_at else _now_iso()
        doc["updatedAt"] = row.updated_at.isoformat() if row.updated_at else _now_iso()
        from app.models.sub_order import SubOrder
        return SubOrder(**doc)

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

        slot = data.deliverySlot
        c_info = data.couponInfo
        s_addr = data.shippingAddress
        b_addr = data.billingAddress

        params = {
            "external_id": secrets.token_hex(16),
            "sub_order_number": (data.subOrderNumber if data.subOrderNumber is not None else ""),
            "parent_order_id": str(data.parentOrderId or ""),
            "parent_order_number": (data.parentOrderNumber if data.parentOrderNumber is not None else ""),
            "seller_id": str(data.sellerId or "") or None,
            "seller_name": data.sellerName,
            "user_id": str(data.user or ""),
            "subtotal": _safe_float(data.subtotal),
            "tax": _safe_float(data.tax),
            "shipping": _safe_float(data.shipping),
            "delivery_gst": _safe_float(data.deliveryGst),
            "discount": _safe_float(data.discount),
            "total": _safe_float(data.total),
            "order_type": data.orderType,
            "status": (data.status if data.status is not None else "pending"),
            "payment_method": data.paymentMethod,
            "payment_status": (data.paymentStatus if data.paymentStatus is not None else "pending"),
            "is_urgent_delivery": 1 if data.isUrgentDelivery else 0,
            "delivery_slot_config_id": slot.configId if slot else None,
            "delivery_slot_id": slot.slotId if slot else None,
            "delivery_slot_date": slot.date if slot else None,
            "notes": data.notes,
            "coupon_code": data.couponCode,
            "coupon_info_type": c_info.discountType if c_info else None,
            "coupon_info_value": _safe_float(c_info.discountValue) if c_info else None,
            "commission_status": (data.commissionStatus if data.commissionStatus is not None else "unrealized"),
            "shipping_name": s_addr.name if s_addr else None,
            "shipping_phone": s_addr.phone if s_addr else None,
            "shipping_line1": s_addr.line1 if s_addr else None,
            "shipping_city": s_addr.city if s_addr else None,
            "shipping_state": s_addr.state if s_addr else None,
            "shipping_pincode": s_addr.pincode if s_addr else None,
            "billing_name": b_addr.name if b_addr else None,
            "billing_phone": b_addr.phone if b_addr else None,
            "billing_line1": b_addr.line1 if b_addr else None,
            "billing_city": b_addr.city if b_addr else None,
            "billing_state": b_addr.state if b_addr else None,
            "billing_pincode": b_addr.pincode if b_addr else None,
            # Valet pickup tracking
            "pickup_status": (data.pickupStatus if data.pickupStatus is not None else "pending_pickup"),
            "assigned_valet": data.assignedValet,
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
                        "product_id": (item.productId if item.productId is not None else ""),
                        "name": (item.name if item.name is not None else ""),
                        "qty": int(item.qty or 0),
                        "price": _safe_float(item.price),
                    },
                )

            await session.commit()

        return await self.findById(str(new_id))

    async def update(self, id: str, data: 'SubOrderInternalUpdate') -> Optional['SubOrder']:
        factory = self._get_session_factory()
        if not factory:
            return None
        now = datetime.now(timezone.utc)
        set_clauses = ["updated_at = :updated_at"]
        params: Dict = {"updated_at": now, "row_id": int(id) if str(id).isdigit() else id}

        if data.status is not None:
            set_clauses.append("status = :status")
            params["status"] = data.status
        if data.shippedAt is not None:
            set_clauses.append("dispatched_at = :dispatched_at")
            params["dispatched_at"] = data.shippedAt
        if data.deliveredAt is not None:
            set_clauses.append("delivered_at = :delivered_at")
            params["delivered_at"] = data.deliveredAt
        if data.cancelledAt is not None:
            set_clauses.append("cancelled_at = :cancelled_at")
            params["cancelled_at"] = data.cancelledAt
        if data.pickupStatus is not None:
            set_clauses.append("pickup_status = :pickup_status")
            params["pickup_status"] = data.pickupStatus
        if data.pickedUpAt is not None:
            set_clauses.append("picked_up_at = :picked_up_at")
            params["picked_up_at"] = data.pickedUpAt
        if data.commissionPct is not None:
            set_clauses.append("commission_pct = :commission_pct")
            params["commission_pct"] = data.commissionPct
        if data.commissionAmount is not None:
            set_clauses.append("commission_amount = :commission_amount")
            params["commission_amount"] = data.commissionAmount
        if data.commissionStatus is not None:
            set_clauses.append("commission_status = :commission_status")
            params["commission_status"] = data.commissionStatus
        if data.assignedValet is not None:
            set_clauses.append("assigned_valet = :assigned_valet")
            params["assigned_valet"] = data.assignedValet

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
