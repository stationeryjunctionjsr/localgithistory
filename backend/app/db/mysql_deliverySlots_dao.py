from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import secrets
import json
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import DeliverySlotConfigInternal
from app.models.daos_flat import DeliverySlotConfigInternalCreate, DeliverySlotConfigInternalUpdate

def now_utc():
    return datetime.now(timezone.utc)

class MySQLDeliverySlotsDAO:
    def __init__(self):
        self.table_name = "sj_delivery_slots"
    
    CHILD_TABLE = "sj_delivery_slot_times"

    @property
    def TABLE(self):
        from app.config.settings import settings
        return self.table_name

    def _factory(self):
        return get_async_session_factory()
        
    async def findById(self, id: str) -> Optional[Any]:
        return await self.findOne({"_id": id})

    async def findOne(self, query=None, **kwargs) -> Optional[Any]:
        if query:
            kwargs.update(query)
        if not kwargs:
            return None
        
        async with self._factory()() as session:
            conditions = []
            params = {}
            
            # Map query keys to db cols
            query_map = {'segment': 'segment', 'date': 'date', 'zone_id': 'zone_id', 'is_active': 'is_active'}
            query_map["_id"] = "id"
            query_map["externalId"] = "external_id"
            
            for k, v in kwargs.items():
                db_col = query_map.get(k, k)
                conditions.append(f"{db_col} = :{k}")
                params[k] = v
                
            where_clause = " AND ".join(conditions)
            q = text(f"SELECT * FROM {self.TABLE} WHERE {where_clause} LIMIT 1")
            result = await session.execute(q, params)
            row = result.fetchone()
            if not row:
                return None
                
            children_map = await self._fetch_children(session, [int(row.id)]) if True else {}
            return self._map_to_schema(row, children_map.get(int(row.id), {}))
            
    async def findAll(self, query: Optional[Dict[str, Any]] = None) -> List[Any]:
        query = query or {}
        async with self._factory()() as session:
            sql = f"SELECT * FROM {self.TABLE}"
            params = {}
            
            query_map = {'segment': 'segment', 'date': 'date', 'zone_id': 'zone_id', 'is_active': 'is_active'}
            query_map["_id"] = "id"
            query_map["externalId"] = "external_id"
            
            if query:
                conditions = []
                for k, v in query.items():
                    db_col = query_map.get(k, k)
                    conditions.append(f"{db_col} = :{k}")
                    params[k] = v
                if conditions:
                    sql += " WHERE " + " AND ".join(conditions)
                    
            q = text(sql)
            result = await session.execute(q, params)
            rows = result.fetchall()
            
            if not rows:
                return []
                
            children_map = await self._fetch_children(session, [int(r.id) for r in rows]) if True else {}
            
            return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]

    async def create(self, data: Any) -> Any:
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        params = {"eid": external_id, "c": now, "u": now}

        if data.segment is not None:
            cols.append("segment")
            params["s_segment"] = data.segment

        if data.date is not None:
            cols.append("date")
            params["s_date"] = data.date

        if data.zone_id is not None:
            cols.append("zone_id")
            params["s_zone_id"] = data.zone_id

        if data.is_active is not None:
            cols.append("is_active")
            params["s_is_active"] = data.is_active

        col_sql = ", ".join(cols)
        val_sql = ", ".join([":eid", ":c", ":u"] + [f":s_{k}" for k in ['segment', 'date', 'zone_id', 'is_active'] if f"s_{k}" in params] + [f":c_{k}" for k in [] if f"c_{k}" in params])
        
        async with factory() as session:
            await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = (
                await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": external_id}
                )
            ).scalar()
            await self._replace_children(session, new_id, data)
            await session.commit()
            
        return await self.findById(str(new_id))

    async def update(self, id: str, data: Any) -> Any:
        factory = self._factory()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now_utc()}

        if data.segment is not None:
            updates.append("segment = :s_segment")
            params["s_segment"] = data.segment

        if data.date is not None:
            updates.append("date = :s_date")
            params["s_date"] = data.date

        if data.zone_id is not None:
            updates.append("zone_id = :s_zoneId")
            params["s_zone_id"] = data.zone_id

        if data.is_active is not None:
            updates.append("is_active = :s_isActive")
            params["s_is_active"] = data.is_active

        if len(updates) > 1:
            upd_sql = ", ".join(updates)
            async with factory() as session:
                await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE id = :id"), params)
                await self._replace_children(session, int(id), data)
                await session.commit()
        else:
            async with factory() as session:
                await self._replace_children(session, int(id), data)
                await session.commit()
                
        return await self.findById(id)

    def _map_to_schema(self, r, children: Dict) -> Any:
        obj = DeliverySlotConfigInternal.model_validate(r)
        for k, v in children.items():
            setattr(obj, k, v)
        return obj

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:
        c_map = {rid: {} for rid in ids}
        if not ids:
            return c_map
            
        id_list = ",".join(map(str, ids))

        q_slots = text(f"SELECT parent_id, start_time, end_time, capacity, booked_count, is_full_day, is_urgent, cutoff_hours FROM sj_delivery_slot_times WHERE parent_id IN ({id_list})")
        res_slots = await session.execute(q_slots)
        rows_slots = res_slots.fetchall()

        for r in rows_slots:
            if "slots" not in c_map[r.parent_id]:
                c_map[r.parent_id]["slots"] = []
            obj = {}

            obj["start_time"] = r[1]
            obj["end_time"] = r[2]
            obj["capacity"] = r[3]
            obj["booked_count"] = r[4]
            obj["is_full_day"] = r[5]
            obj["is_urgent"] = r[6]
            obj["cutoff_hours"] = r[7]
            c_map[r.parent_id]["slots"].append(obj)

        return c_map

    async def _replace_children(self, session, row_id: int, data: Any):

        if data.slots is not None:
            await session.execute(text(f"DELETE FROM sj_delivery_slot_times WHERE parent_id = :id"), {"id": row_id})
            child_list = data.slots or []

            if child_list:
                for item in child_list:
                    p = {"id": row_id}

                    p["v0"] = item.start_time
                    p["v1"] = item.end_time
                    p["v2"] = item.capacity
                    p["v3"] = item.booked_count
                    p["v4"] = item.is_full_day
                    p["v5"] = item.is_urgent
                    p["v6"] = item.cutoff_hours
                    await session.execute(text(f"INSERT INTO sj_delivery_slot_times (parent_id, start_time, end_time, capacity, booked_count, is_full_day, is_urgent, cutoff_hours) VALUES (:id, :v0, :v1, :v2, :v3, :v4, :v5, :v6)"), p)
