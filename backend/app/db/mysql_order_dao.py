from app.models.schemas import ItemSnippet, ValetDeclineHistoryEntry
from app.models.daos import OrderFilter
from app.models.order import Order
from typing import Any, List, Optional, Set, Tuple
import logging
from datetime import datetime

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

    def __map_to_schema(self, r, items_rows=None, declines_rows=None) -> Order:
        order = Order.model_validate(r)
        if items_rows:
            order.items = [
                ItemSnippet(
                    product_id=str(ir.product_id),
                    quantity=int(ir.quantity) if ir.quantity is not None else 0,
                    price=float(ir.price) if ir.price is not None else 0.0,
                )
                for ir in items_rows
                if ir.order_id == r.id
            ]
        else:
            order.items = []

        if declines_rows:
            order.valet_decline_history = [
                ValetDeclineHistoryEntry(
                    valet_id=str(dr.valet_id),
                    reason=dr.reason,
                )
                for dr in declines_rows
                if dr.parent_id == r.id
            ]
        else:
            order.valet_decline_history = []
        return order

    def _build_query_conditions(self, filter: Optional[OrderFilter] = None) -> tuple[str, dict[str, Any]]:
        where_clauses: list[str] = []
        params = {}

        if filter:
            if filter.id is not None:
                if str(filter.id).isdigit():
                    where_clauses.append("id = :id")
                    params["id"] = int(filter.id)
                else:
                    where_clauses.append("1=0")

            if filter.user_id is not None:
                if str(filter.user_id).isdigit():
                    where_clauses.append("user_id = :user_id")
                    params["user_id"] = int(filter.user_id)
                else:
                    where_clauses.append("1=0")

            if filter.user_ids:
                int_uids = [int(u) for u in filter.user_ids if str(u).isdigit()]
                if int_uids:
                    u_params = {f"u_int_{j}": v for j, v in enumerate(int_uids)}
                    params.update(u_params)
                    where_clauses.append(f"user_id IN ({', '.join(f':{k}' for k in u_params)})")
                else:
                    where_clauses.append("1=0")

            if filter.status is not None:
                where_clauses.append("status = :status")
                params["status"] = filter.status

            if filter.statuses is not None:
                placeholders = []
                for idx, st in enumerate(filter.statuses):
                    param_key = f"status_{idx}"
                    placeholders.append(f":{param_key}")
                    params[param_key] = st
                where_clauses.append(f"status IN ({', '.join(placeholders)})")

            if filter.order_type is not None:
                where_clauses.append("order_type = :order_type")
                params["order_type"] = filter.order_type

            if filter.payment_method is not None:
                where_clauses.append("payment_method = :payment_method")
                params["payment_method"] = filter.payment_method

            if filter.start_date is not None:
                where_clauses.append("created_at >= :start_date")
                params["start_date"] = filter.start_date

            if filter.end_date is not None:
                where_clauses.append("created_at <= :end_date")
                params["end_date"] = filter.end_date

            if filter.order_number_prefix is not None:
                where_clauses.append("order_number LIKE :order_prefix")
                params["order_prefix"] = f"{filter.order_number_prefix}%"

            if filter.idempotency_key is not None:
                where_clauses.append("idempotency_key = :idempotency_key")
                params["idempotency_key"] = filter.idempotency_key

            if filter.assigned_valet is not None:
                where_clauses.append("assigned_valet = :assigned_valet")
                params["assigned_valet"] = filter.assigned_valet

            if filter.pending_valet_id is not None:
                where_clauses.append("pending_valet_id = :pending_valet_id")
                params["pending_valet_id"] = filter.pending_valet_id

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        return where_sql, params

    async def findAll(
        self, filter: Optional[OrderFilter] = None, skip: Optional[int] = None, limit: Optional[int] = None
    ) -> List[Order]:
        factory = self._factory()
        if not factory:
            return []

        where_sql, params = self._build_query_conditions(filter)

        pagination_sql = ""
        if skip is not None and limit is not None:
            pagination_sql = "LIMIT :limit OFFSET :skip"
            params["skip"] = skip
            params["limit"] = limit

        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id, user_id, order_number, status, total, subtotal, tax, shipping, discount,
                           order_type, payment_status, payment_method, upi_payment_screenshot,
                           ship_name, ship_street, ship_city, ship_state, ship_pincode, ship_phone, ship_address, ship_district, ship_country, ship_google_location, ship_latitude, ship_longitude, bill_name, bill_street, bill_city, bill_state, bill_pincode, bill_phone, bill_address, bill_district, bill_country, bill_google_location, bill_latitude, bill_longitude, notes, printed_bill, assigned_valet, pending_valet_id, valet_assigned_at, valet_cascade_count, is_urgent_delivery,
                           shipped_at, delivered_at, cod_payment_received, cod_payment_received_at,
                           decline_reason, cancelled_at, cancelled_by, turnaround_hours,
                           idempotency_key, fulfillment_type, courier_partner, tracking_id, awb_code, shipping_label_url, estimated_delivery_date,
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

            order_ids = [int(r.id) for r in rows]
            chunks = [order_ids[i : i + 999] for i in range(0, len(order_ids), 999)]
            items_rows = []
            declines_rows = []

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
                items_rows.extend(items_result.fetchall())

                decl_result = await session.execute(
                    text(f"SELECT parent_id, valet_id, reason FROM sj_order_valet_declines WHERE parent_id IN ({placeholders})"),
                    chunk_params,
                )
                declines_rows.extend(decl_result.fetchall())

            return [self.__map_to_schema(r, items_rows, declines_rows) for r in rows]

    async def findOne(self, filter: Optional[OrderFilter] = None) -> Optional[Order]:
        records = await self.findAll(filter)
        return records[0] if records else None

    async def findById(self, id: str) -> Optional[Order]:
        factory = self._factory()
        if not factory or not id or not str(id).isdigit():
            return None
        pid = int(id)
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id, user_id, order_number, status, total, subtotal, tax, shipping, discount,
                           order_type, payment_status, payment_method, upi_payment_screenshot,
                           ship_name, ship_street, ship_city, ship_state, ship_pincode, ship_phone, ship_address, ship_district, ship_country, ship_google_location, ship_latitude, ship_longitude, bill_name, bill_street, bill_city, bill_state, bill_pincode, bill_phone, bill_address, bill_district, bill_country, bill_google_location, bill_latitude, bill_longitude, notes, printed_bill, assigned_valet, pending_valet_id, valet_assigned_at, valet_cascade_count, is_urgent_delivery,
                           shipped_at, delivered_at, cod_payment_received, cod_payment_received_at,
                           decline_reason, cancelled_at, cancelled_by, turnaround_hours,
                           idempotency_key, fulfillment_type, courier_partner, tracking_id, awb_code, shipping_label_url, estimated_delivery_date,
                           created_at, updated_at
                    FROM {self.TABLE}
                    WHERE id = :id
                    """
                ),
                {"id": pid},
            )
            row = result.fetchone()
            if not row:
                return None
            items_res = await session.execute(
                text(f"SELECT order_id, product_id, quantity, price FROM {self.ITEMS_TABLE} WHERE order_id = :order_id"),
                {"order_id": int(row.id)},
            )
            decl_res = await session.execute(
                text("SELECT parent_id, valet_id, reason FROM sj_order_valet_declines WHERE parent_id = :order_id"),
                {"order_id": int(row.id)},
            )
            return self.__map_to_schema(row, items_res.fetchall(), decl_res.fetchall())

    async def findByIds(self, ids: List[str]) -> List[Order]:
        if not ids:
            return []
        factory = self._factory()
        if not factory:
            return []

        int_ids = [int(i) for i in ids if str(i).isdigit()]
        if not int_ids:
            return []

        clauses: list[str] = []
        params = {}
        chunks_int = [int_ids[i : i + 999] for i in range(0, len(int_ids), 999)]
        for c_idx, chunk in enumerate(chunks_int):
            c_params = {f"iid_{c_idx}_{j}": v for j, v in enumerate(chunk)}
            params.update(c_params)
            clauses.append(f"id IN ({', '.join(f':{k}' for k in c_params)})")

        where_sql = " OR ".join(clauses)
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id, user_id, order_number, status, total, subtotal, tax, shipping, discount,
                           order_type, payment_status, payment_method, upi_payment_screenshot,
                           ship_name, ship_street, ship_city, ship_state, ship_pincode, ship_phone, ship_address, ship_district, ship_country, ship_google_location, ship_latitude, ship_longitude, bill_name, bill_street, bill_city, bill_state, bill_pincode, bill_phone, bill_address, bill_district, bill_country, bill_google_location, bill_latitude, bill_longitude, notes, printed_bill, assigned_valet, pending_valet_id, valet_assigned_at, valet_cascade_count, is_urgent_delivery,
                           shipped_at, delivered_at, cod_payment_received, cod_payment_received_at,
                           decline_reason, cancelled_at, cancelled_by, turnaround_hours,
                           idempotency_key, fulfillment_type, courier_partner, tracking_id, awb_code, shipping_label_url, estimated_delivery_date,
                           created_at, updated_at
                    FROM {self.TABLE}
                    WHERE {where_sql}
                    ORDER BY created_at DESC
                    """
                ),
                params,
            )
            rows = result.fetchall()
            if not rows:
                return []

            order_ids = [int(r.id) for r in rows]
            chunks = [order_ids[i : i + 999] for i in range(0, len(order_ids), 999)]
            items_rows = []
            declines_rows = []

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
                items_rows.extend(items_result.fetchall())

                decl_result = await session.execute(
                    text(f"SELECT parent_id, valet_id, reason FROM sj_order_valet_declines WHERE parent_id IN ({placeholders})"),
                    chunk_params,
                )
                declines_rows.extend(decl_result.fetchall())

            return [self.__map_to_schema(r, items_rows, declines_rows) for r in rows]

    async def _replace_children(self, session, order_id: int, items: List[ItemSnippet], declines: List[ValetDeclineHistoryEntry]) -> None:
        await session.execute(
            text(f"DELETE FROM {self.ITEMS_TABLE} WHERE order_id = :order_id"),
            {"order_id": order_id},
        )
        for it in items or []:
            pid_raw = it.product_id if it.product_id is not None else it.product
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
        pass

    async def create(self, data: 'OrderInternalCreate') -> 'Order':
        res, _ = await self.create_idempotent(data)
        return res

    async def create_idempotent(self, data: 'OrderInternalCreate') -> tuple['Order', bool]:
        """Insert an order, using the DB unique index on (user_id, idempotency_key)
        to eliminate the TOCTOU race in the application-layer check.

        Returns (order, created) where created=False means the row already
        existed (a concurrent request won the race) and the existing order is
        returned.  Callers must skip all post-creation side-effects when
        created=False.

        Falls back to plain create() when idempotency_key is None/empty.
        """


        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        now = now_utc()
        uid = int(data.user) if data.user is not None and str(data.user).isdigit() else None

        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    INSERT IGNORE INTO {self.TABLE} (
                        user_id, order_number, status, total, subtotal, tax, shipping, discount,
                        order_type, payment_status, payment_method, upi_payment_screenshot,
                        ship_name, ship_street, ship_city, ship_state, ship_pincode, ship_phone, ship_address, ship_district, ship_country, ship_google_location, ship_latitude, ship_longitude, bill_name, bill_street, bill_city, bill_state, bill_pincode, bill_phone, bill_address, bill_district, bill_country, bill_google_location, bill_latitude, bill_longitude, notes, printed_bill, assigned_valet, pending_valet_id, valet_assigned_at, valet_cascade_count, is_urgent_delivery,
                        shipped_at, delivered_at, cod_payment_received, cod_payment_received_at,
                        decline_reason, cancelled_at, cancelled_by, turnaround_hours,
                        idempotency_key, fulfillment_type, courier_partner, tracking_id, awb_code, shipping_label_url, estimated_delivery_date,
                        created_at, updated_at
                    ) VALUES (
                        :user_id, :order_number, :status, :total, :subtotal, :tax, :shipping, :discount,
                        :order_type, :payment_status, :payment_method, :upi_payment_screenshot,
                        :ship_name, :ship_street, :ship_city, :ship_state, :ship_pincode, :ship_phone, :ship_address, :ship_district, :ship_country, :ship_google_location, :ship_latitude, :ship_longitude, :bill_name, :bill_street, :bill_city, :bill_state, :bill_pincode, :bill_phone, :bill_address, :bill_district, :bill_country, :bill_google_location, :bill_latitude, :bill_longitude, :notes, :printed_bill, :assigned_valet, :pending_valet_id, :valet_assigned_at, :valet_cascade_count, :is_urgent_delivery,
                        :shipped_at, :delivered_at, :cod_payment_received, :cod_payment_received_at,
                        :decline_reason, :cancelled_at, :cancelled_by, :turnaround_hours,
                        :idempotency_key, :fulfillment_type, :courier_partner, :tracking_id, :awb_code, :shipping_label_url, :estimated_delivery_date,
                        :created_at, :updated_at
                    )
                    """
                ),
                {
                    "user_id": uid,
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
                    "ship_address": data.ship_address,
                    "ship_district": data.ship_district,
                    "ship_country": data.ship_country,
                    "ship_google_location": data.ship_google_location,
                    "ship_latitude": data.ship_latitude,
                    "ship_longitude": data.ship_longitude,
                    "bill_name": data.bill_name,
                    "bill_street": data.bill_street,
                    "bill_city": data.bill_city,
                    "bill_state": data.bill_state,
                    "bill_pincode": data.bill_pincode,
                    "bill_phone": data.bill_phone,
                    "bill_address": data.bill_address,
                    "bill_district": data.bill_district,
                    "bill_country": data.bill_country,
                    "bill_google_location": data.bill_google_location,
                    "bill_latitude": data.bill_latitude,
                    "bill_longitude": data.bill_longitude,
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
                    "fulfillment_type": data.fulfillment_type or "hyperlocal",
                    "courier_partner": data.courier_partner,
                    "tracking_id": data.tracking_id,
                    "awb_code": data.awb_code,
                    "shipping_label_url": data.shipping_label_url,
                    "estimated_delivery_date": _to_ts(data.estimated_delivery_date),
                    "created_at": _to_ts(data.created_at) or now,
                    "updated_at": now,
                },
            )
            created = result.rowcount > 0

            if created:
                # Our INSERT won — wire up children and commit
                new_id = result.lastrowid
                await self._replace_children(session, new_id, data.items or [], data.valet_decline_history or [])
                await session.commit()
                return await self.findById(str(new_id)), True
            else:
                # Another request already inserted this idempotency key — fetch it
                await session.rollback()
                existing = await self.findOne(
                    OrderFilter(user_id=str(uid) if uid else None, idempotency_key=data.idempotency_key)
                )
                return existing, False

    async def update(self, id: str, update_data: 'OrderInternalUpdate') -> Optional[Order]:
        existing = await self.findById(id)
        if not existing:
            return None
        factory = self._factory()
        if not factory:
            return None
        now = now_utc()
        oid = int(existing.id)
        raw_user_id = update_data.user if update_data.user is not None else existing.user
        uid = int(raw_user_id) if raw_user_id is not None and str(raw_user_id).isdigit() else None

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
                        fulfillment_type = :fulfillment_type,
                        courier_partner = :courier_partner,
                        tracking_id = :tracking_id,
                        awb_code = :awb_code,
                        shipping_label_url = :shipping_label_url,
                        estimated_delivery_date = :estimated_delivery_date,
                        updated_at = :updated_at
                    WHERE id = :id
                    """
                ),
                {
                    "id": oid,
                    "user_id": uid,
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
                    "ship_name": update_data.ship_name if update_data.ship_name is not None else existing.ship_name,
                    "ship_street": update_data.ship_street if update_data.ship_street is not None else existing.ship_street,
                    "ship_city": update_data.ship_city if update_data.ship_city is not None else existing.ship_city,
                    "ship_state": update_data.ship_state if update_data.ship_state is not None else existing.ship_state,
                    "ship_pincode": update_data.ship_pincode if update_data.ship_pincode is not None else existing.ship_pincode,
                    "ship_phone": update_data.ship_phone if update_data.ship_phone is not None else existing.ship_phone,
                    "ship_address": update_data.ship_address if update_data.ship_address is not None else existing.ship_address,
                    "ship_district": update_data.ship_district if update_data.ship_district is not None else existing.ship_district,
                    "ship_country": update_data.ship_country if update_data.ship_country is not None else existing.ship_country,
                    "ship_google_location": update_data.ship_google_location if update_data.ship_google_location is not None else existing.ship_google_location,
                    "ship_latitude": update_data.ship_latitude if update_data.ship_latitude is not None else existing.ship_latitude,
                    "ship_longitude": update_data.ship_longitude if update_data.ship_longitude is not None else existing.ship_longitude,
                    "bill_name": update_data.bill_name if update_data.bill_name is not None else existing.bill_name,
                    "bill_street": update_data.bill_street if update_data.bill_street is not None else existing.bill_street,
                    "bill_city": update_data.bill_city if update_data.bill_city is not None else existing.bill_city,
                    "bill_state": update_data.bill_state if update_data.bill_state is not None else existing.bill_state,
                    "bill_pincode": update_data.bill_pincode if update_data.bill_pincode is not None else existing.bill_pincode,
                    "bill_phone": update_data.bill_phone if update_data.bill_phone is not None else existing.bill_phone,
                    "bill_address": update_data.bill_address if update_data.bill_address is not None else existing.bill_address,
                    "bill_district": update_data.bill_district if update_data.bill_district is not None else existing.bill_district,
                    "bill_country": update_data.bill_country if update_data.bill_country is not None else existing.bill_country,
                    "bill_google_location": update_data.bill_google_location if update_data.bill_google_location is not None else existing.bill_google_location,
                    "bill_latitude": update_data.bill_latitude if update_data.bill_latitude is not None else existing.bill_latitude,
                    "bill_longitude": update_data.bill_longitude if update_data.bill_longitude is not None else existing.bill_longitude,
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
                    "fulfillment_type": update_data.fulfillment_type or existing.fulfillment_type or "hyperlocal",
                    "courier_partner": update_data.courier_partner if update_data.courier_partner is not None else existing.courier_partner,
                    "tracking_id": update_data.tracking_id if update_data.tracking_id is not None else existing.tracking_id,
                    "awb_code": update_data.awb_code if update_data.awb_code is not None else existing.awb_code,
                    "shipping_label_url": update_data.shipping_label_url if update_data.shipping_label_url is not None else existing.shipping_label_url,
                    "estimated_delivery_date": _to_ts(update_data.estimated_delivery_date) if update_data.estimated_delivery_date is not None else existing.estimated_delivery_date,
                    "updated_at": now,
                },
            )
            await self._replace_children(session, oid, update_data.items if update_data.items is not None else existing.items or [], update_data.valet_decline_history if update_data.valet_decline_history is not None else existing.valet_decline_history or [])
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory or not id:
            return False
        existing = await self.findById(id)
        if not existing:
            return False
        oid = int(existing.id)
        async with factory() as session:
            await session.execute(
                text("DELETE FROM sj_order_valet_declines WHERE parent_id = :order_id"),
                {"order_id": oid},
            )
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
                    SELECT IFNULL(MAX(CAST(REGEXP_SUBSTR(order_number, '[0-9]+$') AS UNSIGNED)), 0)
                    FROM {self.TABLE}
                    WHERE order_number LIKE :prefix_like
                    """
                ),
                {"prefix_like": prefix_like},
            )
            return int(result.scalar() or 0)

    async def deleteMany(self, filter: Optional[OrderFilter] = None) -> int:
        """Delete matching orders and their child items/declines in SQL pushdown."""
        factory = self._factory()
        if not factory:
            return 0
        where_sql, params = self._build_query_conditions(filter)
        async with factory() as session:
            await session.execute(
                text(f"DELETE FROM {self.ITEMS_TABLE} WHERE order_id IN (SELECT id FROM {self.TABLE} WHERE {where_sql})"),
                params,
            )
            await session.execute(
                text(f"DELETE FROM sj_order_valet_declines WHERE parent_id IN (SELECT id FROM {self.TABLE} WHERE {where_sql})"),
                params,
            )
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE {where_sql}"),
                params,
            )
            await session.commit()
            return result.rowcount or 0

    async def count(self, filter: Optional[OrderFilter] = None) -> int:
        factory = self._factory()
        if not factory:
            return 0
        where_sql, params = self._build_query_conditions(filter)
        async with factory() as session:
            result = await session.execute(text(f"SELECT COUNT(*) FROM {self.TABLE} WHERE {where_sql}"), params)
            return int(result.scalar() or 0)

    async def get_user_purchased_subcategories(
        self, user_id: str, start_date: datetime
    ) -> List[Tuple[str, int]]:
        """
        Aggregate total purchased quantity grouped by subcategory (falling back to category)
        for a specific user since start_date, sorted by quantity ascending.
        """
        factory = self._factory()
        if not factory:
            return []

        if not str(user_id).isdigit():
            return []
        uid = int(user_id)

        sql = f"""
            SELECT COALESCE(NULLIF(p.sub_category, ''), NULLIF(p.category, '')) AS subcat,
                   CAST(SUM(COALESCE(oi.quantity, 1)) AS UNSIGNED) AS total_qty
            FROM {self.ITEMS_TABLE} oi
            JOIN {self.TABLE} o ON o.id = oi.order_id
            JOIN sj_products p ON p.id = oi.product_id
            WHERE o.user_id = :uid
              AND o.created_at >= :start_date
              AND o.status != 'cancelled'
              AND COALESCE(NULLIF(p.sub_category, ''), NULLIF(p.category, '')) IS NOT NULL
            GROUP BY subcat
            ORDER BY total_qty ASC
        """
        params = {"start_date": start_date, "uid": uid}

        async with factory() as session:
            result = await session.execute(text(sql), params)
            return [(str(row.subcat), int(row.total_qty)) for row in result.fetchall() if row.subcat]

    async def get_bestsellers_in_subcategories(
        self, subcategories: List[str], start_date: datetime
    ) -> List[Tuple[str, str, int]]:
        """
        Fetch top products and their sales quantities within the specified subcategories
        since start_date, sorted by sales descending.
        Returns: List[Tuple[product_id, subcategory, total_sales]]
        """
        if not subcategories:
            return []
        factory = self._factory()
        if not factory:
            return []

        sc_params = {f"sc_{i}": sc for i, sc in enumerate(subcategories)}
        sc_placeholders = ", ".join(f":{k}" for k in sc_params)

        sql = f"""
            SELECT CAST(oi.product_id AS CHAR) AS product_id,
                   COALESCE(NULLIF(p.sub_category, ''), NULLIF(p.category, '')) AS subcat,
                   CAST(SUM(COALESCE(oi.quantity, 1)) AS UNSIGNED) AS sales
            FROM {self.ITEMS_TABLE} oi
            JOIN {self.TABLE} o ON o.id = oi.order_id
            JOIN sj_products p ON p.id = oi.product_id
            WHERE o.created_at >= :start_date
              AND o.status != 'cancelled'
              AND p.is_active = 1
              AND COALESCE(NULLIF(p.sub_category, ''), NULLIF(p.category, '')) IN ({sc_placeholders})
            GROUP BY product_id, subcat
            ORDER BY sales DESC
        """
        sc_params["start_date"] = start_date

        async with factory() as session:
            result = await session.execute(text(sql), sc_params)
            return [(str(row.product_id), str(row.subcat), int(row.sales)) for row in result.fetchall()]

    async def get_user_purchased_product_ids(
        self, user_id: str, start_date: Optional[datetime] = None
    ) -> Set[str]:
        """
        Return the set of distinct product IDs purchased by a user.
        Optionally filtered by orders created on or after start_date.
        """
        factory = self._factory()
        if not factory:
            return set()

        if not str(user_id).isdigit():
            return set()
        uid = int(user_id)
        date_cond = "AND o.created_at >= :start_date" if start_date else ""

        sql = f"""
            SELECT DISTINCT CAST(oi.product_id AS CHAR) AS pid
            FROM {self.ITEMS_TABLE} oi
            JOIN {self.TABLE} o ON o.id = oi.order_id
            WHERE o.user_id = :uid
              AND o.status != 'cancelled'
              {date_cond}
        """
        params = {"uid": uid}
        if start_date:
            params["start_date"] = start_date

        async with factory() as session:
            result = await session.execute(text(sql), params)
            return {str(row.pid) for row in result.fetchall() if row.pid}

    async def get_retail_bestsellers(
        self, start_date: datetime, limit: int = 10, exclude_product_ids: Optional[Set[str]] = None
    ) -> List[str]:
        """
        Top bestsellers from retail customer orders (ORDER-RT-) only since start_date.
        """
        factory = self._factory()
        if not factory:
            return []

        sql = f"""
            SELECT CAST(oi.product_id AS CHAR) AS pid,
                   CAST(SUM(COALESCE(oi.quantity, 1)) AS UNSIGNED) AS total_qty
            FROM {self.ITEMS_TABLE} oi
            JOIN {self.TABLE} o ON o.id = oi.order_id
            JOIN sj_users u ON u.id = o.user_id
            WHERE u.role = 'customer'
              AND o.order_number LIKE 'ORDER-RT-%'
              AND o.created_at >= :start_date
              AND o.status != 'cancelled'
            GROUP BY pid
            ORDER BY total_qty DESC
        """
        params = {"start_date": start_date}

        exclude = exclude_product_ids or set()
        async with factory() as session:
            result = await session.execute(text(sql), params)
            out: List[str] = []
            for row in result.fetchall():
                pid = str(row.pid)
                if pid and pid not in exclude:
                    out.append(pid)
                    if len(out) >= limit:
                        break
            return out

    async def get_most_bought_by_wholesalers(
        self, user_id: str, start_date: datetime, limit: int = 10
    ) -> List[str]:
        """
        Products most frequently bought by other wholesalers since start_date.
        """
        factory = self._factory()
        if not factory:
            return []

        uid = int(user_id) if str(user_id).isdigit() else 0

        sql = f"""
            SELECT CAST(oi.product_id AS CHAR) AS pid,
                   CAST(SUM(COALESCE(oi.quantity, 1)) AS UNSIGNED) AS total_qty
            FROM {self.ITEMS_TABLE} oi
            JOIN {self.TABLE} o ON o.id = oi.order_id
            JOIN sj_users u ON u.id = o.user_id
            WHERE u.role = 'wholesaler'
              AND o.user_id != :uid
              AND o.order_number LIKE 'ORDER-WH-%'
              AND o.created_at >= :start_date
              AND o.status != 'cancelled'
            GROUP BY pid
            ORDER BY total_qty DESC
            LIMIT :limit
        """
        params = {"start_date": start_date, "uid": uid, "limit": limit}

        async with factory() as session:
            result = await session.execute(text(sql), params)
            return [str(row.pid) for row in result.fetchall() if row.pid]

    async def get_most_bought_by_user(
        self, user_id: str, start_date: datetime, limit: int = 5
    ) -> List[str]:
        """
        Top products bought by specific user since start_date.
        """
        factory = self._factory()
        if not factory:
            return []

        if not str(user_id).isdigit():
            return []
        uid = int(user_id)

        sql = f"""
            SELECT CAST(oi.product_id AS CHAR) AS pid,
                   CAST(SUM(COALESCE(oi.quantity, 1)) AS UNSIGNED) AS total_qty
            FROM {self.ITEMS_TABLE} oi
            JOIN {self.TABLE} o ON o.id = oi.order_id
            WHERE o.user_id = :uid
              AND o.created_at >= :start_date
              AND o.status != 'cancelled'
            GROUP BY pid
            ORDER BY total_qty DESC
            LIMIT :limit
        """
        params = {"start_date": start_date, "uid": uid, "limit": limit}

        async with factory() as session:
            result = await session.execute(text(sql), params)
            return [str(row.pid) for row in result.fetchall() if row.pid]

    async def get_favourites_by_subcategory(
        self,
        kind: str,
        start_date: datetime,
        city: Optional[str] = None,
    ) -> List[Tuple[str, str, int, int]]:
        """
        Aggregate order count and total quantity per product and subcategory for favourites.
        kind: 'customer' (retail ORDER-RT-, role customer) | 'business' (wholesaler ORDER-WH-)
        Returns: List[Tuple[product_id, subcategory, order_count, total_quantity]]
        """
        factory = self._factory()
        if not factory:
            return []

        prefix = "ORDER-RT-%" if kind == "customer" else "ORDER-WH-%"
        user_join = "JOIN sj_users u ON u.id = o.user_id" if kind == "customer" else ""
        user_filter = "AND u.role = 'customer'" if kind == "customer" else ""

        city_cond = ""
        params = {"prefix": prefix, "start_date": start_date}

        if city and city.strip():
            city_cond = "AND LOWER(TRIM(o.ship_city)) = :city"
            params["city"] = city.strip().lower()

        sql = f"""
            SELECT CAST(oi.product_id AS CHAR) AS pid,
                   COALESCE(NULLIF(p.sub_category, ''), 'None') AS subcat,
                   COUNT(DISTINCT o.id) AS order_count,
                   CAST(SUM(COALESCE(oi.quantity, 1)) AS UNSIGNED) AS total_qty
            FROM {self.ITEMS_TABLE} oi
            JOIN {self.TABLE} o ON o.id = oi.order_id
            JOIN sj_products p ON p.id = oi.product_id
            {user_join}
            WHERE o.order_number LIKE :prefix
              AND o.created_at >= :start_date
              AND o.status != 'cancelled'
              AND p.is_active = 1
              {user_filter}
              {city_cond}
            GROUP BY pid, subcat
            HAVING total_qty > 1
        """

        async with factory() as session:
            result = await session.execute(text(sql), params)
            return [
                (str(row.pid), str(row.subcat), int(row.order_count), int(row.total_qty))
                for row in result.fetchall()
            ]

    async def get_favourites_ranked_data(
        self,
        kind: str,
        start_date: datetime,
        state: Optional[str] = None,
        city: Optional[str] = None,
    ) -> Tuple[List[Tuple[str, int, int]], List[str], List[str]]:
        """
        Fetch ranked product sales stats plus distinct states and cities from matching orders.
        kind: 'customer' (retail ORDER-RT-, role customer) | 'business' (wholesaler ORDER-WH-)
        Returns: (product_stats, distinct_states, distinct_cities)
        where product_stats is [(product_id, order_count, total_quantity), ...]
        """
        factory = self._factory()
        if not factory:
            return [], [], []

        prefix = "ORDER-RT-%" if kind == "customer" else "ORDER-WH-%"
        user_join = "JOIN sj_users u ON u.id = o.user_id" if kind == "customer" else ""
        user_filter = "AND u.role = 'customer'" if kind == "customer" else ""

        geo_params = {"prefix": prefix, "start_date": start_date}

        geo_sql = f"""
            SELECT DISTINCT TRIM(o.ship_state) AS state, TRIM(o.ship_city) AS city
            FROM {self.TABLE} o
            {user_join}
            WHERE o.order_number LIKE :prefix
              AND o.created_at >= :start_date
              AND o.status != 'cancelled'
              {user_filter}
        """

        state_cond = ""
        city_cond = ""
        stats_params = dict(geo_params)
        if state and state.strip():
            state_cond = "AND LOWER(TRIM(o.ship_state)) = :state"
            stats_params["state"] = state.strip().lower()
        if city and city.strip():
            city_cond = "AND LOWER(TRIM(o.ship_city)) = :city"
            stats_params["city"] = city.strip().lower()

        stats_sql = f"""
            SELECT CAST(oi.product_id AS CHAR) AS pid,
                   COUNT(DISTINCT o.id) AS order_count,
                   CAST(SUM(COALESCE(oi.quantity, 1)) AS UNSIGNED) AS total_qty
            FROM {self.ITEMS_TABLE} oi
            JOIN {self.TABLE} o ON o.id = oi.order_id
            {user_join}
            WHERE o.order_number LIKE :prefix
              AND o.created_at >= :start_date
              AND o.status != 'cancelled'
              {user_filter}
              {state_cond}
              {city_cond}
            GROUP BY pid
        """

        async with factory() as session:
            geo_res = await session.execute(text(geo_sql), geo_params)
            states = set()
            cities = set()
            for r in geo_res.fetchall():
                if r.state:
                    states.add(str(r.state))
                if r.city:
                    cities.add(str(r.city))

            stats_res = await session.execute(text(stats_sql), stats_params)
            product_stats = [
                (str(r.pid), int(r.order_count), int(r.total_qty))
                for r in stats_res.fetchall()
                if r.pid
            ]

        return product_stats, sorted(states), sorted(cities)









