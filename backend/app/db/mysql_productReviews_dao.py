"""
Strict SQLAlchemy DAO for sj_product_reviews with native integer IDs and Pydantic models.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc
from app.models.schemas import ProductReviewResponse
from app.models.daos_flat import (
    ProductReviewsInternalCreate,
    ProductReviewsInternalUpdate,
)


def _to_int(val: Any) -> Optional[int]:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


class MySQLProductReviewsDAO:
    TABLE = "sj_product_reviews"

    def _factory(self):
        return get_async_session_factory()

    def _map_to_schema(self, row) -> ProductReviewResponse:
        return ProductReviewResponse(
            id=str(row.id),
            productId=str(row.product_id),
            userId=str(row.user_id),
            rating=int(row.rating) if row.rating is not None else 0,
            reviewText=str(row.review_text) if row.review_text is not None else None,
            status=str(row.status) if row.status is not None else "pending",
            createdAt=row.created_at,
            updatedAt=row.updated_at,
        )

    async def findAll(self, query: Optional[Dict] = None) -> List[ProductReviewResponse]:
        query = query or {}
        where_clauses = []
        params = {}
        if "productId" in query or "product_id" in query:
            p_id = query.get("productId") if "productId" in query else query.get("product_id")
            where_clauses.append("product_id = :productId")
            params["productId"] = str(p_id)
        if "userId" in query or "user_id" in query:
            u_id = query.get("userId") if "userId" in query else query.get("user_id")
            where_clauses.append("user_id = :userId")
            params["userId"] = str(u_id)
        if "rating" in query:
            where_clauses.append("rating = :rating")
            params["rating"] = _to_int(query["rating"])
        if "reviewText" in query or "review_text" in query:
            rt = query.get("reviewText") if "reviewText" in query else query.get("review_text")
            where_clauses.append("review_text = :reviewText")
            params["reviewText"] = str(rt)
        if "status" in query:
            where_clauses.append("status = :status")
            params["status"] = str(query["status"])

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

    async def findOne(self, query: Dict) -> Optional[ProductReviewResponse]:
        if "id" in query:
            id_val = _to_int(query["id"])
            if id_val is not None:
                return await self.findById(id_val)
        records = await self.findAll(query)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[ProductReviewResponse]:
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

    async def create(self, data: ProductReviewsInternalCreate) -> ProductReviewResponse:
        factory = self._factory()
        now = now_utc()
        cols = ["created_at", "updated_at"]
        vals = [":c", ":u"]
        params = {"c": now, "u": now}
        if data.product_id is not None:
            cols.append("product_id")
            vals.append(":productId")
            params["productId"] = str(data.product_id)
        if data.user_id is not None:
            cols.append("user_id")
            vals.append(":userId")
            params["userId"] = str(data.user_id)
        if data.rating is not None:
            cols.append("rating")
            vals.append(":rating")
            params["rating"] = int(data.rating)
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
        async with factory() as session:
            res = await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = res.lastrowid
            await session.commit()
        return await self.findById(new_id)

    async def update(self, id: int, data: ProductReviewsInternalUpdate) -> Optional[ProductReviewResponse]:
        id_val = _to_int(id)
        if id_val is None:
            return None
        existing = await self.findById(id_val)
        if not existing:
            return None

        now = now_utc()
        updates = ["updated_at = :u"]
        params = {"id": id_val, "u": now}
        if data.product_id is not None:
            updates.append("product_id = :productId")
            params["productId"] = str(data.product_id)
        if data.user_id is not None:
            updates.append("user_id = :userId")
            params["userId"] = str(data.user_id)
        if data.rating is not None:
            updates.append("rating = :rating")
            params["rating"] = int(data.rating)
        if data.review_text is not None:
            updates.append("review_text = :reviewText")
            params["reviewText"] = data.review_text
        if data.status is not None:
            updates.append("status = :status")
            params["status"] = data.status

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
