from typing import Any, Dict, List, Optional
import datetime
import secrets
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import CustomerSegmentInternal, CustomerSegmentInternalCreate, CustomerSegmentInternalUpdate
from app.db.db_utils import now_utc

class MySQLCustomerSegmentDAO:
    def __init__(self):
        pass

    def _factory(self):
        return get_async_session_factory()

    def _map_to_schema(self, r, user_ids: List[str]) -> CustomerSegmentInternal:
        d = dict(r._mapping)
        d["user_ids"] = user_ids
        d["filters"] = {
            "min_average_order_value": d.pop("min_avg_order_value", None),
            "max_average_order_value": d.pop("max_avg_order_value", None),
            "start_date": d.pop("start_date", None),
            "end_date": d.pop("end_date", None),
            "min_order_frequency": d.pop("min_order_freq", None),
            "max_order_frequency": d.pop("max_order_freq", None),
            "state": d.pop("state", None),
            "district": d.pop("district", None),
            "app_user": d.pop("app_user", None),
            "behavior": d.pop("behavior", None),
            "role": d.pop("role", None),
        }
        return CustomerSegmentInternal.model_validate(d)

    async def _fetch_user_ids(self, segment_id: str) -> List[str]:
        SessionLocal = self._factory()
        async with SessionLocal() as session:
            result = await session.execute(
                text("SELECT user_id FROM sj_customer_segment_users WHERE segment_id = :sid"), {"sid": segment_id}
            )
            return [r.user_id for r in result.fetchall()]

    async def _save_user_ids(self, segment_id: str, user_ids: List[str]):
        if user_ids is None: return
        SessionLocal = self._factory()
        async with SessionLocal() as session:
            await session.execute(
                text("DELETE FROM sj_customer_segment_users WHERE segment_id = :sid"), {"sid": segment_id}
            )
            if user_ids:
                params = [{"sid": segment_id, "uid": uid} for uid in user_ids]
                await session.execute(
                    text("INSERT INTO sj_customer_segment_users (segment_id, user_id) VALUES (:sid, :uid)"), params
                )
            await session.commit()

    async def findById(self, id: str) -> Optional[CustomerSegmentInternal]:
        pk = int(id) if str(id).isdigit() else None
        if pk is None: return None
        SessionLocal = self._factory()
        async with SessionLocal() as session:
            result = await session.execute(
                text("SELECT * FROM sj_customer_segments WHERE id = :id"), {"id": pk}
            )
            row = result.fetchone()
            if not row: return None
            
            user_ids = await self._fetch_user_ids(row.external_id)
            return self._map_to_schema(row, user_ids)

    async def findAll(self, query: Optional[Dict] = None) -> List[CustomerSegmentInternal]:
        SessionLocal = self._factory()
        async with SessionLocal() as session:
            result = await session.execute(text("SELECT * FROM sj_customer_segments"))
            rows = result.fetchall()
            
            out = []
            for r in rows:
                user_ids = await self._fetch_user_ids(r.external_id)
                out.append(self._map_to_schema(r, user_ids))
            return out

    async def create(self, data: CustomerSegmentInternalCreate) -> CustomerSegmentInternal:
        external_id = secrets.token_hex(16)
        
        p = {
            "external_id": external_id,
            "created_at": now_utc(),
            "updated_at": now_utc(),
            "type": data.type,
            "name": data.name,
            "description": data.description,
            "is_active": data.is_active,
            "is_system": data.is_system,
            "min_avg_order_value": data.filters.min_average_order_value if data.filters else None,
            "max_avg_order_value": data.filters.max_average_order_value if data.filters else None,
            "start_date": data.filters.start_date if data.filters else None,
            "end_date": data.filters.end_date if data.filters else None,
            "min_order_freq": data.filters.min_order_frequency if data.filters else None,
            "max_order_freq": data.filters.max_order_frequency if data.filters else None,
            "state": data.filters.state if data.filters else None,
            "district": data.filters.district if data.filters else None,
            "app_user": data.filters.app_user if data.filters else None,
            "behavior": data.filters.behavior if data.filters else None,
            "role": data.filters.role if data.filters else None,
        }
        
        cols = ", ".join(p.keys())
        vals = ", ".join([f":{k}" for k in p.keys()])
        
        SessionLocal = self._factory()
        async with SessionLocal() as session:
            res = await session.execute(
                text(f"INSERT INTO sj_customer_segments ({cols}) VALUES ({vals})"), p
            )
            new_id = res.lastrowid
            await session.commit()
            
        user_ids = data.user_ids or []
        await self._save_user_ids(external_id, user_ids)
        return await self.findById(str(new_id))

    async def update(self, id: str, data: CustomerSegmentInternalUpdate) -> CustomerSegmentInternal:
        pk = int(id) if str(id).isdigit() else None
        if pk is None: return None
        
        doc = await self.findById(id)
        if not doc: return None
        
        updates = ["updated_at = :u"]
        params = {"id": pk, "u": now_utc()}
        
        if data.type is not None: updates.append("type = :type"); params["type"] = data.type
        if data.name is not None: updates.append("name = :name"); params["name"] = data.name
        if data.description is not None: updates.append("description = :description"); params["description"] = data.description
        if data.is_active is not None: updates.append("is_active = :isActive"); params["isActive"] = data.is_active
        if data.is_system is not None: updates.append("is_system = :isSystem"); params["isSystem"] = data.is_system
        
        if data.filters is not None:
            if data.filters.min_average_order_value is not None: updates.append("min_avg_order_value = :f1"); params["f1"] = data.filters.min_average_order_value
            if data.filters.max_average_order_value is not None: updates.append("max_avg_order_value = :f2"); params["f2"] = data.filters.max_average_order_value
            if data.filters.start_date is not None: updates.append("start_date = :f3"); params["f3"] = data.filters.start_date
            if data.filters.end_date is not None: updates.append("end_date = :f4"); params["f4"] = data.filters.end_date
            if data.filters.min_order_frequency is not None: updates.append("min_order_freq = :f5"); params["f5"] = data.filters.min_order_frequency
            if data.filters.max_order_frequency is not None: updates.append("max_order_freq = :f6"); params["f6"] = data.filters.max_order_frequency
            if data.filters.state is not None: updates.append("state = :f7"); params["f7"] = data.filters.state
            if data.filters.district is not None: updates.append("district = :f8"); params["f8"] = data.filters.district
            if data.filters.app_user is not None: updates.append("app_user = :f9"); params["f9"] = data.filters.app_user
            if data.filters.behavior is not None: updates.append("behavior = :f10"); params["f10"] = data.filters.behavior
            if data.filters.role is not None: updates.append("role = :f11"); params["f11"] = data.filters.role
            
        if len(updates) > 1:
            upd_sql = ", ".join(updates)
            SessionLocal = self._factory()
            async with SessionLocal() as session:
                await session.execute(text(f"UPDATE sj_customer_segments SET {upd_sql} WHERE id = :id"), params)
                await session.commit()
                
        if data.user_ids is not None:
            await self._save_user_ids(doc.external_id, data.user_ids)
            
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        pk = int(id) if str(id).isdigit() else None
        if pk is None: return False
        SessionLocal = self._factory()
        async with SessionLocal() as session:
            res = await session.execute(text("DELETE FROM sj_customer_segments WHERE id = :id"), {"id": pk})
            await session.commit()
            return res.rowcount > 0

    async def deleteMany(self, query: Dict) -> Any:
        return {"deletedCount": 0}
