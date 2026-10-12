"""
Strict SQLAlchemy DAO for sj_pincode_searches with native integer IDs and Pydantic models.
"""
from typing import Any, Dict, List, Optional, Union
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc
from app.models.pincode_searches import PincodeSearches
from app.models.daos_flat import (
    PincodeSearchesInternalCreate,
    PincodeSearchesInternalUpdate,
)


def _to_int(val: Any) -> Optional[int]:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


class MySQLPincodeSearchesDAO:
    TABLE = "sj_pincode_searches"

    def _factory(self):
        return get_async_session_factory()

    def _map_to_schema(self, row) -> PincodeSearches:
        return PincodeSearches(
            id=row.id,
            pincode=row.pincode,
            query=row.query if "query" in row._mapping else None,
            is_serviceable=bool(row.is_serviceable) if ("is_serviceable" in row._mapping and row.is_serviceable is not None) else False,
            timestamp=row.timestamp.isoformat() if ("timestamp" in row._mapping and row.timestamp) else None,
            city=row.city if "city" in row._mapping else None,
            state=row.state if "state" in row._mapping else None,
            district=row.district if "district" in row._mapping else None,
            created_at=row.created_at if "created_at" in row._mapping else None,
            updated_at=row.updated_at if "updated_at" in row._mapping else None,
        )

    async def findAll(self, query: Optional[Dict] = None) -> List[PincodeSearches]:
        query = query or {}
        where_clauses = []
        params = {}
        if "pincode" in query:
            where_clauses.append("pincode = :pincode")
            params["pincode"] = query["pincode"]
        if "query" in query:
            where_clauses.append("query = :query")
            params["query"] = query["query"]
        if "isServiceable" in query or "is_serviceable" in query:
            val = query.get("isServiceable") if "isServiceable" in query else query.get("is_serviceable")
            where_clauses.append("is_serviceable = :isServiceable")
            params["isServiceable"] = 1 if val else 0
        if "timestamp" in query:
            where_clauses.append("timestamp = :timestamp")
            params["timestamp"] = query["timestamp"]

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        factory = self._factory()
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"),
                    params,
                )
            ).fetchall()
        return [self._map_to_schema(r) for r in rows]

    async def findOne(self, query: Dict) -> Optional[PincodeSearches]:
        if "id" in query:
            id_val = _to_int(query["id"])
            if id_val is not None:
                return await self.findById(id_val)
        records = await self.findAll(query)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[PincodeSearches]:
        id_val = _to_int(id)
        if id_val is None:
            return None
        factory = self._factory()
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": id_val},
                )
            ).fetchone()
        return self._map_to_schema(row) if row else None

    async def create(self, data: Union[PincodeSearchesInternalCreate, Dict]) -> PincodeSearches:
        if isinstance(data, dict):
            pincode = data.get("pincode")
            query_val = data.get("query")
            is_srv = data.get("isServiceable") if "isServiceable" in data else data.get("is_serviceable")
            ts = data.get("timestamp") or data.get("searchedAt")
        else:
            pincode = data.pincode
            query_val = data.query
            is_srv = data.is_serviceable
            ts = data.timestamp

        factory = self._factory()
        now = now_utc()
        cols = ["created_at", "updated_at"]
        vals = [":c", ":u"]
        params = {"c": now, "u": now}
        if pincode is not None:
            cols.append("pincode")
            vals.append(":pincode")
            params["pincode"] = pincode
        if query_val is not None:
            cols.append("query")
            vals.append(":query")
            params["query"] = query_val
        if is_srv is not None:
            cols.append("is_serviceable")
            vals.append(":isServiceable")
            params["isServiceable"] = 1 if is_srv else 0
        if ts is not None:
            cols.append("timestamp")
            vals.append(":timestamp")
            params["timestamp"] = ts

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        async with factory() as session:
            res = await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = res.lastrowid
            await session.commit()
        return await self.findById(new_id)

    async def update(self, id: int, data: Union[PincodeSearchesInternalUpdate, Dict]) -> Optional[PincodeSearches]:
        id_val = _to_int(id)
        if id_val is None:
            return None
        existing = await self.findById(id_val)
        if not existing:
            return None

        if isinstance(data, dict):
            pincode = data.get("pincode")
            query_val = data.get("query")
            is_srv = data.get("isServiceable") if "isServiceable" in data else data.get("is_serviceable")
            ts = data.get("timestamp") or data.get("searchedAt")
        else:
            pincode = data.pincode
            query_val = data.query
            is_srv = data.is_serviceable
            ts = data.timestamp

        now = now_utc()
        updates = ["updated_at = :u"]
        params = {"id": id_val, "u": now}
        if pincode is not None:
            updates.append("pincode = :pincode")
            params["pincode"] = pincode
        if query_val is not None:
            updates.append("query = :query")
            params["query"] = query_val
        if is_srv is not None:
            updates.append("is_serviceable = :isServiceable")
            params["isServiceable"] = 1 if is_srv else 0
        if ts is not None:
            updates.append("timestamp = :timestamp")
            params["timestamp"] = ts

        set_sql = ", ".join(updates)
        factory = self._factory()
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
        return await self.findById(id_val)

    async def delete(self, id: int) -> bool:
        id_val = _to_int(id)
        if id_val is None:
            return False
        factory = self._factory()
        async with factory() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": id_val},
            )
            await session.commit()
            return res.rowcount > 0
