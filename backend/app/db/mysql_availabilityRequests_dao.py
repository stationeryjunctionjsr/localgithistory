"""
Strict SQLAlchemy DAO for sj_availability_requests with native integer IDs and Pydantic models.
"""
from typing import List, Optional
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc
from app.models.availability_requests import AvailabilityRequestResponse, AvailabilityRequestFilter
from app.models.daos_flat import (
    AvailabilityRequestsInternalCreate,
    AvailabilityRequestsInternalUpdate,
)


class MySQLAvailabilityRequestsDAO:
    TABLE = "sj_availability_requests"

    def _factory(self):
        return get_async_session_factory()

    def _map_to_schema(self, row) -> AvailabilityRequestResponse:
        return AvailabilityRequestResponse(
            id=row.id,
            productId=row.product_id,
            productName=row.product_name,
            pincode=row.pincode,
            userName=row.user_name,
            userEmail=row.user_email,
            status=row.status if "status" in row._mapping and row.status is not None else "pending",
            createdAt=row.created_at,
            updatedAt=row.updated_at,
        )

    async def count(self, filters: Optional[AvailabilityRequestFilter] = None) -> int:
        factory = self._factory()
        if not factory:
            return 0
        where_clauses = []
        params = {}
        if filters:
            if filters.product_id:
                where_clauses.append("product_id = :product_id")
                params["product_id"] = filters.product_id.strip()
            if filters.product_name:
                where_clauses.append("product_name = :product_name")
                params["product_name"] = filters.product_name.strip()
            if filters.pincode:
                where_clauses.append("pincode = :pincode")
                params["pincode"] = filters.pincode.strip()
            if filters.user_name:
                where_clauses.append("user_name = :user_name")
                params["user_name"] = filters.user_name.strip()
            if filters.user_email:
                where_clauses.append("user_email = :user_email")
                params["user_email"] = filters.user_email.strip()
            if filters.status:
                where_clauses.append("status = :status")
                params["status"] = filters.status.strip()
        where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        async with factory() as session:
            count_val = (
                await session.execute(
                    text(f"SELECT COUNT(*) FROM {self.TABLE}{where_sql}"),
                    params,
                )
            ).scalar()
        return count_val or 0

    async def findAll(
        self,
        filters: Optional[AvailabilityRequestFilter] = None,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        order_by: str = "created_at DESC, id DESC",
    ) -> List[AvailabilityRequestResponse]:
        factory = self._factory()
        if not factory:
            return []
        where_clauses = []
        params = {}
        if filters:
            if filters.product_id:
                where_clauses.append("product_id = :product_id")
                params["product_id"] = filters.product_id.strip()
            if filters.product_name:
                where_clauses.append("product_name = :product_name")
                params["product_name"] = filters.product_name.strip()
            if filters.pincode:
                where_clauses.append("pincode = :pincode")
                params["pincode"] = filters.pincode.strip()
            if filters.user_name:
                where_clauses.append("user_name = :user_name")
                params["user_name"] = filters.user_name.strip()
            if filters.user_email:
                where_clauses.append("user_email = :user_email")
                params["user_email"] = filters.user_email.strip()
            if filters.status:
                where_clauses.append("status = :status")
                params["status"] = filters.status.strip()

        where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        pagination_sql = ""
        if limit is not None:
            pagination_sql += " LIMIT :limit"
            params["limit"] = limit
            if skip is not None:
                pagination_sql += " OFFSET :skip"
                params["skip"] = skip

        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE}{where_sql} ORDER BY {order_by}{pagination_sql}"),
                    params,
                )
            ).fetchall()
        return [self._map_to_schema(r) for r in rows]

    async def findOne(
        self,
        filters: Optional[AvailabilityRequestFilter] = None,
    ) -> Optional[AvailabilityRequestResponse]:
        records = await self.findAll(filters=filters, limit=1)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[AvailabilityRequestResponse]:
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

    async def create(self, data: AvailabilityRequestsInternalCreate) -> Optional[AvailabilityRequestResponse]:
        factory = self._factory()
        if not factory:
            return None
        now = now_utc()
        cols = ["created_at", "updated_at"]
        vals = [":c", ":u"]
        params = {"c": now, "u": now}
        if data.product_id is not None:
            cols.append("product_id")
            vals.append(":productId")
            params["productId"] = data.product_id
        if data.product_name is not None:
            cols.append("product_name")
            vals.append(":productName")
            params["productName"] = data.product_name
        if data.pincode is not None:
            cols.append("pincode")
            vals.append(":pincode")
            params["pincode"] = data.pincode
        if data.user_name is not None:
            cols.append("user_name")
            vals.append(":userName")
            params["userName"] = data.user_name
        if data.user_email is not None:
            cols.append("user_email")
            vals.append(":userEmail")
            params["userEmail"] = data.user_email

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

    async def update(self, id: int, data: AvailabilityRequestsInternalUpdate) -> Optional[AvailabilityRequestResponse]:
        if not id:
            return None
        factory = self._factory()
        if not factory:
            return None

        now = now_utc()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now}

        if "product_id" in data.model_fields_set:
            updates.append("product_id = :productId")
            params["productId"] = data.product_id

        if "product_name" in data.model_fields_set:
            updates.append("product_name = :productName")
            params["productName"] = data.product_name

        if "pincode" in data.model_fields_set:
            updates.append("pincode = :pincode")
            params["pincode"] = data.pincode

        if "user_name" in data.model_fields_set:
            updates.append("user_name = :userName")
            params["userName"] = data.user_name

        if "user_email" in data.model_fields_set:
            updates.append("user_email = :userEmail")
            params["userEmail"] = data.user_email

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
