from typing import List, Optional
import datetime
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import CustomerSegmentInternal, CustomerSegmentInternalCreate, CustomerSegmentInternalUpdate
from app.models.customer_segment import CustomerSegmentFilters
from app.db.db_utils import now_utc

class MySQLCustomerSegmentDAO:
    def __init__(self):
        pass

    def _map_to_schema(self, r, user_ids: List[int]) -> CustomerSegmentInternal:
        return CustomerSegmentInternal(
            id=r.id,
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

    async def _fetch_user_ids(self, segment_id: int) -> List[int]:
        async_session = get_async_session_factory()
        if not async_session:
            return []
        async with async_session() as session:
            result = await session.execute(
                text("SELECT user_id FROM sj_customer_segment_users WHERE segment_id = :sid"), {"sid": segment_id}
            )
            return [int(r.user_id) for r in result.fetchall()]

    async def _save_user_ids(self, segment_id: int, user_ids: List[int]):
        if user_ids is None:
            return
        async_session = get_async_session_factory()
        if not async_session:
            return
        async with async_session() as session:
            await session.execute(
                text("DELETE FROM sj_customer_segment_users WHERE segment_id = :sid"), {"sid": segment_id}
            )
            if user_ids:
                params = [{"sid": segment_id, "uid": int(uid)} for uid in user_ids]
                await session.execute(
                    text("INSERT INTO sj_customer_segment_users (segment_id, user_id) VALUES (:sid, :uid)"), params
                )
            await session.commit()

    async def has_user(self, segment_id: int, user_id: int) -> bool:
        async_session = get_async_session_factory()
        if not async_session:
            return False
        async with async_session() as session:
            result = await session.execute(
                text(
                    "SELECT 1 FROM sj_customer_segment_users "
                    "WHERE segment_id = :sid AND user_id = :uid "
                    "LIMIT 1"
                ),
                {"sid": segment_id, "uid": user_id},
            )
            return result.scalar() is not None

    async def findById(self, id: int) -> Optional[CustomerSegmentInternal]:
        if not id:
            return None
        async_session = get_async_session_factory()
        if not async_session:
            return None
        async with async_session() as session:
            result = await session.execute(
                text("SELECT * FROM sj_customer_segments WHERE id = :id"), {"id": id}
            )
            row = result.fetchone()
            if not row:
                return None
            
            user_ids = await self._fetch_user_ids(row.id)
            return self._map_to_schema(row, user_ids)

    async def findAll(self, query: Optional[object] = None) -> List[CustomerSegmentInternal]:
        async_session = get_async_session_factory()
        if not async_session:
            return []
        async with async_session() as session:
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
            "is_active": 1 if data.is_active else (0 if data.is_active is False else 1),
            "is_system": 1 if data.is_system else 0,
            "min_avg_order_value": data.filters.min_average_order_value if data.filters else None,
            "max_avg_order_value": data.filters.max_average_order_value if data.filters else None,
            "start_date": data.filters.start_date if data.filters else None,
            "end_date": data.filters.end_date if data.filters else None,
            "min_order_freq": data.filters.min_order_frequency if data.filters else None,
            "max_order_freq": data.filters.max_order_frequency if data.filters else None,
            "state": data.filters.state if data.filters else None,
            "district": data.filters.district if data.filters else None,
            "app_user": 1 if (data.filters and data.filters.app_user) else (0 if (data.filters and data.filters.app_user is False) else None),
            "behavior": data.filters.behavior if data.filters else None,
            "role": data.filters.role if data.filters else None,
        }
        
        cols = ", ".join(p.keys())
        vals = ", ".join([f":{k}" for k in p.keys()])
        
        async_session = get_async_session_factory()
        if not async_session:
            raise RuntimeError("Database session factory unavailable")
        async with async_session() as session:
            res = await session.execute(
                text(f"INSERT INTO sj_customer_segments ({cols}) VALUES ({vals})"), p
            )
            new_id = res.lastrowid
            await session.commit()
            
        user_ids = data.user_ids or []
        await self._save_user_ids(new_id, user_ids)
        return await self.findById(new_id)

    async def update(self, id: int, update_data: CustomerSegmentInternalUpdate) -> Optional[CustomerSegmentInternal]:
        if not id:
            return None
        async_session = get_async_session_factory()
        if not async_session:
            return None

        fields = update_data.model_fields_set
        if not fields:
            return await self.findById(id)

        updates = ["updated_at = :u"]
        params = {"id": id, "u": now_utc()}

        if "name" in fields:
            updates.append("name = :name")
            params["name"] = update_data.name
        if "description" in fields:
            updates.append("description = :description")
            params["description"] = update_data.description
        if "is_active" in fields:
            updates.append("is_active = :isActive")
            params["isActive"] = 1 if update_data.is_active else 0

        if "filters" in fields and update_data.filters is not None:
            filter_fields = update_data.filters.model_fields_set
            f = update_data.filters
            if "min_average_order_value" in filter_fields:
                updates.append("min_avg_order_value = :f1")
                params["f1"] = f.min_average_order_value
            if "max_average_order_value" in filter_fields:
                updates.append("max_avg_order_value = :f2")
                params["f2"] = f.max_average_order_value
            if "start_date" in filter_fields:
                updates.append("start_date = :f3")
                params["f3"] = f.start_date
            if "end_date" in filter_fields:
                updates.append("end_date = :f4")
                params["f4"] = f.end_date
            if "min_order_frequency" in filter_fields:
                updates.append("min_order_freq = :f5")
                params["f5"] = f.min_order_frequency
            if "max_order_frequency" in filter_fields:
                updates.append("max_order_freq = :f6")
                params["f6"] = f.max_order_frequency
            if "state" in filter_fields:
                updates.append("state = :f7")
                params["f7"] = f.state
            if "district" in filter_fields:
                updates.append("district = :f8")
                params["f8"] = f.district
            if "app_user" in filter_fields:
                updates.append("app_user = :f9")
                params["f9"] = 1 if f.app_user else (0 if f.app_user is False else None)
            if "behavior" in filter_fields:
                updates.append("behavior = :f10")
                params["f10"] = f.behavior
            if "role" in filter_fields:
                updates.append("role = :f11")
                params["f11"] = f.role

        upd_sql = ", ".join(updates)
        async with async_session() as session:
            await session.execute(text(f"UPDATE sj_customer_segments SET {upd_sql} WHERE id = :id"), params)
            await session.commit()

        if "user_ids" in fields and update_data.user_ids is not None:
            await self._save_user_ids(id, update_data.user_ids)

        return await self.findById(id)

    async def delete(self, id: int) -> bool:
        if not id:
            return False
        async_session = get_async_session_factory()
        if not async_session:
            return False
        async with async_session() as session:
            await session.execute(text("DELETE FROM sj_customer_segment_users WHERE segment_id = :id"), {"id": id})
            res = await session.execute(text("DELETE FROM sj_customer_segments WHERE id = :id"), {"id": id})
            await session.commit()
            return res.rowcount > 0

