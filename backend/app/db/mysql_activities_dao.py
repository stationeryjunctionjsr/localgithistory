from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import secrets
import json
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import ActivityInternal
from app.models.daos_flat import ActivityInternalCreate, ActivityInternalUpdate

def now_utc():
    return datetime.now(timezone.utc)

class MySQLActivitiesDAO:
    def __init__(self):
        self.table_name = "sj_activities"
    
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
            
            query_map = {'userId': 'user_id', 'sessionId': 'session_id', 'action': 'action', 'comment': 'comments', 'isGuest': 'is_guest', 'userAgent': 'user_agent', 'os': 'os', 'osVersion': 'os_version', 'deviceType': 'device_type', 'appVersion': 'app_version', 'deviceModel': 'device_model', 'locale': 'locale', 'ip': 'ip'}
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
            
            query_map = {'userId': 'user_id', 'sessionId': 'session_id', 'action': 'action', 'comment': 'comments', 'isGuest': 'is_guest', 'userAgent': 'user_agent', 'os': 'os', 'osVersion': 'os_version', 'deviceType': 'device_type', 'appVersion': 'app_version', 'deviceModel': 'device_model', 'locale': 'locale', 'ip': 'ip'}
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

        if data.sessionId is not None:
            cols.append("session_id")
            params["s_sessionId"] = data.sessionId

        if data.action is not None:
            cols.append("action")
            params["s_action"] = data.action

        if data.comment is not None:
            cols.append("comments")
            params["s_comment"] = data.comment

        if data.isGuest is not None:
            cols.append("is_guest")
            params["s_isGuest"] = data.isGuest

        if data.user_agent is not None:
            cols.append("user_agent")
            params["s_userAgent"] = data.user_agent

        if data.os is not None:
            cols.append("os")
            params["s_os"] = data.os

        if data.osVersion is not None:
            cols.append("os_version")
            params["s_osVersion"] = data.osVersion

        if data.deviceType is not None:
            cols.append("device_type")
            params["s_deviceType"] = data.deviceType

        if data.appVersion is not None:
            cols.append("app_version")
            params["s_appVersion"] = data.appVersion

        if data.deviceModel is not None:
            cols.append("device_model")
            params["s_deviceModel"] = data.deviceModel

        if data.locale is not None:
            cols.append("locale")
            params["s_locale"] = data.locale

        if data.ip is not None:
            cols.append("ip")
            params["s_ip"] = data.ip

        col_sql = ", ".join(cols)
        val_sql = ", ".join([":eid", ":c", ":u"] + [f":s_{k}" for k in ['userId', 'sessionId', 'action', 'comment', 'isGuest', 'userAgent', 'os', 'osVersion', 'deviceType', 'appVersion', 'deviceModel', 'locale', 'ip'] if f"s_{k}" in params] + [f":c_{k}" for k in [] if f"c_{k}" in params])
        
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

        if data.sessionId is not None:
            updates.append("session_id = :s_sessionId")
            params["s_sessionId"] = data.sessionId

        if data.action is not None:
            updates.append("action = :s_action")
            params["s_action"] = data.action

        if data.comment is not None:
            updates.append("comments = :s_comment")
            params["s_comment"] = data.comment

        if data.isGuest is not None:
            updates.append("is_guest = :s_isGuest")
            params["s_isGuest"] = data.isGuest

        if data.user_agent is not None:
            updates.append("user_agent = :s_userAgent")
            params["s_userAgent"] = data.user_agent

        if data.os is not None:
            updates.append("os = :s_os")
            params["s_os"] = data.os

        if data.osVersion is not None:
            updates.append("os_version = :s_osVersion")
            params["s_osVersion"] = data.osVersion

        if data.deviceType is not None:
            updates.append("device_type = :s_deviceType")
            params["s_deviceType"] = data.deviceType

        if data.appVersion is not None:
            updates.append("app_version = :s_appVersion")
            params["s_appVersion"] = data.appVersion

        if data.deviceModel is not None:
            updates.append("device_model = :s_deviceModel")
            params["s_deviceModel"] = data.deviceModel

        if data.locale is not None:
            updates.append("locale = :s_locale")
            params["s_locale"] = data.locale

        if data.ip is not None:
            updates.append("ip = :s_ip")
            params["s_ip"] = data.ip

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

            await session.execute(text(f"DELETE FROM sj_activity_meta WHERE parent_id = :id"), {"id": pk})

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
        out["sessionId"] = rm["session_id"]
        out["action"] = rm["action"]
        out["comment"] = rm["comments"]
        out["isGuest"] = bool(rm["is_guest"]) if rm["is_guest"] is not None else None
        out["userAgent"] = rm["user_agent"]
        out["os"] = rm["os"]
        out["osVersion"] = rm["os_version"]
        out["deviceType"] = rm["device_type"]
        out["appVersion"] = rm["app_version"]
        out["deviceModel"] = rm["device_model"]
        out["locale"] = rm["locale"]
        out["ip"] = rm["ip"]
        for k, v in children.items():
            out[k] = v
            
        return ActivityInternal(**out)

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:
        c_map = {rid: {} for rid in ids}
        if not ids:
            return c_map
            
        id_list = ",".join(map(str, ids))

        q_meta = text(f"SELECT parent_id, meta_key, meta_value FROM sj_activity_meta WHERE parent_id IN ({id_list})")
        res_meta = await session.execute(q_meta)
        rows_meta = res_meta.fetchall()

        for r in rows_meta:
            if "meta" not in c_map[r.parent_id]:
                c_map[r.parent_id]["meta"] = []
            obj = {}

            obj["key"] = r[1]
            obj["value"] = r[2]
            c_map[r.parent_id]["meta"].append(obj)

        return c_map

    async def _replace_children(self, session, row_id: int, data: Any):

        if data.meta is not None:
            await session.execute(text(f"DELETE FROM sj_activity_meta WHERE parent_id = :id"), {"id": row_id})
            child_list = data.meta or []

            if child_list:
                for item in child_list:
                    p = {"id": row_id}

                    p["v0"] = item.key
                    p["v1"] = item.value
                    await session.execute(text(f"INSERT INTO sj_activity_meta (parent_id, meta_key, meta_value) VALUES (:id, :v0, :v1)"), p)
