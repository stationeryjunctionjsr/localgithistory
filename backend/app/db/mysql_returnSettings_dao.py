from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import ReturnSettingsInternal, ReturnSettingsInternalCreate, ReturnSettingsInternalUpdate

def now_utc():
    return datetime.now(timezone.utc)

class MySQLReturnSettingsDAO:
    def __init__(self):
        self.table_name = "sj_return_settings"
    
    @property
    def TABLE(self):
        return self.table_name

    async def findById(self, id: int) -> Optional[ReturnSettingsInternal]:
        if not id:
            return None
        async_session = get_async_session_factory()
        if not async_session:
            return None
        async with async_session() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE id = :id LIMIT 1")
            result = await session.execute(q, {"id": id})
            row = result.fetchone()
            if not row:
                return None
            return self._map_to_schema(row)

    async def findOne(self, id: Optional[int] = None) -> Optional[ReturnSettingsInternal]:
        if id:
            return await self.findById(id)
        all_settings = await self.findAll()
        return all_settings[0] if all_settings else None
            
    async def findAll(self) -> List[ReturnSettingsInternal]:
        async_session = get_async_session_factory()
        if not async_session:
            return []
        async with async_session() as session:
            q = text(f"SELECT * FROM {self.TABLE} ORDER BY id ASC")
            result = await session.execute(q)
            rows = result.fetchall()
            return [self._map_to_schema(r) for r in rows]

    async def create(self, data: ReturnSettingsInternalCreate) -> ReturnSettingsInternal:
        async_session = get_async_session_factory()
        if not async_session:
            raise RuntimeError("Database session factory unavailable")
        now = now_utc()
        
        cols = ["created_at", "updated_at"]
        val_placeholders = [":c", ":u"]
        params = {"c": now, "u": now}

        if data.return_days is not None:
            cols.append("return_days")
            val_placeholders.append(":return_days")
            params["return_days"] = data.return_days

        col_sql = ", ".join(cols)
        val_sql = ", ".join(val_placeholders)
        
        async with async_session() as session:
            result = await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = result.lastrowid
            await session.commit()
            
        return await self.findById(new_id)

    async def update(self, id: int, update_data: ReturnSettingsInternalUpdate) -> Optional[ReturnSettingsInternal]:
        async_session = get_async_session_factory()
        if not async_session or not id:
            return None

        fields = update_data.model_fields_set
        if not fields:
            return await self.findById(id)

        updates = ["updated_at = :u"]
        params = {"u": now_utc(), "id": id}

        if "return_days" in fields:
            updates.append("return_days = :return_days")
            params["return_days"] = update_data.return_days

        upd_sql = ", ".join(updates)
        async with async_session() as session:
            await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE id = :id"), params)
            await session.commit()
                
        return await self.findById(id)

    async def delete(self, id: int) -> bool:
        async_session = get_async_session_factory()
        if not async_session or not id:
            return False
        async with async_session() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": id},
            )
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(self, r) -> ReturnSettingsInternal:
        return ReturnSettingsInternal(
            id=r.id,
            return_days=int(r.return_days) if r.return_days is not None else None,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
