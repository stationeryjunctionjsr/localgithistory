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
from typing import Dict
from app.models.order import Order, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc


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
        suffix = (settings.table_suffix if settings.table_suffix is not None else "")
        return f"sj_orders{suffix}"

    @property
    def ITEMS_TABLE(self):
        suffix = (settings.table_suffix if settings.table_suffix is not None else "")
        return f"sj_order_items{suffix}"

    def _factory(self):
        return get_async_session_factory()

    async def _load_children(self, session, order_id: int) -> tuple[list[dict], list[dict]]:
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
        items = [{"productId": str(r.product_id), "quantity": int(r.quantity) if r.quantity is not None else 0, "price": float(r.price) if r.price is not None else 0.0} for r in result.fetchall()]

        decl_res = await session.execute(
            text("SELECT valet_id, reason FROM sj_order_valet_declines WHERE parent_id = :order_id"),
            {"order_id": order_id},
        )
        declines = [{"valetId": str(r.valet_id), "reason": r.reason} for r in decl_res.fetchall()]

        return items, declines

    def __map_to_schema(self, r, items: List[Dict], declines: List[Dict]) -> Order:
        return Order(**{
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
            "upiPaymentScreenshot": r.upi_payment_screenshot,
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
            "pendingValetId": r.pending_valet_id,
            "valetAssignedAt": r.valet_assigned_at.isoformat() + "Z" if r.valet_assigned_at else None,
            "valetCascadeCount": (r.valet_cascade_count if r.valet_cascade_count is not None else 0),
            "valetDeclineHistory": declines,
            "isUrgentDelivery": bool((r.is_urgent_delivery if r.is_urgent_delivery is not None else False)),
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
        })

    def _build_query_conditions(self, query: Optional[Dict]) -> tuple[str, Dict]:
        where_clauses = []
        params = {}

        if query:
            for k, v in query.items():
                if k in ("_id", "id"):
                    where_clauses.append("id = :id")
                    params["id"] = int(v) if str(v).isdigit() else None
                elif k == "user":
                    where_clauses.append("user_id = :user_id")
                    params["user_id"] = int(v) if str(v).isdigit() else None
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
    ) -> List[Order]:
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
                           ship_name, ship_street, ship_city, ship_state, ship_pincode, ship_phone, bill_name, bill_street, bill_city, bill_state, bill_pincode, bill_phone, notes, printed_bill, assigned_valet, pending_valet_id, valet_assigned_at, valet_cascade_count, is_urgent_delivery,
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

            declines_map: Dict[int, List[Dict]] = {oid: [] for oid in order_ids}

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
                            "productId": str(ir.product_id),
                            "quantity": int(ir.quantity) if ir.quantity is not None else 0,
                            "price": float(ir.price) if ir.price is not None else 0.0,
                        }
                    )
                
                decl_result = await session.execute(
                    text(f"SELECT parent_id, valet_id, reason FROM sj_order_valet_declines WHERE parent_id IN ({placeholders})"),
                    chunk_params,
                )
                for dr in decl_result.fetchall():
                    declines_map[dr.parent_id].append({"valetId": str(dr.valet_id), "reason": dr.reason})

            return [self.__map_to_schema(r, items_map[int(r.id)], declines_map[int(r.id)]) for r in rows]

    async def findOne(self, query: Dict) -> Optional[Order]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Order]:
        factory = self._factory()
        if not factory:
            return None
        oid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id, external_id, user_id, order_number, status, total, subtotal, tax, shipping, discount,
                           order_type, payment_status, payment_method, upi_payment_screenshot,
                           ship_name, ship_street, ship_city, ship_state, ship_pincode, ship_phone, bill_name, bill_street, bill_city, bill_state, bill_pincode, bill_phone, notes, printed_bill, assigned_valet, pending_valet_id, valet_assigned_at, valet_cascade_count, is_urgent_delivery,
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
            items, declines = await self._load_children(session, oid)
        return self.__map_to_schema(row, items, declines)

    async def _replace_children(self, session, order_id: int, items: List[Dict], declines: List[Dict]) -> None:
        await session.execute(
            text(f"DELETE FROM {self.ITEMS_TABLE} WHERE order_id = :order_id"),
            {"order_id": order_id},
        )
        for it in items or []:
            pid_raw = it.product
            pid = int(pid_raw) if str(pid_raw).isdigit() else None
            if pid is None:
                continue
            qty = (it.quantity if it.quantity is not None else 0) or 0
            price = (it.price if it.price is not None else 0) or 0
            await session.execute(
                text(
                    f"""
                    INSERT INTO {self.ITEMS_TABLE} (order_id, product_id, quantity, price)
                    VALUES (:order_id, :product_id, :quantity, :price)
                    """
                ),
                {"order_id": order_id, "product_id": pid, "quantity": qty, "price": price},
            )
            
        await session.execute(
            text("DELETE FROM sj_order_valet_declines WHERE parent_id = :order_id"),
            {"order_id": order_id},
        )
        for d in declines or []:
            await session.execute(
                text("INSERT INTO sj_order_valet_declines (parent_id, valet_id, reason) VALUES (:order_id, :vid, :r)"),
                {"order_id": order_id, "vid": str((d.valetId if d.valetId is not None else "")), "r": d.reason}
            )

    async def create(self, data: Any) -> Order:
        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        now = now_utc()
        external_id = secrets.token_hex(16)
        user_id = int(data.user) if str((data.user if data.user is not None else "")).isdigit() else None
        if user_id is None:
            raise ValueError("Order user must be numeric id when using MySQL")

        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    INSERT INTO {self.TABLE} (
                        external_id, user_id, order_number, status, total, subtotal, tax, shipping, discount,
                        order_type, payment_status, payment_method, upi_payment_screenshot,
                        ship_name, ship_street, ship_city, ship_state, ship_pincode, ship_phone, bill_name, bill_street, bill_city, bill_state, bill_pincode, bill_phone, notes, printed_bill, assigned_valet, pending_valet_id, valet_assigned_at, valet_cascade_count, is_urgent_delivery,
                        shipped_at, delivered_at, cod_payment_received, cod_payment_received_at,
                        decline_reason, cancelled_at, cancelled_by, turnaround_hours,
                        created_at, updated_at
                    ) VALUES (
                        :external_id, :user_id, :order_number, :status, :total, :subtotal, :tax, :shipping, :discount,
                        :order_type, :payment_status, :payment_method, :upi_payment_screenshot,
                        :ship_name, :ship_street, :ship_city, :ship_state, :ship_pincode, :ship_phone, :bill_name, :bill_street, :bill_city, :bill_state, :bill_pincode, :bill_phone, :notes, :printed_bill, :assigned_valet, :pending_valet_id, :valet_assigned_at, :valet_cascade_count, :is_urgent_delivery,
                                                :shipped_at, :delivered_at, :cod_payment_received, :cod_payment_received_at,
                        :decline_reason, :cancelled_at, :cancelled_by, :turnaround_hours,
                        :created_at, :updated_at
                    )
                    """
                ),
                {
                    "external_id": external_id,
                    "user_id": user_id,
                    "order_number": data.orderNumber,
                    "status": data.status,
                    "total": (data.total if data.total is not None else 0),
                    "subtotal": (data.subtotal if data.subtotal is not None else 0),
                    "tax": (data.tax if data.tax is not None else 0),
                    "shipping": (data.shipping if data.shipping is not None else 0),
                    "discount": (data.discount if data.discount is not None else 0),
                    "order_type": data.orderType,
                    "payment_status": data.paymentStatus,
                    "payment_method": data.paymentMethod,
                    "upi_payment_screenshot": data.upiPaymentScreenshot,
                    "ship_name": ((data.shippingAddress or {})["name"] if "name" in (data.shippingAddress or {}) else None),
                    "ship_street": ((data.shippingAddress or {})["street"] if "street" in (data.shippingAddress or {}) else None),
                    "ship_city": ((data.shippingAddress or {})["city"] if "city" in (data.shippingAddress or {}) else None),
                    "ship_state": ((data.shippingAddress or {})["state"] if "state" in (data.shippingAddress or {}) else None),
                    "ship_pincode": ((data.shippingAddress or {})["pincode"] if "pincode" in (data.shippingAddress or {}) else None),
                    "ship_phone": ((data.shippingAddress or {})["phone"] if "phone" in (data.shippingAddress or {}) else None),
                    "bill_name": ((data.billingAddress or {})["name"] if "name" in (data.billingAddress or {}) else None),
                    "bill_street": ((data.billingAddress or {})["street"] if "street" in (data.billingAddress or {}) else None),
                    "bill_city": ((data.billingAddress or {})["city"] if "city" in (data.billingAddress or {}) else None),
                    "bill_state": ((data.billingAddress or {})["state"] if "state" in (data.billingAddress or {}) else None),
                    "bill_pincode": ((data.billingAddress or {})["pincode"] if "pincode" in (data.billingAddress or {}) else None),
                    "bill_phone": ((data.billingAddress or {})["phone"] if "phone" in (data.billingAddress or {}) else None),
                    "notes": data.notes,
                    "printed_bill": 1 if data.printedBill else None,
                                        "assigned_valet": data.assignedValet,
                    "is_urgent_delivery": 1 if data.isUrgentDelivery else None,
                    "pending_valet_id": data.pendingValetId,
                    "valet_assigned_at": _to_ts(data.valetAssignedAt),
                    "valet_cascade_count": data.valetCascadeCount or 0,
                    
                    "shipped_at": _to_ts(data.shippedAt),
                    "delivered_at": _to_ts(data.deliveredAt),
                    "cod_payment_received": 1 if data.codPaymentReceived else None,
                    "cod_payment_received_at": _to_ts(data.codPaymentReceivedAt),
                    "decline_reason": data.declineReason,
                    "cancelled_at": _to_ts(data.cancelledAt),
                    "cancelled_by": data.cancelledBy,
                    "turnaround_hours": data.turnaroundHours,
                    "created_at": _to_ts(data.createdAt) or now,
                    "updated_at": now,
                },
            )
            r = await session.execute(
                text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"),
                {"eid": external_id},
            )
            new_id = int(r.scalar() or 0)
            await self._replace_children(session, new_id, data.items or [], data.valetDeclineHistory or [])
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: Any) -> Optional[Order]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = {**existing, **update_data}
        factory = self._factory()
        if not factory:
            return None
        now = now_utc()
        oid = int(id) if str(id).isdigit() else None
        user_id = int(update_data.user) if str((update_data.user if update_data.user is not None else "")).isdigit() else None
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
                        pending_valet_id = :pending_valet_id,
                        valet_assigned_at = :valet_assigned_at,
                        valet_cascade_count = :valet_cascade_count,
                        is_urgent_delivery = :is_urgent_delivery,
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
                    "order_number": update_data.orderNumber,
                    "status": update_data.status,
                    "total": (update_data.total if update_data.total is not None else 0),
                    "subtotal": (update_data.subtotal if update_data.subtotal is not None else 0),
                    "tax": (update_data.tax if update_data.tax is not None else 0),
                    "shipping": (update_data.shipping if update_data.shipping is not None else 0),
                    "discount": (update_data.discount if update_data.discount is not None else 0),
                    "order_type": update_data.orderType,
                    "payment_status": update_data.paymentStatus,
                    "payment_method": update_data.paymentMethod,
                    "upi_payment_screenshot": update_data.upiPaymentScreenshot,
                    "ship_name": ((update_data.shippingAddress or {})["name"] if "name" in (update_data.shippingAddress or {}) else None),
                    "ship_street": ((update_data.shippingAddress or {})["street"] if "street" in (update_data.shippingAddress or {}) else None),
                    "ship_city": ((update_data.shippingAddress or {})["city"] if "city" in (update_data.shippingAddress or {}) else None),
                    "ship_state": ((update_data.shippingAddress or {})["state"] if "state" in (update_data.shippingAddress or {}) else None),
                    "ship_pincode": ((update_data.shippingAddress or {})["pincode"] if "pincode" in (update_data.shippingAddress or {}) else None),
                    "ship_phone": ((update_data.shippingAddress or {})["phone"] if "phone" in (update_data.shippingAddress or {}) else None),
                    "bill_name": ((update_data.billingAddress or {})["name"] if "name" in (update_data.billingAddress or {}) else None),
                    "bill_street": ((update_data.billingAddress or {})["street"] if "street" in (update_data.billingAddress or {}) else None),
                    "bill_city": ((update_data.billingAddress or {})["city"] if "city" in (update_data.billingAddress or {}) else None),
                    "bill_state": ((update_data.billingAddress or {})["state"] if "state" in (update_data.billingAddress or {}) else None),
                    "bill_pincode": ((update_data.billingAddress or {})["pincode"] if "pincode" in (update_data.billingAddress or {}) else None),
                    "bill_phone": ((update_data.billingAddress or {})["phone"] if "phone" in (update_data.billingAddress or {}) else None),
                    "notes": update_data.notes,
                    "printed_bill": 1 if update_data.printedBill else None,
                    "assigned_valet": update_data.assignedValet,
                    "pending_valet_id": update_data.pendingValetId,
                    "valet_assigned_at": _to_ts(update_data.valetAssignedAt),
                    "valet_cascade_count": update_data.valetCascadeCount or 0,
                    
                    "is_urgent_delivery": 1 if update_data.isUrgentDelivery else None,
                    "shipped_at": _to_ts(update_data.shippedAt),
                    "delivered_at": _to_ts(update_data.deliveredAt),
                    "cod_payment_received": 1 if update_data.codPaymentReceived else None,
                    "cod_payment_received_at": _to_ts(update_data.codPaymentReceivedAt),
                    "decline_reason": update_data.declineReason,
                    "cancelled_at": _to_ts(update_data.cancelledAt),
                    "cancelled_by": update_data.cancelledBy,
                    "turnaround_hours": update_data.turnaroundHours,
                    "updated_at": now,
                },
            )
            await self._replace_children(session, oid, update_data.items or [], update_data.valetDeclineHistory or [])
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        oid = int(id) if str(id).isdigit() else None
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
            if await self.delete(d._id):
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







