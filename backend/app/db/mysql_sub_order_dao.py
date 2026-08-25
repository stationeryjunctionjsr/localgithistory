"""
MySQL DAO for sub-orders.
Fully normalized storage: no doc JSON.
Table: sj_sub_orders and sj_sub_order_items
"""

import secrets
from datetime import datetime, timezone
from typing import Dict, List, Optional

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
    }

    @property
    def table_name(self) -> str:
        suffix = getattr(settings, "table_suffix", "")
        return f"sj_sub_orders{suffix}"

    @property
    def items_table_name(self) -> str:
        suffix = getattr(settings, "table_suffix", "")
        return f"sj_sub_order_items{suffix}"

    def _get_session_factory(self):
        return get_async_session_factory()

    def _row_to_doc(self, row, items_rows=None) -> Dict:
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

        doc["createdAt"] = row.created_at.isoformat() if row.created_at else _now_iso()
        doc["updatedAt"] = row.updated_at.isoformat() if row.updated_at else _now_iso()
        return doc

    def _build_where(self, query: Dict):
        where_clauses = []
        params = {}
        for k, v in query.items():
            if k in ("_id", "id"):
                where_clauses.append("id = :q_id")
                params["q_id"] = int(v) if str(v).isdigit() else v
                continue
            col = self._COLUMN_MAP.get(k)
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

    async def findAll(self, query: Optional[Dict] = None, skip: int = 0, limit: int = 0) -> List[Dict]:
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

            return [self._row_to_doc(r, items_rows) for r in rows]

    async def findOne(self, query: Dict) -> Optional[Dict]:
        docs = await self.findAll(query, limit=1)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        return await self.findOne({"_id": id})

    async def findByParentOrder(self, parent_order_id: str) -> List[Dict]:
        return await self.findAll({"parentOrderId": parent_order_id})

    async def findBySeller(self, seller_id: str, query: Dict = None, skip: int = 0, limit: int = 0) -> List[Dict]:
        q = dict(query or {})
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

    async def create(self, data: Dict) -> Dict:
        factory = self._get_session_factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        now = datetime.now(timezone.utc)

        slot = data.get("deliverySlot") or {}
        c_info = data.get("couponInfo") or {}
        s_addr = data.get("shippingAddress") or {}
        b_addr = data.get("billingAddress") or {}

        params = {
            "external_id": secrets.token_hex(16),
            "sub_order_number": data.get("subOrderNumber", ""),
            "parent_order_id": str(data.get("parentOrderId") or ""),
            "parent_order_number": data.get("parentOrderNumber", ""),
            "seller_id": str(data.get("sellerId") or "") or None,
            "seller_name": data.get("sellerName"),
            "user_id": str(data.get("user") or ""),
            "subtotal": _safe_float(data.get("subtotal")),
            "tax": _safe_float(data.get("tax")),
            "shipping": _safe_float(data.get("shipping")),
            "delivery_gst": _safe_float(data.get("deliveryGst")),
            "discount": _safe_float(data.get("discount")),
            "total": _safe_float(data.get("total")),
            "order_type": data.get("orderType"),
            "status": data.get("status", "pending"),
            "payment_method": data.get("paymentMethod"),
            "payment_status": data.get("paymentStatus", "pending"),
            "is_urgent_delivery": 1 if data.get("isUrgentDelivery") else 0,
            "delivery_slot_config_id": slot.get("configId"),
            "delivery_slot_id": slot.get("slotId"),
            "delivery_slot_date": slot.get("date"),
            "notes": data.get("notes"),
            "coupon_code": data.get("couponCode"),
            "coupon_info_type": c_info.get("discountType"),
            "coupon_info_value": _safe_float(c_info.get("discountValue")),
            "commission_status": data.get("commissionStatus", "unrealized"),
            "shipping_name": s_addr.get("name"),
            "shipping_phone": s_addr.get("phone"),
            "shipping_line1": s_addr.get("line1"),
            "shipping_city": s_addr.get("city"),
            "shipping_state": s_addr.get("state"),
            "shipping_pincode": s_addr.get("pincode"),
            "billing_name": b_addr.get("name"),
            "billing_phone": b_addr.get("phone"),
            "billing_line1": b_addr.get("line1"),
            "billing_city": b_addr.get("city"),
            "billing_state": b_addr.get("state"),
            "billing_pincode": b_addr.get("pincode"),
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
                 created_at, updated_at)
            VALUES
                (:external_id, :sub_order_number, :parent_order_id, :parent_order_number,
                 :seller_id, :seller_name, :user_id, :subtotal, :tax, :shipping, :delivery_gst,
                 :discount, :total, :order_type, :status, :payment_method, :payment_status,
                 :is_urgent_delivery, :delivery_slot_config_id, :delivery_slot_id, :delivery_slot_date,
                 :notes, :coupon_code, :coupon_info_type, :coupon_info_value, :commission_status,
                 :shipping_name, :shipping_phone, :shipping_line1, :shipping_city, :shipping_state, :shipping_pincode,
                 :billing_name, :billing_phone, :billing_line1, :billing_city, :billing_state, :billing_pincode,
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

            items = data.get("items", [])
            for item in items:
                await session.execute(
                    item_sql,
                    {
                        "sub_order_id": new_id,
                        "product_id": item.get("productId", ""),
                        "name": item.get("name", ""),
                        "qty": int(item.get("qty") or 0),
                        "price": _safe_float(item.get("price")),
                    },
                )

            await session.commit()

        created = dict(data)
        created["_id"] = str(new_id)
        created["createdAt"] = now.isoformat()
        created["updatedAt"] = now.isoformat()
        return created

    async def update(self, id: str, data: Dict) -> Optional[Dict]:
        factory = self._get_session_factory()
        if not factory:
            return None
        now = datetime.now(timezone.utc)
        set_clauses = ["updated_at = :updated_at"]
        params: Dict = {"updated_at": now, "row_id": int(id) if str(id).isdigit() else id}

        for doc_field, col in self._COLUMN_MAP.items():
            if doc_field in data:
                set_clauses.append(f"{col} = :{col}")
                params[col] = data[doc_field]

        # Handle special dates
        if "deliveredAt" in data:
            set_clauses.append("delivered_at = :delivered_at")
            params["delivered_at"] = data["deliveredAt"]
        if "dispatchedAt" in data:
            set_clauses.append("dispatched_at = :dispatched_at")
            params["dispatched_at"] = data["dispatchedAt"]
        if "cancelledAt" in data:
            set_clauses.append("cancelled_at = :cancelled_at")
            params["cancelled_at"] = data["cancelledAt"]

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
