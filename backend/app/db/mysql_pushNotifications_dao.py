from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import secrets
import json
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import PushNotificationsInternal
from app.models.daos_flat import PushNotificationsInternalCreate, PushNotificationsInternalUpdate

def now_utc():
    return datetime.now(timezone.utc)

class MySQLPushNotificationsDAO:
    def __init__(self):
        self.table_name = "sj_push_notifications"
    
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
            
            query_map = {'title': 'title', 'message': 'message', 'link': 'link', 'image': 'image', 'status': 'status', 'scheduledFor': 'scheduled_for', 'deliveredCount': 'delivered_count', 'readCount': 'read_count', 'userSegment': 'user_segment', 'userBehavior': 'user_behavior', 'createdBy': 'created_by'}
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
            
            query_map = {'title': 'title', 'message': 'message', 'link': 'link', 'image': 'image', 'status': 'status', 'scheduledFor': 'scheduled_for', 'deliveredCount': 'delivered_count', 'readCount': 'read_count', 'userSegment': 'user_segment', 'userBehavior': 'user_behavior', 'createdBy': 'created_by'}
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

        if data.title is not None:
            cols.append("title")
            params["s_title"] = data.title

        if data.message is not None:
            cols.append("message")
            params["s_message"] = data.message

        if data.link is not None:
            cols.append("link")
            params["s_link"] = data.link

        if data.image is not None:
            cols.append("image")
            params["s_image"] = data.image

        if data.status is not None:
            cols.append("status")
            params["s_status"] = data.status

        if data.scheduledFor is not None:
            cols.append("scheduled_for")
            params["s_scheduledFor"] = data.scheduledFor

        if data.deliveredCount is not None:
            cols.append("delivered_count")
            params["s_deliveredCount"] = data.deliveredCount

        if data.readCount is not None:
            cols.append("read_count")
            params["s_readCount"] = data.readCount

        if data.userSegment is not None:
            cols.append("user_segment")
            params["s_userSegment"] = data.userSegment

        if data.userBehavior is not None:
            cols.append("user_behavior")
            params["s_userBehavior"] = data.userBehavior

        if data.createdBy is not None:
            cols.append("created_by")
            params["s_createdBy"] = data.createdBy

        col_sql = ", ".join(cols)
        val_sql = ", ".join([":eid", ":c", ":u"] + [f":s_{k}" for k in ['title', 'message', 'link', 'image', 'status', 'scheduledFor', 'deliveredCount', 'readCount', 'userSegment', 'userBehavior', 'createdBy'] if f"s_{k}" in params] + [f":c_{k}" for k in [] if f"c_{k}" in params])
        
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

        if data.title is not None:
            updates.append("title = :s_title")
            params["s_title"] = data.title

        if data.message is not None:
            updates.append("message = :s_message")
            params["s_message"] = data.message

        if data.link is not None:
            updates.append("link = :s_link")
            params["s_link"] = data.link

        if data.image is not None:
            updates.append("image = :s_image")
            params["s_image"] = data.image

        if data.status is not None:
            updates.append("status = :s_status")
            params["s_status"] = data.status

        if data.scheduledFor is not None:
            updates.append("scheduled_for = :s_scheduledFor")
            params["s_scheduledFor"] = data.scheduledFor

        if data.deliveredCount is not None:
            updates.append("delivered_count = :s_deliveredCount")
            params["s_deliveredCount"] = data.deliveredCount

        if data.readCount is not None:
            updates.append("read_count = :s_readCount")
            params["s_readCount"] = data.readCount

        if data.userSegment is not None:
            updates.append("user_segment = :s_userSegment")
            params["s_userSegment"] = data.userSegment

        if data.userBehavior is not None:
            updates.append("user_behavior = :s_userBehavior")
            params["s_userBehavior"] = data.userBehavior

        if data.createdBy is not None:
            updates.append("created_by = :s_createdBy")
            params["s_createdBy"] = data.createdBy

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

        out["title"] = rm["title"]
        out["message"] = rm["message"]
        out["link"] = rm["link"]
        out["image"] = rm["image"]
        out["status"] = rm["status"]
        out["scheduledFor"] = rm["scheduled_for"]
        out["deliveredCount"] = rm["delivered_count"]
        out["readCount"] = rm["read_count"]
        out["userSegment"] = rm["user_segment"]
        out["userBehavior"] = rm["user_behavior"]
        out["createdBy"] = rm["created_by"]
        for k, v in children.items():
            out[k] = v
            
        return PushNotificationsInternal(**out)

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:
        return {}
        
    async def _replace_children(self, session, row_id: int, data: Any):
        pass
