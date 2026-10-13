"""
Strict SQLAlchemy DAO for sj_product_reviews with native integer IDs and Pydantic models.
"""
from typing import List, Optional
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc
from app.models.schemas import ProductReviewResponse
from app.models.daos_flat import (
    ProductReviewsInternalCreate,
    ProductReviewsInternalUpdate,
)


class MySQLProductReviewsDAO:
    TABLE = "sj_product_reviews"

    def _map_to_schema(self, row) -> ProductReviewResponse:
        pid = row.product_id
        if pid is not None:
            try:
                pid = int(str(pid).replace("PDT-", ""))
            except (ValueError, TypeError):
                pid = 0
        else:
            pid = 0
        return ProductReviewResponse(
            id=row.id,
            productId=pid,
            userId=row.user_id,
            rating=row.rating or 0,
            reviewText=row.review_text,
            status=row.status or "pending",
            createdAt=row.created_at,
            updatedAt=row.updated_at,
        )

    async def findAll(
        self,
        product_id: Optional[int] = None,
        user_id: Optional[str] = None,
        rating: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[ProductReviewResponse]:
        async_session = get_async_session_factory()
        where_clauses = []
        params = {}
        if product_id is not None:
            where_clauses.append("product_id = :productId")
            params["productId"] = product_id
        if user_id is not None:
            where_clauses.append("user_id = :userId")
            params["userId"] = user_id
        if rating is not None:
            where_clauses.append("rating = :rating")
            params["rating"] = rating
        if status is not None:
            where_clauses.append("status = :status")
            params["status"] = status

        where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
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
        product_id: Optional[int] = None,
        user_id: Optional[str] = None,
        rating: Optional[int] = None,
        status: Optional[str] = None,
    ) -> Optional[ProductReviewResponse]:
        records = await self.findAll(product_id=product_id, user_id=user_id, rating=rating, status=status)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[ProductReviewResponse]:
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

    async def create(self, data: ProductReviewsInternalCreate) -> Optional[ProductReviewResponse]:
        now = now_utc()
        cols = ["created_at", "updated_at"]
        vals = [":c", ":u"]
        params = {"c": now, "u": now}
        if data.product_id is not None:
            cols.append("product_id")
            vals.append(":productId")
            params["productId"] = data.product_id
        if data.user_id is not None:
            cols.append("user_id")
            vals.append(":userId")
            params["userId"] = data.user_id
        if data.rating is not None:
            cols.append("rating")
            vals.append(":rating")
            params["rating"] = data.rating
        if data.review_text is not None:
            cols.append("review_text")
            vals.append(":reviewText")
            params["reviewText"] = data.review_text
        if data.status is not None:
            cols.append("status")
            vals.append(":status")
            params["status"] = data.status

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

    async def update(self, id: int, data: ProductReviewsInternalUpdate) -> Optional[ProductReviewResponse]:
        if not id:
            return None
        now = now_utc()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now}

        if "product_id" in data.model_fields_set:
            updates.append("product_id = :productId")
            params["productId"] = data.product_id

        if "user_id" in data.model_fields_set:
            updates.append("user_id = :userId")
            params["userId"] = data.user_id

        if "rating" in data.model_fields_set:
            updates.append("rating = :rating")
            params["rating"] = data.rating

        if "review_text" in data.model_fields_set:
            updates.append("review_text = :reviewText")
            params["reviewText"] = data.review_text

        if "status" in data.model_fields_set:
            updates.append("status = :status")
            params["status"] = data.status

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
