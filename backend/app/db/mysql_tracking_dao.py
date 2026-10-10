from collections import defaultdict
from typing import Any, List, Optional, Union
import logging
"""
MySQL DAO for sj_tracking. Fully relational with child tables.
"""

import secrets
from datetime import datetime
from app.models.tracking import Tracking
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

    def _row_to_tracking(self, r, cart_items: List[ItemSnippet]) -> Tracking:
        from app.models.tracking import Tracking
        return Tracking(
            id=str(r.id),
            external_id=r.external_id,
            created_at=r.created_at,
            updated_at=r.updated_at,
            type=r.event_type,
            userId=r.user_id,
            sessionId=r.session_id,
            timestamp=r.event_timestamp.isoformat() if r.event_timestamp and not isinstance(r.event_timestamp, str) else str(r.event_timestamp) if r.event_timestamp else None,
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
            cartItems=cart_items
        )

    async def _fetch_children(self, session, ids: List[int]) -> defaultdict[int, List[ItemSnippet]]:
        c_map: defaultdict[int, List[ItemSnippet]] = defaultdict(list)
        if not ids:
            return c_map
        chunks = [ids[i : i + 999] for i in range(0, len(ids), 999)]

        for chunk in chunks:
            chunk_params = {f"tid_{i}": tid for i, tid in enumerate(chunk)}
            placeholders = ", ".join([f":{k}" for k in chunk_params.keys()])

            res = await session.execute(
                text(f"SELECT tracking_id, product_id, quantity, price FROM sj_tracking_cart_items WHERE tracking_id IN ({placeholders})"),
                chunk_params
            )
            for r in res.fetchall():
                c_map[r.tracking_id].append(
                    ItemSnippet(
                        product_id=str(r.product_id),
                        quantity=int(r.quantity or 1),
                        price=float(r.price) if r.price is not None else None,
                    )
                )

        return c_map

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
            c_map = await self._fetch_children(session, [r.id for r in rows])
        return [self._row_to_tracking(r, c_map[r.id]) for r in rows]

    async def find_by_date_range(
        self,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
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
            c_map = await self._fetch_children(session, [r.id for r in rows])
        return [self._row_to_tracking(r, c_map[r.id]) for r in rows]

    async def findOne(
        self,
        id: Optional[Union[int, str]] = None,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Optional['Tracking']:
        docs = await self.findAll(id=id, event_type=event_type, user_id=user_id, session_id=session_id, limit=1)
        return docs[0] if docs else None

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
        if ts is not None and isinstance(ts, str):
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
        # Pydantic update pattern strictly without dicts
        existing = await self.findById(id)
        if not existing:
            return None
        
        # We don't support updating Analytics events strictly, returning None or existing
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


