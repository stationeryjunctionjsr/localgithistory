from typing import List, Optional, Union
import datetime
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import CustomerSegmentInternal, CustomerSegmentInternalCreate, CustomerSegmentInternalUpdate
from app.models.customer_segment import CustomerSegmentFilters
from app.db.db_utils import now_utc

class MySQLCustomerSegmentDAO:
    def __init__(self):
        pass

    def _factory(self):
        return get_async_session_factory()

    def _map_to_schema(self, r, user_ids: List[str]) -> CustomerSegmentInternal:
        return CustomerSegmentInternal(
            id=str(r.id),
            type=r.type,
            name=r.name,
            description=r.description,
            is_active=bool(r.is_active) if r.is_active is not None else True,
            is_system=bool(r.is_system) if r.is_system is not None else False,
            user_ids=user_ids,
            filters=CustomerSegmentFilters(
                min_average_order_value=float(r.min_avg_order_value) if r.min_avg_order_value is not None else None,
                max_average_order_value=float(r.max_avg_order_value) if r.max_avg_order_value is not None else None,
                start_date=str(r.start_date) if r.start_date is not None else None,
                end_date=str(r.end_date) if r.end_date is not None else None,
                min_order_frequency=int(r.min_order_freq) if r.min_order_freq is not None else None,
                max_order_frequency=int(r.max_order_freq) if r.max_order_freq is not None else None,
                state=r.state,
                district=r.district,
                app_user=bool(r.app_user) if r.app_user is not None else None,
                behavior=r.behavior,
                role=r.role,
            ),
            created_at=r.created_at,
            updated_at=r.updated_at,
        )

    async def _fetch_user_ids(self, segment_id: Union[int, str]) -> List[str]:
        sid = int(segment_id) if str(segment_id).isdigit() else segment_id
        SessionLocal = self._factory()
        async with SessionLocal() as session:
            result = await session.execute(
                text("SELECT user_id FROM sj_customer_segment_users WHERE segment_id = :sid"), {"sid": sid}
            )
            return [str(r.user_id) for r in result.fetchall()]

    async def _save_user_ids(self, segment_id: Union[int, str], user_ids: List[str]):
        if user_ids is None: return
        sid = int(segment_id) if str(segment_id).isdigit() else segment_id
        SessionLocal = self._factory()
        async with SessionLocal() as session:
            await session.execute(
                text("DELETE FROM sj_customer_segment_users WHERE segment_id = :sid"), {"sid": sid}
            )
            if user_ids:
                params = [{"sid": sid, "uid": str(uid)} for uid in user_ids]
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
            
            user_ids = await self._fetch_user_ids(row.id)
            return self._map_to_schema(row, user_ids)

    async def findAll(self, query: Optional[object] = None) -> List[CustomerSegmentInternal]:
        SessionLocal = self._factory()
        async with SessionLocal() as session:
            result = await session.execute(text("SELECT * FROM sj_customer_segments"))
            rows = result.fetchall()
            
            out = []
            for r in rows:
                user_ids = await self._fetch_user_ids(r.id)
                out.append(self._map_to_schema(r, user_ids))
            return out

    async def create(self, data: CustomerSegmentInternalCreate) -> CustomerSegmentInternal:
        p = {
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
        await self._save_user_ids(new_id, user_ids)
        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: CustomerSegmentInternalUpdate) -> Optional[CustomerSegmentInternal]:
        pk = int(id) if str(id).isdigit() else None
        if pk is None: return None
        
        record = await self.findById(id)
        if not record: return None
        
        updates = ["updated_at = :u"]
        params = {"id": pk, "u": now_utc()}
        
        if update_data.name is not None: updates.append("name = :name"); params["name"] = update_data.name
        if update_data.description is not None: updates.append("description = :description"); params["description"] = update_data.description
        if update_data.is_active is not None: updates.append("is_active = :isActive"); params["isActive"] = update_data.is_active
        
        if update_data.filters is not None:
            if update_data.filters.min_average_order_value is not None: updates.append("min_avg_order_value = :f1"); params["f1"] = update_data.filters.min_average_order_value
            if update_data.filters.max_average_order_value is not None: updates.append("max_avg_order_value = :f2"); params["f2"] = update_data.filters.max_average_order_value
            if update_data.filters.start_date is not None: updates.append("start_date = :f3"); params["f3"] = update_data.filters.start_date
            if update_data.filters.end_date is not None: updates.append("end_date = :f4"); params["f4"] = update_data.filters.end_date
            if update_data.filters.min_order_frequency is not None: updates.append("min_order_freq = :f5"); params["f5"] = update_data.filters.min_order_frequency
            if update_data.filters.max_order_frequency is not None: updates.append("max_order_freq = :f6"); params["f6"] = update_data.filters.max_order_frequency
            if update_data.filters.state is not None: updates.append("state = :f7"); params["f7"] = update_data.filters.state
            if update_data.filters.district is not None: updates.append("district = :f8"); params["f8"] = update_data.filters.district
            if update_data.filters.app_user is not None: updates.append("app_user = :f9"); params["f9"] = update_data.filters.app_user
            if update_data.filters.behavior is not None: updates.append("behavior = :f10"); params["f10"] = update_data.filters.behavior
            if update_data.filters.role is not None: updates.append("role = :f11"); params["f11"] = update_data.filters.role
            
        if len(updates) > 1:
            upd_sql = ", ".join(updates)
            SessionLocal = self._factory()
            async with SessionLocal() as session:
                await session.execute(text(f"UPDATE sj_customer_segments SET {upd_sql} WHERE id = :id"), params)
                await session.commit()
                
        if update_data.user_ids is not None:
            await self._save_user_ids(pk, update_data.user_ids)
            
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        pk = int(id) if str(id).isdigit() else None
        if pk is None: return False
        SessionLocal = self._factory()
        async with SessionLocal() as session:
            res = await session.execute(text("DELETE FROM sj_customer_segments WHERE id = :id"), {"id": pk})
            await session.commit()
            return res.rowcount > 0

