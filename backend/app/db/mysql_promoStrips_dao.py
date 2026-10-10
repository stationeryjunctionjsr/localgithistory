from typing import Optional, Dict, List, Any, Union
from datetime import datetime, timezone
import secrets
import json
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import PromoStripsInternal
from app.models.daos_flat import PromoStripsInternalCreate, PromoStripsInternalUpdate

def now_utc():
    return datetime.now(timezone.utc)

class MySQLPromoStripsDAO:
    def __init__(self):
        self.table_name = "sj_promo_strips"
    
    @property
    def TABLE(self):
        from app.config.settings import settings
        return self.table_name

    def _factory(self):
        return get_async_session_factory()
        
    async def findById(self, id: Union[int, str]) -> Optional['PromoStripsInternal']:
        factory = self._factory()
        if not factory or not id:
            return None
        async with factory() as session:
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
            return self._map_to_schema(row)

    async def findOne(
        self,
        query: Optional[dict] = None,
        is_active: Optional[bool] = None,
        text_filter: Optional[str] = None,
    ) -> Optional['PromoStripsInternal']:
        if query:
            if "_id" in query or "id" in query:
                return await self.findById(query.get("_id") or query.get("id"))
            if "externalId" in query and query["externalId"]:
                return await self.findById(query["externalId"])
        results = await self.findAll(query=query, is_active=is_active, text_filter=text_filter)
        return results[0] if results else None

    async def findAll(
        self,
        query: Optional[dict] = None,
        is_active: Optional[bool] = None,
        text_filter: Optional[str] = None,
    ) -> List['PromoStripsInternal']:
        if query:
            if is_active is None and "is_active" in query:
                is_active = query["is_active"]
            if text_filter is None and "text" in query:
                text_filter = query["text"]

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

    async def create(self, data: 'PromoStripsInternalCreate') -> 'PromoStripsInternal':
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        params = {"eid": external_id, "c": now, "u": now}

        if data.text is not None:
            cols.append("text")
            params["s_text"] = data.text

        if data.is_active is not None:
            cols.append("is_active")
            params["s_is_active"] = data.is_active

        if data.zone_ids is not None:
            cols.append("zone_ids")
            params["s_zone_ids"] = json.dumps(data.zone_ids)

        col_sql = ", ".join(cols)
        val_parts = [":eid", ":c", ":u"]
        if "s_text" in params:
            val_parts.append(":s_text")
        if "s_is_active" in params:
            val_parts.append(":s_is_active")
        if "s_zone_ids" in params:
            val_parts.append(":s_zone_ids")
        val_sql = ", ".join(val_parts)
        
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

    async def update(self, id: str, update_data: 'PromoStripsInternalUpdate') -> Optional['PromoStripsInternal']:
        factory = self._factory()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now_utc()}

        if update_data.text is not None:
            updates.append("text = :s_text")
            params["s_text"] = update_data.text

        if update_data.is_active is not None:
            updates.append("is_active = :s_is_active")
            params["s_is_active"] = update_data.is_active

        if update_data.zone_ids is not None:
            updates.append("zone_ids = :s_zone_ids")
            params["s_zone_ids"] = json.dumps(update_data.zone_ids)

        if len(updates) > 1:
            upd_sql = ", ".join(updates)
            async with factory() as session:
                await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE id = :id"), params)
                await session.commit()
                
        return await self.findById(id)

    async def delete(self, id: Union[int, str]) -> bool:
        factory = self._factory()
        if not factory or not id:
            return False
        async with factory() as session:
            if str(id).isdigit():
                pk = int(id)
            else:
                res = await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": str(id)}
                )
                pk = res.scalar()
                if not pk:
                    return False

            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pk},
            )
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(self, r, children: Dict = None) -> 'PromoStripsInternal':
        from app.models.daos_flat import PromoStripsInternal
        zone_ids = None
        raw_zone = r.zone_ids
        if raw_zone:
            if isinstance(raw_zone, str):
                try:
                    zone_ids = json.loads(raw_zone)
                except Exception:
                    zone_ids = []
            elif isinstance(raw_zone, list):
                zone_ids = raw_zone

        return PromoStripsInternal(
            id=str(r.id),
            external_id=r.external_id,
            is_active=bool(r.is_active) if r.is_active is not None else None,
            text=r.text,
            zone_ids=zone_ids,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:
        return {}
        
    async def _replace_children(self, session, row_id: int, data: 'CamelBaseModel'):
        pass

