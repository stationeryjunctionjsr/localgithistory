"""
Strict SQLAlchemy DAO for sj_privacy_policy with native integer IDs and Pydantic models.
"""
from typing import Dict, List, Optional
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc
from app.models.privacy_policy import PrivacyPolicy
from app.models.daos_flat import PrivacyPolicyInternalCreate, PrivacyPolicyInternalUpdate


class MySQLPrivacyPolicyDAO:
    TABLE = "sj_privacy_policy"

    def _factory(self):
        return get_async_session_factory()

    def _map_to_schema(self, row) -> PrivacyPolicy:
        return PrivacyPolicy(
            id=row.id,
            version=row.version,
            content=row.content,
            effective_date=row.effective_date,
            is_active=bool(row.is_active) if ("is_active" in row._mapping and row.is_active is not None) else False,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def findAll(self, query: Optional[Dict] = None) -> List[PrivacyPolicy]:
        query = query or {}
        where_clauses = []
        params = {}
        if "version" in query:
            where_clauses.append("version = :version")
            params["version"] = query["version"]
        if "content" in query:
            where_clauses.append("content = :content")
            params["content"] = query["content"]
        if "effectiveDate" in query:
            where_clauses.append("effective_date = :effectiveDate")
            params["effectiveDate"] = query["effectiveDate"]
        if "isActive" in query:
            where_clauses.append("is_active = :isActive")
            params["isActive"] = 1 if query["isActive"] else 0

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

    async def findOne(self, query: Dict) -> Optional[PrivacyPolicy]:
        if "id" in query:
            return await self.findById(int(query["id"]))
        records = await self.findAll(query)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[PrivacyPolicy]:
        factory = self._factory()
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": id},
                )
            ).fetchone()
        return self._map_to_schema(row) if row else None

    async def create(self, data: PrivacyPolicyInternalCreate) -> PrivacyPolicy:
        factory = self._factory()
        now = now_utc()
        cols = ["created_at", "updated_at"]
        vals = [":c", ":u"]
        params = {"c": now, "u": now}
        if data.version is not None:
            cols.append("version")
            vals.append(":version")
            params["version"] = data.version
        if data.content is not None:
            cols.append("content")
            vals.append(":content")
            params["content"] = data.content
        if data.effective_date is not None:
            cols.append("effective_date")
            vals.append(":effectiveDate")
            params["effectiveDate"] = data.effective_date
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

    async def update(self, id: int, data: PrivacyPolicyInternalUpdate) -> Optional[PrivacyPolicy]:
        existing = await self.findById(id)
        if not existing:
            return None
        now = now_utc()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now}
        if data.version is not None:
            updates.append("version = :version")
            params["version"] = data.version
        if data.content is not None:
            updates.append("content = :content")
            params["content"] = data.content
        if data.effective_date is not None:
            updates.append("effective_date = :effectiveDate")
            params["effectiveDate"] = data.effective_date
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
        return await self.findById(id)

    async def delete(self, id: int) -> bool:
        factory = self._factory()
        async with factory() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": id},
            )
            await session.commit()
            return res.rowcount > 0
