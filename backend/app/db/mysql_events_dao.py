import secrets
from typing import Optional, Dict, List, Any
from datetime import datetime

from sqlalchemy import text
from pydantic import BaseModel

from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc

class EventPayloadItem(BaseModel):
    key: str
    value: str

class EventCreate(BaseModel):
    eventType: Optional[str] = None
    payload: Optional[List[EventPayloadItem]] = None

class EventUpdate(BaseModel):
    eventType: Optional[str] = None
    payload: Optional[List[EventPayloadItem]] = None

class EventResponse(BaseModel):
    id: str
    externalId: str
    eventType: Optional[str] = None
    payload: Optional[List[EventPayloadItem]] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

class MySQLEventsDAO:
    TABLE = "sj_events"

    def _factory(self):
        return get_async_session_factory()

    async def findAll(self, query: Optional[Dict] = None) -> List[EventResponse]:
        query = query or {}
        where_clauses = []
        params = {}
        
        if "eventType" in query:
            where_clauses.append("event_type = :eventType")
            params["eventType"] = query["eventType"]
            
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        factory = self._factory()
        
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"),
                    params,
                )
            ).fetchall()
            
            if not rows:
                return []
                
            ids = [r.id for r in rows]
            id_placeholders = ", ".join([f":id_{i}" for i in range(len(ids))])
            id_params = {f"id_{i}": pid for i, pid in enumerate(ids)}
            
            child_rows = (
                await session.execute(
                    text(f"SELECT parent_id, payload_key, payload_value FROM sj_event_payload WHERE parent_id IN ({id_placeholders})"),
                    id_params
                )
            ).fetchall()
            
        payload_map = {pid: [] for pid in ids}
        for cr in child_rows:
            payload_map[cr.parent_id].append(EventPayloadItem(key=cr.payload_key, value=cr.payload_value))
            
        result = []
        for r in rows:
            result.append(EventResponse(
                id=str(r.id),
                externalId=r.external_id,
                eventType=r.event_type,
                payload=(payload_map[r.id] if r.id in payload_map else []),
                createdAt=r.created_at,
                updatedAt=r.updated_at
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
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid}
                )
            ).fetchone()
            
            if not row:
                return None
                
            child_rows = (
                await session.execute(
                    text("SELECT payload_key, payload_value FROM sj_event_payload WHERE parent_id = :id"),
                    {"id": pid}
                )
            ).fetchall()
            
        payload_list = []
        for cr in child_rows:
            payload_list.append(EventPayloadItem(key=cr.payload_key, value=cr.payload_value))
            
        return EventResponse(
            id=str(row.id),
            externalId=row.external_id,
            eventType=row.event_type,
            payload=payload_list,
            createdAt=row.created_at,
            updatedAt=row.updated_at
        )

    async def create(self, data: EventCreate) -> Optional[EventResponse]:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        
        if data.eventType is not None:
            cols.append("event_type")
            vals.append(":eventType")
            params["eventType"] = data.eventType
            
        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        
        async with factory() as session:
            await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params
            )
            new_id = (await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": ext_id})).scalar()
            
            if data.payload is not None:
                for item in data.payload:
                    await session.execute(
                        text("INSERT INTO sj_event_payload (parent_id, payload_key, payload_value) VALUES (:pid, :k, :v)"),
                        {"pid": new_id, "k": item.key, "v": item.value}
                    )
            
            await session.commit()
            
        return await self.findById(str(new_id))

    async def update(self, id: str, data: EventUpdate) -> Optional[EventResponse]:
        existing = await self.findById(id)
        if not existing:
            return None
            
        pid = int(id) if str(id).isdigit() else None
        now = now_utc()
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        
        if data.eventType is not None:
            updates.append("event_type = :eventType")
            params["eventType"] = data.eventType
            
        set_sql = ", ".join(updates)
        factory = self._factory()
        
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params
            )
            
            if data.payload is not None:
                await session.execute(
                    text("DELETE FROM sj_event_payload WHERE parent_id = :pid"),
                    {"pid": pid}
                )
                for item in data.payload:
                    await session.execute(
                        text("INSERT INTO sj_event_payload (parent_id, payload_key, payload_value) VALUES (:pid, :k, :v)"),
                        {"pid": pid, "k": item.key, "v": item.value}
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
