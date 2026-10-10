from typing import Optional, Dict, List, Union, Any
from datetime import datetime, timezone
import secrets
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos import (
    NotificationInternal,
    NotificationInternalCreate,
    NotificationInternalUpdate,
    NotificationMetadata,
)

def now_utc():
    return datetime.now(timezone.utc)

class MySQLNotificationsDAO:
    def __init__(self):
        self.table_name = "sj_notifications"
    
    @property
    def TABLE(self):
        return self.table_name

    def _factory(self):
        return get_async_session_factory()
        
    async def findById(self, id: Union[int, str]) -> Optional[NotificationInternal]:
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
        type: Optional[str] = None,
        is_read: Optional[bool] = None,
    ) -> Optional[NotificationInternal]:
        if id:
            return await self.findById(id)
        results = await self.findAll(user_id=user_id, type=type, is_read=is_read, limit=1)
        return results[0] if results else None

    async def findAll(
        self,
        user_id: Optional[str] = None,
        is_read: Optional[bool] = None,
        is_acknowledged: Optional[bool] = None,
        type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[NotificationInternal]:
        clauses = []
        params = {}
        if user_id is not None:
            clauses.append("user_id = :user_id")
            params["user_id"] = str(user_id)
        if is_read is not None:
            clauses.append("is_read = :is_read")
            params["is_read"] = 1 if is_read else 0
        if is_acknowledged is not None:
            clauses.append("is_acknowledged = :is_ack")
            params["is_ack"] = 1 if is_acknowledged else 0
        if type is not None:
            clauses.append("type = :type")
            params["type"] = type

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

    async def create(self, data: NotificationInternalCreate) -> NotificationInternal:
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at", "user_id", "type", "title", "message", "is_read", "is_acknowledged"]
        val_placeholders = [":eid", ":c", ":u", ":user_id", ":type", ":title", ":message", ":is_read", ":is_ack"]
        params = {
            "eid": external_id,
            "c": now,
            "u": now,
            "user_id": str(data.user_id),
            "type": data.type,
            "title": data.title,
            "message": data.message,
            "is_read": 1 if data.is_read else 0,
            "is_ack": 1 if data.is_acknowledged else 0,
        }

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

    async def update(self, id: Union[int, str], update_data: NotificationInternalUpdate) -> Optional[NotificationInternal]:
        factory = self._factory()
        updates = ["updated_at = :u"]
        params = {"u": now_utc()}

        if update_data.is_read is not None:
            updates.append("is_read = :s_is_read")
            params["s_is_read"] = 1 if update_data.is_read else 0

        if update_data.is_acknowledged is not None:
            updates.append("is_acknowledged = :s_is_acknowledged")
            params["s_is_acknowledged"] = 1 if update_data.is_acknowledged else 0

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

            await session.execute(text("DELETE FROM sj_notification_data WHERE parent_id = :id"), {"id": pk})
            result = await session.execute(text(f"DELETE FROM {self.TABLE} WHERE {del_where}"), params)
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(self, r, metadata: Optional[Dict[str, Any]] = None) -> NotificationInternal:
        meta_obj = None
        if metadata:
            try:
                meta_obj = NotificationMetadata.model_validate(metadata)
            except Exception:
                meta_obj = None
        return NotificationInternal(
            _id=str(r.id),
            user_id=str(r.user_id),
            type=r.type,
            title=r.title,
            message=r.message,
            is_read=bool(r.is_read) if r.is_read is not None else False,
            is_acknowledged=bool(r.is_acknowledged) if r.is_acknowledged is not None else False,
            metadata=meta_obj,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict[str, Any]]:
        c_map: Dict[int, Dict[str, Any]] = {rid: {} for rid in ids}
        if not ids:
            return c_map
            
        id_list = ",".join(str(int(i)) for i in ids)
        q_data = text(f"SELECT parent_id, data_key, data_value FROM sj_notification_data WHERE parent_id IN ({id_list})")
        res_data = await session.execute(q_data)
        rows_data = res_data.fetchall()

        for r in rows_data:
            c_map[r.parent_id][r.data_key] = r.data_value

        return c_map

    async def _replace_children(self, session, row_id: int, data: NotificationInternalCreate):
        if data.metadata is not None:
            await session.execute(text("DELETE FROM sj_notification_data WHERE parent_id = :id"), {"id": row_id})
            meta_dict = data.metadata.model_dump()
            for k, v in meta_dict.items():
                if v is not None:
                    await session.execute(
                        text("INSERT INTO sj_notification_data (parent_id, data_key, data_value) VALUES (:id, :k, :v)"),
                        {"id": row_id, "k": k, "v": str(v)},
                    )
