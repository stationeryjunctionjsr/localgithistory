from typing import Optional, List, Union
from datetime import datetime, timezone
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

def _parse_slot_row(r) -> DeliverySlotInternal:
    return DeliverySlotInternal(
        start_time=r.start_time,
        end_time=r.end_time,
        capacity=int(r.capacity) if r.capacity is not None else None,
        booked_count=int(r.booked_count) if r.booked_count is not None else 0,
        is_full_day=bool(r.is_full_day) if r.is_full_day is not None else False,
        is_urgent=bool(r.is_urgent) if r.is_urgent is not None else False,
        cutoff_hours=int(r.cutoff_hours) if r.cutoff_hours is not None else None,
    )

class MySQLDeliverySlotsDAO:
    def __init__(self):
        self.table_name = "sj_delivery_slots"
    
    CHILD_TABLE = "sj_delivery_slot_times"

    @property
    def TABLE(self):
        return self.table_name

    async def findById(self, id: int) -> Optional[DeliverySlotConfigInternal]:
        if not id:
            return None
        async_session = get_async_session_factory()
        if not async_session:
            return None
        async with async_session() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE id = :id LIMIT 1")
            params = {"id": id}
            result = await session.execute(q, params)
            row = result.fetchone()
            if not row:
                return None
                
            slots = await self._fetch_slots(session, row.id)
            return self._map_to_schema(row, slots)

    async def findOne(
        self,
        id: Optional[int] = None,
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

        async_session = get_async_session_factory()
        if not async_session:
            return []
        async with async_session() as session:
            result = await session.execute(text(sql), params)
            rows = result.fetchall()
            if not rows:
                return []
            parent_ids = [r.id for r in rows]
            id_list = ",".join(str(i) for i in parent_ids)
            slots_res = await session.execute(
                text(f"SELECT parent_id, start_time, end_time, capacity, booked_count, is_full_day, is_urgent, cutoff_hours FROM {self.CHILD_TABLE} WHERE parent_id IN ({id_list}) ORDER BY id ASC")
            )
            all_slot_rows = slots_res.fetchall()
            return [
                self._map_to_schema(
                    r,
                    slots=[
                        _parse_slot_row(sr)
                        for sr in all_slot_rows
                        if sr.parent_id == r.id
                    ],
                )
                for r in rows
            ]

    async def create(self, data: DeliverySlotConfigInternalCreate) -> DeliverySlotConfigInternal:
        async_session = get_async_session_factory()
        if not async_session:
            raise RuntimeError("Database session factory unavailable")
        now = now_utc()
        
        cols = ["created_at", "updated_at"]
        val_placeholders = [":c", ":u"]
        params = {"c": now, "u": now}

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
        
        async with async_session() as session:
            result = await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = result.lastrowid
            await self._replace_children(session, new_id, data)
            await session.commit()
            
        return await self.findById(new_id)

    async def update(self, id: int, update_data: DeliverySlotConfigInternalUpdate) -> Optional[DeliverySlotConfigInternal]:
        async_session = get_async_session_factory()
        if not async_session or not id:
            return None

        fields = update_data.model_fields_set
        if not fields:
            return await self.findById(id)

        updates = ["updated_at = :u"]
        params = {"pk": id, "u": now_utc()}

        if "segment" in fields:
            updates.append("segment = :segment")
            params["segment"] = update_data.segment

        if "date" in fields:
            updates.append("date = :date")
            params["date"] = update_data.date

        if "zone_id" in fields:
            updates.append("zone_id = :zone_id")
            params["zone_id"] = update_data.zone_id

        if "is_active" in fields:
            updates.append("is_active = :is_active")
            params["is_active"] = 1 if update_data.is_active else 0

        upd_sql = ", ".join(updates)
        async with async_session() as session:
            await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE id = :pk"), params)
            await self._replace_children(session, id, update_data)
            await session.commit()
                
        return await self.findById(id)

    async def delete(self, id: int) -> bool:
        async_session = get_async_session_factory()
        if not async_session or not id:
            return False
        async with async_session() as session:
            params = {"id": id}

            await session.execute(text(f"DELETE FROM {self.CHILD_TABLE} WHERE parent_id = :id"), params)
            result = await session.execute(text(f"DELETE FROM {self.TABLE} WHERE id = :id"), params)
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(self, r, slots: Optional[List[DeliverySlotInternal]] = None) -> DeliverySlotConfigInternal:
        return DeliverySlotConfigInternal(
            id=r.id,
            segment=r.segment,
            date=r.date,
            zone_id=r.zone_id,
            is_active=bool(r.is_active) if r.is_active is not None else None,
            slots=slots,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )

    async def _fetch_slots(self, session, parent_id: int) -> List[DeliverySlotInternal]:
        q_slots = text(f"SELECT start_time, end_time, capacity, booked_count, is_full_day, is_urgent, cutoff_hours FROM {self.CHILD_TABLE} WHERE parent_id = :pid ORDER BY id ASC")
        res_slots = await session.execute(q_slots, {"pid": parent_id})
        return [_parse_slot_row(r) for r in res_slots.fetchall()]

    async def _replace_children(self, session, row_id: int, data: Union[DeliverySlotConfigInternalCreate, DeliverySlotConfigInternalUpdate]):
        fields = data.model_fields_set
        if "slots" in fields and data.slots is not None:
            await session.execute(text(f"DELETE FROM {self.CHILD_TABLE} WHERE parent_id = :id"), {"id": row_id})
            if data.slots:
                params = [
                    {
                        "id": row_id,
                        "v0": item.start_time,
                        "v1": item.end_time,
                        "v2": item.capacity,
                        "v3": item.booked_count or 0,
                        "v4": 1 if item.is_full_day else 0,
                        "v5": 1 if item.is_urgent else 0,
                        "v6": item.cutoff_hours,
                    }
                    for item in data.slots
                ]
                await session.execute(
                    text(f"INSERT INTO {self.CHILD_TABLE} (parent_id, start_time, end_time, capacity, booked_count, is_full_day, is_urgent, cutoff_hours) VALUES (:id, :v0, :v1, :v2, :v3, :v4, :v5, :v6)"),
                    params,
                )
