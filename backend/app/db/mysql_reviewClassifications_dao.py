"""
Strict SQLAlchemy DAO for sj_review_classifications with native integer IDs and Pydantic models.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc
from app.models.review_classifications import ReviewClassifications
from app.models.daos_flat import (
    ReviewClassificationsInternalCreate,
    ReviewClassificationsInternalUpdate,
)


def _to_int(val: Any) -> Optional[int]:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


class MySQLReviewClassificationsDAO:
    TABLE = "sj_review_classifications"

    def _factory(self):
        return get_async_session_factory()

    def _map_to_schema(self, row) -> ReviewClassifications:
        return ReviewClassifications(
            id=row.id,
            review_id=str(row.review_id) if row.review_id is not None else None,
            category=str(row.category) if row.category is not None else None,
            confidence_score=float(row.confidence_score) if row.confidence_score is not None else None,
            sentiment=str(row.sentiment) if row.sentiment is not None else None,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def findAll(self, query: Optional[Dict] = None) -> List[ReviewClassifications]:
        query = query or {}
        where_clauses = []
        params = {}
        if "reviewId" in query or "review_id" in query:
            r_id = query.get("reviewId") if "reviewId" in query else query.get("review_id")
            where_clauses.append("review_id = :reviewId")
            params["reviewId"] = str(r_id)
        if "category" in query:
            where_clauses.append("category = :category")
            params["category"] = query["category"]
        if "confidenceScore" in query or "confidence_score" in query:
            cs = query.get("confidenceScore") if "confidenceScore" in query else query.get("confidence_score")
            where_clauses.append("confidence_score = :confidenceScore")
            params["confidenceScore"] = float(cs)
        if "sentiment" in query:
            where_clauses.append("sentiment = :sentiment")
            params["sentiment"] = query["sentiment"]

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

    async def findOne(self, query: Dict) -> Optional[ReviewClassifications]:
        if "id" in query:
            id_val = _to_int(query["id"])
            if id_val is not None:
                return await self.findById(id_val)
        records = await self.findAll(query)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[ReviewClassifications]:
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

    async def create(self, data: ReviewClassificationsInternalCreate) -> ReviewClassifications:
        factory = self._factory()
        now = now_utc()
        cols = ["created_at", "updated_at"]
        vals = [":c", ":u"]
        params = {"c": now, "u": now}
        if data.review_id is not None:
            cols.append("review_id")
            vals.append(":reviewId")
            params["reviewId"] = str(data.review_id)
        if data.category is not None:
            cols.append("category")
            vals.append(":category")
            params["category"] = data.category
        if data.confidence_score is not None:
            cols.append("confidence_score")
            vals.append(":confidenceScore")
            params["confidenceScore"] = float(data.confidence_score)
        if data.sentiment is not None:
            cols.append("sentiment")
            vals.append(":sentiment")
            params["sentiment"] = data.sentiment

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

    async def update(self, id: int, data: ReviewClassificationsInternalUpdate) -> Optional[ReviewClassifications]:
        id_val = _to_int(id)
        if id_val is None:
            return None
        existing = await self.findById(id_val)
        if not existing:
            return None

        now = now_utc()
        updates = ["updated_at = :u"]
        params = {"id": id_val, "u": now}
        if data.review_id is not None:
            updates.append("review_id = :reviewId")
            params["reviewId"] = str(data.review_id)
        if data.category is not None:
            updates.append("category = :category")
            params["category"] = data.category
        if data.confidence_score is not None:
            updates.append("confidence_score = :confidenceScore")
            params["confidenceScore"] = float(data.confidence_score)
        if data.sentiment is not None:
            updates.append("sentiment = :sentiment")
            params["sentiment"] = data.sentiment

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
