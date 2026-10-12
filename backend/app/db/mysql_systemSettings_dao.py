"""
Strict SQLAlchemy DAO for sj_system_settings with native integer IDs and Pydantic models.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc
from app.models.system_settings import SystemSettingsResponse, SystemSettingsUpdate


def _to_int(val: Any) -> Optional[int]:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


class MySQLSystemSettingsDAO:
    TABLE = "sj_system_settings"

    def _factory(self):
        return get_async_session_factory()

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

    async def findAll(self, query: Optional[Dict] = None) -> List[SystemSettingsResponse]:
        query = query or {}
        where_clauses = []
        params = {}
        if "maintenanceMode" in query:
            where_clauses.append("maintenance_mode = :maintenanceMode")
            params["maintenanceMode"] = 1 if query["maintenanceMode"] else 0
        if "allowSignups" in query:
            where_clauses.append("allow_signups = :allowSignups")
            params["allowSignups"] = 1 if query["allowSignups"] else 0
        if "maxUploadSizeMb" in query:
            where_clauses.append("max_upload_size_mb = :maxUploadSizeMb")
            params["maxUploadSizeMb"] = _to_int(query["maxUploadSizeMb"])
        if "defaultCurrency" in query:
            where_clauses.append("default_currency = :defaultCurrency")
            params["defaultCurrency"] = query["defaultCurrency"]
        if "timezone" in query:
            where_clauses.append("timezone = :timezone")
            params["timezone"] = query["timezone"]

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

    async def findOne(self, query: Dict) -> Optional[SystemSettingsResponse]:
        if "id" in query:
            id_val = _to_int(query["id"])
            if id_val is not None:
                return await self.findById(id_val)
        records = await self.findAll(query)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[SystemSettingsResponse]:
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

    async def create(self, data: SystemSettingsUpdate) -> SystemSettingsResponse:
        factory = self._factory()
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
        async with factory() as session:
            res = await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = res.lastrowid
            await session.commit()
        return await self.findById(new_id)

    async def update(self, id: int, data: SystemSettingsUpdate) -> Optional[SystemSettingsResponse]:
        id_val = _to_int(id)
        if id_val is None:
            return None
        existing = await self.findById(id_val)
        if not existing:
            return None

        now = now_utc()
        updates = ["updated_at = :u"]
        params = {"id": id_val, "u": now}
        if data.maintenance_mode is not None:
            updates.append("maintenance_mode = :maintenanceMode")
            params["maintenanceMode"] = 1 if data.maintenance_mode else 0
        if data.allow_signups is not None:
            updates.append("allow_signups = :allowSignups")
            params["allowSignups"] = 1 if data.allow_signups else 0
        if data.max_upload_size_mb is not None:
            updates.append("max_upload_size_mb = :maxUploadSizeMb")
            params["maxUploadSizeMb"] = data.max_upload_size_mb
        if data.default_currency is not None:
            updates.append("default_currency = :defaultCurrency")
            params["defaultCurrency"] = data.default_currency
        if data.timezone is not None:
            updates.append("timezone = :timezone")
            params["timezone"] = data.timezone

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
