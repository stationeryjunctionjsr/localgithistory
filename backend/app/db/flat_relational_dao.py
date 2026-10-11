import logging
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union
from pydantic import BaseModel

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc


def _q(col: str) -> str:
    return f"`{col}`"


def _param(col: str) -> str:
    return f"p_{col}" if col.lower() == "date" else col


def _to_ts(val) -> Optional[datetime]:
    if val is None:
        return None
    try:
        val.isoformat
        return val
    except AttributeError:
        pass
    try:
        return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
    except Exception as e:
        logging.warning("_ensure_datetime: could not parse datetime value %r: %s", val, e, exc_info=e)
        return None


from app.config.settings import settings


class FlatRelationalDAO:
    def __init__(
        self,
        table_name: str,
        scalar_map: Dict[str, str],
        clob_map: Optional[Dict[str, str]] = None,
        *,
        has_external_id: bool = True,
        bool_api_keys: Optional[Set[str]] = None,
        schema_cls=None,
    ):
        self.schema_cls = schema_cls
        self._raw_table_name = table_name
        self.scalar_map = scalar_map
        self.clob_map = clob_map or {}
        self.has_external_id = has_external_id
        self.bool_api_keys = bool_api_keys or set()

    @property
    def table_name(self) -> str:
        return self._raw_table_name

    def _factory(self):
        return get_async_session_factory()

    def _map_to_schema(self, r) -> 'CamelBaseModel':
        out = {"_id": str(r.id)}
        rev = {v: k for k, v in self.scalar_map.items()}
        for col, api_key in rev.items():
            try:
                val = r._mapping[col]
            except KeyError:
                continue
            if val is None:
                continue
            if api_key in self.bool_api_keys and val in (0, 1):
                out[api_key] = bool(val)
            elif not isinstance(val, str):
                try:
                    out[api_key] = val.isoformat()
                except AttributeError:
                    out[api_key] = val
            else:
                out[api_key] = val
        for api_key, col in self.clob_map.items():
            try:
                val = r._mapping[col]
            except KeyError:
                continue
            if val is not None:
                out[api_key] = val
        try:
            if r.created_at is not None:
                out["createdAt"] = r.created_at.isoformat()
        except AttributeError:
            pass
        try:
            if r.updated_at is not None:
                out["updatedAt"] = r.updated_at.isoformat()
        except AttributeError:
            pass
        return self.schema_cls(**out) if self.schema_cls else out

    def _doc_to_params(self, data: Dict, now: datetime) -> Dict:
        params = {"created_at": now, "updated_at": now}
        if self.has_external_id:
            params["external_id"] = secrets.token_hex(16)
        for api_key, col in self.scalar_map.items():
            val = data[api_key] if api_key in data else None
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
            val = data[api_key] if api_key in data else None
            params[col] = val
        return params

    def _all_columns(self) -> List[str]:
        cols = ["id", "created_at", "updated_at"]
        if self.has_external_id:
            cols.append("external_id")
        cols.extend(self.scalar_map.values())
        cols.extend(self.clob_map.values())
        # Use dict.fromkeys for uniqueness, then quote
        return [_q(c) for c in dict.fromkeys(cols)]

    async def findAll(self, id: Optional[Union[int, str]] = None) -> List[Any]:
        factory = self._factory()
        if not factory:
            return []

        where_clauses = []
        params = {}
        if id is not None:
            where_clauses.append("id = :id")
            params["id"] = int(id) if str(id).isdigit() else None

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        cols = ", ".join(self._all_columns())

        async with factory() as session:
            result = await session.execute(
                text(f"SELECT {cols} FROM {self.table_name} WHERE {where_sql} ORDER BY id ASC"), params
            )
            rows = result.fetchall()
        return [self._map_to_schema(r) for r in rows]

    async def findOne(self, id: Optional[Union[int, str]] = None) -> Optional[Any]:
        docs = await self.findAll(id=id)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        factory = self._factory()
        if not factory:
            return None
        pk = int(id) if str(id).isdigit() else None
        cols = ", ".join(self._all_columns())
        async with factory() as session:
            result = await session.execute(
                text(f"SELECT {cols} FROM {self.table_name} WHERE id = :id"),
                {"id": pk},
            )
            row = result.fetchone()
        return self._map_to_schema(row) if row else None

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

        if not self.has_external_id:
            raise RuntimeError("Cannot retrieve new row id without external_id")

        # Open a fresh session after commit to fetch the new row id
        async with factory() as session:
            result = await session.execute(
                text(f"SELECT id FROM {self.table_name} WHERE external_id = :eid"),
                {"eid": bind_params["external_id"]},
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
        existing_data = existing.model_dump(by_alias=True) if isinstance(existing, BaseModel) else existing
        merged = {**existing_data, **update_data}
        factory = self._factory()
        if not factory:
            return None
        now = now_utc()
        params = self._doc_to_params(merged, now)
        params["id"] = int(id) if str(id).isdigit() else None
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
        pk = int(id) if str(id).isdigit() else None
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.table_name} WHERE id = :id"),
                {"id": pk},
            )
            await session.commit()
            return result.rowcount > 0

    async def count(self, id: Optional[Union[int, str]] = None) -> int:
        """Count rows matching criteria using SELECT COUNT(*) — never loads row data."""
        factory = self._factory()
        if not factory:
            return 0
        where_clauses = []
        params = {}
        if id is not None:
            where_clauses.append("id = :id")
            params["id"] = int(id) if str(id).isdigit() else None
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        async with factory() as session:
            result = await session.execute(
                text(f"SELECT COUNT(*) FROM {self.table_name} WHERE {where_sql}"),
                params,
            )
            return int(result.scalar() or 0)



