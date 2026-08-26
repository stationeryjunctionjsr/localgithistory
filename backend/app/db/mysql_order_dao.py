"""
MySQL DAO for sj_orders (+ sj_order_items).
Implements FileStorage-like interface for 'orders' so repositories keep working.

Assumptions (matches current MySQLUserDAO / MySQLDocStore behavior):
- API/_id values are numeric `id` PKs (not external_id).
- Order `user` field stores numeric user id as string.
- Order items store `product` as numeric product id as string.
"""

import secrets
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.oracle_utils import json_dumps, json_loads, now_utc


def _to_ts(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


class MySQLOrderDAO:
    @property
    def TABLE(self):
        suffix = getattr(settings, "table_suffix", "")
        return f"sj_orders{suffix}"

    @property
    def ITEMS_TABLE(self):
        suffix = getattr(settings, "table_suffix", "")
        return f"sj_order_items{suffix}"

    def _factory(self):
        return get_async_session_factory()

    async def _load_items(self, session, order_id: int) -> List[Dict]:
        result = await session.execute(
            text(
                f"""
                SELECT product_id, quantity, price
                FROM {self.ITEMS_TABLE}
                WHERE order_id = :order_id
                """
            ),
            {"order_id": order_id},
        )
        rows = result.fetchall()
        items: List[Dict] = []
        for r in rows:
            items.append(
                {
                    "product": str(r.product_id),
                    "quantity": int(r.quantity) if r.quantity is not None else 0,
                    "price": float(r.price) if r.price is not None else 0.0,
                }
            )
        return items

    def _row_to_doc(self, r, items: List[Dict]) -> Dict:
        return {
            "_id": str(r.id),
            "orderNumber": r.order_number,
            "user": str(r.user_id),
            "items": items,
            "subtotal": float(r.subtotal) if r.subtotal is not None else 0.0,
            "tax": float(r.tax) if r.tax is not None else 0.0,
            "shipping": float(r.shipping) if r.shipping is not None else 0.0,
            "discount": float(r.discount) if r.discount is not None else 0.0,
            "total": float(r.total) if r.total is not None else 0.0,
            "orderType": r.order_type,
            "status": r.status,
            "paymentStatus": r.payment_status,
            "paymentMethod": r.payment_method,
            "upiPaymentScreenshot": json_loads(r.upi_payment_screenshot)
            if r.upi_payment_screenshot
            else r.upi_payment_screenshot,
            "shippingAddress": {
                "name": r.ship_name,
                "phone": r.ship_phone,
                "street": r.ship_street,
                "city": r.ship_city,
                "state": r.ship_state,
                "pincode": r.ship_pincode,
            },
            "billingAddress": {
                "name": r.bill_name,
                "phone": r.bill_phone,
                "street": r.bill_street,
                "city": r.bill_city,
                "state": r.bill_state,
                "pincode": r.bill_pincode,
            },
            "notes": r.notes or "",
            "printedBill": bool(r.printed_bill) if r.printed_bill is not None else False,
            "assignedValet": r.assigned_valet,
            "shippedAt": r.shipped_at.isoformat() if r.shipped_at else None,
            "deliveredAt": r.delivered_at.isoformat() if r.delivered_at else None,
            "codPaymentReceived": bool(r.cod_payment_received) if r.cod_payment_received is not None else False,
            "codPaymentReceivedAt": r.cod_payment_received_at.isoformat() if r.cod_payment_received_at else None,
            "declineReason": r.decline_reason,
            "cancelledAt": r.cancelled_at.isoformat() if r.cancelled_at else None,
            "cancelledBy": r.cancelled_by,
            "turnaroundHours": float(r.turnaround_hours) if r.turnaround_hours is not None else None,
            "createdAt": r.created_at.isoformat() if r.created_at else None,
            "updatedAt": r.updated_at.isoformat() if r.updated_at else None,
        }

    def _build_query_conditions(self, query: Optional[Dict]) -> tuple[str, Dict]:
        where_clauses = []
        params = {}

        if query:
            for k, v in query.items():
                if k in ("_id", "id"):
                    where_clauses.append("id = :id")
                    params["id"] = int(v) if str(v).isdigit() else 0
                elif k == "user":
                    where_clauses.append("user_id = :user_id")
                    params["user_id"] = int(v) if str(v).isdigit() else 0
                elif k == "status":
                    where_clauses.append("status = :status")
                    params["status"] = v
                elif k == "orderType":
                    where_clauses.append("order_type = :orderType")
                    params["orderType"] = v
                elif k == "paymentMethod":
                    where_clauses.append("payment_method = :paymentMethod")
                    params["paymentMethod"] = v
                elif k == "startDate":
                    dt = _to_ts(v)
                    if dt:
                        where_clauses.append("created_at >= :startDate")
                        params["startDate"] = dt
                elif k == "endDate":
                    dt = _to_ts(v)
                    if dt:
                        where_clauses.append("created_at <= :endDate")
                        params["endDate"] = dt
                elif k == "orderNumber_prefix":
                    if v:
                        where_clauses.append("order_number LIKE :order_prefix")
                        params["order_prefix"] = f"{v}%"

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        return where_sql, params

    async def findAll(
        self, query: Optional[Dict] = None, skip: Optional[int] = None, limit: Optional[int] = None
    ) -> List[Dict]:
        factory = self._factory()
        if not factory:
            return []

        where_sql, params = self._build_query_conditions(query)

        pagination_sql = ""
        if skip is not None and limit is not None:
            # Oracle: pagination_sql = "OFFSET :skip ROWS FETCH NEXT :limit ROWS ONLY"
            # MySQL syntax for pagination
            pagination_sql = "LIMIT :limit OFFSET :skip"
            params["skip"] = skip
            params["limit"] = limit

        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id, external_id, user_id, order_number, status, total, subtotal, tax, shipping, discount,
                           order_type, payment_status, payment_method, upi_payment_screenshot,
                           ship_name, ship_street, ship_city, ship_state, ship_pincode, ship_phone, bill_name, bill_street, bill_city, bill_state, bill_pincode, bill_phone, notes, printed_bill, assigned_valet,
                           shipped_at, delivered_at, cod_payment_received, cod_payment_received_at,
                           decline_reason, cancelled_at, cancelled_by, turnaround_hours,
                           created_at, updated_at
                    FROM {self.TABLE}
                    WHERE {where_sql}
                    ORDER BY created_at DESC
                    {pagination_sql}
                    """
                ),
                params,
            )
            rows = result.fetchall()
            if not rows:
                return []

            # Bulk load items to avoid N+1 problem
            order_ids = [int(r.id) for r in rows]
            # Handle MySQL IN limit
            items_map: Dict[int, List[Dict]] = {oid: [] for oid in order_ids}
            chunks = [order_ids[i : i + 999] for i in range(0, len(order_ids), 999)]

            for chunk in chunks:
                chunk_params = {f"oid_{i}": oid for i, oid in enumerate(chunk)}
                placeholders = ", ".join([f":{k}" for k in chunk_params.keys()])
                items_result = await session.execute(
                    text(
                        f"""
                        SELECT order_id, product_id, quantity, price
                        FROM {self.ITEMS_TABLE}
                        WHERE order_id IN ({placeholders})
                        """
                    ),
                    chunk_params,
                )
                for ir in items_result.fetchall():
                    items_map[ir.order_id].append(
                        {
                            "product": str(ir.product_id),
                            "quantity": int(ir.quantity) if ir.quantity is not None else 0,
                            "price": float(ir.price) if ir.price is not None else 0.0,
                        }
                    )

            return [self._row_to_doc(r, items_map[int(r.id)]) for r in rows]

    async def findOne(self, query: Dict) -> Optional[Dict]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        factory = self._factory()
        if not factory:
            return None
        oid = int(id) if str(id).isdigit() else 0
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id, external_id, user_id, order_number, status, total, subtotal, tax, shipping, discount,
                           order_type, payment_status, payment_method, upi_payment_screenshot,
                           ship_name, ship_street, ship_city, ship_state, ship_pincode, ship_phone, bill_name, bill_street, bill_city, bill_state, bill_pincode, bill_phone, notes, printed_bill, assigned_valet,
                           shipped_at, delivered_at, cod_payment_received, cod_payment_received_at,
                           decline_reason, cancelled_at, cancelled_by, turnaround_hours,
                           created_at, updated_at
                    FROM {self.TABLE}
                    WHERE id = :id
                    """
                ),
                {"id": oid},
            )
            row = result.fetchone()
            if not row:
                return None
            items = await self._load_items(session, oid)
        return self._row_to_doc(row, items)

    async def _replace_items(self, session, order_id: int, items: List[Dict]) -> None:
        await session.execute(
            text(f"DELETE FROM {self.ITEMS_TABLE} WHERE order_id = :order_id"),
            {"order_id": order_id},
        )
        for it in items or []:
            pid_raw = it.get("product")
            pid = int(pid_raw) if str(pid_raw).isdigit() else None
            if pid is None:
                continue
            qty = it.get("quantity", 0) or 0
            price = it.get("price", 0) or 0
            await session.execute(
                text(
                    f"""
                    INSERT INTO {self.ITEMS_TABLE} (order_id, product_id, quantity, price)
                    VALUES (:order_id, :product_id, :quantity, :price)
                    """
                ),
                {"order_id": order_id, "product_id": pid, "quantity": qty, "price": price},
            )

    async def create(self, data: Dict) -> Dict:
        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        now = now_utc()
        external_id = secrets.token_hex(16)
        user_id = int(data.get("user")) if str(data.get("user", "")).isdigit() else None
        if user_id is None:
            raise ValueError("Order user must be numeric id when using MySQL")

        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    INSERT INTO {self.TABLE} (
                        external_id, user_id, order_number, status, total, subtotal, tax, shipping, discount,
                        order_type, payment_status, payment_method, upi_payment_screenshot,
                        ship_name, ship_street, ship_city, ship_state, ship_pincode, ship_phone, bill_name, bill_street, bill_city, bill_state, bill_pincode, bill_phone, notes, printed_bill, assigned_valet,
                        shipped_at, delivered_at, cod_payment_received, cod_payment_received_at,
                        decline_reason, cancelled_at, cancelled_by, turnaround_hours,
                        created_at, updated_at
                    ) VALUES (
                        :external_id, :user_id, :order_number, :status, :total, :subtotal, :tax, :shipping, :discount,
                        :order_type, :payment_status, :payment_method, :upi_payment_screenshot,
                        :ship_name, :ship_street, :ship_city, :ship_state, :ship_pincode, :ship_phone, :bill_name, :bill_street, :bill_city, :bill_state, :bill_pincode, :bill_phone, :notes, :printed_bill, :assigned_valet,
                        :shipped_at, :delivered_at, :cod_payment_received, :cod_payment_received_at,
                        :decline_reason, :cancelled_at, :cancelled_by, :turnaround_hours,
                        :created_at, :updated_at
                    )
                    """
                ),
                {
                    "external_id": external_id,
                    "user_id": user_id,
                    "order_number": data.get("orderNumber"),
                    "status": data.get("status"),
                    "total": data.get("total", 0),
                    "subtotal": data.get("subtotal", 0),
                    "tax": data.get("tax", 0),
                    "shipping": data.get("shipping", 0),
                    "discount": data.get("discount", 0),
                    "order_type": data.get("orderType"),
                    "payment_status": data.get("paymentStatus"),
                    "payment_method": data.get("paymentMethod"),
                    "upi_payment_screenshot": json_dumps(data.get("upiPaymentScreenshot"))
                    if isinstance(data.get("upiPaymentScreenshot"), (dict, list))
                    else data.get("upiPaymentScreenshot"),
                    "ship_name": (data.get("shippingAddress") or {}).get("name"),
                    "ship_street": (data.get("shippingAddress") or {}).get("street"),
                    "ship_city": (data.get("shippingAddress") or {}).get("city"),
                    "ship_state": (data.get("shippingAddress") or {}).get("state"),
                    "ship_pincode": (data.get("shippingAddress") or {}).get("pincode"),
                    "ship_phone": (data.get("shippingAddress") or {}).get("phone"),
                    "bill_name": (data.get("billingAddress") or {}).get("name"),
                    "bill_street": (data.get("billingAddress") or {}).get("street"),
                    "bill_city": (data.get("billingAddress") or {}).get("city"),
                    "bill_state": (data.get("billingAddress") or {}).get("state"),
                    "bill_pincode": (data.get("billingAddress") or {}).get("pincode"),
                    "bill_phone": (data.get("billingAddress") or {}).get("phone"),
                    "notes": data.get("notes"),
                    "printed_bill": 1 if data.get("printedBill") else 0,
                    "assigned_valet": data.get("assignedValet"),
                    "shipped_at": _to_ts(data.get("shippedAt")),
                    "delivered_at": _to_ts(data.get("deliveredAt")),
                    "cod_payment_received": 1 if data.get("codPaymentReceived") else 0,
                    "cod_payment_received_at": _to_ts(data.get("codPaymentReceivedAt")),
                    "decline_reason": data.get("declineReason"),
                    "cancelled_at": _to_ts(data.get("cancelledAt")),
                    "cancelled_by": data.get("cancelledBy"),
                    "turnaround_hours": data.get("turnaroundHours"),
                    "created_at": _to_ts(data.get("createdAt")) or now,
                    "updated_at": now,
                },
            )
            r = await session.execute(
                text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"),
                {"eid": external_id},
            )
            new_id = int(r.scalar() or 0)
            await self._replace_items(session, new_id, data.get("items") or [])
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: Dict) -> Optional[Dict]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = {**existing, **update_data}
        factory = self._factory()
        if not factory:
            return None
        now = now_utc()
        oid = int(id) if str(id).isdigit() else 0
        user_id = int(merged.get("user")) if str(merged.get("user", "")).isdigit() else None
        if user_id is None:
            return None

        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    UPDATE {self.TABLE} SET
                        user_id = :user_id,
                        order_number = :order_number,
                        status = :status,
                        total = :total,
                        subtotal = :subtotal,
                        tax = :tax,
                        shipping = :shipping,
                        discount = :discount,
                        order_type = :order_type,
                        payment_status = :payment_status,
                        payment_method = :payment_method,
                        upi_payment_screenshot = :upi_payment_screenshot,
                        ship_name = :ship_name, ship_street = :ship_street, ship_city = :ship_city, ship_state = :ship_state, ship_pincode = :ship_pincode, ship_phone = :ship_phone,
                        bill_name = :bill_name, bill_street = :bill_street, bill_city = :bill_city, bill_state = :bill_state, bill_pincode = :bill_pincode, bill_phone = :bill_phone,
                        notes = :notes,
                        printed_bill = :printed_bill,
                        assigned_valet = :assigned_valet,
                        shipped_at = :shipped_at,
                        delivered_at = :delivered_at,
                        cod_payment_received = :cod_payment_received,
                        cod_payment_received_at = :cod_payment_received_at,
                        decline_reason = :decline_reason,
                        cancelled_at = :cancelled_at,
                        cancelled_by = :cancelled_by,
                        turnaround_hours = :turnaround_hours,
                        updated_at = :updated_at
                    WHERE id = :id
                    """
                ),
                {
                    "id": oid,
                    "user_id": user_id,
                    "order_number": merged.get("orderNumber"),
                    "status": merged.get("status"),
                    "total": merged.get("total", 0),
                    "subtotal": merged.get("subtotal", 0),
                    "tax": merged.get("tax", 0),
                    "shipping": merged.get("shipping", 0),
                    "discount": merged.get("discount", 0),
                    "order_type": merged.get("orderType"),
                    "payment_status": merged.get("paymentStatus"),
                    "payment_method": merged.get("paymentMethod"),
                    "upi_payment_screenshot": json_dumps(merged.get("upiPaymentScreenshot"))
                    if isinstance(merged.get("upiPaymentScreenshot"), (dict, list))
                    else merged.get("upiPaymentScreenshot"),
                    "ship_name": (merged.get("shippingAddress") or {}).get("name"),
                    "ship_street": (merged.get("shippingAddress") or {}).get("street"),
                    "ship_city": (merged.get("shippingAddress") or {}).get("city"),
                    "ship_state": (merged.get("shippingAddress") or {}).get("state"),
                    "ship_pincode": (merged.get("shippingAddress") or {}).get("pincode"),
                    "ship_phone": (merged.get("shippingAddress") or {}).get("phone"),
                    "bill_name": (merged.get("billingAddress") or {}).get("name"),
                    "bill_street": (merged.get("billingAddress") or {}).get("street"),
                    "bill_city": (merged.get("billingAddress") or {}).get("city"),
                    "bill_state": (merged.get("billingAddress") or {}).get("state"),
                    "bill_pincode": (merged.get("billingAddress") or {}).get("pincode"),
                    "bill_phone": (merged.get("billingAddress") or {}).get("phone"),
                    "notes": merged.get("notes"),
                    "printed_bill": 1 if merged.get("printedBill") else 0,
                    "assigned_valet": merged.get("assignedValet"),
                    "shipped_at": _to_ts(merged.get("shippedAt")),
                    "delivered_at": _to_ts(merged.get("deliveredAt")),
                    "cod_payment_received": 1 if merged.get("codPaymentReceived") else 0,
                    "cod_payment_received_at": _to_ts(merged.get("codPaymentReceivedAt")),
                    "decline_reason": merged.get("declineReason"),
                    "cancelled_at": _to_ts(merged.get("cancelledAt")),
                    "cancelled_by": merged.get("cancelledBy"),
                    "turnaround_hours": merged.get("turnaroundHours"),
                    "updated_at": now,
                },
            )
            if "items" in update_data:
                await self._replace_items(session, oid, update_data.get("items") or [])
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        oid = int(id) if str(id).isdigit() else 0
        async with factory() as session:
            # order_items has ON DELETE CASCADE, but delete explicitly is fine too
            await session.execute(
                text(f"DELETE FROM {self.ITEMS_TABLE} WHERE order_id = :order_id"),
                {"order_id": oid},
            )
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": oid},
            )
            await session.commit()
            return result.rowcount > 0

    async def get_max_order_number_suffix(self, prefix: str) -> int:
        factory = self._factory()
        if not factory:
            return 0
        prefix_like = prefix + "%"
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    -- Oracle: SELECT IFNULL(MAX(TO_NUMBER(REGEXP_SUBSTR(order_number, '[0-9]+$'))), 0)
                    -- MySQL:  CAST(... AS UNSIGNED) replaces TO_NUMBER
                    SELECT IFNULL(MAX(CAST(REGEXP_SUBSTR(order_number, '[0-9]+$') AS UNSIGNED)), 0)
                    FROM {self.TABLE}
                    WHERE order_number LIKE :prefix_like
                    """
                ),
                {"prefix_like": prefix_like},
            )
            return int(result.scalar() or 0)

    async def deleteMany(self, query: Dict) -> Dict:
        docs = await self.findAll(query)
        deleted = 0
        for d in docs:
            if await self.delete(d.get("_id")):
                deleted += 1
        return {"deletedCount": deleted}

    async def count(self, query: Optional[Dict] = None) -> int:
        factory = self._factory()
        if not factory:
            return 0
        where_sql, params = self._build_query_conditions(query)
        async with factory() as session:
            result = await session.execute(text(f"SELECT COUNT(*) FROM {self.TABLE} WHERE {where_sql}"), params)
            return int(result.scalar() or 0)

    find_all = findAll
    find_by_id = findById
    find_one = findOne
