from typing import Optional, Dict, List, Union
from datetime import datetime, timezone
import secrets
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import (
    DeliverySlotConfigInternal,
    DeliverySlotConfigInternalCreate,
    DeliverySlotConfigInternalUpdate,
    DeliverySlotInternal,
)

def now_utc():
    return datetime.now(timezone.utc)

class MySQLDeliverySlotsDAO:
    def __init__(self):
        self.table_name = "sj_delivery_slots"
    
    CHILD_TABLE = "sj_delivery_slot_times"

    @property
    def TABLE(self):
        return self.table_name

    def _factory(self):
        return get_async_session_factory()
        
    async def findById(self, id: Union[int, str]) -> Optional[DeliverySlotConfigInternal]:
        if not id:
            return None
        async with self._factory()() as session:
            if str(id).isdigit():
                q = text(f"SELECT * FROM {self.TABLE} WHERE id = :id LIMIT 1")
                params = {"id": int(id)}
            else:
                q = text(f"SELECT * FROM {self.TABLE} WHERE external_id = :id LIMIT 1")
                params = {"id": str(id)}
            result = await session.execute(q, params)
            row = result.fetchone()
            if not row:
                return None
                
            children_map = await self._fetch_children(session, [int(row.id)])
            return self._map_to_schema(row, children_map.get(int(row.id)))

    async def findOne(
        self,
        id: Optional[Union[int, str]] = None,
        date: Optional[str] = None,
        zone_id: Optional[str] = None,
        segment: Optional[str] = None,
    ) -> Optional[DeliverySlotConfigInternal]:
        if id:
            return await self.findById(id)
        results = await self.findAll(date=date, zone_id=zone_id, segment=segment, limit=1)
        return results[0] if results else None

    async def findAll(
        self,
        date: Optional[str] = None,
        zone_id: Optional[str] = None,
        segment: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: Optional[int] = None,
    ) -> List[DeliverySlotConfigInternal]:
        clauses = []
        params = {}
        if date is not None:
            clauses.append("date = :date")
            params["date"] = date
        if zone_id is not None:
            clauses.append("zone_id = :zone_id")
            params["zone_id"] = zone_id
        if segment is not None:
            clauses.append("segment = :segment")
            params["segment"] = segment
        if is_active is not None:
            clauses.append("is_active = :act")
            params["act"] = 1 if is_active else 0

        where_sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        limit_sql = f" LIMIT {int(limit)}" if limit else ""
        sql = f"SELECT * FROM {self.TABLE}{where_sql} ORDER BY id ASC{limit_sql}"

        async with self._factory()() as session:
            result = await session.execute(text(sql), params)
            rows = result.fetchall()
            if not rows:
                return []
            children_map = await self._fetch_children(session, [int(r.id) for r in rows])
            return [self._map_to_schema(r, children_map.get(int(r.id))) for r in rows]

    async def create(self, data: DeliverySlotConfigInternalCreate) -> DeliverySlotConfigInternal:
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        val_placeholders = [":eid", ":c", ":u"]
        params = {"eid": external_id, "c": now, "u": now}

        if data.segment is not None:
            cols.append("segment")
            val_placeholders.append(":segment")
            params["segment"] = data.segment

        if data.date is not None:
            cols.append("date")
            val_placeholders.append(":date")
            params["date"] = data.date

        if data.zone_id is not None:
            cols.append("zone_id")
            val_placeholders.append(":zone_id")
            params["zone_id"] = data.zone_id

        if data.is_active is not None:
            cols.append("is_active")
            val_placeholders.append(":is_active")
            params["is_active"] = 1 if data.is_active else 0

        col_sql = ", ".join(cols)
        val_sql = ", ".join(val_placeholders)
        
        async with factory() as session:
            await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = (
                await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": external_id}
                )
            ).scalar()
            await self._replace_children(session, new_id, data)
            await session.commit()
            
        return await self.findById(int(new_id))

    async def update(self, id: Union[int, str], update_data: DeliverySlotConfigInternalUpdate) -> Optional[DeliverySlotConfigInternal]:
        factory = self._factory()
        updates = ["updated_at = :u"]
        params = {"u": now_utc()}

        if update_data.segment is not None:
            updates.append("segment = :segment")
            params["segment"] = update_data.segment

        if update_data.date is not None:
            updates.append("date = :date")
            params["date"] = update_data.date

        if update_data.zone_id is not None:
            updates.append("zone_id = :zone_id")
            params["zone_id"] = update_data.zone_id

        if update_data.is_active is not None:
            updates.append("is_active = :is_active")
            params["is_active"] = 1 if update_data.is_active else 0

        upd_sql = ", ".join(updates)
        async with factory() as session:
            if str(id).isdigit():
                pk = int(id)
                upd_where = "id = :pk"
            else:
                res = await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": str(id)}
                )
                pk = res.scalar()
                if not pk:
                    return None
                upd_where = "id = :pk"
            params["pk"] = pk

            await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE {upd_where}"), params)
            await self._replace_children(session, pk, update_data)
            await session.commit()
                
        return await self.findById(pk)

    async def delete(self, id: Union[int, str]) -> bool:
        factory = self._factory()
        if not factory or not id:
            return False
        async with factory() as session:
            if str(id).isdigit():
                pk = int(id)
                del_where = "id = :pk"
                params = {"pk": pk}
            else:
                res = await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": str(id)}
                )
                pk = res.scalar()
                if not pk:
                    return False
                del_where = "id = :pk"
                params = {"pk": pk}

            await session.execute(text(f"DELETE FROM {self.CHILD_TABLE} WHERE parent_id = :id"), {"id": pk})
            result = await session.execute(text(f"DELETE FROM {self.TABLE} WHERE {del_where}"), params)
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(self, r, slots: Optional[List[DeliverySlotInternal]] = None) -> DeliverySlotConfigInternal:
        return DeliverySlotConfigInternal(
            id=str(r.id),
            external_id=r.external_id,
            segment=r.segment,
            date=r.date,
            zone_id=r.zone_id,
            is_active=bool(r.is_active) if r.is_active is not None else None,
            slots=slots,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, List[DeliverySlotInternal]]:
        c_map: Dict[int, List[DeliverySlotInternal]] = {rid: [] for rid in ids}
        if not ids:
            return c_map
            
        id_list = ",".join(str(int(i)) for i in ids)
        q_slots = text(f"SELECT parent_id, start_time, end_time, capacity, booked_count, is_full_day, is_urgent, cutoff_hours FROM sj_delivery_slot_times WHERE parent_id IN ({id_list})")
        res_slots = await session.execute(q_slots)
        rows_slots = res_slots.fetchall()

        for r in rows_slots:
            slot = DeliverySlotInternal(
                start_time=r.start_time,
                end_time=r.end_time,
                capacity=int(r.capacity) if r.capacity is not None else None,
                booked_count=int(r.booked_count) if r.booked_count is not None else 0,
                is_full_day=bool(r.is_full_day) if r.is_full_day is not None else False,
                is_urgent=bool(r.is_urgent) if r.is_urgent is not None else False,
                cutoff_hours=int(r.cutoff_hours) if r.cutoff_hours is not None else None,
            )
            c_map[r.parent_id].append(slot)

        return c_map

    async def _replace_children(self, session, row_id: int, data: Union[DeliverySlotConfigInternalCreate, DeliverySlotConfigInternalUpdate]):
        if data.slots is not None:
            await session.execute(text(f"DELETE FROM {self.CHILD_TABLE} WHERE parent_id = :id"), {"id": row_id})
            for item in data.slots:
                p = {
                    "id": row_id,
                    "v0": item.start_time,
                    "v1": item.end_time,
                    "v2": item.capacity,
                    "v3": item.booked_count or 0,
                    "v4": 1 if item.is_full_day else 0,
                    "v5": 1 if item.is_urgent else 0,
                    "v6": item.cutoff_hours,
                }
                await session.execute(
                    text(f"INSERT INTO {self.CHILD_TABLE} (parent_id, start_time, end_time, capacity, booked_count, is_full_day, is_urgent, cutoff_hours) VALUES (:id, :v0, :v1, :v2, :v3, :v4, :v5, :v6)"),
                    p,
                )
