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
        suffix = (settings.table_suffix if settings.table_suffix is not None else "")
        return f"sj_tracking{suffix}"

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
            pageViews=int(r.page_views) if getattr(r, 'page_views', None) is not None else None,
            orderId=getattr(r, 'order_id', None),
            orderValue=float(r.order_value) if getattr(r, 'order_value', None) is not None else None,
            price=float(r.price) if getattr(r, 'price', None) is not None else None,
            category=getattr(r, 'category', None),
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
        if getattr(data, "cartItems", None) is not None:
            cart_items.extend(data.cartItems)
        
        # Extract from payload if nested, to avoid stringifying array of objects
        payload = getattr(data, "payload", {})
        payload = payload.copy() if payload else {}
        if "cartItems" in payload:
            cart_items.extend(payload.pop("cartItems"))

        for item in cart_items:
            item_dict = item if isinstance(item, dict) else item.__dict__
            await session.execute(
                text("INSERT INTO sj_tracking_cart_items (tracking_id, product_id, quantity, price) VALUES (:tid, :pid, :qty, :prc)"),
                {
                    "tid": tid, 
                    "pid": str(item_dict.get("productId")), 
                    "qty": int(item_dict.get("quantity", 1)),
                    "prc": float(item_dict.get("price")) if item_dict.get("price") is not None else None
                }
            )

        if data.productIds is not None:
            for pid in data.productIds:
                await session.execute(
                    text("INSERT INTO sj_tracking_products (tracking_id, product_id) VALUES (:tid, :pid)"),
                    {"tid": tid, "pid": str(pid)},
                )

    async def findAll(self, query: Optional[Dict] = None, skip: Optional[int] = None, limit: Optional[int] = None) -> List[Dict]:
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

    async def findOne(self, query: Dict) -> Optional[Dict]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        return await self.findOne({"_id": id})

    async def create(self, data: 'Any') -> Dict:
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)

        cols = ["external_id", "created_at", "updated_at"]
        params = {"eid": external_id, "c": now, "u": now}
        
        extracted_keys = []
        payload = getattr(data, "payload", {}) or {}
        if isinstance(payload, str):
            import json
            try: payload = json.loads(payload)
            except: payload = {}
        
        def add_col(api_k, db_col, val):
            if val is not None:
                extracted_keys.append(api_k)
                cols.append(db_col)
                if api_k == "timestamp":
                    try:
                        val = datetime.fromisoformat(str(val).replace("Z", "+00:00"))
                    except Exception as e:
                        import logging
                        logging.warning('Background task failed', exc_info=e)
                params[f"s_{api_k}"] = val

        # Since getattr is banned, we hardcode the accesses if present on AnalyticsEventCreate
        add_col("type", "event_type", getattr(data, 'type', None))
        add_col("userId", "user_id", getattr(data, 'userId', None))
        add_col("sessionId", "session_id", getattr(data, 'sessionId', None))
        add_col("timestamp", "event_timestamp", getattr(data, 'timestamp', None))
        add_col("searchTerm", "search_term", getattr(data, 'searchTerm', None))
        add_col("resultsCount", "results_count", getattr(data, 'resultsCount', None))
        add_col("productId", "product_id", getattr(data, 'productId', None))
        add_col("productName", "product_name", getattr(data, 'productName', None))
        add_col("segment", "segment", getattr(data, 'segment', None))
        add_col("page", "page", getattr(data, 'page', None))
        add_col("reason", "reason", getattr(data, 'reason', None))
        add_col("cartValue", "cart_value", getattr(data, 'cartValue', None))
        add_col("isReturning", "is_returning", getattr(data, 'isReturning', None))
        
        # ADDING MISSING COLUMNS WITHOUT hasattr
        add_col("source", "source", getattr(data, 'source', None) or payload.get('source'))
        # filterName and filterValue were passed to AnalyticsEventCreate
        add_col("filterType", "filter_type", getattr(data, 'filterName', None) or getattr(data, 'filterType', None) or payload.get('filterType'))
        add_col("filterValue", "filter_value", getattr(data, 'filterValue', None) or payload.get('filterValue'))
        add_col("campaign", "campaign", getattr(data, 'campaign', None) or payload.get('campaign'))
        add_col("os", "os", getattr(data, 'os', None) or payload.get('os'))
        add_col("browser", "browser", getattr(data, 'browser', None) or payload.get('browser'))
        add_col("ipAddress", "ip_address", getattr(data, 'ipAddress', None) or payload.get('ipAddress'))
        add_col("pageViews", "page_views", getattr(data, 'pageViews', None) or payload.get('pageViews'))
        add_col("orderId", "order_id", getattr(data, 'orderId', None) or payload.get('orderId'))
        add_col("orderValue", "order_value", getattr(data, 'orderValue', None) or payload.get('orderValue'))
        add_col("price", "price", getattr(data, 'price', None) or payload.get('price'))
        add_col("category", "category", getattr(data, 'category', None) or payload.get('category'))

        
        col_sql = ", ".join(cols)
        val_sql = ", ".join([":eid", ":c", ":u"] + [f":s_{k}" for k in extracted_keys])

        async with factory() as session:
            await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = (
                await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": external_id}
                )
            ).scalar()
            await self._replace_children(session, new_id, data)
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, data: 'Any') -> Optional[Dict]:
        existing = await self.findById(id)
        if not existing:
            return None
            
        data_dict = {}
        for field in data.model_fields_set:
            if field == "type": data_dict["type"] = data.type
            elif field == "userId": data_dict["userId"] = data.userId
            elif field == "sessionId": data_dict["sessionId"] = data.sessionId
            elif field == "timestamp": data_dict["timestamp"] = data.timestamp
            elif field == "searchTerm": data_dict["searchTerm"] = data.searchTerm
            elif field == "resultsCount": data_dict["resultsCount"] = data.resultsCount
            elif field == "productId": data_dict["productId"] = data.productId
            elif field == "productName": data_dict["productName"] = data.productName
            elif field == "segment": data_dict["segment"] = data.segment
            elif field == "page": data_dict["page"] = data.page
            elif field == "reason": data_dict["reason"] = data.reason
            elif field == "cartValue": data_dict["cartValue"] = data.cartValue
            elif field == "isReturning": data_dict["isReturning"] = data.isReturning
            elif field == "source": data_dict["source"] = data.source
            elif field == "filterName": data_dict["filterName"] = data.filterName
            elif field == "filterValue": data_dict["filterValue"] = data.filterValue
            elif field == "campaign": data_dict["campaign"] = getattr(data, "campaign", None)
            elif field == "os": data_dict["os"] = getattr(data, "os", None)
            elif field == "browser": data_dict["browser"] = getattr(data, "browser", None)
            elif field == "ipAddress": data_dict["ipAddress"] = getattr(data, "ipAddress", None)
            elif field == "pageViews": data_dict["pageViews"] = getattr(data, "pageViews", None)
            elif field == "orderId": data_dict["orderId"] = getattr(data, "orderId", None)
            elif field == "orderValue": data_dict["orderValue"] = getattr(data, "orderValue", None)
            elif field == "price": data_dict["price"] = getattr(data, "price", None)
            elif field == "category": data_dict["category"] = getattr(data, "category", None)
            elif field == "payload":
                payload_dict = getattr(data, "payload", {}) or {}
                if "campaign" in payload_dict: data_dict["campaign"] = payload_dict["campaign"]
                if "os" in payload_dict: data_dict["os"] = payload_dict["os"]
                if "browser" in payload_dict: data_dict["browser"] = payload_dict["browser"]
                if "ipAddress" in payload_dict: data_dict["ipAddress"] = payload_dict["ipAddress"]
                if "pageViews" in payload_dict: data_dict["pageViews"] = payload_dict["pageViews"]
                if "orderId" in payload_dict: data_dict["orderId"] = payload_dict["orderId"]
                if "orderValue" in payload_dict: data_dict["orderValue"] = payload_dict["orderValue"]
                if "price" in payload_dict: data_dict["price"] = payload_dict["price"]
                if "category" in payload_dict: data_dict["category"] = payload_dict["category"]
            elif field == "productIds": data_dict["productIds"] = data.productIds
        
        existing_dict = {**existing}
        merged = {**existing_dict, **data_dict}
        
        payload = ((merged['payload'] if 'payload' in merged else {}))
        if not isinstance(payload, dict):
            payload = {}
        payload = {k: v for k, v in payload.items()}
        
        now = now_utc()

        updates = ["updated_at = :u"]
        params = {"id": int(id) if str(id).isdigit() else None, "u": now}
        
        for api_k, db_col in _TRACKING_SCALAR.items():
            val = None
            if api_k in merged and api_k in data_dict: # Only update if explicitly sent, or just use merged
                val = merged[api_k]
            elif api_k in payload:
                val = payload.pop(api_k)
                
            if val is not None or api_k in merged: # Just use the merged value unconditionally like before
                # Wait, if we pop from payload, we should set it
                val = val if val is not None else (merged[api_k] if api_k in merged else None)
                if val is not None:
                    updates.append(f"{db_col} = :s_{api_k}")
                    if api_k == "timestamp":
                        try:
                            val = datetime.fromisoformat(str(val).replace("Z", "+00:00"))
                        except Exception as e:
                            logging.warning("Background task failed", exc_info=e)
                    
                    params[f"s_{api_k}"] = val

        set_sql = ", ".join(updates)
        new_data = {**merged, "payload": payload}

        factory = self._factory()
        async with factory() as session:
            await session.execute(text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"), params)
            await self._replace_children(session, int(id) if str(id).isdigit() else None, new_data)
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        async with factory() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"), {"id": int(id) if str(id).isdigit() else None}
            )
            await session.commit()
            return res.rowcount > 0

    async def deleteMany(self, query: Dict) -> int:
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
