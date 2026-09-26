import re
import secrets
from typing import Optional, Dict, List, Any
from datetime import datetime

from sqlalchemy import text
from pydantic import BaseModel
from app.models.base import CamelBaseModel

from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc

class EventPayloadItem(CamelBaseModel):
    key: str
    value: str

class EventCreate(CamelBaseModel):
    event_type: Optional[str] = None
    payload: Optional[List[EventPayloadItem]] = None
    tracking_id: Optional[int] = None

class EventUpdate(CamelBaseModel):
    event_type: Optional[str] = None
    payload: Optional[List[EventPayloadItem]] = None

class EventResponse(CamelBaseModel):
    id: str
    external_id: str
    event_type: Optional[str] = None
    payload: Optional[List[EventPayloadItem]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class MySQLEventsDAO:
    TABLE = "sj_events"

    def _factory(self):
        return get_async_session_factory()

    async def findAll(self, query: Optional[Dict] = None) -> List[EventResponse]:
        query = query or {}
        where_clauses = []
        params = {}
        
        if "event_type" in query:
            where_clauses.append("event_type = :event_type")
            params["event_type"] = query["event_type"]
            
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        factory = self._factory()
        
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT e.*, t.session_id, t.user_id, t.ip_address, t.os, t.browser, t.campaign, t.source, t.device_type, t.device_os_version, t.device_model, t.device_app_version FROM {self.TABLE} e LEFT JOIN sj_tracking t ON e.tracking_id = t.id WHERE {where_sql.replace('event_type', 'e.event_type')} ORDER BY e.id ASC"),
                    params,
                )
            ).fetchall()
            
            if not rows:
                return []
                
            ids = [r.id for r in rows]
            id_placeholders = ", ".join([f":id_{i}" for i in range(len(ids))])
            id_params = {f"id_{i}": pid for i, pid in enumerate(ids)}
            
            payload_map = {pid: [] for pid in ids}
            

        # Unmap flat columns back to payload
        valid_columns = {
            "session_id": "sessionId", "user_id": "userId", "ip_address": "ipAddress", 
            "os": "os", "browser": "browser", "campaign": "campaign", "source": "source",
            "product_id": "productId", "product_name": "productName", "quantity": "quantity", 
            "query": "query", "results_count": "resultsCount", "reason": "reason",
            "page": "page", "screen": "screen", "test_run_id": "testRunId", 
            "device_type": "device_type", 
            "device_os_version": "device_os_version", "device_model": "device_model", 
            "device_app_version": "device_app_version"
        }

        result = []
        for r in rows:
            result.append(EventResponse(
                id=str(r.id),
                external_id=r.external_id,
                event_type=r.event_type,
                payload=[EventPayloadItem(key=k_camel, value=str(getattr(r, k_db))) for k_db, k_camel in valid_columns.items() if hasattr(r, k_db) and getattr(r, k_db) is not None],
                created_at=r.created_at,
                updated_at=r.updated_at
            ))

            
        return result

    async def findOne(self, query: Dict) -> Optional[EventResponse]:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[EventResponse]:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT e.*, t.session_id, t.user_id, t.ip_address, t.os, t.browser, t.campaign, t.source, t.device_type, t.device_os_version, t.device_model, t.device_app_version FROM {self.TABLE} e LEFT JOIN sj_tracking t ON e.tracking_id = t.id WHERE e.id = :id"),
                    {"id": pid}
                )
            ).fetchone()
            
            if not row:
                return None
                

        # Unmap flat columns back to payload
        valid_columns = {
            "session_id": "sessionId", "user_id": "userId", "ip_address": "ipAddress", 
            "os": "os", "browser": "browser", "campaign": "campaign", "source": "source",
            "product_id": "productId", "product_name": "productName", "quantity": "quantity", 
            "query": "query", "results_count": "resultsCount", "reason": "reason",
            "page": "page", "screen": "screen", "test_run_id": "testRunId", 
            "device_type": "device_type", 
            "device_os_version": "device_os_version", "device_model": "device_model", 
            "device_app_version": "device_app_version"
        }

        payload_list = [EventPayloadItem(key=k_camel, value=str(getattr(row, k_db))) for k_db, k_camel in valid_columns.items() if hasattr(row, k_db) and getattr(row, k_db) is not None]
            
        return EventResponse(
            id=str(row.id),
            external_id=row.external_id,
            event_type=row.event_type,
            payload=payload_list,
            created_at=row.created_at,
            updated_at=row.updated_at
        )


    async def create(self, data: EventCreate) -> Optional[EventResponse]:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        

        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if data.event_type is not None:
            cols.append("event_type")
            vals.append(":event_type")
            params["event_type"] = data.event_type
            
        # Map flat payload items if payload exists
        if data.payload is not None:
            for item in data.payload:

                # We map keys to columns safely
                col_name = item.key
                if col_name == "ipAddress": col_name = "ip_address"
                elif col_name == "testRunId": col_name = "test_run_id"
                elif col_name == "productId": col_name = "product_id"
                elif col_name == "productName": col_name = "product_name"
                elif col_name == "sessionId": col_name = "session_id"
                elif col_name == "userId": col_name = "user_id"
                elif col_name == "resultsCount": col_name = "results_count"
                
                valid_columns = {
                    "product_id", "product_name", "quantity", "query", "results_count", "reason",
                    "page", "screen", "test_run_id"
                }
                
                # Ensure column is alphanumeric to prevent SQL injection and is a valid column
                if re.match(r'^[a-zA-Z0-9_]+$', col_name) and col_name in valid_columns:
                    cols.append(col_name)
                    vals.append(f":{col_name}")
                    params[col_name] = item.value

                    
        if hasattr(data, 'tracking_id') and data.tracking_id is not None:
            cols.append("tracking_id")
            vals.append(":tracking_id")
            params["tracking_id"] = data.tracking_id
            
        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        
        async with factory() as session:
            await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params
            )
            new_id = (await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": ext_id})).scalar()
            await session.commit()

            
        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: EventUpdate) -> Optional[EventResponse]:
        existing = await self.findById(id)
        if not existing:
            return None
            
        pid = int(id) if str(id).isdigit() else None
        now = now_utc()
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        
        if data.event_type is not None:
            updates.append("event_type = :event_type")
            params["event_type"] = data.event_type
            
        set_sql = ", ".join(updates)
        factory = self._factory()
        
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params
            )
            
            
                    
            await session.commit()
            
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pid}
            )
            await session.commit()
            return res.rowcount > 0


