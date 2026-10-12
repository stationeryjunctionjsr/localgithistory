"""
Strict SQLAlchemy DAO for sj_classification_tags with native integer IDs and Pydantic models.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc
from app.models.schemas import ClassificationTagResponse
from app.models.daos_flat import (
    ClassificationTagsInternalCreate,
    ClassificationTagsInternalUpdate,
)


def _to_int(val: Any) -> Optional[int]:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


class MySQLClassificationTagsDAO:
    TABLE = "sj_classification_tags"

    def _factory(self):
        return get_async_session_factory()

    def _map_to_schema(self, row) -> ClassificationTagResponse:
        return ClassificationTagResponse(
            id=str(row.id),
            name=row.name,
            isActive=bool(row.is_active),
            createdAt=row.created_at,
            updatedAt=row.updated_at,
        )

    async def findAll(self, query: Optional[Dict] = None) -> List[ClassificationTagResponse]:
        query = query or {}
        where_clauses = []
        params = {}
        if "name" in query:
            where_clauses.append("name = :name")
            params["name"] = query["name"]
        if "isActive" in query or "is_active" in query:
            val = query.get("isActive") if "isActive" in query else query.get("is_active")
            where_clauses.append("is_active = :isActive")
            params["isActive"] = 1 if val else 0

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

    async def findOne(self, query: Dict) -> Optional[ClassificationTagResponse]:
        if "id" in query:
            id_val = _to_int(query["id"])
            if id_val is not None:
                return await self.findById(id_val)
        records = await self.findAll(query)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[ClassificationTagResponse]:
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

    async def create(self, data: ClassificationTagsInternalCreate) -> ClassificationTagResponse:
        factory = self._factory()
        now = now_utc()
        cols = ["created_at", "updated_at"]
        vals = [":c", ":u"]
        params = {"c": now, "u": now}
        if data.name is not None:
            cols.append("name")
            vals.append(":name")
            params["name"] = data.name
        if data.is_active is not None:
            cols.append("is_active")
            vals.append(":isActive")
            params["isActive"] = 1 if data.is_active else 0

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

    async def update(self, id: int, data: ClassificationTagsInternalUpdate) -> Optional[ClassificationTagResponse]:
        id_val = _to_int(id)
        if id_val is None:
            return None
        existing = await self.findById(id_val)
        if not existing:
            return None

        now = now_utc()
        updates = ["updated_at = :u"]
        params = {"id": id_val, "u": now}
        if data.name is not None:
            updates.append("name = :name")
            params["name"] = data.name
        if data.is_active is not None:
            updates.append("is_active = :isActive")
            params["isActive"] = 1 if data.is_active else 0

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
