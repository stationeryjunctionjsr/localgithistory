from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import secrets
import json
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos import NotificationInternal, NotificationInternalCreate, NotificationInternalUpdate

def now_utc():
    return datetime.now(timezone.utc)

class MySQLNotificationsDAO:
    def __init__(self):
        self.table_name = "sj_notifications"
    
    @property
    def TABLE(self):
        from app.config.settings import settings
        suffix = (settings.table_suffix if settings.table_suffix is not None else "")
        return f"{self.table_name}{suffix}"

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
            
            query_map = {'userId': 'user_id', 'type': 'type', 'title': 'title', 'message': 'message', 'isRead': 'is_read', 'isAcknowledged': 'is_acknowledged'}
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
                
            children_map = await self._fetch_children(session, [int(row.id)]) if True else {}
            return self._map_to_schema(row, children_map.get(int(row.id), {}))
            
    async def findAll(self, query: Optional[Dict[str, Any]] = None) -> List[Any]:
        query = query or {}
        async with self._factory()() as session:
            sql = f"SELECT * FROM {self.TABLE}"
            params = {}
            
            query_map = {'userId': 'user_id', 'type': 'type', 'title': 'title', 'message': 'message', 'isRead': 'is_read', 'isAcknowledged': 'is_acknowledged'}
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
                
            children_map = await self._fetch_children(session, [int(r.id) for r in rows]) if True else {}
            
            return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]

    async def create(self, data: Any) -> Any:
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        params = {"eid": external_id, "c": now, "u": now}

        if data.userId is not None:
            cols.append("user_id")
            params["s_userId"] = data.userId

        if data.type is not None:
            cols.append("type")
            params["s_type"] = data.type

        if data.title is not None:
            cols.append("title")
            params["s_title"] = data.title

        if data.message is not None:
            cols.append("message")
            params["s_message"] = data.message

        if data.isRead is not None:
            cols.append("is_read")
            params["s_isRead"] = data.isRead

        if data.isAcknowledged is not None:
            cols.append("is_acknowledged")
            params["s_isAcknowledged"] = data.isAcknowledged

        col_sql = ", ".join(cols)
        val_sql = ", ".join([":eid", ":c", ":u"] + [f":s_{k}" for k in ['userId', 'type', 'title', 'message', 'isRead', 'isAcknowledged'] if f"s_{k}" in params] + [f":c_{k}" for k in [] if f"c_{k}" in params])
        
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

        if data.userId is not None:
            updates.append("user_id = :s_userId")
            params["s_userId"] = data.userId

        if data.type is not None:
            updates.append("type = :s_type")
            params["s_type"] = data.type

        if data.title is not None:
            updates.append("title = :s_title")
            params["s_title"] = data.title

        if data.message is not None:
            updates.append("message = :s_message")
            params["s_message"] = data.message

        if data.isRead is not None:
            updates.append("is_read = :s_isRead")
            params["s_isRead"] = data.isRead

        if data.isAcknowledged is not None:
            updates.append("is_acknowledged = :s_isAcknowledged")
            params["s_isAcknowledged"] = data.isAcknowledged

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

            await session.execute(text(f"DELETE FROM sj_notification_data WHERE parent_id = :id"), {"id": pk})

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

        out["userId"] = rm["user_id"]
        out["type"] = rm["type"]
        out["title"] = rm["title"]
        out["message"] = rm["message"]
        out["isRead"] = bool(rm["is_read"]) if rm["is_read"] is not None else None
        out["isAcknowledged"] = bool(rm["is_acknowledged"]) if rm["is_acknowledged"] is not None else None
        for k, v in children.items():
            out[k] = v
            
        return NotificationInternal(**out)

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:
        c_map = {rid: {} for rid in ids}
        if not ids:
            return c_map
            
        id_list = ",".join(map(str, ids))

        q_data = text(f"SELECT parent_id, data_key, data_value FROM sj_notification_data WHERE parent_id IN ({id_list})")
        res_data = await session.execute(q_data)
        rows_data = res_data.fetchall()

        for r in rows_data:
            if "data" not in c_map[r.parent_id]:
                c_map[r.parent_id]["data"] = {}
            c_map[r.parent_id]["data"][r[1]] = r[2]

        return c_map

    async def _replace_children(self, session, row_id: int, data: Any):

        if getattr(data, "metadata", getattr(data, "data", None)) is not None:
            await session.execute(text(f"DELETE FROM sj_notification_data WHERE parent_id = :id"), {"id": row_id})
            child_list = getattr(data, "metadata", getattr(data, "data", None)) or {}

            if child_list:
                child_dict = child_list.model_dump() if hasattr(child_list, "model_dump") else child_list
            for k, v in (child_dict.items() if isinstance(child_dict, dict) else []):
                    await session.execute(text(f"INSERT INTO sj_notification_data (parent_id, data_key, data_value) VALUES (:id, :k, :v)"), {"id": row_id, "k": k, "v": v})
