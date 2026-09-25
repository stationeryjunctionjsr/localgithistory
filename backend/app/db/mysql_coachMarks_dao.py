from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import secrets
import json
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import CoachMarkInternal
from app.models.daos_flat import CoachMarkInternalCreate, CoachMarkInternalUpdate

def now_utc():
    return datetime.now(timezone.utc)

class MySQLCoachMarksDAO:
    def __init__(self):
        self.table_name = "sj_coach_marks"
    
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
            
            query_map = {'anchorId': 'anchor_id', 'title': 'title', 'description': 'description', 'screenName': 'screen_name', 'sequenceOrder': 'sequence_order', 'isActive': 'is_active'}
            query_map["_id"] = "id"
            query_map["externalId"] = "external_id"
            
            for k, v in kwargs.items():
                db_col = query_map[k] if k in query_map else k
                conditions.append(f"{db_col} = :{k}")
                params[k] = v
                
            where_clause = " AND ".join(conditions)
            q = text(f"SELECT * FROM {self.TABLE} WHERE {where_clause} LIMIT 1")
            result = await session.execute(q, params)
            row = result.fetchone()
            if not row:
                return None
                
            children_map = await self._fetch_children(session, [int(row.id)]) if False else {}
            return self._map_to_schema(row, children_map.get(int(row.id), {}))
            
    async def findAll(self, query: Optional[Dict[str, Any]] = None) -> List[Any]:
        query = query or {}
        async with self._factory()() as session:
            sql = f"SELECT * FROM {self.TABLE}"
            params = {}
            
            query_map = {'anchorId': 'anchor_id', 'title': 'title', 'description': 'description', 'screenName': 'screen_name', 'sequenceOrder': 'sequence_order', 'isActive': 'is_active'}
            query_map["_id"] = "id"
            query_map["externalId"] = "external_id"
            
            if query:
                conditions = []
                for k, v in query.items():
                    db_col = query_map[k] if k in query_map else k
                    conditions.append(f"{db_col} = :{k}")
                    params[k] = v
                if conditions:
                    sql += " WHERE " + " AND ".join(conditions)
                    
            q = text(sql)
            result = await session.execute(q, params)
            rows = result.fetchall()
            
            if not rows:
                return []
                
            children_map = await self._fetch_children(session, [int(r.id) for r in rows]) if False else {}
            
            return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]

    async def create(self, data: Any) -> Any:
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        params = {"eid": external_id, "c": now, "u": now}

        if data.anchorId is not None:
            cols.append("anchor_id")
            params["s_anchorId"] = data.anchorId

        if data.title is not None:
            cols.append("title")
            params["s_title"] = data.title

        if data.description is not None:
            cols.append("description")
            params["s_description"] = data.description

        if data.screenName is not None:
            cols.append("screen_name")
            params["s_screenName"] = data.screenName

        if data.sequenceOrder is not None:
            cols.append("sequence_order")
            params["s_sequenceOrder"] = data.sequenceOrder

        if data.isActive is not None:
            cols.append("is_active")
            params["s_isActive"] = data.isActive

        col_sql = ", ".join(cols)
        val_sql = ", ".join([":eid", ":c", ":u"] + [f":s_{k}" for k in ['anchorId', 'title', 'description', 'screenName', 'sequenceOrder', 'isActive'] if f"s_{k}" in params] + [f":c_{k}" for k in [] if f"c_{k}" in params])
        
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

        if data.anchorId is not None:
            updates.append("anchor_id = :s_anchorId")
            params["s_anchorId"] = data.anchorId

        if data.title is not None:
            updates.append("title = :s_title")
            params["s_title"] = data.title

        if data.description is not None:
            updates.append("description = :s_description")
            params["s_description"] = data.description

        if data.screenName is not None:
            updates.append("screen_name = :s_screenName")
            params["s_screenName"] = data.screenName

        if data.sequenceOrder is not None:
            updates.append("sequence_order = :s_sequenceOrder")
            params["s_sequenceOrder"] = data.sequenceOrder

        if data.isActive is not None:
            updates.append("is_active = :s_isActive")
            params["s_isActive"] = data.isActive

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

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        pk = int(id) if str(id).isdigit() else None
        async with factory() as session:

            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pk},
            )
            await session.commit()
            return result.rowcount > 0

    async def deleteMany(self, query: Dict) -> Any:
        docs = await self.findAll(query)
        deleted = 0
        for d in docs:
            # Depending on schema format, id might be _id or id
            d_id = d.id
            if d_id and await self.delete(d_id):
                deleted += 1
        return {"deletedCount": deleted}

    def _map_to_schema(self, r, children: Dict) -> Any:
        rm = r._mapping
        out = {
            "_id": str(rm["id"]), 
            "externalId": rm["external_id"]
        }
        
        created_at = rm["created_at"]
        if created_at:
            out["createdAt"] = created_at.isoformat()
            
        updated_at = rm["updated_at"]
        if updated_at:
            out["updatedAt"] = updated_at.isoformat()

        out["anchorId"] = rm["anchor_id"]
        out["title"] = rm["title"]
        out["description"] = rm["description"]
        out["screenName"] = rm["screen_name"]
        out["sequenceOrder"] = rm["sequence_order"]
        out["isActive"] = bool(rm["is_active"]) if rm["is_active"] is not None else None
        for k, v in children.items():
            out[k] = v
            
        return CoachMarkInternal(**out)

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:
        return {}
        
    async def _replace_children(self, session, row_id: int, data: Any):
        pass
