"""
Strict SQLAlchemy DAO for sj_google_reviews with native integer IDs and Pydantic models.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc
from app.models.daos_flat import (
    Google_reviewsInternal,
    Google_reviewsInternalCreate,
    Google_reviewsInternalUpdate,
)


def _to_int(val: Any) -> Optional[int]:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


class MySQLGoogleReviewsDAO:
    TABLE = "sj_google_reviews"

    def _factory(self):
        return get_async_session_factory()

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

    async def findAll(self, query: Optional[Dict] = None) -> List[Google_reviewsInternal]:
        query = query or {}
        where_clauses = []
        params = {}
        if "rating" in query:
            where_clauses.append("rating = :rating")
            params["rating"] = query["rating"]
        if "reviewCount" in query:
            where_clauses.append("review_count = :reviewCount")
            params["reviewCount"] = _to_int(query["reviewCount"])
        if "lastUpdated" in query:
            where_clauses.append("last_updated = :lastUpdated")
            params["lastUpdated"] = query["lastUpdated"]
        if "method" in query:
            where_clauses.append("method = :method")
            params["method"] = query["method"]

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

    async def findOne(self, query: Dict) -> Optional[Google_reviewsInternal]:
        if "id" in query:
            id_val = _to_int(query["id"])
            if id_val is not None:
                return await self.findById(id_val)
        records = await self.findAll(query)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[Google_reviewsInternal]:
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

    async def create(self, data: Google_reviewsInternalCreate) -> Google_reviewsInternal:
        factory = self._factory()
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
            params["reviewCount"] = _to_int(data.reviewCount)
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
        async with factory() as session:
            res = await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = res.lastrowid
            await session.commit()
        return await self.findById(new_id)

    async def update(self, id: int, data: Google_reviewsInternalUpdate) -> Optional[Google_reviewsInternal]:
        id_val = _to_int(id)
        if id_val is None:
            return None
        existing = await self.findById(id_val)
        if not existing:
            return None

        now = now_utc()
        updates = ["updated_at = :u"]
        params = {"id": id_val, "u": now}
        if data.rating is not None:
            updates.append("rating = :rating")
            params["rating"] = data.rating
        if data.reviewCount is not None:
            updates.append("review_count = :reviewCount")
            params["reviewCount"] = _to_int(data.reviewCount)
        if data.lastUpdated is not None:
            updates.append("last_updated = :lastUpdated")
            params["lastUpdated"] = data.lastUpdated
        if data.method is not None:
            updates.append("method = :method")
            params["method"] = data.method

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
