"""
Strict SQLAlchemy DAO for sj_about_us with native integer IDs and Pydantic models.
"""
from typing import Dict, List, Optional
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc
from app.models.about_us import AboutUs
from app.models.daos_flat import AboutUsInternalCreate, AboutUsInternalUpdate


class MySQLAboutUsDAO:
    TABLE = "sj_about_us"

    def _factory(self):
        return get_async_session_factory()

    def _map_to_schema(self, row) -> AboutUs:
        return AboutUs(
            id=row.id,
            title=row.title,
            content=row.content,
            version=row.version,
            is_published=bool(row.is_published) if ("is_published" in row._mapping and row.is_published is not None) else False,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def findAll(self, query: Optional[Dict] = None) -> List[AboutUs]:
        query = query or {}
        where_clauses = []
        params = {}
        if "title" in query:
            where_clauses.append("title = :title")
            params["title"] = query["title"]
        if "content" in query:
            where_clauses.append("content = :content")
            params["content"] = query["content"]
        if "version" in query:
            where_clauses.append("version = :version")
            params["version"] = query["version"]
        if "isPublished" in query:
            where_clauses.append("is_published = :isPublished")
            params["isPublished"] = 1 if query["isPublished"] else 0

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

    async def findOne(self, query: Dict) -> Optional[AboutUs]:
        if "id" in query:
            return await self.findById(int(query["id"]))
        records = await self.findAll(query)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[AboutUs]:
        factory = self._factory()
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": id},
                )
            ).fetchone()
        return self._map_to_schema(row) if row else None

    async def create(self, data: AboutUsInternalCreate) -> AboutUs:
        factory = self._factory()
        now = now_utc()
        cols = ["created_at", "updated_at"]
        vals = [":c", ":u"]
        params = {"c": now, "u": now}
        if data.title is not None:
            cols.append("title")
            vals.append(":title")
            params["title"] = data.title
        if data.content is not None:
            cols.append("content")
            vals.append(":content")
            params["content"] = data.content
        if data.version is not None:
            cols.append("version")
            vals.append(":version")
            params["version"] = data.version
        if data.is_published is not None:
            cols.append("is_published")
            vals.append(":isPublished")
            params["isPublished"] = 1 if data.is_published else 0

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

    async def update(self, id: int, data: AboutUsInternalUpdate) -> Optional[AboutUs]:
        existing = await self.findById(id)
        if not existing:
            return None
        now = now_utc()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now}
        if data.title is not None:
            updates.append("title = :title")
            params["title"] = data.title
        if data.content is not None:
            updates.append("content = :content")
            params["content"] = data.content
        if data.version is not None:
            updates.append("version = :version")
            params["version"] = data.version
        if data.is_published is not None:
            updates.append("is_published = :isPublished")
            params["isPublished"] = 1 if data.is_published else 0

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
