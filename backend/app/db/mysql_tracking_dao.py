from typing import List, Optional, Union
import logging
"""
MySQL DAO for sj_tracking. Fully relational with child tables.
"""

import secrets
from datetime import datetime
from app.models.tracking import (
    Tracking,
    RecentlyViewedProductItem,
    TopProductItem,
    DropOffPointItem,
    MostSearchedItem,
    ZeroResultSearchItem,
    MostViewedItem,
    MostAbandonedProductItem,
    ReturningUserItem,
)
from app.models.schemas import ItemSnippet

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc

logger = logging.getLogger(__name__)

# Columns that exist directly on sj_tracking (flat scalar fields).
# Removed after table restructure: is_returning, os, browser, ip_address,
# campaign — these fields now live in sj_analytics_sessions (one row per
# analytics session) and are written by MySQLAnalyticsSessionDAO.
_TRACKING_SCALAR = {
    "type": "event_type",
    "userId": "user_id",
    "sessionId": "session_id",
    "timestamp": "event_timestamp",
    "searchTerm": "search_term",
    "resultsCount": "results_count",
    "productId": "product_id",
    "productName": "product_name",
    "segment": "segment",
    "page": "page",
    "reason": "reason",
    "filterType": "filter_type",
    "filterValue": "filter_value",
    "cartValue": "cart_value",
    "source": "source",
    "orderId": "order_id",
    "orderValue": "order_value",
    "price": "price",
    "category": "category",
}



class MySQLTrackingDAO:
    @property
    def TABLE(self):
        return "sj_tracking"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_tracking(self, r, cart_items_rows=None) -> Tracking:
        from app.models.tracking import Tracking
        items = (
            [
                ItemSnippet(
                    product_id=str(ir.product_id),
                    quantity=int(ir.quantity or 1),
                    price=float(ir.price) if ir.price is not None else None,
                )
                for ir in cart_items_rows
                if ir.tracking_id == r.id
            ]
            if cart_items_rows
            else []
        )
        return Tracking(
            id=str(r.id),
            external_id=r.external_id,
            created_at=r.created_at,
            updated_at=r.updated_at,
            type=r.event_type,
            userId=r.user_id,
            sessionId=r.session_id,
            timestamp=r.event_timestamp.isoformat() if r.event_timestamp and type(r.event_timestamp) is not str else str(r.event_timestamp) if r.event_timestamp else None,
            searchTerm=r.search_term,
            resultsCount=int(r.results_count) if r.results_count is not None else None,
            productId=r.product_id,
            productName=r.product_name,
            segment=r.segment,
            page=r.page,
            reason=r.reason,
            filterType=r.filter_type,
            filterValue=r.filter_value,
            cartValue=float(r.cart_value) if r.cart_value is not None else None,
            source=r.source,
            orderId=r.order_id,
            orderValue=float(r.order_value) if r.order_value is not None else None,
            price=float(r.price) if r.price is not None else None,
            category=r.category,
            cartItems=items
        )

    async def _fetch_cart_items(self, session, ids: List[int]):
        if not ids:
            return []
        chunks = [ids[i : i + 999] for i in range(0, len(ids), 999)]
        items_rows = []

        for chunk in chunks:
            chunk_params = {f"tid_{i}": tid for i, tid in enumerate(chunk)}
            placeholders = ", ".join([f":{k}" for k in chunk_params.keys()])

            res = await session.execute(
                text(f"SELECT tracking_id, product_id, quantity, price FROM sj_tracking_cart_items WHERE tracking_id IN ({placeholders})"),
                chunk_params
            )
            items_rows.extend(res.fetchall())

        return items_rows

    async def _replace_children(self, session, tid: int, data: 'CamelBaseModel'):
        await session.execute(text("DELETE FROM sj_tracking_cart_items WHERE tracking_id = :tid"), {"tid": tid})

        cart_items = []
        if data.cartItems is not None:
            cart_items.extend(data.cartItems)

        for item in cart_items:
            await session.execute(
                text("INSERT INTO sj_tracking_cart_items (tracking_id, product_id, quantity, price) VALUES (:tid, :pid, :qty, :prc)"),
                {
                    "tid": tid,
                    "pid": str(item.product_id),
                    "qty": int(item.quantity or 1),
                    "prc": float(item.price) if item.price is not None else None
                }
            )

    async def findAll(
        self,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        product_id: Optional[str] = None,
        id: Optional[Union[int, str]] = None,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List['Tracking']:
        factory = self._factory()
        if not factory:
            return []

        where_clauses = []
        params = {}
        if id is not None:
            where_clauses.append("id = :id")
            params["id"] = int(id) if str(id).isdigit() else -1
        if event_type is not None:
            where_clauses.append("event_type = :event_type")
            params["event_type"] = event_type
        if user_id is not None:
            where_clauses.append("user_id = :user_id")
            params["user_id"] = user_id
        if session_id is not None:
            where_clauses.append("session_id = :session_id")
            params["session_id"] = session_id
        if product_id is not None:
            where_clauses.append("product_id = :product_id")
            params["product_id"] = product_id

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        query_str = f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"
        if limit is not None:
            query_str += f" LIMIT {int(limit)}"
        if skip is not None:
            query_str += f" OFFSET {int(skip)}"
            
        async with factory() as session:
            res = await session.execute(text(query_str), params)
            rows = res.fetchall()
            items_rows = await self._fetch_cart_items(session, [r.id for r in rows])
        return [self._row_to_tracking(r, items_rows) for r in rows]

    async def find_by_date_range(
        self,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        segment: Optional[str] = None,
    ) -> List['Tracking']:
        """Return tracking rows filtered by event_type and/or date range at SQL level.
        Far more efficient than findAll() + Python filtering for analytics queries."""
        factory = self._factory()
        if not factory:
            return []
        where_clauses = []
        params = {}
        if event_type:
            where_clauses.append("event_type = :event_type")
            params["event_type"] = event_type
        if segment:
            where_clauses.append("segment = :segment")
            params["segment"] = str(segment)
        if start_date:
            where_clauses.append("event_timestamp >= :start_date")
            params["start_date"] = start_date
        if end_date:
            where_clauses.append("event_timestamp <= :end_date")
            params["end_date"] = end_date
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        async with factory() as session:
            res = await session.execute(
                text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"),
                params,
            )
            rows = res.fetchall()
            items_rows = await self._fetch_cart_items(session, [r.id for r in rows])
        return [self._row_to_tracking(r, items_rows) for r in rows]

    async def get_recently_viewed_products(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[RecentlyViewedProductItem]:
        factory = self._factory()
        if not factory or (not user_id and not session_id):
            return []
        where_clauses = ["t.event_type = 'product_view'", "t.product_id IS NOT NULL", "t.product_id != ''"]
        params = {"limit": int(limit)}
        if user_id:
            where_clauses.append("t.user_id = :user_id")
            params["user_id"] = str(user_id)
        elif session_id:
            where_clauses.append("t.session_id = :session_id")
            params["session_id"] = str(session_id)
        where_sql = " AND ".join(where_clauses)
        async with factory() as session:
            rows = (
                await session.execute(
                    text(
                        f"SELECT t.product_id, MAX(t.event_timestamp) as latest_ts, "
                        f"COALESCE(MAX(p.name), MAX(t.product_name), '') as product_name, "
                        f"(SELECT pi.image_url FROM sj_product_images pi WHERE pi.product_id = MAX(p.id) ORDER BY pi.order_index ASC LIMIT 1) as display_image, "
                        f"MAX(p.mrp) as price "
                        f"FROM {self.TABLE} t "
                        f"LEFT JOIN sj_products p ON (p.id = t.product_id OR p.external_id = t.product_id) "
                        f"WHERE {where_sql} "
                        f"GROUP BY t.product_id "
                        f"ORDER BY latest_ts DESC LIMIT :limit"
                    ),
                    params,
                )
            ).fetchall()
        return [
            RecentlyViewedProductItem(
                product_id=str(r.product_id),
                product_name=str(r.product_name),
                display_image=str(r.display_image) if r.display_image else None,
                price=float(r.price) if r.price is not None else None,
            )
            for r in rows
        ]

    async def get_recent_user_searches(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[str]:
        factory = self._factory()
        if not factory or (not user_id and not session_id):
            return []
        
        user_filter = "user_id = :user_id" if user_id else "session_id = :session_id"
        u_params = {"user_id": str(user_id)} if user_id else {"session_id": str(session_id)}
        
        async with factory() as session:
            last_cleared = (
                await session.execute(
                    text(f"SELECT MAX(event_timestamp) FROM {self.TABLE} WHERE event_type = 'search_history_clear' AND {user_filter}"),
                    u_params,
                )
            ).scalar()
            
            where_clauses = [
                "event_type = 'product_search'",
                user_filter,
                "search_term IS NOT NULL",
                "TRIM(search_term) != ''",
            ]
            params = {k: v for k, v in u_params.items()}
            params["limit"] = int(limit)
            if last_cleared:
                where_clauses.append("event_timestamp > :last_cleared")
                params["last_cleared"] = last_cleared
            where_sql = " AND ".join(where_clauses)
            rows = (
                await session.execute(
                    text(
                        f"SELECT search_term, MAX(event_timestamp) as latest_ts "
                        f"FROM {self.TABLE} WHERE {where_sql} "
                        f"GROUP BY LOWER(TRIM(search_term)), search_term "
                        f"ORDER BY latest_ts DESC LIMIT :limit"
                    ),
                    params,
                )
            ).fetchall()
        return [str(r.search_term) for r in rows]

    async def get_sessions_count(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        factory = self._factory()
        if not factory:
            return 0
        where_clauses = ["event_type = 'session'"]
        params = {}
        if start_date:
            where_clauses.append("event_timestamp >= :start_date")
            params["start_date"] = start_date
        if end_date:
            where_clauses.append("event_timestamp <= :end_date")
            params["end_date"] = end_date
        where_sql = " AND ".join(where_clauses)
        async with factory() as session:
            count = (
                await session.execute(
                    text(f"SELECT COUNT(*) FROM {self.TABLE} WHERE {where_sql}"),
                    params,
                )
            ).scalar()
        return int(count or 0)

    async def get_top_products(
        self,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[TopProductItem]:
        factory = self._factory()
        if not factory:
            return []
        where_clauses = ["event_type = 'product_view'", "product_id IS NOT NULL", "product_id != ''"]
        params = {"limit": int(limit)}
        if start_date:
            where_clauses.append("event_timestamp >= :start_date")
            params["start_date"] = start_date
        if end_date:
            where_clauses.append("event_timestamp <= :end_date")
            params["end_date"] = end_date
        where_sql = " AND ".join(where_clauses)
        async with factory() as session:
            rows = (
                await session.execute(
                    text(
                        f"SELECT product_id, COALESCE(product_name, 'Unknown') as product_name, COUNT(*) as views "
                        f"FROM {self.TABLE} WHERE {where_sql} "
                        f"GROUP BY product_id, product_name "
                        f"ORDER BY views DESC LIMIT :limit"
                    ),
                    params,
                )
            ).fetchall()
        return [
            TopProductItem(product_id=str(r.product_id), product_name=str(r.product_name), views=int(r.views))
            for r in rows
        ]

    async def get_drop_offs(
        self,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[DropOffPointItem]:
        factory = self._factory()
        if not factory:
            return []
        where_clauses = ["event_type = 'drop_off'", "page IS NOT NULL", "page != ''"]
        params = {"limit": int(limit)}
        if start_date:
            where_clauses.append("event_timestamp >= :start_date")
            params["start_date"] = start_date
        if end_date:
            where_clauses.append("event_timestamp <= :end_date")
            params["end_date"] = end_date
        where_sql = " AND ".join(where_clauses)
        async with factory() as session:
            rows = (
                await session.execute(
                    text(
                        f"SELECT sub.page, CAST(SUM(sub.rcount) AS UNSIGNED) AS total_count, "
                        f"JSON_OBJECTAGG(sub.reason, sub.rcount) AS reasons_json "
                        f"FROM ("
                        f"  SELECT page, COALESCE(reason, 'unspecified') AS reason, COUNT(*) AS rcount "
                        f"  FROM {self.TABLE} "
                        f"  WHERE {where_sql} "
                        f"  GROUP BY page, reason "
                        f") sub "
                        f"GROUP BY sub.page "
                        f"ORDER BY total_count DESC LIMIT :limit"
                    ),
                    params,
                )
            ).fetchall()

        import json
        items: List[DropOffPointItem] = []
        for r in rows:
            reasons_val = r.reasons_json
            if type(reasons_val) is str:
                try:
                    reasons_val = json.loads(reasons_val)
                except Exception:
                    reasons_val = {}
            items.append(
                DropOffPointItem(
                    page=str(r.page),
                    count=int(r.total_count),
                    reasons=reasons_val or {},
                )
            )
        return items

    async def get_most_searched(
        self,
        limit: int = 5,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[MostSearchedItem]:
        factory = self._factory()
        if not factory:
            return []
        where_clauses = ["event_type = 'product_search'", "search_term IS NOT NULL", "TRIM(search_term) != ''"]
        params = {"limit": int(limit)}
        if start_date:
            where_clauses.append("event_timestamp >= :start_date")
            params["start_date"] = start_date
        if end_date:
            where_clauses.append("event_timestamp <= :end_date")
            params["end_date"] = end_date
        where_sql = " AND ".join(where_clauses)
        async with factory() as session:
            rows = (
                await session.execute(
                    text(
                        f"SELECT LOWER(TRIM(search_term)) as term, COUNT(*) as count, "
                        f"ROUND(AVG(COALESCE(results_count, 0)), 1) as avg_results "
                        f"FROM {self.TABLE} WHERE {where_sql} "
                        f"GROUP BY LOWER(TRIM(search_term)) "
                        f"ORDER BY count DESC LIMIT :limit"
                    ),
                    params,
                )
            ).fetchall()
        return [
            MostSearchedItem(term=str(r.term), count=int(r.count), avg_products_found=float(r.avg_results or 0.0))
            for r in rows
        ]

    async def get_zero_result_searches(
        self,
        limit: int = 50,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[ZeroResultSearchItem]:
        factory = self._factory()
        if not factory:
            return []
        where_clauses = [
            "event_type = 'product_search'",
            "search_term IS NOT NULL",
            "TRIM(search_term) != ''",
            "COALESCE(results_count, 0) = 0",
        ]
        params = {"limit": int(limit)}
        if start_date:
            where_clauses.append("event_timestamp >= :start_date")
            params["start_date"] = start_date
        if end_date:
            where_clauses.append("event_timestamp <= :end_date")
            params["end_date"] = end_date
        where_sql = " AND ".join(where_clauses)
        async with factory() as session:
            rows = (
                await session.execute(
                    text(
                        f"SELECT LOWER(TRIM(search_term)) as term, COUNT(*) as count "
                        f"FROM {self.TABLE} WHERE {where_sql} "
                        f"GROUP BY LOWER(TRIM(search_term)) "
                        f"ORDER BY count DESC LIMIT :limit"
                    ),
                    params,
                )
            ).fetchall()
        return [
            ZeroResultSearchItem(term=str(r.term), count=int(r.count))
            for r in rows
        ]

    async def get_most_viewed(
        self,
        limit: int = 5,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[MostViewedItem]:
        factory = self._factory()
        if not factory:
            return []
        where_clauses = ["event_type = 'product_view'", "product_id IS NOT NULL", "product_id != ''"]
        params = {"limit": int(limit)}
        if start_date:
            where_clauses.append("event_timestamp >= :start_date")
            params["start_date"] = start_date
        if end_date:
            where_clauses.append("event_timestamp <= :end_date")
            params["end_date"] = end_date
        where_sql = " AND ".join(where_clauses)
        async with factory() as session:
            rows = (
                await session.execute(
                    text(
                        f"SELECT product_id, COALESCE(product_name, 'Unknown') as product_name, COUNT(*) as count "
                        f"FROM {self.TABLE} WHERE {where_sql} "
                        f"GROUP BY product_id, product_name "
                        f"ORDER BY count DESC LIMIT :limit"
                    ),
                    params,
                )
            ).fetchall()
        return [
            MostViewedItem(product_id=str(r.product_id), product_name=str(r.product_name), count=int(r.count))
            for r in rows
        ]

    async def get_cart_abandonments(
        self,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List['Tracking']:
        factory = self._factory()
        if not factory:
            return []
        where_clauses = ["event_type = 'cart_abandonment'"]
        params = {"limit": int(limit)}
        if start_date:
            where_clauses.append("event_timestamp >= :start_date")
            params["start_date"] = start_date
        if end_date:
            where_clauses.append("event_timestamp <= :end_date")
            params["end_date"] = end_date
        where_sql = " AND ".join(where_clauses)
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY event_timestamp DESC, id DESC LIMIT :limit"),
                    params,
                )
            ).fetchall()
            items_rows = await self._fetch_cart_items(session, [r.id for r in rows])
        return [self._row_to_tracking(r, items_rows) for r in rows]

    async def get_most_abandoned_products(
        self,
        limit: int = 50,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[MostAbandonedProductItem]:
        factory = self._factory()
        if not factory:
            return []
        where_clauses = ["t.event_type = 'cart_abandonment'", "ci.product_id IS NOT NULL", "ci.product_id != ''"]
        params = {"limit": int(limit)}
        if start_date:
            where_clauses.append("t.event_timestamp >= :start_date")
            params["start_date"] = start_date
        if end_date:
            where_clauses.append("t.event_timestamp <= :end_date")
            params["end_date"] = end_date
        where_sql = " AND ".join(where_clauses)
        async with factory() as session:
            rows = (
                await session.execute(
                    text(
                        f"""
                        SELECT 
                            ci.product_id,
                            COALESCE(MAX(p.name), 'Unknown') as product_name,
                            COALESCE(MAX(p.category), 'Uncategorized') as category,
                            COUNT(DISTINCT ci.tracking_id) as abandon_count,
                            SUM(COALESCE(ci.quantity, 1)) as quantity_abandoned,
                            SUM(COALESCE(ci.quantity, 1) * COALESCE(ci.price, 0)) as value_lost
                        FROM sj_tracking_cart_items ci
                        JOIN {self.TABLE} t ON t.id = ci.tracking_id
                        LEFT JOIN sj_products p ON (p.id = ci.product_id OR p.external_id = ci.product_id)
                        WHERE {where_sql}
                        GROUP BY ci.product_id
                        ORDER BY abandon_count DESC LIMIT :limit
                        """
                    ),
                    params,
                )
            ).fetchall()

        return [
            MostAbandonedProductItem(
                product_id=str(r.product_id),
                product_name=str(r.product_name),
                category=str(r.category),
                abandon_count=int(r.abandon_count),
                quantity_abandoned=int(r.quantity_abandoned or 0),
                value_lost=round(float(r.value_lost or 0.0), 2),
            )
            for r in rows
        ]

    async def get_returning_user_ids(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[ReturningUserItem]:
        factory = self._factory()
        if not factory:
            return []
        where_clauses = ["user_id IS NOT NULL", "user_id != ''"]
        params = {}
        if start_date:
            where_clauses.append("start_time >= :start_date")
            params["start_date"] = start_date
        if end_date:
            where_clauses.append("start_time <= :end_date")
            params["end_date"] = end_date
        where_sql = " AND ".join(where_clauses)
        async with factory() as session:
            rows = (
                await session.execute(
                    text(
                        f"SELECT user_id, MAX(start_time) as last_seen "
                        f"FROM sj_analytics_sessions WHERE {where_sql} "
                        f"GROUP BY user_id HAVING COUNT(*) > 1"
                    ),
                    params,
                )
            ).fetchall()
        return [
            ReturningUserItem(
                user_id=str(r.user_id),
                name="",
                email="",
                last_seen=r.last_seen.isoformat() if r.last_seen and type(r.last_seen) is not str else str(r.last_seen or ""),
            )
            for r in rows
        ]

    async def findOne(
        self,
        id: Optional[Union[int, str]] = None,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Optional['Tracking']:
        records = await self.findAll(id=id, event_type=event_type, user_id=user_id, session_id=session_id, limit=1)
        return records[0] if records else None

    async def findById(self, id: str) -> Optional['Tracking']:
        return await self.findOne(id=id)

    async def create(self, data: 'AnalyticsEventCreate') -> 'AnalyticsEvent':
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        params = {"eid": external_id, "c": now, "u": now}
        extracted_keys = []

        def add_col(api_key, db_col, val):
            if val is not None:
                cols.append(db_col)
                params[f"s_{api_key}"] = val
                extracted_keys.append(api_key)

        payload = data.payload

        add_col("type", "event_type", data.type)
        add_col("user_id", "user_id", data.user_id)
        add_col("session_id", "session_id", data.session_id)
        
        ts = data.timestamp
        if ts is not None and type(ts) is str:
            try:
                from datetime import datetime
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                logger.warning("Tracking event has unparseable timestamp %r; storing raw string.", ts, exc_info=True)
        add_col("timestamp", "event_timestamp", ts)
        
        add_col("search_term", "search_term", data.search_term)
        add_col("results_count", "results_count", data.results_count)
        add_col("product_id", "product_id", data.product_id)
        add_col("product_name", "product_name", data.product_name)
        add_col("segment", "segment", data.segment)
        add_col("page", "page", data.page)
        add_col("reason", "reason", data.reason)
        add_col("cart_value", "cart_value", data.cart_value)

        def get_payload_extra(key):
            if payload and payload.model_extra and key in payload.model_extra:
                return payload.model_extra[key]
            return None

        add_col("source", "source", data.source if data.source is not None else get_payload_extra("source"))
        
        filter_type = data.filter_name if data.filter_name is not None else get_payload_extra("filterType")
        add_col("filter_type", "filter_type", filter_type)
        
        add_col("filter_value", "filter_value", data.filter_value if data.filter_value is not None else get_payload_extra("filter_value"))
        add_col("order_id", "order_id", data.order_id if data.order_id is not None else get_payload_extra("order_id"))
        add_col("order_value", "order_value", data.order_value if data.order_value is not None else get_payload_extra("order_value"))
        add_col("price", "price", data.price if data.price is not None else get_payload_extra("price"))
        add_col("category", "category", data.category if data.category is not None else get_payload_extra("category"))

        col_sql = ", ".join(cols)
        val_sql = ", ".join([":eid", ":c", ":u"] + [f":s_{k}" for k in extracted_keys])

        async with factory() as session:
            from sqlalchemy import text
            await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = (
                await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": external_id}
                )
            ).scalar()
            await self._replace_children(session, new_id, data)
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, data: 'AnalyticsEventUpdate') -> Optional['AnalyticsEvent']:
        existing = await self.findById(id)
        if not existing:
            return None
        
        return existing

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        async with factory() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"), {"id": int(id) if str(id).isdigit() else None}
            )
            await session.commit()
            return res.rowcount > 0

    async def deleteMany(
        self,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> int:
        from sqlalchemy import text

        factory = self._factory()
        where_clauses = []
        params = {}
        if event_type is not None:
            where_clauses.append("event_type = :event_type")
            params["event_type"] = event_type
        if user_id is not None:
            where_clauses.append("user_id = :user_id")
            params["user_id"] = user_id
        if session_id is not None:
            where_clauses.append("session_id = :session_id")
            params["session_id"] = session_id

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        async with factory() as session:
            res = await session.execute(text(f"DELETE FROM {self.TABLE} WHERE {where_sql}"), params)
            await session.commit()
            return res.rowcount


