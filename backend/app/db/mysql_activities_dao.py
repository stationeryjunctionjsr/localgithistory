from typing import Optional, Dict, List, Union
from datetime import datetime, timezone
import secrets
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import (
    ActivityInternal,
    ActivityInternalCreate,
    ActivityInternalUpdate,
    ActivityMetaInternal,
)

def now_utc():
    return datetime.now(timezone.utc)

class MySQLActivitiesDAO:
    def __init__(self):
        self.table_name = "sj_activities"
    
    @property
    def TABLE(self):
        return self.table_name

    def _factory(self):
        return get_async_session_factory()
        
    async def findById(self, id: Union[int, str]) -> Optional[ActivityInternal]:
        if not id:
            return None
        async with self._factory()() as session:
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
                
            children_map = await self._fetch_children(session, [int(row.id)])
            return self._map_to_schema(row, children_map.get(int(row.id)))

    async def findOne(
        self,
        id: Optional[Union[int, str]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        action: Optional[str] = None,
    ) -> Optional[ActivityInternal]:
        if id:
            return await self.findById(id)
        results = await self.findAll(user_id=user_id, session_id=session_id, action=action, limit=1)
        return results[0] if results else None

    async def findAll(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        action: Optional[str] = None,
        is_guest: Optional[bool] = None,
        limit: Optional[int] = None,
    ) -> List[ActivityInternal]:
        clauses = []
        params = {}
        if user_id is not None:
            clauses.append("user_id = :user_id")
            params["user_id"] = user_id
        if session_id is not None:
            clauses.append("session_id = :session_id")
            params["session_id"] = session_id
        if action is not None:
            clauses.append("action = :action")
            params["action"] = action
        if is_guest is not None:
            clauses.append("is_guest = :is_guest")
            params["is_guest"] = 1 if is_guest else 0

        where_sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        limit_sql = f" LIMIT {int(limit)}" if limit else ""
        sql = f"SELECT * FROM {self.TABLE}{where_sql} ORDER BY id DESC{limit_sql}"

        async with self._factory()() as session:
            result = await session.execute(text(sql), params)
            rows = result.fetchall()
            if not rows:
                return []
            children_map = await self._fetch_children(session, [int(r.id) for r in rows])
            return [self._map_to_schema(r, children_map.get(int(r.id))) for r in rows]

    async def create(self, data: ActivityInternalCreate) -> ActivityInternal:
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        val_placeholders = [":eid", ":c", ":u"]
        params = {"eid": external_id, "c": now, "u": now}

        if data.user_id is not None:
            cols.append("user_id")
            val_placeholders.append(":user_id")
            params["user_id"] = data.user_id

        if data.session_id is not None:
            cols.append("session_id")
            val_placeholders.append(":session_id")
            params["session_id"] = data.session_id

        if data.action is not None:
            cols.append("action")
            val_placeholders.append(":action")
            params["action"] = data.action

        if data.comments is not None:
            cols.append("comments")
            val_placeholders.append(":comments")
            params["comments"] = data.comments

        if data.is_guest is not None:
            cols.append("is_guest")
            val_placeholders.append(":is_guest")
            params["is_guest"] = 1 if data.is_guest else 0

        if data.user_agent is not None:
            cols.append("user_agent")
            val_placeholders.append(":user_agent")
            params["user_agent"] = data.user_agent

        if data.os is not None:
            cols.append("os")
            val_placeholders.append(":os")
            params["os"] = data.os

        if data.os_version is not None:
            cols.append("os_version")
            val_placeholders.append(":os_version")
            params["os_version"] = data.os_version

        if data.device_type is not None:
            cols.append("device_type")
            val_placeholders.append(":device_type")
            params["device_type"] = data.device_type

        col_sql = ", ".join(cols)
        val_sql = ", ".join(val_placeholders)
        
        async with factory() as session:
            await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = (
                await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": external_id}
                )
            ).scalar()
            await self._replace_children(session, new_id, data)
            await session.commit()
            
        return await self.findById(int(new_id))

    async def update(self, id: Union[int, str], update_data: ActivityInternalUpdate) -> Optional[ActivityInternal]:
        factory = self._factory()
        updates = ["updated_at = :u"]
        params = {"u": now_utc()}

        if update_data.user_id is not None:
            updates.append("user_id = :user_id")
            params["user_id"] = update_data.user_id

        if update_data.comments is not None:
            updates.append("comments = :comments")
            params["comments"] = update_data.comments

        if update_data.is_guest is not None:
            updates.append("is_guest = :is_guest")
            params["is_guest"] = 1 if update_data.is_guest else 0

        upd_sql = ", ".join(updates)
        async with factory() as session:
            if str(id).isdigit():
                pk = int(id)
                upd_where = "id = :pk"
            else:
                res = await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": str(id)}
                )
                pk = res.scalar()
                if not pk:
                    return None
                upd_where = "id = :pk"
            params["pk"] = pk

            await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE {upd_where}"), params)
            await self._replace_children(session, pk, update_data)
            await session.commit()
                
        return await self.findById(pk)

    async def delete(self, id: Union[int, str]) -> bool:
        factory = self._factory()
        if not factory or not id:
            return False
        async with factory() as session:
            if str(id).isdigit():
                pk = int(id)
                del_where = "id = :pk"
                params = {"pk": pk}
            else:
                res = await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": str(id)}
                )
                pk = res.scalar()
                if not pk:
                    return False
                del_where = "id = :pk"
                params = {"pk": pk}

            await session.execute(text("DELETE FROM sj_activity_meta WHERE parent_id = :id"), {"id": pk})
            result = await session.execute(text(f"DELETE FROM {self.TABLE} WHERE {del_where}"), params)
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(self, r, meta: Optional[List[ActivityMetaInternal]] = None) -> ActivityInternal:
        return ActivityInternal(
            _id=str(r.id),
            user_id=r.user_id,
            session_id=r.session_id,
            action=r.action,
            comments=r.comments,
            is_guest=bool(r.is_guest) if r.is_guest is not None else None,
            user_agent=r.user_agent,
            os=r.os,
            os_version=r.os_version,
            device_type=r.device_type,
            created_at=r.created_at,
            updated_at=r.updated_at,
            meta=meta if meta else None,
        )

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, List[ActivityMetaInternal]]:
        c_map: Dict[int, List[ActivityMetaInternal]] = {rid: [] for rid in ids}
        if not ids:
            return c_map
            
        id_list = ",".join(str(int(i)) for i in ids)
        q_meta = text(f"SELECT parent_id, meta_key, meta_value FROM sj_activity_meta WHERE parent_id IN ({id_list})")
        res_meta = await session.execute(q_meta)
        rows_meta = res_meta.fetchall()

        for r in rows_meta:
            c_map[r.parent_id].append(ActivityMetaInternal(key=r.meta_key, value=r.meta_value))

        return c_map

    async def _replace_children(self, session, row_id: int, data: Union[ActivityInternalCreate, ActivityInternalUpdate]):
        if isinstance(data, ActivityInternalCreate) and data.meta is not None:
            await session.execute(text("DELETE FROM sj_activity_meta WHERE parent_id = :id"), {"id": row_id})
            for item in data.meta:
                await session.execute(
                    text("INSERT INTO sj_activity_meta (parent_id, meta_key, meta_value) VALUES (:id, :v0, :v1)"),
                    {"id": row_id, "v0": item.key, "v1": item.value},
                )
