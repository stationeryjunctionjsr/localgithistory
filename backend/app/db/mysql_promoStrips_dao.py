from typing import Optional, List
from datetime import datetime, timezone
import json
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import PromoStripsInternal, PromoStripsInternalCreate, PromoStripsInternalUpdate

def now_utc():
    return datetime.now(timezone.utc)

class MySQLPromoStripsDAO:
    def __init__(self):
        self.table_name = "sj_promo_strips"
    
    @property
    def TABLE(self):
        return self.table_name

    def _factory(self):
        return get_async_session_factory()
        
    async def findById(self, id: int) -> Optional[PromoStripsInternal]:
        factory = self._factory()
        if not factory or not id:
            return None
        async with factory() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE id = :id LIMIT 1")
            result = await session.execute(q, {"id": id})
            row = result.fetchone()
            if not row:
                return None
            return self._map_to_schema(row)

    async def findOne(
        self,
        id: Optional[int] = None,
        is_active: Optional[bool] = None,
        text_filter: Optional[str] = None,
    ) -> Optional[PromoStripsInternal]:
        if id:
            return await self.findById(id)
        results = await self.findAll(is_active=is_active, text_filter=text_filter)
        return results[0] if results else None

    async def findAll(
        self,
        is_active: Optional[bool] = None,
        text_filter: Optional[str] = None,
    ) -> List[PromoStripsInternal]:
        clauses = []
        params = {}
        if is_active is not None:
            clauses.append("is_active = :act")
            params["act"] = 1 if is_active else 0
        if text_filter is not None:
            clauses.append("text = :txt")
            params["txt"] = text_filter

        where_sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT * FROM {self.TABLE}{where_sql} ORDER BY id ASC"

        factory = self._factory()
        if not factory:
            return []
        async with factory() as session:
            result = await session.execute(text(sql), params)
            rows = result.fetchall()
            return [self._map_to_schema(r) for r in rows]

    async def create(self, data: PromoStripsInternalCreate) -> PromoStripsInternal:
        factory = self._factory()
        now = now_utc()
        
        cols = ["created_at", "updated_at"]
        params = {"c": now, "u": now}

        if data.text is not None:
            cols.append("text")
            params["s_text"] = data.text

        if data.is_active is not None:
            cols.append("is_active")
            params["s_is_active"] = 1 if data.is_active else 0

        if data.zone_ids is not None:
            cols.append("zone_ids")
            params["s_zone_ids"] = json.dumps(data.zone_ids)

        col_sql = ", ".join(cols)
        val_parts = [":c", ":u"]
        if "s_text" in params:
            val_parts.append(":s_text")
        if "s_is_active" in params:
            val_parts.append(":s_is_active")
        if "s_zone_ids" in params:
            val_parts.append(":s_zone_ids")
        val_sql = ", ".join(val_parts)
        
        async with factory() as session:
            result = await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = result.lastrowid
            await session.commit()
            
        return await self.findById(new_id)

    async def update(self, id: int, update_data: PromoStripsInternalUpdate) -> Optional[PromoStripsInternal]:
        factory = self._factory()
        if not factory or not id:
            return None
        updates = ["updated_at = :u"]
        params = {"u": now_utc(), "id": id}

        if update_data.text is not None:
            updates.append("text = :s_text")
            params["s_text"] = update_data.text

        if update_data.is_active is not None:
            updates.append("is_active = :s_is_active")
            params["s_is_active"] = 1 if update_data.is_active else 0

        if update_data.zone_ids is not None:
            updates.append("zone_ids = :s_zone_ids")
            params["s_zone_ids"] = json.dumps(update_data.zone_ids)

        if len(updates) > 1:
            upd_sql = ", ".join(updates)
            async with factory() as session:
                await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE id = :id"), params)
                await session.commit()
                
        return await self.findById(id)

    async def delete(self, id: int) -> bool:
        factory = self._factory()
        if not factory or not id:
            return False
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": id},
            )
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(self, r) -> PromoStripsInternal:
        zone_ids = json.loads(r.zone_ids) if r.zone_ids else None
        return PromoStripsInternal(
            id=r.id,
            is_active=bool(r.is_active) if r.is_active is not None else None,
            text=r.text,
            zone_ids=zone_ids,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
