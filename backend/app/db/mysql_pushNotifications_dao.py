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
        return self.table_name

    def _factory(self):
        return get_async_session_factory()
        
    async def findById(self, id: str) -> Optional['PushNotificationsInternal']:
        return await self.findOne({"_id": id})

    async def findOne(self, query=None, **kwargs) -> Optional['PushNotificationsInternal']:
        if query:
            kwargs.update(query)
        if not kwargs:
            return None
        
        async with self._factory()() as session:
            conditions = []
            params = {}
            
            query_map = {'title': 'title', 'message': 'message', 'link': 'link', 'image': 'image', 'status': 'status', 'scheduled_for': 'scheduled_for', 'delivered_count': 'delivered_count', 'read_count': 'read_count', 'user_segment': 'user_segment', 'user_behavior': 'user_behavior', 'created_by': 'created_by'}
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
            
    async def findAll(self, query: Optional[dict] = None) -> List['PushNotificationsInternal']:
        query = query or {}
        async with self._factory()() as session:
            sql = f"SELECT * FROM {self.TABLE}"
            params = {}
            
            query_map = {'title': 'title', 'message': 'message', 'link': 'link', 'image': 'image', 'status': 'status', 'scheduled_for': 'scheduled_for', 'delivered_count': 'delivered_count', 'read_count': 'read_count', 'user_segment': 'user_segment', 'user_behavior': 'user_behavior', 'created_by': 'created_by'}
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

    async def create(self, data: 'PushNotificationsInternalCreate') -> 'PushNotificationsInternal':
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

        if data.scheduled_for is not None:
            cols.append("scheduled_for")
            params["s_scheduled_for"] = data.scheduled_for

        if data.delivered_count is not None:
            cols.append("delivered_count")
            params["s_delivered_count"] = data.delivered_count

        if data.read_count is not None:
            cols.append("read_count")
            params["s_read_count"] = data.read_count

        if data.user_segment is not None:
            cols.append("user_segment")
            params["s_user_segment"] = data.user_segment

        if data.user_behavior is not None:
            cols.append("user_behavior")
            params["s_user_behavior"] = data.user_behavior

        if data.created_by is not None:
            cols.append("created_by")
            params["s_created_by"] = data.created_by

        col_sql = ", ".join(cols)
        val_sql = ", ".join([":eid", ":c", ":u"] + [f":s_{k}" for k in ['title', 'message', 'link', 'image', 'status', 'scheduled_for', 'delivered_count', 'read_count', 'user_segment', 'user_behavior', 'created_by'] if f"s_{k}" in params] + [f":c_{k}" for k in [] if f"c_{k}" in params])
        
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

    async def update(self, id: str, update_data: 'PushNotificationsInternalUpdate') -> 'PushNotificationsInternal':
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

        if data.scheduled_for is not None:
            updates.append("scheduled_for = :s_scheduledFor")
            params["s_scheduled_for"] = data.scheduled_for

        if data.delivered_count is not None:
            updates.append("delivered_count = :s_deliveredCount")
            params["s_delivered_count"] = data.delivered_count

        if data.read_count is not None:
            updates.append("read_count = :s_readCount")
            params["s_read_count"] = data.read_count

        if data.user_segment is not None:
            updates.append("user_segment = :s_userSegment")
            params["s_user_segment"] = data.user_segment

        if data.user_behavior is not None:
            updates.append("user_behavior = :s_userBehavior")
            params["s_user_behavior"] = data.user_behavior

        if data.created_by is not None:
            updates.append("created_by = :s_createdBy")
            params["s_created_by"] = data.created_by

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

    async def deleteMany(self, query: Dict) -> 'PushNotificationsInternal':
        docs = await self.findAll(query)
        deleted = 0
        for d in docs:
            # Depending on schema format, id might be _id or id
            d_id = d.id
            if d_id and await self.delete(d_id):
                deleted += 1
        return {"deletedCount": deleted}

    def _map_to_schema(self, r, children: Dict) -> 'PushNotificationsInternal':
        obj = PushNotificationsInternal.model_validate(r)
        for k, v in children.items():
            setattr(obj, k, v)
        return obj

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:
        return {}
        
    async def _replace_children(self, session, row_id: int, data: 'CamelBaseModel'):
        pass
