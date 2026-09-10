"""
Oracle DAO for sj_tracking. Parent-only: fixed columns + product_ids JSON + payload JSON.
No child table. Implements storage interface for tracking repository.
"""

from app.config.settings import settings
import secrets
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.oracle_utils import json_dumps, json_loads, now_utc

# API key -> column name (scalars)
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
    "source": "source",
    "cartValue": "cart_value",
}
# API key -> column name (JSON, array or object)
_TRACKING_CLOB = {
    "productIds": "product_ids",
    "payload": "payload",
}


def _row_to_dict(r) -> Dict:
    out = {"_id": str(r.id)}
    # scalar columns -> api keys
    rev = {v: k for k, v in _TRACKING_SCALAR.items()}
    for col, api_key in rev.items():
        val = getattr(r, col, None)
        if val is None:
            continue
        if hasattr(val, "isoformat"):
            out[api_key] = val.isoformat()
        else:
            out[api_key] = val
    # timestamp: repo expects "timestamp"
    if hasattr(r, "event_timestamp") and r.event_timestamp:
        out["timestamp"] = r.event_timestamp.isoformat()
    # JSON columns
    if hasattr(r, "product_ids") and r.product_ids:
        out["productIds"] = json_loads(r.product_ids) or []
    if hasattr(r, "payload") and r.payload:
        payload = json_loads(r.payload)
        if isinstance(payload, dict):
            out.update(payload)
    # created_at, updated_at
    if r.created_at:
        out["createdAt"] = r.created_at.isoformat()
    if r.updated_at:
        out["updatedAt"] = r.updated_at.isoformat()
    return out


def _doc_to_params(data: Dict, now: datetime) -> Dict:
    params = {
        "external_id": secrets.token_hex(16),
        "created_at": now,
        "updated_at": now,
    }
    payload_extra = {}
    for api_key, col in _TRACKING_SCALAR.items():
        val = data.get(api_key)
        if api_key == "timestamp":
            if val:
                try:
                    params["event_timestamp"] = datetime.fromisoformat(str(val).replace("Z", "+00:00"))
                except Exception:
                    params["event_timestamp"] = now
            continue
        params[col] = val
    for api_key, col in _TRACKING_CLOB.items():
        val = data.get(api_key)
        params[col] = json_dumps(val) if val is not None else None
    # Everything else (cartItems, pageViews, isReturning, quantity, etc.) -> payload
    known = set(_TRACKING_SCALAR) | set(_TRACKING_CLOB) | {"_id", "createdAt", "updatedAt", "timestamp"}
    for k, v in data.items():
        if k not in known and v is not None:
            payload_extra[k] = v
    if payload_extra:
        params["payload"] = json_dumps(payload_extra)
    return params


def _build_select_columns() -> str:
    scalars = list(_TRACKING_SCALAR.values()) + ["id", "created_at", "updated_at"]
    clobs = list(_TRACKING_CLOB.values())
    return ", ".join(set(scalars) | set(clobs))


class OracleTrackingDAO:
    @property
    def TABLE(self):
        suffix = getattr(settings, "table_suffix", "")
        return f"sj_tracking{suffix}"

    def _factory(self):
        return get_async_session_factory()

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        factory = self._factory()
        if not factory:
            return []

        where_clauses = []
        params = {}
        if query:
            for k, v in query.items():
                if k in ("_id", "id"):
                    where_clauses.append("id = :id")
                    params["id"] = int(v) if str(v).isdigit() else 0
                elif k in _TRACKING_SCALAR:
                    col = _TRACKING_SCALAR[k]
                    where_clauses.append(f"{col} = :{col}")
                    params[col] = v

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        cols = _build_select_columns()

        async with factory() as session:
            result = await session.execute(
                text(f"SELECT {cols} FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"), params
            )
            rows = result.fetchall()
        return [_row_to_dict(r) for r in rows]

    async def findOne(self, query: Dict) -> Optional[Dict]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        factory = self._factory()
        if not factory:
            return None
        pid = int(id) if str(id).isdigit() else 0
        cols = _build_select_columns()
        async with factory() as session:
            result = await session.execute(
                text(f"SELECT {cols} FROM {self.TABLE} WHERE id = :id"),
                {"id": pid},
            )
            row = result.fetchone()
        return _row_to_dict(row) if row else None

    async def create(self, data: Dict) -> Dict:
        factory = self._factory()
        if not factory:
            raise RuntimeError("Oracle not configured")
        now = now_utc()
        params = _doc_to_params(data, now)
        # Ensure timestamp
        if "event_timestamp" not in params or params["event_timestamp"] is None:
            params["event_timestamp"] = now
        cols = list(params.keys())
        placeholders = ":" + ", :".join(cols)
        cols_str = ", ".join(cols)
        async with factory() as session:
            await session.execute(
                text(f"INSERT INTO {self.TABLE} ({cols_str}) VALUES ({placeholders})"),
                params,
            )
            await session.commit()
            result = await session.execute(
                text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"),
                {"eid": params["external_id"]},
            )
            new_id = result.scalar()
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
        params = _doc_to_params(merged, now)
        params["id"] = int(id) if str(id).isdigit() else 0
        params["updated_at"] = now
        # Build SET clause (exclude id and external_id)
        set_parts = []
        for k in params:
            if k in ("id", "external_id"):
                continue
            set_parts.append(f"{k} = :{k}")
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {', '.join(set_parts)} WHERE id = :id"),
                params,
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        pid = int(id) if str(id).isdigit() else 0
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pid},
            )
            await session.commit()
            return result.rowcount > 0

    async def deleteMany(self, query: Dict) -> Dict:
        docs = await self.findAll(query)
        deleted = 0
        for d in docs:
            if await self.delete(d.get("_id")):
                deleted += 1
        return {"deletedCount": deleted}

    async def count(self, query: Optional[Dict] = None) -> int:
        docs = await self.findAll(query)
        return len(docs)

    find_all = findAll
    find_by_id = findById
    find_one = findOne
