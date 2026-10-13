"""
Strict SQLAlchemy DAO for sj_stock_reservations with native integer IDs and Pydantic models.
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc
from app.models.stock_reservation import StockReservation, ProductReservedStock
from app.models.daos_flat import (
    StockReservationsInternalCreate,
    StockReservationsInternalUpdate,
)


class MySQLStockReservationsDAO:
    TABLE = "sj_stock_reservations"

    def _factory(self):
        return get_async_session_factory()

    def _map_to_schema(self, row) -> StockReservation:
        return StockReservation(
            id=row.id,
            productId=row.product_id,
            userId=row.user_id,
            quantity=row.quantity or 0,
            status=row.status or "active",
            expiresAt=row.expires_at,
            createdAt=row.created_at,
            updatedAt=row.updated_at,
        )

    async def get_reserved_quantities_by_product_ids(
        self, product_ids: List[str], exclude_user_id: Optional[str] = None
    ) -> List[ProductReservedStock]:
        if not product_ids:
            return []
        factory = self._factory()
        if not factory:
            return []
        now = now_utc()

        placeholders = [f":pid_{i}" for i in range(len(product_ids))]
        params = {f"pid_{i}": pid for i, pid in enumerate(product_ids)}
        params["status"] = "active"
        params["now"] = now

        user_clause = ""
        if exclude_user_id:
            user_clause = "AND (user_id IS NULL OR user_id != :exclude_uid)"
            params["exclude_uid"] = exclude_user_id

        sql = f"""
            SELECT product_id, SUM(quantity) as total_reserved
            FROM {self.TABLE}
            WHERE status = :status
              AND expires_at > :now
              AND product_id IN ({', '.join(placeholders)})
              {user_clause}
            GROUP BY product_id
        """
        async with factory() as session:
            rows = (await session.execute(text(sql), params)).fetchall()
            return [
                ProductReservedStock(
                    product_id=r.product_id,
                    reserved_quantity=int(r.total_reserved or 0),
                )
                for r in rows
            ]

    async def findAll(
        self,
        product_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[StockReservation]:
        factory = self._factory()
        if not factory:
            return []
        where_clauses = []
        params = {}
        if product_id is not None:
            where_clauses.append("product_id = :productId")
            params["productId"] = product_id
        if user_id is not None:
            where_clauses.append("user_id = :userId")
            params["userId"] = user_id
        if status is not None:
            where_clauses.append("status = :status")
            params["status"] = status

        where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE}{where_sql} ORDER BY id ASC"),
                    params,
                )
            ).fetchall()
        return [self._map_to_schema(r) for r in rows]

    async def findOne(
        self,
        product_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Optional[StockReservation]:
        records = await self.findAll(product_id=product_id, user_id=user_id, status=status)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[StockReservation]:
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

    async def create(self, data: StockReservationsInternalCreate) -> Optional[StockReservation]:
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
        if data.user_id is not None:
            cols.append("user_id")
            vals.append(":userId")
            params["userId"] = data.user_id
        if data.quantity is not None:
            cols.append("quantity")
            vals.append(":quantity")
            params["quantity"] = data.quantity
        if data.status is not None:
            cols.append("status")
            vals.append(":status")
            params["status"] = data.status
        if data.expires_at is not None:
            cols.append("expires_at")
            vals.append(":expiresAt")
            exp = str(data.expires_at)
            if exp.endswith("Z"):
                exp = exp[:-1]
                if not exp.endswith("+00:00") and "+" not in exp[-6:] and "-" not in exp[-6:]:
                    exp += "+00:00"
            params["expiresAt"] = datetime.fromisoformat(exp).replace(tzinfo=None)

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

    async def update(self, id: int, data: StockReservationsInternalUpdate) -> Optional[StockReservation]:
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

        if "user_id" in data.model_fields_set:
            updates.append("user_id = :userId")
            params["userId"] = data.user_id

        if "quantity" in data.model_fields_set:
            updates.append("quantity = :quantity")
            params["quantity"] = data.quantity

        if "status" in data.model_fields_set:
            updates.append("status = :status")
            params["status"] = data.status

        if "expires_at" in data.model_fields_set:
            updates.append("expires_at = :expiresAt")
            exp = str(data.expires_at) if data.expires_at is not None else None
            if exp and exp.endswith("Z"):
                exp = exp[:-1]
                if not exp.endswith("+00:00") and "+" not in exp[-6:] and "-" not in exp[-6:]:
                    exp += "+00:00"
            params["expiresAt"] = datetime.fromisoformat(exp).replace(tzinfo=None) if exp else None

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

    async def cleanup_expired(self) -> int:
        now = now_utc()
        factory = self._factory()
        if not factory:
            return 0
        async with factory() as session:
            res = await session.execute(
                text(f"UPDATE {self.TABLE} SET status = 'expired', updated_at = :now WHERE status = 'active' AND expires_at <= :now"),
                {"now": now},
            )
            await session.commit()
            return res.rowcount or 0
