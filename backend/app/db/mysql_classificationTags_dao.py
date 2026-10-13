"""
Strict SQLAlchemy DAO for sj_classification_tags with native integer IDs and Pydantic models.
"""
from typing import List, Optional
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc
from app.models.schemas import ClassificationTagResponse
from app.models.daos_flat import (
    ClassificationTagsInternalCreate,
    ClassificationTagsInternalUpdate,
)


class MySQLClassificationTagsDAO:
    TABLE = "sj_classification_tags"

    def _factory(self):
        return get_async_session_factory()

    def _map_to_schema(self, row) -> ClassificationTagResponse:
        return ClassificationTagResponse(
            id=row.id,
            name=row.name,
            isActive=bool(row.is_active),
            createdAt=row.created_at,
            updatedAt=row.updated_at,
        )

    async def findAll(
        self,
        is_active: Optional[bool] = None,
        name: Optional[str] = None,
    ) -> List[ClassificationTagResponse]:
        factory = self._factory()
        if not factory:
            return []
        where_clauses = []
        params = {}
        if name is not None:
            where_clauses.append("name = :name")
            params["name"] = name
        if is_active is not None:
            where_clauses.append("is_active = :isActive")
            params["isActive"] = 1 if is_active else 0

        where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE}{where_sql} ORDER BY id ASC"),
                    params,
                )
            ).fetchall()
        return [self._map_to_schema(r) for r in rows]

    async def findOne(
        self,
        is_active: Optional[bool] = None,
        name: Optional[str] = None,
    ) -> Optional[ClassificationTagResponse]:
        records = await self.findAll(is_active=is_active, name=name)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[ClassificationTagResponse]:
        if not id:
            return None
        factory = self._factory()
        if not factory:
            return None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": id},
                )
            ).fetchone()
        return self._map_to_schema(row) if row else None

    async def create(self, data: ClassificationTagsInternalCreate) -> Optional[ClassificationTagResponse]:
        factory = self._factory()
        if not factory:
            return None
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
        if not id:
            return None
        factory = self._factory()
        if not factory:
            return None

        now = now_utc()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now}

        if "name" in data.model_fields_set:
            updates.append("name = :name")
            params["name"] = data.name

        if "is_active" in data.model_fields_set:
            updates.append("is_active = :isActive")
            params["isActive"] = 1 if data.is_active else 0

        set_sql = ", ".join(updates)
        async with factory() as session:
            res = await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
            if res.rowcount == 0:
                existing = await self.findById(id)
                if not existing:
                    return None

        return await self.findById(id)

    async def delete(self, id: int) -> bool:
        if not id:
            return False
        factory = self._factory()
        if not factory:
            return False
        async with factory() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": id},
            )
            await session.commit()
            return res.rowcount > 0
