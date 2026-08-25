"""
Generic MySQL DAO for parent-only tables: fixed columns + JSON columns for arrays/arbitrary dicts.
No child tables. Implements same interface as FileStorage/MySQLDocStore.
Config: scalar_map (API key -> db column), clob_map (API key -> db column; stored as JSON type).
Table must have: id (IDENTITY), external_id, created_at, updated_at, plus configured columns.
"""

import secrets
from datetime import datetime
from typing import Dict, List, Optional, Set

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.oracle_utils import json_dumps, json_loads, now_utc


def _q(col: str) -> str:
    # Oracle:
    # if col.lower() == 'date':
    #     return '"DATE"'
    # return col
    return f"`{col}`"


def _param(col: str) -> str:
    if col.lower() == "date":
        return "p_date"
    return col


def _to_ts(val) -> Optional[datetime]:
    if val is None:
        return None
    if hasattr(val, "isoformat"):
        return val
    try:
        return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
    except Exception:
        return None


from app.config.settings import settings


class MySQLTypedDocDAO:
    def __init__(
        self,
        table_name: str,
        scalar_map: Dict[str, str],
        clob_map: Optional[Dict[str, str]] = None,
        *,
        has_external_id: bool = True,
        bool_api_keys: Optional[Set[str]] = None,
    ):
        self._raw_table_name = table_name
        self.scalar_map = scalar_map
        self.clob_map = clob_map or {}
        self.has_external_id = has_external_id
        self.bool_api_keys = bool_api_keys or set()

    @property
    def table_name(self) -> str:
        suffix = getattr(settings, "table_suffix", "")
        return f"{self._raw_table_name}{suffix}"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_doc(self, r) -> Dict:
        out = {"_id": str(r.id)}
        rev = {v: k for k, v in self.scalar_map.items()}
        for col, api_key in rev.items():
            if not hasattr(r, col):
                continue
            val = getattr(r, col)
            if val is None:
                continue
            if api_key in self.bool_api_keys and val in (0, 1):
                out[api_key] = bool(val)
            elif hasattr(val, "isoformat") and not isinstance(val, str):
                out[api_key] = val.isoformat()
            else:
                out[api_key] = val
        for api_key, col in self.clob_map.items():
            if not hasattr(r, col):
                continue
            val = getattr(r, col)
            if val is not None:
                parsed = json_loads(val)
                if parsed is not None:
                    out[api_key] = parsed
        if hasattr(r, "created_at") and r.created_at:
            out["createdAt"] = r.created_at.isoformat()
        if hasattr(r, "updated_at") and r.updated_at:
            out["updatedAt"] = r.updated_at.isoformat()
        return out

    def _doc_to_params(self, data: Dict, now: datetime) -> Dict:
        params = {"created_at": now, "updated_at": now}
        if self.has_external_id:
            params["external_id"] = secrets.token_hex(16)
        for api_key, col in self.scalar_map.items():
            val = data.get(api_key)
            if val is None:
                params[col] = None
                continue
            if api_key in self.bool_api_keys and isinstance(val, bool):
                params[col] = 1 if val else 0
            elif isinstance(val, str) and (
                col.endswith("_at")
                or col.endswith("_updated")
                or col.endswith("_on")
                or "date" in col.lower()
                or "timestamp" in col
            ):
                params[col] = _to_ts(val) or val
            else:
                params[col] = val
        for api_key, col in self.clob_map.items():
            val = data.get(api_key)
            params[col] = json_dumps(val) if val is not None else None
        return params

    def _all_columns(self) -> List[str]:
        cols = ["id", "created_at", "updated_at"]
        if self.has_external_id:
            cols.append("external_id")
        cols.extend(self.scalar_map.values())
        cols.extend(self.clob_map.values())
        # Use dict.fromkeys for uniqueness, then quote
        return [_q(c) for c in dict.fromkeys(cols)]

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
                elif k in self.scalar_map:
                    col = self.scalar_map[k]
                    p = _param(col)
                    where_clauses.append(f"{_q(col)} = :{p}")
                    if k in self.bool_api_keys:
                        params[p] = 1 if v else 0
                    else:
                        params[p] = v
                # Note: CLOB filtering not supported here (requires JSON_VALUE/JSON_EXISTS)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        cols = ", ".join(self._all_columns())

        async with factory() as session:
            result = await session.execute(
                text(f"SELECT {cols} FROM {self.table_name} WHERE {where_sql} ORDER BY id ASC"), params
            )
            rows = result.fetchall()
        return [self._row_to_doc(r) for r in rows]

    async def findOne(self, query: Dict) -> Optional[Dict]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        factory = self._factory()
        if not factory:
            return None
        pk = int(id) if str(id).isdigit() else 0
        cols = ", ".join(self._all_columns())
        async with factory() as session:
            result = await session.execute(
                text(f"SELECT {cols} FROM {self.table_name} WHERE id = :id"),
                {"id": pk},
            )
            row = result.fetchone()
        return self._row_to_doc(row) if row else None

    async def create(self, data: Dict) -> Dict:
        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        now = now_utc()
        params = self._doc_to_params(data, now)
        skip = {"id"}
        cols = [k for k in params if k not in skip]

        bind_params = {}
        placeholders = []
        for k in cols:
            p = _param(k)
            placeholders.append(":" + p)
            bind_params[p] = params[k]

        cols_str = ", ".join(_q(k) for k in cols)
        async with factory() as session:
            await session.execute(
                text(f"INSERT INTO {self.table_name} ({cols_str}) VALUES ({', '.join(placeholders)})"),
                bind_params,
            )
            await session.commit()
            new_id = None
            if self.has_external_id:
                result = await session.execute(
                    text(f"SELECT id FROM {self.table_name} WHERE external_id = :eid"),
                    {"eid": params["external_id"]},
                )
                row = result.fetchone()
                new_id = row[0] if row else None
        if new_id is None:
            raise RuntimeError("Could not obtain new row id after insert")
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
        params = self._doc_to_params(merged, now)
        params["id"] = int(id) if str(id).isdigit() else 0
        params["updated_at"] = now

        bind_params = {"id": params["id"]}
        set_parts = []
        for k in params:
            if k not in ("id", "external_id", "created_at"):
                p = _param(k)
                set_parts.append(f"{_q(k)} = :{p}")
                bind_params[p] = params[k]

        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.table_name} SET {', '.join(set_parts)} WHERE id = :id"),
                bind_params,
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        pk = int(id) if str(id).isdigit() else 0
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.table_name} WHERE id = :id"),
                {"id": pk},
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

    async def updateMany(self, query: Dict, update_data: Dict) -> int:
        factory = self._factory()
        if not factory:
            return 0

        where_clauses = []
        params = {}
        if query:
            for k, v in query.items():
                if k in ("_id", "id"):
                    where_clauses.append("id = :id")
                    params["id"] = int(v) if str(v).isdigit() else 0
                elif k in self.scalar_map:
                    col = self.scalar_map[k]
                    p = _param(col)
                    where_clauses.append(f"{_q(col)} = :{p}")
                    if k in self.bool_api_keys:
                        params[p] = 1 if v else 0
                    else:
                        params[p] = v

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        now = now_utc()
        set_parts = ["updated_at = :updated_at"]
        params["updated_at"] = now

        for k, v in update_data.items():
            if k in self.scalar_map:
                col = self.scalar_map[k]
                param_key = f"u_{_param(col)}"
                set_parts.append(f"{_q(col)} = :{param_key}")
                if k in self.bool_api_keys:
                    params[param_key] = 1 if v else 0
                else:
                    params[param_key] = v
            elif k in self.clob_map:
                col = self.clob_map[k]
                param_key = f"u_{_param(col)}"
                set_parts.append(f"{_q(col)} = :{param_key}")
                params[param_key] = json_dumps(v) if v is not None else None

        async with factory() as session:
            result = await session.execute(
                text(f"UPDATE {self.table_name} SET {', '.join(set_parts)} WHERE {where_sql}"),
                params,
            )
            await session.commit()
            return result.rowcount

    async def count(self, query: Optional[Dict] = None) -> int:
        return len(await self.findAll(query))

    find_all = findAll
    find_by_id = findById
    find_one = findOne
