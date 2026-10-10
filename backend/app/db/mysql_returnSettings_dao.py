from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import secrets
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
        
    async def findById(self, id: str) -> Optional[ReturnSettingsInternal]:
        pk = int(id) if str(id).isdigit() else None
        if pk is None:
            return None
        async with self._factory()() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE id = :id LIMIT 1")
            result = await session.execute(q, {"id": pk})
            row = result.fetchone()
            if not row:
                return None
            return self._map_to_schema(row)

    async def findOne(self, query: Optional[dict] = None, **kwargs) -> Optional[ReturnSettingsInternal]:
        params_dict = {}
        if query:
            params_dict.update(query)
        params_dict.update(kwargs)
        if not params_dict:
            return None
        
        async with self._factory()() as session:
            conditions = []
            params: Dict[str, Any] = {}
            for k, v in params_dict.items():
                if k in ("_id", "id"):
                    conditions.append("id = :id")
                    params["id"] = int(v) if str(v).isdigit() else v
                elif k in ("externalId", "external_id"):
                    conditions.append("external_id = :external_id")
                    params["external_id"] = str(v)
                elif k in ("returnDays", "return_days"):
                    conditions.append("return_days = :return_days")
                    params["return_days"] = int(v)
                else:
                    conditions.append(f"{k} = :{k}")
                    params[k] = v
                
            where_clause = " AND ".join(conditions)
            q = text(f"SELECT * FROM {self.TABLE} WHERE {where_clause} LIMIT 1")
            result = await session.execute(q, params)
            row = result.fetchone()
            if not row:
                return None
            return self._map_to_schema(row)
            
    async def findAll(self, query: Optional[dict] = None) -> List[ReturnSettingsInternal]:
        async with self._factory()() as session:
            conditions = []
            params: Dict[str, Any] = {}
            if query:
                for k, v in query.items():
                    if k in ("_id", "id"):
                        conditions.append("id = :id")
                        params["id"] = int(v) if str(v).isdigit() else v
                    elif k in ("externalId", "external_id"):
                        conditions.append("external_id = :external_id")
                        params["external_id"] = str(v)
                    elif k in ("returnDays", "return_days"):
                        conditions.append("return_days = :return_days")
                        params["return_days"] = int(v)
                    else:
                        conditions.append(f"{k} = :{k}")
                        params[k] = v
                        
            sql = f"SELECT * FROM {self.TABLE}"
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
                    
            q = text(sql)
            result = await session.execute(q, params)
            rows = result.fetchall()
            return [self._map_to_schema(r) for r in rows]

    async def create(self, data: ReturnSettingsInternalCreate) -> ReturnSettingsInternal:
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        val_placeholders = [":eid", ":c", ":u"]
        params: Dict[str, Any] = {"eid": external_id, "c": now, "u": now}

        if data.return_days is not None:
            cols.append("return_days")
            val_placeholders.append(":return_days")
            params["return_days"] = data.return_days

        col_sql = ", ".join(cols)
        val_sql = ", ".join(val_placeholders)
        
        async with factory() as session:
            await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = (
                await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": external_id}
                )
            ).scalar()
            await session.commit()
            
        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: ReturnSettingsInternalUpdate) -> ReturnSettingsInternal:
        factory = self._factory()
        updates = ["updated_at = :u"]
        params: Dict[str, Any] = {"id": int(id) if str(id).isdigit() else id, "u": now_utc()}

        if update_data.return_days is not None:
            updates.append("return_days = :return_days")
            params["return_days"] = update_data.return_days

        upd_sql = ", ".join(updates)
        async with factory() as session:
            await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE id = :id"), params)
            await session.commit()
                
        return await self.findById(str(id))

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        pk = int(id) if str(id).isdigit() else None
        if pk is None:
            return False
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pk},
            )
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(self, r) -> ReturnSettingsInternal:
        return ReturnSettingsInternal(
            id=str(r.id),
            external_id=getattr(r, "external_id", None),
            return_days=int(r.return_days) if getattr(r, "return_days", None) is not None else None,
            created_at=getattr(r, "created_at", None),
            updated_at=getattr(r, "updated_at", None),
        )
