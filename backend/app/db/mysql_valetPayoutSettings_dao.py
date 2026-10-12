"""
Strict SQLAlchemy DAO for sj_valet_payout_settings with native integer IDs and Pydantic models.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc
from app.models.valet_payout_settings import ValetPayoutSettings
from app.models.daos_flat import (
    ValetPayoutSettingsInternalCreate,
    ValetPayoutSettingsInternalUpdate,
)


def _to_int(val: Any) -> Optional[int]:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


class MySQLValetPayoutSettingsDAO:
    TABLE = "sj_valet_payout_settings"

    def _factory(self):
        return get_async_session_factory()

    def _map_to_schema(self, row) -> ValetPayoutSettings:
        return ValetPayoutSettings(
            id=row.id,
            delivery_charge_per_order=float(row.delivery_charge_per_order) if row.delivery_charge_per_order is not None else 0.0,
            return_pickup_charge_per_order=float(row.return_pickup_charge_per_order) if row.return_pickup_charge_per_order is not None else 0.0,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def findAll(self, query: Optional[Dict] = None) -> List[ValetPayoutSettings]:
        query = query or {}
        where_clauses = []
        params = {}
        if "deliveryChargePerOrder" in query:
            where_clauses.append("delivery_charge_per_order = :deliveryChargePerOrder")
            params["deliveryChargePerOrder"] = query["deliveryChargePerOrder"]
        if "returnPickupChargePerOrder" in query:
            where_clauses.append("return_pickup_charge_per_order = :returnPickupChargePerOrder")
            params["returnPickupChargePerOrder"] = query["returnPickupChargePerOrder"]

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

    async def findOne(self, query: Dict) -> Optional[ValetPayoutSettings]:
        if "id" in query:
            id_val = _to_int(query["id"])
            if id_val is not None:
                return await self.findById(id_val)
        records = await self.findAll(query)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[ValetPayoutSettings]:
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

    async def create(self, data: ValetPayoutSettingsInternalCreate) -> ValetPayoutSettings:
        factory = self._factory()
        now = now_utc()
        cols = ["created_at", "updated_at"]
        vals = [":c", ":u"]
        params = {"c": now, "u": now}
        if data.delivery_charge_per_order is not None:
            cols.append("delivery_charge_per_order")
            vals.append(":deliveryChargePerOrder")
            params["deliveryChargePerOrder"] = data.delivery_charge_per_order
        if data.return_pickup_charge_per_order is not None:
            cols.append("return_pickup_charge_per_order")
            vals.append(":returnPickupChargePerOrder")
            params["returnPickupChargePerOrder"] = data.return_pickup_charge_per_order

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

    async def update(self, id: int, data: ValetPayoutSettingsInternalUpdate) -> Optional[ValetPayoutSettings]:
        id_val = _to_int(id)
        if id_val is None:
            return None
        existing = await self.findById(id_val)
        if not existing:
            return None

        now = now_utc()
        updates = ["updated_at = :u"]
        params = {"id": id_val, "u": now}
        if data.delivery_charge_per_order is not None:
            updates.append("delivery_charge_per_order = :deliveryChargePerOrder")
            params["deliveryChargePerOrder"] = data.delivery_charge_per_order
        if data.return_pickup_charge_per_order is not None:
            updates.append("return_pickup_charge_per_order = :returnPickupChargePerOrder")
            params["returnPickupChargePerOrder"] = data.return_pickup_charge_per_order

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
