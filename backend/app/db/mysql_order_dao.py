from app.models.schemas import ItemSnippet, ValetDeclineHistoryEntry
from typing import Any
import logging
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
    except Exception as e:
        logging.warning("mysql_order_dao._to_ts: could not parse timestamp %r: %s", value, e, exc_info=e)
        return None


class MySQLOrderDAO:
    @property
    def TABLE(self):
        return "sj_orders"

    @property
    def ITEMS_TABLE(self):
        return "sj_order_items"

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
        order = Order.model_validate(r)
        order.items = [ItemSnippet.model_validate(i) for i in items]
        order.valet_decline_history = [ValetDeclineHistoryEntry.model_validate(d) for d in declines]
        return order

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
                elif k == "order_type":
                    where_clauses.append("order_type = :order_type")
                    params["order_type"] = v
                elif k == "payment_method":
                    where_clauses.append("payment_method = :payment_method")
                    params["payment_method"] = v
                elif k == "start_date":
                    dt = _to_ts(v)
                    if dt:
                        where_clauses.append("created_at >= :start_date")
                        params["start_date"] = dt
                elif k == "end_date":
                    dt = _to_ts(v)
                    if dt:
                        where_clauses.append("created_at <= :end_date")
                        params["end_date"] = dt
                elif k == "order_number_prefix":
                    if v:
                        where_clauses.append("order_number LIKE :order_prefix")
                        params["order_prefix"] = f"{v}%"
                elif k == "idempotencyKey":
                    where_clauses.append("idempotency_key = :idempotency_key")
                    params["idempotency_key"] = v

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
                           ship_name, ship_street, ship_city, ship_state, ship_pincode, ship_phone, ship_address, ship_district, ship_country, ship_google_location, ship_latitude, ship_longitude, bill_name, bill_street, bill_city, bill_state, bill_pincode, bill_phone, bill_address, bill_district, bill_country, bill_google_location, bill_latitude, bill_longitude, notes, printed_bill, assigned_valet, pending_valet_id, valet_assigned_at, valet_cascade_count, is_urgent_delivery,
                           shipped_at, delivered_at, cod_payment_received, cod_payment_received_at,
                           decline_reason, cancelled_at, cancelled_by, turnaround_hours,
                           idempotency_key,
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
                           ship_name, ship_street, ship_city, ship_state, ship_pincode, ship_phone, ship_address, ship_district, ship_country, ship_google_location, ship_latitude, ship_longitude, bill_name, bill_street, bill_city, bill_state, bill_pincode, bill_phone, bill_address, bill_district, bill_country, bill_google_location, bill_latitude, bill_longitude, notes, printed_bill, assigned_valet, pending_valet_id, valet_assigned_at, valet_cascade_count, is_urgent_delivery,
                           shipped_at, delivered_at, cod_payment_received, cod_payment_received_at,
                           decline_reason, cancelled_at, cancelled_by, turnaround_hours,
                           idempotency_key,
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
            pid_raw = getattr(it, "productId", None) or getattr(it, "product", None)
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
                {"order_id": order_id, "vid": str((d.valet_id if d.valet_id is not None else "")), "r": d.reason}
            )

    async def ensure_idempotency_index(self) -> None:
        """Idempotently add the idempotency_key column + unique index to sj_orders.

        Called once at application startup (from order_service or startup.py).
        Safe to call from all 4 workers simultaneously — each statement is a
        no-op if the column / index already exists.
        """
        factory = self._factory()
        if not factory:
            return
        async with factory() as session:
            # Add the column if it doesn't exist yet
            await session.execute(
                text(
                    "ALTER TABLE sj_orders "
                    "ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(128) NULL DEFAULT NULL"
                )
            )
            # Add the unique index if it doesn't exist yet.
            # MySQL 8.0+ supports CREATE INDEX IF NOT EXISTS; for older versions
            # we swallow the duplicate-key-name error silently.
            try:
                await session.execute(
                    text(
                        "CREATE UNIQUE INDEX IF NOT EXISTS uq_orders_user_idempotency "
                        "ON sj_orders (user_id, idempotency_key)"
                    )
                )
            except Exception:
                # Index already exists — nothing to do
                pass
            await session.commit()

    async def create_idempotent(self, data: 'OrderInternalCreate') -> tuple['Order', bool]:
        """Insert an order, using the DB unique index on (user_id, idempotency_key)
        to eliminate the TOCTOU race in the application-layer check.

        Returns (order, created) where created=False means the row already
        existed (a concurrent request won the race) and the existing order is
        returned.  Callers must skip all post-creation side-effects when
        created=False.

        Falls back to plain create() when idempotency_key is None/empty.
        """
        if not data.idempotency_key:
            return await self.create(data), True

        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        now = now_utc()
        external_id = secrets.token_hex(16)
        user_val = str(data.user) if data.user is not None else ""
        if user_val and not user_val.isdigit():
            user_id_subquery = "(SELECT id FROM sj_users WHERE external_id = :uid)"
            uid_param = user_val
        else:
            user_id_subquery = ":uid"
            uid_param = int(user_val) if user_val else None

        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    INSERT IGNORE INTO {self.TABLE} (
                        external_id, user_id, order_number, status, total, subtotal, tax, shipping, discount,
                        order_type, payment_status, payment_method, upi_payment_screenshot,
                        ship_name, ship_street, ship_city, ship_state, ship_pincode, ship_phone, ship_address, ship_district, ship_country, ship_google_location, ship_latitude, ship_longitude, bill_name, bill_street, bill_city, bill_state, bill_pincode, bill_phone, bill_address, bill_district, bill_country, bill_google_location, bill_latitude, bill_longitude, notes, printed_bill, assigned_valet, pending_valet_id, valet_assigned_at, valet_cascade_count, is_urgent_delivery,
                        shipped_at, delivered_at, cod_payment_received, cod_payment_received_at,
                        decline_reason, cancelled_at, cancelled_by, turnaround_hours,
                        idempotency_key,
                        created_at, updated_at
                    ) VALUES (
                        :external_id, {user_id_subquery}, :order_number, :status, :total, :subtotal, :tax, :shipping, :discount,
                        :order_type, :payment_status, :payment_method, :upi_payment_screenshot,
                        :ship_name, :ship_street, :ship_city, :ship_state, :ship_pincode, :ship_phone, :ship_address, :ship_district, :ship_country, :ship_google_location, :ship_latitude, :ship_longitude, :bill_name, :bill_street, :bill_city, :bill_state, :bill_pincode, :bill_phone, :bill_address, :bill_district, :bill_country, :bill_google_location, :bill_latitude, :bill_longitude, :notes, :printed_bill, :assigned_valet, :pending_valet_id, :valet_assigned_at, :valet_cascade_count, :is_urgent_delivery,
                        :shipped_at, :delivered_at, :cod_payment_received, :cod_payment_received_at,
                        :decline_reason, :cancelled_at, :cancelled_by, :turnaround_hours,
                        :idempotency_key,
                        :created_at, :updated_at
                    )
                    """
                ),
                {
                    "external_id": external_id,
                    "uid": uid_param,
                    "order_number": data.order_number,
                    "status": data.status,
                    "total": (data.total if data.total is not None else 0),
                    "subtotal": (data.subtotal if data.subtotal is not None else 0),
                    "tax": (data.tax if data.tax is not None else 0),
                    "shipping": (data.shipping if data.shipping is not None else 0),
                    "discount": (data.discount if data.discount is not None else 0),
                    "order_type": data.order_type,
                    "payment_status": data.payment_status,
                    "payment_method": data.payment_method,
                    "upi_payment_screenshot": data.upi_payment_screenshot,
                    "ship_name": data.ship_name,
                    "ship_street": data.ship_street,
                    "ship_city": data.ship_city,
                    "ship_state": data.ship_state,
                    "ship_pincode": data.ship_pincode,
                    "ship_phone": data.ship_phone,
                    "ship_address": getattr(data, "ship_address", None),
                    "ship_district": getattr(data, "ship_district", None),
                    "ship_country": getattr(data, "ship_country", None),
                    "ship_google_location": getattr(data, "ship_google_location", None),
                    "ship_latitude": getattr(data, "ship_latitude", None),
                    "ship_longitude": getattr(data, "ship_longitude", None),
                    "bill_name": data.bill_name,
                    "bill_street": data.bill_street,
                    "bill_city": data.bill_city,
                    "bill_state": data.bill_state,
                    "bill_pincode": data.bill_pincode,
                    "bill_phone": data.bill_phone,
                    "bill_address": getattr(data, "bill_address", None),
                    "bill_district": getattr(data, "bill_district", None),
                    "bill_country": getattr(data, "bill_country", None),
                    "bill_google_location": getattr(data, "bill_google_location", None),
                    "bill_latitude": getattr(data, "bill_latitude", None),
                    "bill_longitude": getattr(data, "bill_longitude", None),
                    "notes": data.notes,
                    "printed_bill": 1 if data.printed_bill else 0,
                    "assigned_valet": data.assigned_valet,
                    "is_urgent_delivery": 1 if data.is_urgent_delivery else 0,
                    "pending_valet_id": data.pending_valet_id,
                    "valet_assigned_at": _to_ts(data.valet_assigned_at),
                    "valet_cascade_count": data.valet_cascade_count or 0,
                    "shipped_at": _to_ts(data.shipped_at),
                    "delivered_at": _to_ts(data.delivered_at),
                    "cod_payment_received": 1 if data.cod_payment_received else 0,
                    "cod_payment_received_at": _to_ts(data.cod_payment_received_at),
                    "decline_reason": data.decline_reason,
                    "cancelled_at": _to_ts(data.cancelled_at),
                    "cancelled_by": data.cancelled_by,
                    "turnaround_hours": data.turnaround_hours,
                    "idempotency_key": data.idempotency_key,
                    "created_at": _to_ts(data.created_at) or now,
                    "updated_at": now,
                },
            )
            created = result.rowcount > 0

            if created:
                # Our INSERT won — wire up children and commit
                r = await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"),
                    {"eid": external_id},
                )
                new_id = int(r.scalar() or 0)
                await self._replace_children(session, new_id, data.items or [], data.valet_decline_history or [])
                await session.commit()
                return await self.findById(str(new_id)), True
            else:
                # Another request already inserted this idempotency key — fetch it
                await session.rollback()
                existing = await self.findOne(
                    {"user": str(uid_param), "idempotencyKey": data.idempotency_key}
                )
                return existing, False


        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        now = now_utc()
        external_id = secrets.token_hex(16)
        user_val = str(data.user) if data.user is not None else ""
        if user_val and not user_val.isdigit():
            user_id_subquery = f"(SELECT id FROM sj_users WHERE external_id = :uid)"
            uid_param = user_val
        else:
            user_id_subquery = ":uid"
            uid_param = int(user_val) if user_val else None

        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    INSERT INTO {self.TABLE} (
                        external_id, user_id, order_number, status, total, subtotal, tax, shipping, discount,
                        order_type, payment_status, payment_method, upi_payment_screenshot,
                        ship_name, ship_street, ship_city, ship_state, ship_pincode, ship_phone, ship_address, ship_district, ship_country, ship_google_location, ship_latitude, ship_longitude, bill_name, bill_street, bill_city, bill_state, bill_pincode, bill_phone, bill_address, bill_district, bill_country, bill_google_location, bill_latitude, bill_longitude, notes, printed_bill, assigned_valet, pending_valet_id, valet_assigned_at, valet_cascade_count, is_urgent_delivery,
                        shipped_at, delivered_at, cod_payment_received, cod_payment_received_at,
                        decline_reason, cancelled_at, cancelled_by, turnaround_hours,
                        idempotency_key,
                        created_at, updated_at
                    ) VALUES (
                        :external_id, {user_id_subquery}, :order_number, :status, :total, :subtotal, :tax, :shipping, :discount,
                        :order_type, :payment_status, :payment_method, :upi_payment_screenshot,
                        :ship_name, :ship_street, :ship_city, :ship_state, :ship_pincode, :ship_phone, :ship_address, :ship_district, :ship_country, :ship_google_location, :ship_latitude, :ship_longitude, :bill_name, :bill_street, :bill_city, :bill_state, :bill_pincode, :bill_phone, :bill_address, :bill_district, :bill_country, :bill_google_location, :bill_latitude, :bill_longitude, :notes, :printed_bill, :assigned_valet, :pending_valet_id, :valet_assigned_at, :valet_cascade_count, :is_urgent_delivery,
                        :shipped_at, :delivered_at, :cod_payment_received, :cod_payment_received_at,
                        :decline_reason, :cancelled_at, :cancelled_by, :turnaround_hours,
                        :idempotency_key,
                        :created_at, :updated_at
                    )
                    """
                ),
                {
                    "external_id": external_id,
                    "uid": uid_param,
                    "order_number": data.order_number,
                    "status": data.status,
                    "total": (data.total if data.total is not None else 0),
                    "subtotal": (data.subtotal if data.subtotal is not None else 0),
                    "tax": (data.tax if data.tax is not None else 0),
                    "shipping": (data.shipping if data.shipping is not None else 0),
                    "discount": (data.discount if data.discount is not None else 0),
                    "order_type": data.order_type,
                    "payment_status": data.payment_status,
                    "payment_method": data.payment_method,
                    "upi_payment_screenshot": data.upi_payment_screenshot,
                    "ship_name": data.ship_name,
                    "ship_street": data.ship_street,
                    "ship_city": data.ship_city,
                    "ship_state": data.ship_state,
                    "ship_pincode": data.ship_pincode,
                    "ship_phone": data.ship_phone,
                    "ship_address": getattr(data, "ship_address", None),
                    "ship_district": getattr(data, "ship_district", None),
                    "ship_country": getattr(data, "ship_country", None),
                    "ship_google_location": getattr(data, "ship_google_location", None),
                    "ship_latitude": getattr(data, "ship_latitude", None),
                    "ship_longitude": getattr(data, "ship_longitude", None),
                    "bill_name": data.bill_name,
                    "bill_street": data.bill_street,
                    "bill_city": data.bill_city,
                    "bill_state": data.bill_state,
                    "bill_pincode": data.bill_pincode,
                    "bill_phone": data.bill_phone,
                    "bill_address": getattr(data, "bill_address", None),
                    "bill_district": getattr(data, "bill_district", None),
                    "bill_country": getattr(data, "bill_country", None),
                    "bill_google_location": getattr(data, "bill_google_location", None),
                    "bill_latitude": getattr(data, "bill_latitude", None),
                    "bill_longitude": getattr(data, "bill_longitude", None),
                    "notes": data.notes,
                    "printed_bill": 1 if data.printed_bill else 0,
                    "assigned_valet": data.assigned_valet,
                    "is_urgent_delivery": 1 if data.is_urgent_delivery else 0,
                    "pending_valet_id": data.pending_valet_id,
                    "valet_assigned_at": _to_ts(data.valet_assigned_at),
                    "valet_cascade_count": data.valet_cascade_count or 0,
                    "shipped_at": _to_ts(data.shipped_at),
                    "delivered_at": _to_ts(data.delivered_at),
                    "cod_payment_received": 1 if data.cod_payment_received else 0,
                    "cod_payment_received_at": _to_ts(data.cod_payment_received_at),
                    "decline_reason": data.decline_reason,
                    "cancelled_at": _to_ts(data.cancelled_at),
                    "cancelled_by": data.cancelled_by,
                    "turnaround_hours": data.turnaround_hours,
                    "idempotency_key": getattr(data, "idempotency_key", None),
                    "created_at": _to_ts(data.created_at) or now,
                    "updated_at": now,
                },
            )
            r = await session.execute(
                text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"),
                {"eid": external_id},
            )
            new_id = int(r.scalar() or 0)
            await self._replace_children(session, new_id, data.items or [], data.valet_decline_history or [])
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: 'OrderInternalUpdate') -> Optional[Order]:
        existing = await self.findById(id)
        if not existing:
            return None
        factory = self._factory()
        if not factory:
            return None
        now = now_utc()
        oid = int(id) if str(id).isdigit() else None
        raw_user_id = update_data.user if update_data.user is not None else existing.user
        user_val = str(raw_user_id) if raw_user_id is not None else ""
        if user_val and not user_val.isdigit():
            user_id_subquery = f"(SELECT id FROM sj_users WHERE external_id = :uid)"
            uid_param = user_val
        else:
            user_id_subquery = ":uid"
            uid_param = int(user_val) if user_val else None

        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    UPDATE {self.TABLE} SET
                        user_id = {user_id_subquery},
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
                        ship_name = :ship_name, ship_street = :ship_street, ship_city = :ship_city, ship_state = :ship_state, ship_pincode = :ship_pincode, ship_phone = :ship_phone, ship_address = :ship_address, ship_district = :ship_district, ship_country = :ship_country, ship_google_location = :ship_google_location, ship_latitude = :ship_latitude, ship_longitude = :ship_longitude,
                        bill_name = :bill_name, bill_street = :bill_street, bill_city = :bill_city, bill_state = :bill_state, bill_pincode = :bill_pincode, bill_phone = :bill_phone, bill_address = :bill_address, bill_district = :bill_district, bill_country = :bill_country, bill_google_location = :bill_google_location, bill_latitude = :bill_latitude, bill_longitude = :bill_longitude,
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
                    "uid": uid_param,
                    "order_number": update_data.order_number if update_data.order_number is not None else existing.order_number,
                    "status": update_data.status if update_data.status is not None else existing.status,
                    "total": (update_data.total if update_data.total is not None else (existing.total if existing.total is not None else 0)),
                    "subtotal": (update_data.subtotal if update_data.subtotal is not None else (existing.subtotal if existing.subtotal is not None else 0)),
                    "tax": (update_data.tax if update_data.tax is not None else (existing.tax if existing.tax is not None else 0)),
                    "shipping": (update_data.shipping if update_data.shipping is not None else (existing.shipping if existing.shipping is not None else 0)),
                    "discount": (update_data.discount if update_data.discount is not None else (existing.discount if existing.discount is not None else 0)),
                    "order_type": update_data.order_type if update_data.order_type is not None else existing.order_type,
                    "payment_status": update_data.payment_status if update_data.payment_status is not None else existing.payment_status,
                    "payment_method": update_data.payment_method if update_data.payment_method is not None else existing.payment_method,
                    "upi_payment_screenshot": update_data.upi_payment_screenshot if update_data.upi_payment_screenshot is not None else existing.upi_payment_screenshot,
                    "ship_name": update_data.ship_name if getattr(update_data, "ship_name", None) is not None else existing.ship_name,
                    "ship_street": update_data.ship_street if getattr(update_data, "ship_street", None) is not None else existing.ship_street,
                    "ship_city": update_data.ship_city if getattr(update_data, "ship_city", None) is not None else existing.ship_city,
                    "ship_state": update_data.ship_state if getattr(update_data, "ship_state", None) is not None else existing.ship_state,
                    "ship_pincode": update_data.ship_pincode if getattr(update_data, "ship_pincode", None) is not None else existing.ship_pincode,
                    "ship_phone": update_data.ship_phone if getattr(update_data, "ship_phone", None) is not None else existing.ship_phone,
                    "ship_address": getattr(update_data, "ship_address", None) if getattr(update_data, "ship_address", None) is not None else getattr(existing, "ship_address", None),
                    "ship_district": getattr(update_data, "ship_district", None) if getattr(update_data, "ship_district", None) is not None else getattr(existing, "ship_district", None),
                    "ship_country": getattr(update_data, "ship_country", None) if getattr(update_data, "ship_country", None) is not None else getattr(existing, "ship_country", None),
                    "ship_google_location": getattr(update_data, "ship_google_location", None) if getattr(update_data, "ship_google_location", None) is not None else getattr(existing, "ship_google_location", None),
                    "ship_latitude": getattr(update_data, "ship_latitude", None) if getattr(update_data, "ship_latitude", None) is not None else getattr(existing, "ship_latitude", None),
                    "ship_longitude": getattr(update_data, "ship_longitude", None) if getattr(update_data, "ship_longitude", None) is not None else getattr(existing, "ship_longitude", None),
                    "bill_name": update_data.bill_name if getattr(update_data, "bill_name", None) is not None else existing.bill_name,
                    "bill_street": update_data.bill_street if getattr(update_data, "bill_street", None) is not None else existing.bill_street,
                    "bill_city": update_data.bill_city if getattr(update_data, "bill_city", None) is not None else existing.bill_city,
                    "bill_state": update_data.bill_state if getattr(update_data, "bill_state", None) is not None else existing.bill_state,
                    "bill_pincode": update_data.bill_pincode if getattr(update_data, "bill_pincode", None) is not None else existing.bill_pincode,
                    "bill_phone": update_data.bill_phone if getattr(update_data, "bill_phone", None) is not None else existing.bill_phone,
                    "bill_address": getattr(update_data, "bill_address", None) if getattr(update_data, "bill_address", None) is not None else getattr(existing, "bill_address", None),
                    "bill_district": getattr(update_data, "bill_district", None) if getattr(update_data, "bill_district", None) is not None else getattr(existing, "bill_district", None),
                    "bill_country": getattr(update_data, "bill_country", None) if getattr(update_data, "bill_country", None) is not None else getattr(existing, "bill_country", None),
                    "bill_google_location": getattr(update_data, "bill_google_location", None) if getattr(update_data, "bill_google_location", None) is not None else getattr(existing, "bill_google_location", None),
                    "bill_latitude": getattr(update_data, "bill_latitude", None) if getattr(update_data, "bill_latitude", None) is not None else getattr(existing, "bill_latitude", None),
                    "bill_longitude": getattr(update_data, "bill_longitude", None) if getattr(update_data, "bill_longitude", None) is not None else getattr(existing, "bill_longitude", None),
                    "notes": update_data.notes if update_data.notes is not None else existing.notes,
                    "printed_bill": 1 if (update_data.printed_bill if update_data.printed_bill is not None else existing.printed_bill) else 0,
                    "assigned_valet": update_data.assigned_valet if update_data.assigned_valet is not None else existing.assigned_valet,
                    "pending_valet_id": update_data.pending_valet_id if update_data.pending_valet_id is not None else existing.pending_valet_id,
                    "valet_assigned_at": _to_ts(update_data.valet_assigned_at if update_data.valet_assigned_at is not None else existing.valet_assigned_at),
                    "valet_cascade_count": update_data.valet_cascade_count if update_data.valet_cascade_count is not None else existing.valet_cascade_count or 0,
                    
                    "is_urgent_delivery": 1 if (update_data.is_urgent_delivery if update_data.is_urgent_delivery is not None else existing.is_urgent_delivery) else 0,
                    "shipped_at": _to_ts(update_data.shipped_at if update_data.shipped_at is not None else existing.shipped_at),
                    "delivered_at": _to_ts(update_data.delivered_at if update_data.delivered_at is not None else existing.delivered_at),
                    "cod_payment_received": 1 if (update_data.cod_payment_received if update_data.cod_payment_received is not None else existing.cod_payment_received) else 0,
                    "cod_payment_received_at": _to_ts(update_data.cod_payment_received_at if update_data.cod_payment_received_at is not None else existing.cod_payment_received_at),
                    "decline_reason": update_data.decline_reason if update_data.decline_reason is not None else existing.decline_reason,
                    "cancelled_at": _to_ts(update_data.cancelled_at if update_data.cancelled_at is not None else existing.cancelled_at),
                    "cancelled_by": update_data.cancelled_by if update_data.cancelled_by is not None else existing.cancelled_by,
                    "turnaround_hours": update_data.turnaround_hours if update_data.turnaround_hours is not None else existing.turnaround_hours,
                    "updated_at": now,
                },
            )
            await self._replace_children(session, oid, update_data.items if update_data.items is not None else existing.items or [], update_data.valet_decline_history if update_data.valet_decline_history is not None else existing.valet_decline_history or [])
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
        """Delete matching orders in a single statement (or batched statements) instead of N+1."""
        docs = await self.findAll(query)
        if not docs:
            return {"deletedCount": 0}
        
        ids = [int(d.id) for d in docs if str(d.id).isdigit()]
        if not ids:
            return {"deletedCount": 0}
            
        factory = self._factory()
        if not factory:
            return {"deletedCount": 0}
            
        deleted_total = 0
        chunks = [ids[i : i + 999] for i in range(0, len(ids), 999)]
        
        async with factory() as session:
            for chunk in chunks:
                id_params = {f"id_{i}": v for i, v in enumerate(chunk)}
                placeholders = ", ".join(f":{k}" for k in id_params)
                
                # Delete items first (maintains referential integrity if ON DELETE CASCADE is missing)
                await session.execute(
                    text(f"DELETE FROM {self.ITEMS_TABLE} WHERE order_id IN ({placeholders})"),
                    id_params,
                )
                # Delete orders
                result = await session.execute(
                    text(f"DELETE FROM {self.TABLE} WHERE id IN ({placeholders})"),
                    id_params,
                )
                deleted_total += result.rowcount
            await session.commit()
            
        return {"deletedCount": deleted_total}

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









