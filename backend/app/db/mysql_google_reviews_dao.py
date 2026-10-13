"""
Strict SQLAlchemy DAO for sj_google_reviews with native integer IDs and Pydantic models.
"""
from typing import List, Optional
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc
from app.models.daos_flat import (
    Google_reviewsInternal,
    Google_reviewsInternalCreate,
    Google_reviewsInternalUpdate,
)


class MySQLGoogleReviewsDAO:
    TABLE = "sj_google_reviews"

    def _map_to_schema(self, row) -> Google_reviewsInternal:
        return Google_reviewsInternal(
            id=row.id,
            rating=float(row.rating) if row.rating is not None else None,
            reviewCount=str(row.review_count) if row.review_count is not None else None,
            lastUpdated=row.last_updated,
            method=row.method,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def findAll(self, method: Optional[str] = None) -> List[Google_reviewsInternal]:
        where_clauses = []
        params = {}
        if method is not None:
            where_clauses.append("method = :method")
            params["method"] = method

        where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        async_session = get_async_session_factory()
        async with async_session() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE}{where_sql} ORDER BY id ASC"),
                    params,
                )
            ).fetchall()
        return [self._map_to_schema(r) for r in rows]

    async def findOne(self, method: Optional[str] = None) -> Optional[Google_reviewsInternal]:
        records = await self.findAll(method=method)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[Google_reviewsInternal]:
        if not id:
            return None
        async_session = get_async_session_factory()
        async with async_session() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": id},
                )
            ).fetchone()
        return self._map_to_schema(row) if row else None

    async def create(self, data: Google_reviewsInternalCreate) -> Optional[Google_reviewsInternal]:
        now = now_utc()
        cols = ["created_at", "updated_at"]
        vals = [":c", ":u"]
        params = {"c": now, "u": now}
        if data.rating is not None:
            cols.append("rating")
            vals.append(":rating")
            params["rating"] = data.rating
        if data.reviewCount is not None:
            cols.append("review_count")
            vals.append(":reviewCount")
            params["reviewCount"] = int(data.reviewCount)
        if data.lastUpdated is not None:
            cols.append("last_updated")
            vals.append(":lastUpdated")
            params["lastUpdated"] = data.lastUpdated
        if data.method is not None:
            cols.append("method")
            vals.append(":method")
            params["method"] = data.method

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        async_session = get_async_session_factory()
        async with async_session() as session:
            res = await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = res.lastrowid
            await session.commit()
        return await self.findById(new_id)

    async def update(self, id: int, data: Google_reviewsInternalUpdate) -> Optional[Google_reviewsInternal]:
        if not id:
            return None

        now = now_utc()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now}

        if "rating" in data.model_fields_set:
            updates.append("rating = :rating")
            params["rating"] = data.rating

        if "reviewCount" in data.model_fields_set:
            updates.append("review_count = :reviewCount")
            params["reviewCount"] = int(data.reviewCount) if data.reviewCount is not None else None

        if "lastUpdated" in data.model_fields_set:
            updates.append("last_updated = :lastUpdated")
            params["lastUpdated"] = data.lastUpdated

        if "method" in data.model_fields_set:
            updates.append("method = :method")
            params["method"] = data.method

        set_sql = ", ".join(updates)
        async_session = get_async_session_factory()
        async with async_session() as session:
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
        async_session = get_async_session_factory()
        async with async_session() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": id},
            )
            await session.commit()
            return res.rowcount > 0
