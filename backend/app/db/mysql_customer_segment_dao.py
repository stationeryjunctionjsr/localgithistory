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
        rm = r._mapping
        out = {
            "id": str(rm["id"]),
            "externalId": rm["external_id"],
            "type": rm["type"],
            "name": rm["name"],
            "description": rm["description"],
            "isActive": bool(rm["is_active"]) if rm["is_active"] is not None else None,
            "isSystem": bool(rm["is_system"]) if rm["is_system"] is not None else None,
            "minAverageOrderValue": rm["min_avg_order_value"],
            "maxAverageOrderValue": rm["max_avg_order_value"],
            "startDate": rm["start_date"],
            "endDate": rm["end_date"],
            "minOrderFrequency": rm["min_order_freq"],
            "maxOrderFrequency": rm["max_order_freq"],
            "state": rm["state"],
            "district": rm["district"],
            "appUser": bool(rm["app_user"]) if rm["app_user"] is not None else None,
            "behavior": rm["behavior"],
            "role": rm["role"],
            "createdAt": rm["created_at"].isoformat() if rm["created_at"] else None,
            "updatedAt": rm["updated_at"].isoformat() if rm["updated_at"] else None,
            "userIds": user_ids
        }
        
        # move to filters
        filters = {}
        for k in ["minAverageOrderValue", "maxAverageOrderValue", "startDate", "endDate", "minOrderFrequency", "maxOrderFrequency", "state", "district", "appUser", "behavior", "role"]:
            if out.get(k) is not None:
                filters[k] = out.pop(k)
        if filters:
            out["filters"] = filters
            
        return CustomerSegmentInternal.model_validate(out)

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
        
        # Unpack filters safely
        filters = data.filters.model_dump() if data.filters else {}
        p = {
            "external_id": external_id,
            "created_at": now_utc(),
            "updated_at": now_utc(),
            "type": data.type,
            "name": data.name,
            "description": data.description,
            "is_active": data.isActive,
            "is_system": data.isSystem,
            "min_avg_order_value": filters.get("minAverageOrderValue"),
            "max_avg_order_value": filters.get("maxAverageOrderValue"),
            "start_date": filters.get("startDate"),
            "end_date": filters.get("endDate"),
            "min_order_freq": filters.get("minOrderFrequency"),
            "max_order_freq": filters.get("maxOrderFrequency"),
            "state": filters.get("state"),
            "district": filters.get("district"),
            "app_user": filters.get("appUser"),
            "behavior": filters.get("behavior"),
            "role": filters.get("role"),
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
            
        user_ids = data.userIds or []
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
        if data.isActive is not None: updates.append("is_active = :isActive"); params["isActive"] = data.isActive
        if data.isSystem is not None: updates.append("is_system = :isSystem"); params["isSystem"] = data.isSystem
        
        if data.filters is not None:
            filters = data.filters.model_dump(exclude_unset=True)
            if "minAverageOrderValue" in filters: updates.append("min_avg_order_value = :f1"); params["f1"] = filters["minAverageOrderValue"]
            if "maxAverageOrderValue" in filters: updates.append("max_avg_order_value = :f2"); params["f2"] = filters["maxAverageOrderValue"]
            if "startDate" in filters: updates.append("start_date = :f3"); params["f3"] = filters["startDate"]
            if "endDate" in filters: updates.append("end_date = :f4"); params["f4"] = filters["endDate"]
            if "minOrderFrequency" in filters: updates.append("min_order_freq = :f5"); params["f5"] = filters["minOrderFrequency"]
            if "maxOrderFrequency" in filters: updates.append("max_order_freq = :f6"); params["f6"] = filters["maxOrderFrequency"]
            if "state" in filters: updates.append("state = :f7"); params["f7"] = filters["state"]
            if "district" in filters: updates.append("district = :f8"); params["f8"] = filters["district"]
            if "appUser" in filters: updates.append("app_user = :f9"); params["f9"] = filters["appUser"]
            if "behavior" in filters: updates.append("behavior = :f10"); params["f10"] = filters["behavior"]
            if "role" in filters: updates.append("role = :f11"); params["f11"] = filters["role"]
            
        if len(updates) > 1:
            upd_sql = ", ".join(updates)
            SessionLocal = self._factory()
            async with SessionLocal() as session:
                await session.execute(text(f"UPDATE sj_customer_segments SET {upd_sql} WHERE id = :id"), params)
                await session.commit()
                
        if data.userIds is not None:
            await self._save_user_ids(doc.externalId, data.userIds)
            
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
