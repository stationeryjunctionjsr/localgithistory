"""
Strict SQLAlchemy DAO for sj_stock_reservations with native integer IDs and Pydantic models.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc
from app.models.stock_reservation import StockReservation, ProductReservedStock
from app.models.daos_flat import (
    StockReservationsInternalCreate,
    StockReservationsInternalUpdate,
)


def _to_int(val: Any) -> Optional[int]:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


class MySQLStockReservationsDAO:
    TABLE = "sj_stock_reservations"

    def _factory(self):
        return get_async_session_factory()

    def _map_to_schema(self, row) -> StockReservation:
        return StockReservation(
            id=row.id,
            productId=str(row.product_id),
            userId=str(row.user_id) if row.user_id is not None else None,
            quantity=int(row.quantity),
            status=str(row.status),
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
        now = now_utc()

        placeholders = [f":pid_{i}" for i in range(len(product_ids))]
        params = {f"pid_{i}": str(pid) for i, pid in enumerate(product_ids)}
        params["status"] = "active"
        params["now"] = now

        user_clause = ""
        if exclude_user_id:
            user_clause = "AND (user_id IS NULL OR user_id != :exclude_uid)"
            params["exclude_uid"] = str(exclude_user_id)

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
                    product_id=str(r.product_id),
                    reserved_quantity=int(r.total_reserved or 0),
                )
                for r in rows
            ]

    async def findAll(self, query: Optional[Dict] = None) -> List[StockReservation]:
        query = query or {}
        where_clauses = []
        params = {}
        if "productId" in query:
            where_clauses.append("product_id = :productId")
            params["productId"] = query["productId"]
        if "userId" in query:
            where_clauses.append("user_id = :userId")
            params["userId"] = query["userId"]
        if "quantity" in query:
            where_clauses.append("quantity = :quantity")
            params["quantity"] = query["quantity"]
        if "status" in query:
            where_clauses.append("status = :status")
            params["status"] = query["status"]
        if "expiresAt" in query:
            where_clauses.append("expires_at = :expiresAt")
            params["expiresAt"] = query["expiresAt"]

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

    async def findOne(self, query: Dict) -> Optional[StockReservation]:
        if "id" in query:
            id_val = _to_int(query["id"])
            if id_val is not None:
                return await self.findById(id_val)
        records = await self.findAll(query)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[StockReservation]:
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

    async def create(self, data: StockReservationsInternalCreate) -> StockReservation:
        factory = self._factory()
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
        id_val = _to_int(id)
        if id_val is None:
            return None
        existing = await self.findById(id_val)
        if not existing:
            return None
        now = now_utc()
        updates = ["updated_at = :u"]
        params = {"id": id_val, "u": now}

        product_id = data.product_id if data.product_id is not None else existing.product_id
        if product_id is not None:
            updates.append("product_id = :productId")
            params["productId"] = product_id

        user_id = data.user_id if data.user_id is not None else existing.user_id
        if user_id is not None:
            updates.append("user_id = :userId")
            params["userId"] = user_id

        quantity = data.quantity if data.quantity is not None else existing.quantity
        if quantity is not None:
            updates.append("quantity = :quantity")
            params["quantity"] = quantity

        status = data.status if data.status is not None else existing.status
        if status is not None:
            updates.append("status = :status")
            params["status"] = status

        expires_at = data.expires_at if data.expires_at is not None else existing.expires_at
        if expires_at is not None:
            updates.append("expires_at = :expiresAt")
            params["expiresAt"] = expires_at

        set_clause = ", ".join(updates)
        q = f"UPDATE {self.TABLE} SET {set_clause} WHERE id = :id"
        factory = self._factory()
        async with factory() as session:
            await session.execute(text(q), params)
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
