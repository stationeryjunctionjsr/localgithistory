"""
Strict SQLAlchemy DAO for sj_product_notifications with native integer IDs and Pydantic models.
"""
from typing import List, Optional
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc
from app.models.daos_flat import (
    ProductNotificationsInternal,
    ProductNotificationsInternalCreate,
    ProductNotificationsInternalUpdate,
)


class MySQLProductNotificationsDAO:
    TABLE = "sj_product_notifications"

    def _map_to_schema(self, row) -> ProductNotificationsInternal:
        return ProductNotificationsInternal(
            id=row.id,
            product_id=row.product_id,
            user_id=row.user_id,
            email=row.email,
            phone=row.phone,
            status=row.status or "active",
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def findAll(
        self,
        product_id: Optional[int] = None,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[ProductNotificationsInternal]:
        async_session = get_async_session_factory()
        where_clauses = []
        params = {}
        if product_id is not None:
            where_clauses.append("product_id = :productId")
            params["productId"] = product_id
        if user_id is not None:
            where_clauses.append("user_id = :userId")
            params["userId"] = user_id
        if email is not None:
            where_clauses.append("email = :email")
            params["email"] = email
        if phone is not None:
            where_clauses.append("phone = :phone")
            params["phone"] = phone
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
        email: Optional[str] = None,
        phone: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Optional[ProductNotificationsInternal]:
        records = await self.findAll(product_id=product_id, user_id=user_id, email=email, phone=phone, status=status)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[ProductNotificationsInternal]:
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

    async def create(self, data: ProductNotificationsInternalCreate) -> Optional[ProductNotificationsInternal]:
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
        if data.email is not None:
            cols.append("email")
            vals.append(":email")
            params["email"] = data.email
        if data.phone is not None:
            cols.append("phone")
            vals.append(":phone")
            params["phone"] = data.phone
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

    async def update(self, id: int, data: ProductNotificationsInternalUpdate) -> Optional[ProductNotificationsInternal]:
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

        if "email" in data.model_fields_set:
            updates.append("email = :email")
            params["email"] = data.email

        if "phone" in data.model_fields_set:
            updates.append("phone = :phone")
            params["phone"] = data.phone

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
