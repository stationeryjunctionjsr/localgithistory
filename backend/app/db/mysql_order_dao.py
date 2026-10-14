from app.models.schemas import ItemSnippet, ValetDeclineHistoryEntry
from app.models.daos import OrderFilter
from app.models.order import Order, OrderInternalCreate, OrderInternalUpdate
from typing import Any, List, Optional, Set, Tuple
import logging
from datetime import datetime, timezone

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc


from app.models.base import CamelBaseModel
from app.models.analytics_schemas import (
    SalesOverTimeResponse,
    SalesBreakdownResponse,
    AverageOrderValueResponse,
    SalesByChannelResponse,
    SalesByProductResponse,
    ConversionOrderStats,
    ProductsSellThroughResponse,
    CustomerCohortResponse,
    TopUsersReportResponse,
    UserOrderStatsResponse,
    PaymentMethodsReportResponse,
    RevenueByCategoryResponse,
    FulfillmentTimeReportResponse,
    CouponUsageReportResponse,
    SalesByLocationReportResponse,
)


class OrderSummaryStats(CamelBaseModel):
    total_orders: int = 0
    total_revenue: float = 0.0


class OrderKpiStats(CamelBaseModel):
    gross_sales: float = 0.0
    returning_customer_rate: float = 0.0
    orders_fulfilled: int = 0
    orders: int = 0


class MySQLOrderDAO:
    @property
    def TABLE(self):
        return "sj_orders"

    @property
    def ITEMS_TABLE(self):
        return "sj_order_items"

    def __map_to_schema(self, r, items_rows=None, declines_rows=None) -> Order:
        order = Order.model_validate(r)
        if items_rows:
            order.items = [
                ItemSnippet(
                    product_id=ir.product_id,
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
                try:
                    where_clauses.append("id = :id")
                    params["id"] = int(filter.id)
                except (ValueError, TypeError):
                    where_clauses.append("1=0")

            if filter.user_id is not None:
                try:
                    where_clauses.append("user_id = :user_id")
                    params["user_id"] = int(filter.user_id)
                except (ValueError, TypeError):
                    where_clauses.append("1=0")

            if filter.user_ids:
                int_uids = []
                for u in filter.user_ids:
                    try:
                        int_uids.append(int(u))
                    except (ValueError, TypeError):
                        continue
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
        where_sql, params = self._build_query_conditions(filter)

        pagination_sql = ""
        if skip is not None and limit is not None:
            pagination_sql = "LIMIT :limit OFFSET :skip"
            params["skip"] = skip
            params["limit"] = limit

        async_session = get_async_session_factory()
        async with async_session() as session:
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

    async def get_summary_stats(self, filter: Optional[OrderFilter] = None) -> OrderSummaryStats:
        """Returns (total_orders, total_revenue) via direct SQL aggregate without loading records."""
        where_sql, params = self._build_query_conditions(filter)
        async_session = get_async_session_factory()
        async with async_session() as session:
            q = text(f"SELECT COUNT(*) AS total_orders, COALESCE(SUM(total), 0.0) AS total_revenue FROM {self.TABLE} WHERE {where_sql}")
            res = (await session.execute(q, params)).fetchone()
            if not res:
                return OrderSummaryStats(total_orders=0, total_revenue=0.0)
            return OrderSummaryStats(total_orders=res.total_orders or 0, total_revenue=float(res.total_revenue or 0.0))

    async def get_kpi_stats(self, filter: Optional[OrderFilter] = None) -> OrderKpiStats:
        """Direct SQL pushdown for KPI metrics: gross sales, total orders, fulfilled orders, returning customer rate."""
        where_sql, params = self._build_query_conditions(filter)
        async_session = get_async_session_factory()
        async with async_session() as session:
            q = text(
                f"""
                SELECT 
                    COALESCE(SUM(total), 0.0) AS gross_sales,
                    COUNT(*) AS total_orders,
                    COUNT(CASE WHEN status IN ('delivered', 'completed', 'dispatched') THEN 1 END) AS orders_fulfilled
                FROM {self.TABLE}
                WHERE {where_sql}
                """
            )
            agg = (await session.execute(q, params)).fetchone()
            gross_sales = float(agg.gross_sales or 0.0) if agg else 0.0
            total_orders = agg.total_orders or 0 if agg else 0
            orders_fulfilled = agg.orders_fulfilled or 0 if agg else 0

            q_returning = text(
                f"""
                SELECT 
                    COUNT(DISTINCT user_id) AS total_customers,
                    COUNT(DISTINCT CASE WHEN order_count > 1 THEN user_id END) AS returning_customers
                FROM (
                    SELECT user_id, COUNT(*) AS order_count
                    FROM {self.TABLE}
                    WHERE {where_sql} AND user_id IS NOT NULL
                    GROUP BY user_id
                ) t
                """
            )
            ret_res = (await session.execute(q_returning, params)).fetchone()
            tot_cust = ret_res.total_customers or 0 if ret_res else 0
            ret_cust = ret_res.returning_customers or 0 if ret_res else 0
            rate = round((ret_cust / tot_cust * 100), 2) if tot_cust > 0 else 0.0

            return OrderKpiStats(
                gross_sales=round(gross_sales, 2),
                returning_customer_rate=rate,
                orders_fulfilled=orders_fulfilled,
                orders=total_orders,
            )

    async def findOne(self, filter: Optional[OrderFilter] = None) -> Optional[Order]:
        records = await self.findAll(filter)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[Order]:
        if not id:
            return None
        async_session = get_async_session_factory()
        async with async_session() as session:
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
                {"id": id},
            )
            row = result.fetchone()
            if not row:
                return None
            items_res = await session.execute(
                text(f"SELECT order_id, product_id, quantity, price FROM {self.ITEMS_TABLE} WHERE order_id = :order_id"),
                {"order_id": row.id},
            )
            decl_res = await session.execute(
                text("SELECT parent_id, valet_id, reason FROM sj_order_valet_declines WHERE parent_id = :order_id"),
                {"order_id": row.id},
            )
            return self.__map_to_schema(row, items_res.fetchall(), decl_res.fetchall())

    async def findByIds(self, ids: List[int]) -> List[Order]:
        if not ids:
            return []

        int_ids = [i for i in ids if i]
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
        async_session = get_async_session_factory()
        async with async_session() as session:
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

    async def _sync_items(self, session, order_id: int, items: Optional[List[ItemSnippet]]) -> None:
        await session.execute(
            text(f"DELETE FROM {self.ITEMS_TABLE} WHERE order_id = :order_id"),
            {"order_id": order_id},
        )
        for it in items or []:
            pid = it.product_id
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

    async def _sync_valet_declines(self, session, order_id: int, declines: Optional[List[ValetDeclineHistoryEntry]]) -> None:
        await session.execute(
            text("DELETE FROM sj_order_valet_declines WHERE parent_id = :order_id"),
            {"order_id": order_id},
        )
        for d in declines or []:
            await session.execute(
                text("INSERT INTO sj_order_valet_declines (parent_id, valet_id, reason) VALUES (:order_id, :vid, :r)"),
                {"order_id": order_id, "vid": str((d.valet_id if d.valet_id is not None else "")), "r": d.reason}
            )

    async def _replace_children(self, session, order_id: int, items: List[ItemSnippet], declines: List[ValetDeclineHistoryEntry]) -> None:
        await self._sync_items(session, order_id, items)
        await self._sync_valet_declines(session, order_id, declines)

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


        async_session = get_async_session_factory()
        now = now_utc()
        uid = data.user

        async with async_session() as session:
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
                    "valet_assigned_at": data.valet_assigned_at,
                    "valet_cascade_count": data.valet_cascade_count or 0,
                    "shipped_at": data.shipped_at,
                    "delivered_at": data.delivered_at,
                    "cod_payment_received": 1 if data.cod_payment_received else 0,
                    "cod_payment_received_at": data.cod_payment_received_at,
                    "decline_reason": data.decline_reason,
                    "cancelled_at": data.cancelled_at,
                    "cancelled_by": data.cancelled_by,
                    "turnaround_hours": data.turnaround_hours,
                    "idempotency_key": data.idempotency_key,
                    "fulfillment_type": data.fulfillment_type or "hyperlocal",
                    "courier_partner": data.courier_partner,
                    "tracking_id": data.tracking_id,
                    "awb_code": data.awb_code,
                    "shipping_label_url": data.shipping_label_url,
                    "estimated_delivery_date": data.estimated_delivery_date,
                    "created_at": data.created_at or now,
                    "updated_at": now,
                },
            )
            created = result.rowcount > 0

            if created:
                # Our INSERT won — wire up children and commit
                new_id = result.lastrowid
                await self._replace_children(session, new_id, data.items or [], data.valet_decline_history or [])
                await session.commit()
                return await self.findById(new_id), True
            else:
                # Another request already inserted this idempotency key — fetch it
                await session.rollback()
                existing = await self.findOne(
                    OrderFilter(user_id=str(uid) if uid else None, idempotency_key=data.idempotency_key)
                )
                return existing, False

    async def update(self, id: int, update_data: OrderInternalUpdate) -> Optional[Order]:
        if not id:
            return None

        fields = update_data.model_fields_set
        if not fields:
            return await self.findById(id)

        now = now_utc()
        updates = ["updated_at = :updated_at"]
        params = {"id": id, "updated_at": now}

        if "user" in fields:
            raw_uid = update_data.user
            uid = None
            if raw_uid is not None:
                try:
                    uid = int(raw_uid)
                except (ValueError, TypeError):
                    uid = None
            updates.append("user_id = :user_id")
            params["user_id"] = uid
        if "order_number" in fields:
            updates.append("order_number = :order_number")
            params["order_number"] = update_data.order_number
        if "status" in fields:
            updates.append("status = :status")
            params["status"] = update_data.status
        if "total" in fields:
            updates.append("total = :total")
            params["total"] = update_data.total
        if "subtotal" in fields:
            updates.append("subtotal = :subtotal")
            params["subtotal"] = update_data.subtotal
        if "tax" in fields:
            updates.append("tax = :tax")
            params["tax"] = update_data.tax
        if "shipping" in fields:
            updates.append("shipping = :shipping")
            params["shipping"] = update_data.shipping
        if "discount" in fields:
            updates.append("discount = :discount")
            params["discount"] = update_data.discount
        if "order_type" in fields:
            updates.append("order_type = :order_type")
            params["order_type"] = update_data.order_type
        if "payment_status" in fields:
            updates.append("payment_status = :payment_status")
            params["payment_status"] = update_data.payment_status
        if "payment_method" in fields:
            updates.append("payment_method = :payment_method")
            params["payment_method"] = update_data.payment_method
        if "upi_payment_screenshot" in fields:
            updates.append("upi_payment_screenshot = :upi_payment_screenshot")
            params["upi_payment_screenshot"] = update_data.upi_payment_screenshot
        if "ship_name" in fields:
            updates.append("ship_name = :ship_name")
            params["ship_name"] = update_data.ship_name
        if "ship_street" in fields:
            updates.append("ship_street = :ship_street")
            params["ship_street"] = update_data.ship_street
        if "ship_city" in fields:
            updates.append("ship_city = :ship_city")
            params["ship_city"] = update_data.ship_city
        if "ship_state" in fields:
            updates.append("ship_state = :ship_state")
            params["ship_state"] = update_data.ship_state
        if "ship_pincode" in fields:
            updates.append("ship_pincode = :ship_pincode")
            params["ship_pincode"] = update_data.ship_pincode
        if "ship_phone" in fields:
            updates.append("ship_phone = :ship_phone")
            params["ship_phone"] = update_data.ship_phone
        if "ship_address" in fields:
            updates.append("ship_address = :ship_address")
            params["ship_address"] = update_data.ship_address
        if "ship_district" in fields:
            updates.append("ship_district = :ship_district")
            params["ship_district"] = update_data.ship_district
        if "ship_country" in fields:
            updates.append("ship_country = :ship_country")
            params["ship_country"] = update_data.ship_country
        if "ship_google_location" in fields:
            updates.append("ship_google_location = :ship_google_location")
            params["ship_google_location"] = update_data.ship_google_location
        if "ship_latitude" in fields:
            updates.append("ship_latitude = :ship_latitude")
            params["ship_latitude"] = update_data.ship_latitude
        if "ship_longitude" in fields:
            updates.append("ship_longitude = :ship_longitude")
            params["ship_longitude"] = update_data.ship_longitude
        if "bill_name" in fields:
            updates.append("bill_name = :bill_name")
            params["bill_name"] = update_data.bill_name
        if "bill_street" in fields:
            updates.append("bill_street = :bill_street")
            params["bill_street"] = update_data.bill_street
        if "bill_city" in fields:
            updates.append("bill_city = :bill_city")
            params["bill_city"] = update_data.bill_city
        if "bill_state" in fields:
            updates.append("bill_state = :bill_state")
            params["bill_state"] = update_data.bill_state
        if "bill_pincode" in fields:
            updates.append("bill_pincode = :bill_pincode")
            params["bill_pincode"] = update_data.bill_pincode
        if "bill_phone" in fields:
            updates.append("bill_phone = :bill_phone")
            params["bill_phone"] = update_data.bill_phone
        if "bill_address" in fields:
            updates.append("bill_address = :bill_address")
            params["bill_address"] = update_data.bill_address
        if "bill_district" in fields:
            updates.append("bill_district = :bill_district")
            params["bill_district"] = update_data.bill_district
        if "bill_country" in fields:
            updates.append("bill_country = :bill_country")
            params["bill_country"] = update_data.bill_country
        if "bill_google_location" in fields:
            updates.append("bill_google_location = :bill_google_location")
            params["bill_google_location"] = update_data.bill_google_location
        if "bill_latitude" in fields:
            updates.append("bill_latitude = :bill_latitude")
            params["bill_latitude"] = update_data.bill_latitude
        if "bill_longitude" in fields:
            updates.append("bill_longitude = :bill_longitude")
            params["bill_longitude"] = update_data.bill_longitude
        if "notes" in fields:
            updates.append("notes = :notes")
            params["notes"] = update_data.notes
        if "printed_bill" in fields:
            updates.append("printed_bill = :printed_bill")
            params["printed_bill"] = 1 if update_data.printed_bill else 0
        if "assigned_valet" in fields:
            updates.append("assigned_valet = :assigned_valet")
            params["assigned_valet"] = update_data.assigned_valet
        if "pending_valet_id" in fields:
            updates.append("pending_valet_id = :pending_valet_id")
            params["pending_valet_id"] = update_data.pending_valet_id
        if "valet_assigned_at" in fields:
            updates.append("valet_assigned_at = :valet_assigned_at")
            params["valet_assigned_at"] = update_data.valet_assigned_at
        if "valet_cascade_count" in fields:
            updates.append("valet_cascade_count = :valet_cascade_count")
            params["valet_cascade_count"] = update_data.valet_cascade_count if update_data.valet_cascade_count is not None else 0
        if "is_urgent_delivery" in fields:
            updates.append("is_urgent_delivery = :is_urgent_delivery")
            params["is_urgent_delivery"] = 1 if update_data.is_urgent_delivery else 0
        if "shipped_at" in fields:
            updates.append("shipped_at = :shipped_at")
            params["shipped_at"] = update_data.shipped_at
        if "delivered_at" in fields:
            updates.append("delivered_at = :delivered_at")
            params["delivered_at"] = update_data.delivered_at
        if "cod_payment_received" in fields:
            updates.append("cod_payment_received = :cod_payment_received")
            params["cod_payment_received"] = 1 if update_data.cod_payment_received else 0
        if "cod_payment_received_at" in fields:
            updates.append("cod_payment_received_at = :cod_payment_received_at")
            params["cod_payment_received_at"] = update_data.cod_payment_received_at
        if "decline_reason" in fields:
            updates.append("decline_reason = :decline_reason")
            params["decline_reason"] = update_data.decline_reason
        if "cancelled_at" in fields:
            updates.append("cancelled_at = :cancelled_at")
            params["cancelled_at"] = update_data.cancelled_at
        if "cancelled_by" in fields:
            updates.append("cancelled_by = :cancelled_by")
            params["cancelled_by"] = update_data.cancelled_by
        if "turnaround_hours" in fields:
            updates.append("turnaround_hours = :turnaround_hours")
            params["turnaround_hours"] = update_data.turnaround_hours
        if "fulfillment_type" in fields:
            updates.append("fulfillment_type = :fulfillment_type")
            params["fulfillment_type"] = update_data.fulfillment_type
        if "courier_partner" in fields:
            updates.append("courier_partner = :courier_partner")
            params["courier_partner"] = update_data.courier_partner
        if "tracking_id" in fields:
            updates.append("tracking_id = :tracking_id")
            params["tracking_id"] = update_data.tracking_id
        if "awb_code" in fields:
            updates.append("awb_code = :awb_code")
            params["awb_code"] = update_data.awb_code
        if "shipping_label_url" in fields:
            updates.append("shipping_label_url = :shipping_label_url")
            params["shipping_label_url"] = update_data.shipping_label_url
        if "estimated_delivery_date" in fields:
            updates.append("estimated_delivery_date = :estimated_delivery_date")
            params["estimated_delivery_date"] = update_data.estimated_delivery_date

        has_child_updates = "items" in fields or "valet_decline_history" in fields
        async_session = get_async_session_factory()
        async with async_session() as session:
            try:
                rowcount = 0
                if len(updates) > 1:
                    set_sql = ", ".join(updates)
                    result = await session.execute(
                        text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                        params,
                    )
                    rowcount = result.rowcount

                if "items" in fields:
                    await self._sync_items(session, id, update_data.items or [])
                if "valet_decline_history" in fields:
                    await self._sync_valet_declines(session, id, update_data.valet_decline_history or [])

                await session.commit()

                if rowcount == 0 and not has_child_updates:
                    existing = await self.findById(id)
                    if not existing:
                        return None
            except Exception:
                await session.rollback()
                raise

        return await self.findById(id)

    async def delete(self, id: int) -> bool:
        if not id:
            return False
        async_session = get_async_session_factory()
        async with async_session() as session:
            await session.execute(
                text("DELETE FROM sj_order_valet_declines WHERE parent_id = :order_id"),
                {"order_id": id},
            )
            await session.execute(
                text(f"DELETE FROM {self.ITEMS_TABLE} WHERE order_id = :order_id"),
                {"order_id": id},
            )
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": id},
            )
            await session.commit()
            return result.rowcount > 0

    async def get_max_order_number_suffix(self, prefix: str) -> int:
        prefix_like = prefix + "%"
        async_session = get_async_session_factory()
        async with async_session() as session:
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
        where_sql, params = self._build_query_conditions(filter)
        async_session = get_async_session_factory()
        async with async_session() as session:
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
        where_sql, params = self._build_query_conditions(filter)
        async_session = get_async_session_factory()
        async with async_session() as session:
            result = await session.execute(text(f"SELECT COUNT(*) FROM {self.TABLE} WHERE {where_sql}"), params)
            return int(result.scalar() or 0)

    async def get_user_purchased_subcategories(
        self, user_id: int, start_date: datetime
    ) -> List[Tuple[str, int]]:
        """
        Aggregate total purchased quantity grouped by subcategory (falling back to category)
        for a specific user since start_date, sorted by quantity ascending.
        """
        try:
            uid = int(user_id)
        except (ValueError, TypeError):
            return []

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

        async_session = get_async_session_factory()
        async with async_session() as session:
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

        async_session = get_async_session_factory()
        async with async_session() as session:
            result = await session.execute(text(sql), sc_params)
            return [(str(row.product_id), str(row.subcat), int(row.sales)) for row in result.fetchall()]

    async def get_user_purchased_product_ids(
        self, user_id: int, start_date: Optional[datetime] = None
    ) -> Set[str]:
        """
        Return the set of distinct product IDs purchased by a user.
        Optionally filtered by orders created on or after start_date.
        """
        try:
            uid = int(user_id)
        except (ValueError, TypeError):
            return set()
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

        async_session = get_async_session_factory()
        async with async_session() as session:
            result = await session.execute(text(sql), params)
            return {str(row.pid) for row in result.fetchall() if row.pid}

    async def get_retail_bestsellers(
        self, start_date: datetime, limit: int = 10, exclude_product_ids: Optional[Set[str]] = None
    ) -> List[str]:
        """
        Top bestsellers from retail customer orders (ORDER-RT-) only since start_date.
        """
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
        async_session = get_async_session_factory()
        async with async_session() as session:
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
        self, user_id: int, start_date: datetime, limit: int = 10
    ) -> List[str]:
        """
        Products most frequently bought by other wholesalers since start_date.
        """
        try:
            uid = int(user_id)
        except (ValueError, TypeError):
            uid = 0

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

        async_session = get_async_session_factory()
        async with async_session() as session:
            result = await session.execute(text(sql), params)
            return [str(row.pid) for row in result.fetchall() if row.pid]

    async def get_most_bought_by_user(
        self, user_id: int, start_date: datetime, limit: int = 5
    ) -> List[str]:
        """
        Top products bought by specific user since start_date.
        """
        try:
            uid = int(user_id)
        except (ValueError, TypeError):
            return []

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

        async_session = get_async_session_factory()
        async with async_session() as session:
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

        async_session = get_async_session_factory()
        async with async_session() as session:
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

        async_session = get_async_session_factory()
        async with async_session() as session:
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

    async def get_sales_over_time_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "hour",
        seller_id: Optional[str] = None,
    ) -> List[SalesOverTimeResponse]:
        fmt = "%Y-%m-%d %H:00" if group_by == "hour" else ("%Y-%m" if group_by == "month" else "%Y-%m-%d")

        where_clauses = ["created_at IS NOT NULL"]
        params = {"fmt": fmt}

        if start_date:
            where_clauses.append("created_at >= :start_date")
            params["start_date"] = start_date
        if end_date:
            where_clauses.append("created_at <= :end_date")
            params["end_date"] = end_date

        seller_clause = ""
        if seller_id:
            seller_clause = f"AND EXISTS (SELECT 1 FROM sj_sub_orders so WHERE so.parent_order_id = {self.TABLE}.id AND so.seller_id = :seller_id)"
            params["seller_id"] = seller_id

        where_sql = " AND ".join(where_clauses)

        sql = text(
            f"""
            SELECT 
                DATE_FORMAT(created_at, :fmt) AS period,
                COALESCE(SUM(total), 0.0) AS sales,
                COUNT(*) AS order_count
            FROM {self.TABLE}
            WHERE {where_sql} {seller_clause}
            GROUP BY period
            ORDER BY period ASC
            """
        )
        async_session = get_async_session_factory()
        async with async_session() as session:
            rows = (await session.execute(sql, params)).fetchall()
            result = []
            for r in rows:
                sales = round(float(r.sales or 0.0), 2)
                cnt = r.order_count or 0
                aov = round(sales / cnt, 2) if cnt > 0 else 0.0
                result.append(
                    SalesOverTimeResponse(
                        period=r.period,
                        sales=sales,
                        orderCount=cnt,
                        aov=aov,
                    )
                )
            return result

    async def get_sales_breakdown_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> SalesBreakdownResponse:
        where_clauses = ["1=1"]
        params = {}

        if start_date:
            where_clauses.append("created_at >= :start_date")
            params["start_date"] = start_date
        if end_date:
            where_clauses.append("created_at <= :end_date")
            params["end_date"] = end_date

        where_sql = " AND ".join(where_clauses)

        sql = text(
            f"""
            SELECT 
                COALESCE(SUM(total), 0.0) AS gross_sales,
                COALESCE(SUM(COALESCE(discount, 0.0)), 0.0) AS discounts,
                COALESCE(SUM(COALESCE(shipping, 0.0)), 0.0) AS shipping_charges,
                COALESCE(SUM(COALESCE(tax, 0.0)), 0.0) AS taxes,
                COALESCE(SUM(CASE WHEN status IN ('returned', 'cancelled') THEN total ELSE 0.0 END), 0.0) AS returns
            FROM {self.TABLE}
            WHERE {where_sql}
            """
        )
        async_session = get_async_session_factory()
        async with async_session() as session:
            r = (await session.execute(sql, params)).fetchone()
            gross = round(float(r.gross_sales or 0.0), 2) if r else 0.0
            discounts = round(float(r.discounts or 0.0), 2) if r else 0.0
            shipping = round(float(r.shipping_charges or 0.0), 2) if r else 0.0
            taxes = round(float(r.taxes or 0.0), 2) if r else 0.0
            returns = round(float(r.returns or 0.0), 2) if r else 0.0
            net = round(gross - discounts - returns, 2)

            return SalesBreakdownResponse(
                gross_sales=gross,
                discounts=discounts,
                returns=returns,
                net_sales=net,
                shipping_charges=shipping,
                return_fees=0.0,
                taxes=taxes,
                total_sales=gross,
            )

    async def get_average_order_value_over_time_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "hour",
    ) -> List[AverageOrderValueResponse]:
        fmt = "%Y-%m-%d %H:00" if group_by == "hour" else ("%Y-%m" if group_by == "month" else "%Y-%m-%d")

        where_clauses = ["created_at IS NOT NULL"]
        params = {"fmt": fmt}

        if start_date:
            where_clauses.append("created_at >= :start_date")
            params["start_date"] = start_date
        if end_date:
            where_clauses.append("created_at <= :end_date")
            params["end_date"] = end_date

        where_sql = " AND ".join(where_clauses)

        sql = text(
            f"""
            SELECT 
                DATE_FORMAT(created_at, :fmt) AS period,
                COALESCE(SUM(total) / COUNT(*), 0.0) AS avg_aov
            FROM {self.TABLE}
            WHERE {where_sql}
            GROUP BY period
            ORDER BY period ASC
            """
        )
        async_session = get_async_session_factory()
        async with async_session() as session:
            rows = (await session.execute(sql, params)).fetchall()
            return [
                AverageOrderValueResponse(
                    period=r.period,
                    average_order_value=round(float(r.avg_aov or 0.0), 2),
                )
                for r in rows
            ]

    async def get_sales_by_channel_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[SalesByChannelResponse]:
        where_clauses = ["1=1"]
        params = {}

        if start_date:
            where_clauses.append("created_at >= :start_date")
            params["start_date"] = start_date
        if end_date:
            where_clauses.append("created_at <= :end_date")
            params["end_date"] = end_date

        where_sql = " AND ".join(where_clauses)

        sql = text(
            f"""
            SELECT COALESCE(SUM(total), 0.0) AS total_sales
            FROM {self.TABLE}
            WHERE {where_sql}
            """
        )
        async_session = get_async_session_factory()
        async with async_session() as session:
            r = (await session.execute(sql, params)).fetchone()
            total_sales = round(float(r.total_sales or 0.0), 2) if r else 0.0

            return [
                SalesByChannelResponse(channel="desktop_web", sales=total_sales),
                SalesByChannelResponse(channel="mobile_web", sales=0.0),
                SalesByChannelResponse(channel="mobile_app", sales=0.0),
            ]

    async def get_sales_by_product_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10,
        seller_id: Optional[str] = None,
    ) -> List[SalesByProductResponse]:
        where_clauses = ["o.status != 'cancelled'"]
        params = {"limit": limit}

        if start_date:
            where_clauses.append("o.created_at >= :start_date")
            params["start_date"] = start_date
        if end_date:
            where_clauses.append("o.created_at <= :end_date")
            params["end_date"] = end_date

        seller_clause = ""
        if seller_id:
            seller_clause = f"AND EXISTS (SELECT 1 FROM sj_sub_orders so WHERE so.parent_order_id = o.id AND so.seller_id = :seller_id)"
            params["seller_id"] = seller_id

        where_sql = " AND ".join(where_clauses)

        sql = text(
            f"""
            SELECT 
                CAST(oi.product_id AS CHAR) AS product_id,
                COALESCE(p.name, 'Unknown Product') AS product_name,
                CAST(COALESCE(SUM(oi.quantity), 0) AS UNSIGNED) AS quantity,
                COALESCE(SUM(oi.price * oi.quantity), 0.0) AS revenue
            FROM {self.ITEMS_TABLE} oi
            JOIN {self.TABLE} o ON o.id = oi.order_id
            LEFT JOIN sj_products p ON p.id = oi.product_id
            WHERE {where_sql} {seller_clause}
            GROUP BY oi.product_id, p.name
            ORDER BY quantity DESC, revenue DESC
            LIMIT :limit
            """
        )
        async_session = get_async_session_factory()
        async with async_session() as session:
            rows = (await session.execute(sql, params)).fetchall()
            return [
                SalesByProductResponse(
                    product_id=r.product_id,
                    name=r.product_name,
                    quantity=r.quantity,
                    revenue=round(float(r.revenue or 0.0), 2),
                )
                for r in rows
            ]

    async def get_conversion_order_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> ConversionOrderStats:
        where_clauses = ["1=1"]
        params = {}
        if start_date:
            where_clauses.append("created_at >= :start_date")
            params["start_date"] = start_date
        if end_date:
            where_clauses.append("created_at <= :end_date")
            params["end_date"] = end_date

        where_sql = " AND ".join(where_clauses)

        sql = text(
            f"""
            SELECT 
                COUNT(*) AS total_orders,
                COUNT(CASE WHEN status != 'cancelled' THEN 1 END) AS non_cancelled_orders,
                COUNT(DISTINCT CASE WHEN status != 'cancelled' AND session_id IS NOT NULL AND session_id != '' THEN session_id END) AS completed_sessions
            FROM {self.TABLE}
            WHERE {where_sql}
            """
        )
        async_session = get_async_session_factory()
        async with async_session() as session:
            r = (await session.execute(sql, params)).fetchone()
            if not r:
                return ConversionOrderStats(total_orders=0, non_cancelled_orders=0, completed_sessions=0)
            return ConversionOrderStats(
                total_orders=r.total_orders or 0,
                non_cancelled_orders=r.non_cancelled_orders or 0,
                completed_sessions=r.completed_sessions or 0,
            )

    async def get_products_sell_through_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10,
        seller_id: Optional[str] = None,
    ) -> List[ProductsSellThroughResponse]:
        where_clauses = ["o.status != 'cancelled'"]
        params = {"limit": limit}

        if start_date:
            where_clauses.append("o.created_at >= :start_date")
            params["start_date"] = start_date
        if end_date:
            where_clauses.append("o.created_at <= :end_date")
            params["end_date"] = end_date

        seller_clause = ""
        if seller_id:
            seller_clause = f"AND EXISTS (SELECT 1 FROM sj_sub_orders so WHERE so.parent_order_id = o.id AND so.seller_id = :seller_id)"
            params["seller_id"] = seller_id

        where_sql = " AND ".join(where_clauses)

        sql = text(
            f"""
            SELECT 
                CAST(p.id AS CHAR) AS product_id,
                p.name AS product_name,
                COALESCE(p.stock, 0) AS stock,
                COALESCE(SUM(oi.quantity), 0) AS sold
            FROM sj_products p
            LEFT JOIN {self.ITEMS_TABLE} oi ON oi.product_id = p.id
            LEFT JOIN {self.TABLE} o ON o.id = oi.order_id AND {where_sql} {seller_clause}
            GROUP BY p.id, p.name, p.stock
            ORDER BY (COALESCE(SUM(oi.quantity), 0) / (COALESCE(p.stock, 0) + COALESCE(SUM(oi.quantity), 0))) DESC
            LIMIT :limit
            """
        )
        async_session = get_async_session_factory()
        async with async_session() as session:
            rows = (await session.execute(sql, params)).fetchall()
            result = []
            for r in rows:
                sold = r.sold or 0
                stock = r.stock or 0
                total_avail = stock + sold
                rate = round((sold / total_avail * 100), 2) if total_avail > 0 else 0.0
                result.append(
                    ProductsSellThroughResponse(
                        product_id=r.product_id,
                        name=r.product_name or "Unknown",
                        sold=sold,
                        stock=stock,
                        sell_through_rate=rate,
                    )
                )
            return result

    async def get_customer_cohort_stats(self) -> List[CustomerCohortResponse]:
        sql = text(
            f"""
            WITH first_orders AS (
                SELECT 
                    user_id,
                    MIN(created_at) AS first_order_date
                FROM {self.TABLE}
                WHERE user_id IS NOT NULL AND created_at IS NOT NULL
                GROUP BY user_id
            ),
            order_months AS (
                SELECT 
                    DATE_FORMAT(fo.first_order_date, '%Y-%m') AS cohort_month,
                    TIMESTAMPDIFF(MONTH, fo.first_order_date, o.created_at) AS month_index
                FROM {self.TABLE} o
                JOIN first_orders fo ON fo.user_id = o.user_id
                WHERE o.created_at >= fo.first_order_date
            )
            SELECT 
                cohort_month,
                month_index,
                COUNT(*) AS order_count
            FROM order_months
            GROUP BY cohort_month, month_index
            ORDER BY cohort_month ASC, month_index ASC
            """
        )
        async_session = get_async_session_factory()
        async with async_session() as session:
            rows = (await session.execute(sql)).fetchall()
            result: List[CustomerCohortResponse] = []
            current_cohort: Optional[str] = None
            current_months: List[int] = []

            for r in rows:
                if r.cohort_month != current_cohort:
                    if current_cohort is not None:
                        result.append(CustomerCohortResponse(cohort=current_cohort, months=current_months))
                    current_cohort = r.cohort_month
                    current_months = []

                while len(current_months) < r.month_index:
                    current_months.append(0)
                current_months.append(r.order_count or 0)

            if current_cohort is not None:
                result.append(CustomerCohortResponse(cohort=current_cohort, months=current_months))

            return result

    async def get_top_users_by_revenue_stats(
        self,
        role: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10,
    ) -> List[TopUsersReportResponse]:
        where_clauses = ["o.user_id IS NOT NULL"]
        params = {"limit": limit}

        if start_date:
            where_clauses.append("o.created_at >= :start_date")
            params["start_date"] = start_date
        if end_date:
            where_clauses.append("o.created_at <= :end_date")
            params["end_date"] = end_date

        role_clause = ""
        if role:
            role_clause = "AND u.role = :role"
            params["role"] = role

        where_sql = " AND ".join(where_clauses)

        sql = text(
            f"""
            SELECT 
                CAST(o.user_id AS CHAR) AS user_id,
                COALESCE(u.name, 'Unknown') AS user_name,
                COALESCE(u.email, 'Unknown') AS user_email,
                COALESCE(u.role, 'customer') AS user_role,
                COALESCE(SUM(o.total), 0.0) AS revenue,
                COUNT(*) AS order_count
            FROM {self.TABLE} o
            JOIN sj_users u ON u.id = o.user_id
            WHERE {where_sql} {role_clause}
            GROUP BY o.user_id, u.name, u.email, u.role
            ORDER BY revenue DESC
            LIMIT :limit
            """
        )
        async_session = get_async_session_factory()
        async with async_session() as session:
            rows = (await session.execute(sql, params)).fetchall()
            return [
                TopUsersReportResponse(
                    userId=r.user_id,
                    name=r.user_name,
                    userName=r.user_name,
                    email=r.user_email,
                    userEmail=r.user_email,
                    role=r.user_role,
                    revenue=round(float(r.revenue or 0.0), 2),
                    orderCount=r.order_count or 0,
                )
                for r in rows
            ]

    async def get_user_order_stats_report(
        self,
        role: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[UserOrderStatsResponse]:
        where_clauses = ["o.user_id IS NOT NULL"]
        params = {}

        if start_date:
            where_clauses.append("o.created_at >= :start_date")
            params["start_date"] = start_date
        if end_date:
            where_clauses.append("o.created_at <= :end_date")
            params["end_date"] = end_date

        role_clause = ""
        if role:
            role_clause = "AND u.role = :role"
            params["role"] = role

        where_sql = " AND ".join(where_clauses)

        sql = text(
            f"""
            SELECT 
                CAST(o.user_id AS CHAR) AS user_id,
                COALESCE(u.name, 'Unknown') AS user_name,
                COALESCE(u.email, 'Unknown') AS user_email,
                COUNT(*) AS total_orders,
                COALESCE(SUM(o.total), 0.0) AS total_revenue,
                CASE 
                    WHEN MAX(o.created_at) IS NOT NULL 
                    THEN GREATEST(0, DATEDIFF(UTC_TIMESTAMP(), MAX(o.created_at)))
                    ELSE NULL 
                END AS days_since_last,
                CASE 
                    WHEN MIN(o.created_at) IS NOT NULL 
                    THEN GREATEST(1, DATEDIFF(UTC_TIMESTAMP(), MIN(o.created_at)))
                    ELSE NULL 
                END AS delta_days
            FROM {self.TABLE} o
            JOIN sj_users u ON u.id = o.user_id
            WHERE {where_sql} {role_clause}
            GROUP BY o.user_id, u.name, u.email
            ORDER BY total_orders DESC
            """
        )
        async_session = get_async_session_factory()
        async with async_session() as session:
            rows = (await session.execute(sql, params)).fetchall()
            result = []
            for r in rows:
                tot_orders = r.total_orders or 0
                tot_rev = float(r.total_revenue or 0.0)
                aov = round(tot_rev / tot_orders, 2) if tot_orders > 0 else 0.0

                days_since_last = r.days_since_last
                avg_orders_per_month = 0.0
                if r.delta_days is not None:
                    months_active = max(1.0, r.delta_days / 30.44)
                    avg_orders_per_month = round(tot_orders / months_active, 2)

                result.append(
                    UserOrderStatsResponse(
                        userId=r.user_id,
                        name=r.user_name,
                        email=r.user_email,
                        totalOrders=tot_orders,
                        averageOrderValue=aov,
                        daysSinceLastOrder=days_since_last,
                        avgOrdersPerMonth=avg_orders_per_month,
                    )
                )
            return result

    async def get_payment_methods_report_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        seller_id: Optional[str] = None,
    ) -> List[PaymentMethodsReportResponse]:
        where_clauses = ["1=1"]
        params = {}

        if start_date:
            where_clauses.append("o.created_at >= :start_date")
            params["start_date"] = start_date
        if end_date:
            where_clauses.append("o.created_at <= :end_date")
            params["end_date"] = end_date

        seller_clause = ""
        if seller_id:
            seller_clause = "AND EXISTS (SELECT 1 FROM sj_sub_orders so WHERE so.parent_order_id = o.id AND so.seller_id = :seller_id)"
            params["seller_id"] = seller_id

        where_sql = " AND ".join(where_clauses)

        sql = text(
            f"""
            SELECT 
                COALESCE(NULLIF(o.payment_method, ''), 'unknown') AS payment_method,
                COUNT(*) AS order_count,
                COALESCE(SUM(o.total), 0.0) AS revenue,
                ROUND(COALESCE(AVG(o.total), 0.0), 2) AS avg_order_value
            FROM {self.TABLE} o
            WHERE {where_sql} {seller_clause}
            GROUP BY COALESCE(NULLIF(o.payment_method, ''), 'unknown')
            ORDER BY revenue DESC
            """
        )
        async_session = get_async_session_factory()
        async with async_session() as session:
            rows = (await session.execute(sql, params)).fetchall()
            return [
                PaymentMethodsReportResponse(
                    paymentMethod=r.payment_method,
                    orderCount=r.order_count,
                    revenue=round(float(r.revenue or 0.0), 2),
                    avgOrderValue=float(r.avg_order_value or 0.0),
                )
                for r in rows
            ]

    async def get_revenue_by_category_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 20,
        seller_id: Optional[str] = None,
    ) -> List[RevenueByCategoryResponse]:
        where_clauses = ["1=1"]
        params = {"limit": limit}

        if start_date:
            where_clauses.append("o.created_at >= :start_date")
            params["start_date"] = start_date
        if end_date:
            where_clauses.append("o.created_at <= :end_date")
            params["end_date"] = end_date

        seller_clause = ""
        if seller_id:
            seller_clause = "AND EXISTS (SELECT 1 FROM sj_sub_orders so WHERE so.parent_order_id = o.id AND so.seller_id = :seller_id)"
            params["seller_id"] = seller_id

        where_sql = " AND ".join(where_clauses)

        sql = text(
            f"""
            SELECT 
                COALESCE(NULLIF(p.category, ''), 'Uncategorized') AS category,
                COUNT(DISTINCT oi.order_id) AS order_count,
                CAST(COALESCE(SUM(oi.quantity), 0) AS UNSIGNED) AS quantity,
                COALESCE(SUM(oi.price * oi.quantity), 0.0) AS revenue
            FROM {self.ITEMS_TABLE} oi
            JOIN {self.TABLE} o ON o.id = oi.order_id
            LEFT JOIN sj_products p ON p.id = oi.product_id
            WHERE {where_sql} {seller_clause}
            GROUP BY COALESCE(NULLIF(p.category, ''), 'Uncategorized')
            ORDER BY revenue DESC
            LIMIT :limit
            """
        )
        async_session = get_async_session_factory()
        async with async_session() as session:
            rows = (await session.execute(sql, params)).fetchall()
            return [
                RevenueByCategoryResponse(
                    category=r.category,
                    orderCount=r.order_count,
                    quantity=r.quantity,
                    revenue=round(float(r.revenue or 0.0), 2),
                )
                for r in rows
            ]

    async def get_fulfillment_time_report_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        seller_id: Optional[str] = None,
    ) -> List[FulfillmentTimeReportResponse]:
        where_clauses = [
            "o.status IN ('delivered', 'completed', 'cancelled', 'returned')",
            "o.created_at IS NOT NULL",
            "o.updated_at IS NOT NULL",
        ]
        params = {}

        if start_date:
            where_clauses.append("o.created_at >= :start_date")
            params["start_date"] = start_date
        if end_date:
            where_clauses.append("o.created_at <= :end_date")
            params["end_date"] = end_date

        seller_clause = ""
        if seller_id:
            seller_clause = "AND EXISTS (SELECT 1 FROM sj_sub_orders so WHERE so.parent_order_id = o.id AND so.seller_id = :seller_id)"
            params["seller_id"] = seller_id

        where_sql = " AND ".join(where_clauses)

        sql = text(
            f"""
            SELECT 
                CAST(o.id AS CHAR) AS order_id,
                COALESCE(o.order_number, '') AS order_number,
                DATE_FORMAT(o.created_at, '%Y-%m-%dT%H:%i:%s') AS created_at,
                o.status AS status,
                COALESCE(o.total, 0.0) AS order_total,
                COALESCE(u.name, 'Unknown') AS user_name,
                ROUND(TIMESTAMPDIFF(SECOND, o.created_at, o.updated_at) / 3600.0, 1) AS fulfillment_hours,
                ROUND(TIMESTAMPDIFF(SECOND, o.created_at, o.updated_at) / 86400.0, 1) AS fulfillment_days
            FROM {self.TABLE} o
            LEFT JOIN sj_users u ON u.id = o.user_id
            WHERE {where_sql} {seller_clause}
              AND TIMESTAMPDIFF(SECOND, o.created_at, o.updated_at) >= 0
            ORDER BY o.created_at DESC
            """
        )
        async_session = get_async_session_factory()
        async with async_session() as session:
            rows = (await session.execute(sql, params)).fetchall()
            return [
                FulfillmentTimeReportResponse(
                    orderId=r.order_id,
                    orderNumber=r.order_number,
                    createdAt=r.created_at,
                    status=r.status,
                    orderTotal=round(float(r.order_total or 0.0), 2),
                    userName=r.user_name,
                    fulfillmentHours=float(r.fulfillment_hours) if r.fulfillment_hours is not None else None,
                    fulfillmentDays=float(r.fulfillment_days) if r.fulfillment_days is not None else None,
                )
                for r in rows
            ]

    async def get_coupon_usage_report_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        seller_id: Optional[str] = None,
    ) -> List[CouponUsageReportResponse]:
        where_clauses = ["so.coupon_code IS NOT NULL", "so.coupon_code != ''"]
        params = {}

        if start_date:
            where_clauses.append("so.created_at >= :start_date")
            params["start_date"] = start_date
        if end_date:
            where_clauses.append("so.created_at <= :end_date")
            params["end_date"] = end_date

        seller_clause = ""
        if seller_id:
            seller_clause = "AND so.seller_id = :seller_id"
            params["seller_id"] = seller_id

        where_sql = " AND ".join(where_clauses)

        sql = text(
            f"""
            SELECT 
                so.coupon_code AS coupon_code,
                COALESCE(so.coupon_info_type, 'percentage') AS discount_type,
                COALESCE(so.coupon_info_value, 0.0) AS discount_value,
                COUNT(*) AS usage_count,
                COALESCE(SUM(so.discount), 0.0) AS total_discount_given,
                COALESCE(SUM(so.total), 0.0) AS total_revenue
            FROM sj_sub_orders so
            WHERE {where_sql} {seller_clause}
            GROUP BY so.coupon_code, so.coupon_info_type, so.coupon_info_value
            ORDER BY usage_count DESC
            """
        )
        async_session = get_async_session_factory()
        async with async_session() as session:
            rows = (await session.execute(sql, params)).fetchall()
            return [
                CouponUsageReportResponse(
                    couponCode=r.coupon_code,
                    discountType=r.discount_type,
                    discountValue=float(r.discount_value or 0.0),
                    usageCount=r.usage_count,
                    totalDiscountGiven=round(float(r.total_discount_given or 0.0), 2),
                    totalRevenue=round(float(r.total_revenue or 0.0), 2),
                )
                for r in rows
            ]

    async def get_sales_by_location_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        seller_id: Optional[str] = None,
    ) -> List[SalesByLocationReportResponse]:
        where_clauses = ["o.status IN ('delivered', 'completed', 'shipped', 'dispatched')"]
        params = {"limit": limit}

        if start_date:
            where_clauses.append("o.created_at >= :start_date")
            params["start_date"] = start_date
        if end_date:
            where_clauses.append("o.created_at <= :end_date")
            params["end_date"] = end_date

        seller_clause = ""
        if seller_id:
            seller_clause = "AND EXISTS (SELECT 1 FROM sj_sub_orders so WHERE so.parent_order_id = o.id AND so.seller_id = :seller_id)"
            params["seller_id"] = seller_id

        where_sql = " AND ".join(where_clauses)

        sql = text(
            f"""
            WITH order_totals AS (
                SELECT 
                    o.id AS order_id,
                    o.total AS total,
                    CASE
                        WHEN (o.ship_city IS NOT NULL AND o.ship_city != '') AND (o.ship_state IS NOT NULL AND o.ship_state != '')
                            THEN CONCAT(TRIM(o.ship_city), ', ', TRIM(o.ship_state))
                        WHEN (o.ship_city IS NOT NULL AND o.ship_city != '')
                            THEN TRIM(o.ship_city)
                        WHEN (o.ship_state IS NOT NULL AND o.ship_state != '')
                            THEN TRIM(o.ship_state)
                        ELSE 'Unknown'
                    END AS location,
                    COALESCE(item_aggs.total_qty, 0) AS total_qty
                FROM {self.TABLE} o
                LEFT JOIN (
                    SELECT order_id, SUM(quantity) AS total_qty
                    FROM {self.ITEMS_TABLE}
                    GROUP BY order_id
                ) item_aggs ON item_aggs.order_id = o.id
                WHERE {where_sql} {seller_clause}
            )
            SELECT 
                location,
                COUNT(*) AS order_count,
                CAST(COALESCE(SUM(total_qty), 0) AS UNSIGNED) AS quantity,
                COALESCE(SUM(total), 0.0) AS revenue
            FROM order_totals
            GROUP BY location
            ORDER BY revenue DESC
            LIMIT :limit
            """
        )
        async_session = get_async_session_factory()
        async with async_session() as session:
            rows = (await session.execute(sql, params)).fetchall()
            return [
                SalesByLocationReportResponse(
                    location=r.location,
                    orderCount=r.order_count,
                    quantity=r.quantity,
                    revenue=round(float(r.revenue or 0.0), 2),
                )
                for r in rows
            ]

















