from typing import Optional, List, Union
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

    def _factory(self):
        return get_async_session_factory()
        
    async def findById(self, id: Union[int, str]) -> Optional[ReturnSettingsInternal]:
        if not id:
            return None
        pid = int(id) if str(id).isdigit() else None
        if pid is None:
            return None
        async with self._factory()() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE id = :id LIMIT 1")
            result = await session.execute(q, {"id": pid})
            row = result.fetchone()
            if not row:
                return None
            return self._map_to_schema(row)

    async def findOne(self, id: Optional[Union[int, str]] = None) -> Optional[ReturnSettingsInternal]:
        if id:
            return await self.findById(id)
        all_settings = await self.findAll()
        return all_settings[0] if all_settings else None
            
    async def findAll(self) -> List[ReturnSettingsInternal]:
        async with self._factory()() as session:
            q = text(f"SELECT * FROM {self.TABLE} ORDER BY id ASC")
            result = await session.execute(q)
            rows = result.fetchall()
            return [self._map_to_schema(r) for r in rows]

    async def create(self, data: ReturnSettingsInternalCreate) -> ReturnSettingsInternal:
        factory = self._factory()
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
        
        async with factory() as session:
            result = await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = result.lastrowid
            await session.commit()
            
        return await self.findById(int(new_id))

    async def update(self, id: Union[int, str], update_data: ReturnSettingsInternalUpdate) -> Optional[ReturnSettingsInternal]:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        if not pid:
            return None
        updates = ["updated_at = :u"]
        params = {"u": now_utc(), "id": pid}

        if update_data.return_days is not None:
            updates.append("return_days = :return_days")
            params["return_days"] = update_data.return_days

        upd_sql = ", ".join(updates)
        async with factory() as session:
            await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE id = :id"), params)
            await session.commit()
                
        return await self.findById(pid)

    async def delete(self, id: Union[int, str]) -> bool:
        factory = self._factory()
        if not factory or not id:
            return False
        pid = int(id) if str(id).isdigit() else None
        if not pid:
            return False
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pid},
            )
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(self, r) -> ReturnSettingsInternal:
        return ReturnSettingsInternal(
            id=str(r.id),
            return_days=int(r.return_days) if r.return_days is not None else None,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
