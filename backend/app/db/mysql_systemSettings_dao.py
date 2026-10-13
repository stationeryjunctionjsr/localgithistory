"""
Strict SQLAlchemy DAO for sj_system_settings with native integer IDs and Pydantic models.
"""
from typing import List, Optional
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc
from app.models.system_settings import SystemSettingsResponse, SystemSettingsUpdate


class MySQLSystemSettingsDAO:
    TABLE = "sj_system_settings"

    def _map_to_schema(self, row) -> SystemSettingsResponse:
        return SystemSettingsResponse(
            id=row.id,
            maintenance_mode=bool(row.maintenance_mode) if ("maintenance_mode" in row._mapping and row.maintenance_mode is not None) else False,
            allow_signups=bool(row.allow_signups) if ("allow_signups" in row._mapping and row.allow_signups is not None) else False,
            max_upload_size_mb=row.max_upload_size_mb,
            default_currency=row.default_currency,
            timezone=row.timezone,
            created_at=row.created_at.isoformat() if row.created_at else None,
            updated_at=row.updated_at.isoformat() if row.updated_at else None,
        )

    async def findAll(
        self,
        maintenance_mode: Optional[bool] = None,
        allow_signups: Optional[bool] = None,
    ) -> List[SystemSettingsResponse]:
        where_clauses = []
        params = {}
        if maintenance_mode is not None:
            where_clauses.append("maintenance_mode = :maintenanceMode")
            params["maintenanceMode"] = 1 if maintenance_mode else 0
        if allow_signups is not None:
            where_clauses.append("allow_signups = :allowSignups")
            params["allowSignups"] = 1 if allow_signups else 0

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        async_session = get_async_session_factory()
        if not async_session:
            return []
        async with async_session() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"),
                    params,
                )
            ).fetchall()
        return [self._map_to_schema(r) for r in rows]

    async def findOne(self, id: Optional[int] = None) -> Optional[SystemSettingsResponse]:
        if id is not None:
            return await self.findById(id)
        records = await self.findAll()
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[SystemSettingsResponse]:
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

    async def create(self, data: SystemSettingsUpdate) -> SystemSettingsResponse:
        async_session = get_async_session_factory()
        if not async_session:
            raise RuntimeError("Database not available")
        now = now_utc()
        cols = ["created_at", "updated_at"]
        vals = [":c", ":u"]
        params = {"c": now, "u": now}
        if data.maintenance_mode is not None:
            cols.append("maintenance_mode")
            vals.append(":maintenanceMode")
            params["maintenanceMode"] = 1 if data.maintenance_mode else 0
        if data.allow_signups is not None:
            cols.append("allow_signups")
            vals.append(":allowSignups")
            params["allowSignups"] = 1 if data.allow_signups else 0
        if data.max_upload_size_mb is not None:
            cols.append("max_upload_size_mb")
            vals.append(":maxUploadSizeMb")
            params["maxUploadSizeMb"] = data.max_upload_size_mb
        if data.default_currency is not None:
            cols.append("default_currency")
            vals.append(":defaultCurrency")
            params["defaultCurrency"] = data.default_currency
        if data.timezone is not None:
            cols.append("timezone")
            vals.append(":timezone")
            params["timezone"] = data.timezone

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

    async def update(self, id: int, data: SystemSettingsUpdate) -> Optional[SystemSettingsResponse]:
        if not id:
            return None
        async_session = get_async_session_factory()
        if not async_session:
            return None

        now = now_utc()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now}

        if "maintenance_mode" in data.model_fields_set:
            updates.append("maintenance_mode = :maintenanceMode")
            params["maintenanceMode"] = 1 if data.maintenance_mode else 0

        if "allow_signups" in data.model_fields_set:
            updates.append("allow_signups = :allowSignups")
            params["allowSignups"] = 1 if data.allow_signups else 0

        if "max_upload_size_mb" in data.model_fields_set:
            updates.append("max_upload_size_mb = :maxUploadSizeMb")
            params["maxUploadSizeMb"] = data.max_upload_size_mb

        if "default_currency" in data.model_fields_set:
            updates.append("default_currency = :defaultCurrency")
            params["defaultCurrency"] = data.default_currency

        if "timezone" in data.model_fields_set:
            updates.append("timezone = :timezone")
            params["timezone"] = data.timezone

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
