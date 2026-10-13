"""
Strict SQLAlchemy DAO for sj_valet_payout_settings with native integer IDs and Pydantic models.
"""
from typing import List, Optional
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc
from app.models.valet_payout_settings import ValetPayoutSettings
from app.models.daos_flat import (
    ValetPayoutSettingsInternalCreate,
    ValetPayoutSettingsInternalUpdate,
)


class MySQLValetPayoutSettingsDAO:
    TABLE = "sj_valet_payout_settings"

    def _map_to_schema(self, row) -> ValetPayoutSettings:
        return ValetPayoutSettings(
            id=row.id,
            delivery_charge_per_order=float(row.delivery_charge_per_order) if row.delivery_charge_per_order is not None else 0.0,
            return_pickup_charge_per_order=float(row.return_pickup_charge_per_order) if row.return_pickup_charge_per_order is not None else 0.0,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def findAll(self) -> List[ValetPayoutSettings]:
        async_session = get_async_session_factory()
        if not async_session:
            return []
        async with async_session() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} ORDER BY id ASC")
                )
            ).fetchall()
        return [self._map_to_schema(r) for r in rows]

    async def findOne(self, id: Optional[int] = None) -> Optional[ValetPayoutSettings]:
        if id is not None:
            return await self.findById(id)
        records = await self.findAll()
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[ValetPayoutSettings]:
        if not id:
            return None
        async_session = get_async_session_factory()
        if not async_session:
            return None
        async with async_session() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": id},
                )
            ).fetchone()
        return self._map_to_schema(row) if row else None

    async def create(self, data: ValetPayoutSettingsInternalCreate) -> ValetPayoutSettings:
        async_session = get_async_session_factory()
        if not async_session:
            raise RuntimeError("Database not available")
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
        async with async_session() as session:
            res = await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = res.lastrowid
            await session.commit()
        return await self.findById(new_id)

    async def update(self, id: int, data: ValetPayoutSettingsInternalUpdate) -> Optional[ValetPayoutSettings]:
        if not id:
            return None
        async_session = get_async_session_factory()
        if not async_session:
            return None

        now = now_utc()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now}

        if "delivery_charge_per_order" in data.model_fields_set:
            updates.append("delivery_charge_per_order = :deliveryChargePerOrder")
            params["deliveryChargePerOrder"] = data.delivery_charge_per_order

        if "return_pickup_charge_per_order" in data.model_fields_set:
            updates.append("return_pickup_charge_per_order = :returnPickupChargePerOrder")
            params["returnPickupChargePerOrder"] = data.return_pickup_charge_per_order

        set_sql = ", ".join(updates)
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
        if not async_session:
            return False
        async with async_session() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": id},
            )
            await session.commit()
            return res.rowcount > 0
