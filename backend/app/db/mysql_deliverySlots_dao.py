import json
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy import text
from app.config.database import get_async_session_factory
from pydantic import BaseModel, Field, ConfigDict
from app.db.db_utils import now_utc
from app.config.settings import settings

class DeliverySlotInternal(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    startTime: Optional[str] = None
    endTime: Optional[str] = None
    capacity: Optional[int] = None

class DeliverySlotConfigInternal(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: Optional[str] = Field(None, alias="_id")
    segment: Optional[str] = None
    date: Optional[str] = None
    zoneId: Optional[str] = None
    isActive: Optional[bool] = None
    slots: List[DeliverySlotInternal] = Field(default_factory=list)
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class MySQLDeliveryslotsDAO:
    @property
    def TABLE(self):
        suffix = settings.table_suffix if settings.table_suffix is not None else ""
        return f"sj_delivery_slots{suffix}"

    @property
    def CHILD_TABLE(self):
        suffix = settings.table_suffix if settings.table_suffix is not None else ""
        return f"sj_delivery_slot_times{suffix}"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_obj(self, r, children: Dict) -> DeliverySlotConfigInternal:
        return DeliverySlotConfigInternal(
            _id=str(r.id),
            segment=r.segment,
            date=r.date,
            zoneId=r.zone_id,
            isActive=bool(r.is_active) if r.is_active is not None else None,
            slots=children[r.id] if r.id in children else [],
            createdAt=r.created_at.isoformat() if r.created_at else None,
            updatedAt=r.updated_at.isoformat() if r.updated_at else None,
        )

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, List[DeliverySlotInternal]]:
        c_map: Dict[int, List[DeliverySlotInternal]] = {rid: [] for rid in ids}
        if not ids:
            return c_map
        chunks = [ids[i : i + 999] for i in range(0, len(ids), 999)]
        for chunk in chunks:
            chunk_params = {f"id_{i}": cid for i, cid in enumerate(chunk)}
            placeholders = ", ".join([f":{k}" for k in chunk_params.keys()])
            res = await session.execute(
                text(f"SELECT parent_id, slot_uuid, start_time, end_time, capacity, booked_count FROM {self.CHILD_TABLE} WHERE parent_id IN ({placeholders})"),
                chunk_params,
            )
            for r in res.fetchall():
                c_map[r.parent_id].append(
                    DeliverySlotInternal(
                        id=r.slot_uuid,
                        startTime=r.start_time,
                        endTime=r.end_time,
                        capacity=r.capacity,
                        bookedCount=r.booked_count,
                    )
                )
        return c_map

    async def _replace_children(self, session, parent_id: int, data: Any):
        await session.execute(
            text(f"DELETE FROM {self.CHILD_TABLE} WHERE parent_id = :pid"),
            {"pid": parent_id},
        )
        if data.slots:
            for slot in data.slots:
                # generate uuid if missing
                if not slot.id:
                    slot.id = str(uuid.uuid4())
                await session.execute(
                    text(f"INSERT INTO {self.CHILD_TABLE} (parent_id, slot_uuid, start_time, end_time, capacity, booked_count) VALUES (:pid, :slot_uuid, :start_time, :end_time, :capacity, :booked_count)"),
                    {
                        "pid": parent_id,
                        "slot_uuid": slot.id,
                        "start_time": slot.startTime,
                        "end_time": slot.endTime,
                        "capacity": slot.capacity,
                        "booked_count": slot.bookedCount if slot.bookedCount is not None else 0,
                    },
                )

    async def findAll(self, query: Optional[Dict] = None) -> List[DeliverySlotConfigInternal]:
        factory = self._factory()
        if not factory:
            return []

        where_clauses = []
        params = {}
        if query:
            for k, v in query.items():
                if k in ("_id", "id"):
                    where_clauses.append("id = :id")
                    params["id"] = int(v) if str(v).isdigit() else None
                elif k == "isActive":
                    where_clauses.append("is_active = :is_active")
                    params["is_active"] = int(bool(v))
                elif k == "segment":
                    where_clauses.append("segment = :segment")
                    params["segment"] = str(v)
                elif k == "date":
                    where_clauses.append("date = :date")
                    params["date"] = str(v)
                elif k == "zoneId":
                    where_clauses.append("zone_id = :zoneId")
                    params["zoneId"] = str(v)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        async with factory() as session:
            result = await session.execute(
                text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"), params
            )
            rows = result.fetchall()
            c_map = await self._fetch_children(session, [r.id for r in rows])
        return [self._row_to_obj(r, c_map) for r in rows]

    async def findOne(self, query: Dict) -> Optional[DeliverySlotConfigInternal]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[DeliverySlotConfigInternal]:
        return await self.findOne({"_id": id})

    async def create(self, data: Any) -> DeliverySlotConfigInternal:
        factory = self._factory()
        now = now_utc()
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    INSERT INTO {self.TABLE} (
                        segment, date, zone_id, is_active, created_at, updated_at
                    ) VALUES (
                        :segment, :date, :zone_id, :is_active, :created_at, :updated_at
                    )
                    """
                ),
                {
                    "segment": data.segment,
                    "date": data.date,
                    "zone_id": data.zoneId,
                    "is_active": 1 if data.isActive else 0,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            new_id = result.lastrowid
            await self._replace_children(session, new_id, data)
            await session.commit()
            return await self.findById(str(new_id))

    async def update(self, id: str, data: Any) -> Optional[DeliverySlotConfigInternal]:
        factory = self._factory()
        now = now_utc()
        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    UPDATE {self.TABLE} SET
                        segment = :segment,
                        date = :date,
                        zone_id = :zone_id,
                        is_active = :is_active,
                        updated_at = :updated_at
                    WHERE id = :id
                    """
                ),
                {
                    "id": int(id),
                    "segment": data.segment,
                    "date": data.date,
                    "zone_id": data.zoneId,
                    "is_active": 1 if data.isActive else 0,
                    "updated_at": now,
                },
            )
            await self._replace_children(session, int(id), data)
            await session.commit()
            return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        async with factory() as session:
            await session.execute(
                text(f"DELETE FROM {self.CHILD_TABLE} WHERE parent_id = :id"),
                {"id": int(id)},
            )
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"), {"id": int(id)}
            )
            await session.commit()
            return result.rowcount > 0
