from typing import Any
import logging
"""
MySQL DAO for sj_tracking. Fully relational with child tables.
"""

import secrets
from datetime import datetime
from typing import Dict
from app.models.tracking import Tracking, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc

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
    "isReturning": "is_returning",
    "source": "source",
    "campaign": "campaign",
    "os": "os",
    "browser": "browser",
    "ipAddress": "ip_address",
    "pageViews": "page_views",
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

    def _row_to_tracking(self, r, children) -> Tracking:
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
            isReturning=bool(r.is_returning) if r.is_returning is not None else None,
            source=r.source,
            campaign=r.campaign,
            os=r.os,
            browser=r.browser,
            ipAddress=r.ip_address,
            pageViews=int(r.page_views) if r.page_views is not None else None,
            orderId=r.order_id,
            orderValue=float(r.order_value) if r.order_value is not None else None,
            price=float(r.price) if r.price is not None else None,
            category=r.category,
            product_ids=children["product_ids"] if "product_ids" in children else [],
            payload={},
            cartItems=children["cartItems"] if "cartItems" in children else []
        )

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:
        c_map = {rid: {"product_ids": []} for rid in ids}
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
                if "cartItems" not in c_map[r.tracking_id]:
                    c_map[r.tracking_id]["cartItems"] = []
                c_map[r.tracking_id]["cartItems"].append({"productId": r.product_id, "quantity": r.quantity, "price": r.price})

        for chunk in chunks:
            chunk_params = {f"id_{i}": cid for i, cid in enumerate(chunk)}
            placeholders = ", ".join([f":{k}" for k in chunk_params.keys()])

            p_res = await session.execute(
                text(f"SELECT tracking_id, product_id FROM sj_tracking_products WHERE tracking_id IN ({placeholders})"),
                chunk_params,
            )
            for r in p_res.fetchall():
                c_map[r.tracking_id]["product_ids"].append(r.product_id)

        return c_map

    async def _replace_children(self, session, tid: int, data: 'Any'):
        await session.execute(text("DELETE FROM sj_tracking_products WHERE tracking_id = :tid"), {"tid": tid})
        await session.execute(text("DELETE FROM sj_tracking_cart_items WHERE tracking_id = :tid"), {"tid": tid})

        cart_items = []
        if data.cartItems is not None:
            cart_items.extend(data.cartItems)
        
        # Extract from payload if nested, to avoid stringifying array of objects
        payload = data.payload
        payload = payload.copy() if payload else {}
        if "cartItems" in payload:
            cart_items.extend(payload.pop("cartItems"))

        for item in cart_items:
            item_dict = item
            await session.execute(
                text("INSERT INTO sj_tracking_cart_items (tracking_id, product_id, quantity, price) VALUES (:tid, :pid, :qty, :prc)"),
                {
                    "tid": tid, 
                    "pid": str(item_dict.productId), 
                    "qty": int(item_dict.quantity or 1),
                    "prc": float(item_dict.price) if item_dict.price is not None else None
                }
            )

        if data.productIds is not None:
            for pid in data.productIds:
                await session.execute(
                    text("INSERT INTO sj_tracking_products (tracking_id, product_id) VALUES (:tid, :pid)"),
                    {"tid": tid, "pid": str(pid)},
                )

    async def findAll(self, query: Optional[Dict] = None, skip: Optional[int] = None, limit: Optional[int] = None) -> Any:
        factory = self._factory()
        if not factory:
            return []

        where_clauses = []
        params = {}
        if query:
            for k, v in query.items():
                if k in ("_id", "id"):
                    where_clauses.append("id = :id")
                    params["id"] = int(v) if str(v).isdigit() else None
                elif k in _TRACKING_SCALAR:
                    where_clauses.append(f"{_TRACKING_SCALAR[k]} = :{k}")
                    params[k] = v

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

    async def findOne(self, query: Any) -> Any:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Any:
        return await self.findOne({"_id": id})

    async def create(self, data: 'Any') -> Any:
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
        add_col("userId", "user_id", data.userId)
        add_col("sessionId", "session_id", data.sessionId)
        
        ts = data.timestamp
        if ts is not None and isinstance(ts, str):
            try:
                from datetime import datetime
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                pass
        add_col("timestamp", "event_timestamp", ts)
        
        add_col("searchTerm", "search_term", data.searchTerm)
        add_col("resultsCount", "results_count", data.resultsCount)
        add_col("productId", "product_id", data.productId)
        add_col("productName", "product_name", data.productName)
        add_col("segment", "segment", data.segment)
        add_col("page", "page", data.page)
        add_col("reason", "reason", data.reason)
        add_col("cartValue", "cart_value", data.cartValue)
        add_col("isReturning", "is_returning", data.isReturning)

        def get_payload_extra(key):
            if payload and payload.model_extra and key in payload.model_extra:
                return payload.model_extra[key]
            return None

        # we use python hasattr instead of getattr to enforce the rule
        add_col("source", "source", data.source if data.source is not None else get_payload_extra("source"))
        
        filter_type = data.filterName if data.filterName is not None else get_payload_extra("filterType")
        add_col("filterType", "filter_type", filter_type)
        
        add_col("filterValue", "filter_value", data.filterValue if data.filterValue is not None else get_payload_extra("filterValue"))
        add_col("campaign", "campaign", data.campaign if data.campaign is not None else get_payload_extra("campaign"))
        add_col("os", "os", data.os if data.os is not None else get_payload_extra("os"))
        add_col("browser", "browser", data.browser if data.browser is not None else get_payload_extra("browser"))
        add_col("ipAddress", "ip_address", data.ipAddress if data.ipAddress is not None else get_payload_extra("ipAddress"))
        add_col("pageViews", "page_views", data.pageViews if data.pageViews is not None else get_payload_extra("pageViews"))
        add_col("orderId", "order_id", data.orderId if data.orderId is not None else get_payload_extra("orderId"))
        add_col("orderValue", "order_value", data.orderValue if data.orderValue is not None else get_payload_extra("orderValue"))
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

    async def update(self, id: str, data: 'Any') -> Any:
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

    async def deleteMany(self, query: Any) -> int:
        from sqlalchemy import text

        factory = self._factory()
        where_clauses = []
        params = {}
        for k, v in query.items():
            if k in _TRACKING_SCALAR:
                where_clauses.append(f"{_TRACKING_SCALAR[k]} = :{k}")
                params[k] = v
            elif k in ("_id", "id"):
                where_clauses.append("id = :id")
                params["id"] = int(v) if str(v).isdigit() else None
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        async with factory() as session:
            res = await session.execute(text(f"DELETE FROM {self.TABLE} WHERE {where_sql}"), params)
            await session.commit()
            return res.rowcount
