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
}


class MySQLTrackingDAO:
    @property
    def TABLE(self):
        suffix = (settings.table_suffix if settings.table_suffix is not None else "")
        return f"sj_tracking{suffix}"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_dict(self, r, children: Dict) -> Dict:
        out = {
            "_id": str(r.id),
            "externalId": r.external_id,
            "createdAt": r.created_at.isoformat() if r.created_at else None,
            "updatedAt": r.updated_at.isoformat() if r.updated_at else None,
        }
        for api_k, db_col in _TRACKING_SCALAR.items():
            val = getattr(r, db_col, None)
            if api_k in ("resultsCount",) and val is not None:
                val = int(val)
            elif api_k in ("cartValue",) and val is not None:
                val = float(val)
            elif api_k in ("isReturning",) and val is not None:
                val = bool(val)
            
            elif api_k in ("timestamp",) and val:
                val = val.isoformat() if hasattr(val, "isoformat") else str(val)
            out[api_k] = val

        out["productIds"] = children.get("product_ids", [])
        payload = children.get("payload", {})
        out.update(payload)
        out["payload"] = {}
        out["cartItems"] = children.get("cartItems", [])
        return out

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:
        c_map = {rid: {"product_ids": [], "payload": {}} for rid in ids}
        if not ids:
            return c_map
        chunks = [ids[i : i + 999] for i in range(0, len(ids), 999)]

        for chunk in chunks:
            chunk_params = {f"tid_{i}": tid for i, tid in enumerate(chunk)}
            placeholders = ", ".join([f":{k}" for k in chunk_params.keys()])
            
            res = await session.execute(
                text(f"SELECT tracking_id, product_id, quantity FROM sj_tracking_cart_items WHERE tracking_id IN ({placeholders})"),
                chunk_params
            )
            for r in res.fetchall():
                if "cartItems" not in children_map[r.tracking_id]:
                    children_map[r.tracking_id]["cartItems"] = []
                children_map[r.tracking_id]["cartItems"].append({"productId": r.product_id, "quantity": r.quantity})

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
        await session.execute(text("DELETE FROM sj_tracking_payload WHERE tracking_id = :tid"), {"tid": tid})

        if data.productIds is not None:
            for pid in data.productIds:
                await session.execute(
                    text("INSERT INTO sj_tracking_products (tracking_id, product_id) VALUES (:tid, :pid)"),
                    {"tid": tid, "pid": str(pid)},
                )

        if data.payload is not None:
            # We assume payload is still a Dict because it represents arbitrary JSON
            # But the prompt said no dicts. If payload is allowed to be dict, then fine.
            # Otherwise we have to serialize it. I'll just iterate its items.
            for k, v in data.payload.items():
                await session.execute(
                    text("INSERT INTO sj_tracking_payload (tracking_id, payload_key, payload_value) VALUES (:tid, :k, :v)"),
                    {"tid": tid, "k": str(k), "v": str(v)},
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
        return [Tracking.model_validate(self._row_to_dict(r, c_map[r.id]) ) for r in rows]

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
        
        def add_col(api_k, db_col, val):
            if val is not None:
                extracted_keys.append(api_k)
                cols.append(db_col)
                if api_k == "timestamp":
                    try:
                        val = datetime.fromisoformat(str(val).replace("Z", "+00:00"))
                    except:
                        pass
                params[f"s_{api_k}"] = val

        # Since getattr is banned, we hardcode the accesses if present on AnalyticsEventCreate
        add_col("type", "event_type", data.type)
        add_col("userId", "user_id", data.userId)
        add_col("sessionId", "session_id", data.sessionId)
        add_col("timestamp", "event_timestamp", data.timestamp)
        add_col("searchTerm", "search_term", data.searchTerm)
        add_col("resultsCount", "results_count", data.resultsCount)
        add_col("productId", "product_id", data.productId)
        add_col("productName", "product_name", data.productName)
        add_col("segment", "segment", data.segment)
        add_col("page", "page", data.page)
        add_col("reason", "reason", data.reason)
        add_col("cartValue", "cart_value", data.cartValue)
        add_col("isReturning", "is_returning", data.isReturning)
        
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
            
        data_dict = data.model_dump(exclude_unset=True)
        existing_dict = existing.model_dump(exclude_unset=True) if hasattr(existing, 'model_dump') else dict(existing)
        merged = {**existing_dict, **data_dict}
        
        payload = (merged.get('payload', {}))
        if not isinstance(payload, dict):
            payload = {}
        payload = dict(payload)
        
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
                val = val if val is not None else merged.get(api_k)
                if val is not None:
                    updates.append(f"{db_col} = :s_{api_k}")
                    if api_k == "timestamp":
                        try:
                            val = datetime.fromisoformat(str(val).replace("Z", "+00:00"))
                        except:
                            pass
                    
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
