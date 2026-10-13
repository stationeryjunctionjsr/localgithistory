"""
Strict SQLAlchemy DAO for sj_review_classifications with native integer IDs and Pydantic models.
"""
from typing import List, Optional
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc
from app.models.review_classifications import ReviewClassifications
from app.models.daos_flat import (
    ReviewClassificationsInternalCreate,
    ReviewClassificationsInternalUpdate,
)


class MySQLReviewClassificationsDAO:
    TABLE = "sj_review_classifications"

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

    async def findAll(
        self,
        review_id: Optional[str] = None,
        category: Optional[str] = None,
        sentiment: Optional[str] = None,
    ) -> List[ReviewClassifications]:
        where_clauses = []
        params = {}
        if review_id is not None:
            where_clauses.append("review_id = :reviewId")
            params["reviewId"] = review_id
        if category is not None:
            where_clauses.append("category = :category")
            params["category"] = category
        if sentiment is not None:
            where_clauses.append("sentiment = :sentiment")
            params["sentiment"] = sentiment

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

    async def findOne(
        self,
        review_id: Optional[str] = None,
        category: Optional[str] = None,
        sentiment: Optional[str] = None,
    ) -> Optional[ReviewClassifications]:
        records = await self.findAll(review_id=review_id, category=category, sentiment=sentiment)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[ReviewClassifications]:
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

    async def create(self, data: ReviewClassificationsInternalCreate) -> Optional[ReviewClassifications]:
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
        async_session = get_async_session_factory()
        async with async_session() as session:
            res = await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = res.lastrowid
            await session.commit()
        return await self.findById(new_id)

    async def update(self, id: int, data: ReviewClassificationsInternalUpdate) -> Optional[ReviewClassifications]:
        if not id:
            return None

        now = now_utc()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now}

        if "review_id" in data.model_fields_set:
            updates.append("review_id = :reviewId")
            params["reviewId"] = str(data.review_id) if data.review_id is not None else None

        if "category" in data.model_fields_set:
            updates.append("category = :category")
            params["category"] = data.category

        if "confidence_score" in data.model_fields_set:
            updates.append("confidence_score = :confidenceScore")
            params["confidenceScore"] = float(data.confidence_score) if data.confidence_score is not None else None

        if "sentiment" in data.model_fields_set:
            updates.append("sentiment = :sentiment")
            params["sentiment"] = data.sentiment

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
