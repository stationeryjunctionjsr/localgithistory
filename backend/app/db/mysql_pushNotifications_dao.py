from typing import Optional, Dict, List, Union
from datetime import datetime, timezone
import secrets
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import (
    PushNotificationsInternal,
    PushNotificationsInternalCreate,
    PushNotificationsInternalUpdate,
)

def now_utc():
    return datetime.now(timezone.utc)

class MySQLPushNotificationsDAO:
    def __init__(self):
        self.table_name = "sj_push_notifications"
    
    @property
    def TABLE(self):
        return self.table_name

    def _factory(self):
        return get_async_session_factory()
        
    async def findById(self, id: Union[int, str]) -> Optional[PushNotificationsInternal]:
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
            return self._map_to_schema(row)

    async def findOne(
        self,
        id: Optional[Union[int, str]] = None,
        status: Optional[str] = None,
        user_segment: Optional[str] = None,
    ) -> Optional[PushNotificationsInternal]:
        if id:
            return await self.findById(id)
        results = await self.findAll(status=status, user_segment=user_segment, limit=1)
        return results[0] if results else None

    async def findAll(
        self,
        status: Optional[str] = None,
        user_segment: Optional[str] = None,
        user_behavior: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[PushNotificationsInternal]:
        clauses = []
        params = {}
        if status is not None:
            clauses.append("status = :status")
            params["status"] = status
        if user_segment is not None:
            clauses.append("user_segment = :user_segment")
            params["user_segment"] = user_segment
        if user_behavior is not None:
            clauses.append("user_behavior = :user_behavior")
            params["user_behavior"] = user_behavior

        where_sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        limit_sql = f" LIMIT {int(limit)}" if limit else ""
        sql = f"SELECT * FROM {self.TABLE}{where_sql} ORDER BY id DESC{limit_sql}"

        async with self._factory()() as session:
            result = await session.execute(text(sql), params)
            rows = result.fetchall()
            return [self._map_to_schema(r) for r in rows]

    async def create(self, data: PushNotificationsInternalCreate) -> PushNotificationsInternal:
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        val_placeholders = [":eid", ":c", ":u"]
        params = {"eid": external_id, "c": now, "u": now}

        if data.title is not None:
            cols.append("title")
            val_placeholders.append(":title")
            params["title"] = data.title

        if data.message is not None:
            cols.append("message")
            val_placeholders.append(":message")
            params["message"] = data.message

        if data.link is not None:
            cols.append("link")
            val_placeholders.append(":link")
            params["link"] = data.link

        if data.image is not None:
            cols.append("image")
            val_placeholders.append(":image")
            params["image"] = data.image

        if data.status is not None:
            cols.append("status")
            val_placeholders.append(":status")
            params["status"] = data.status

        if data.scheduled_for is not None:
            cols.append("scheduled_for")
            val_placeholders.append(":scheduled_for")
            params["scheduled_for"] = data.scheduled_for

        if data.delivered_count is not None:
            cols.append("delivered_count")
            val_placeholders.append(":delivered_count")
            params["delivered_count"] = data.delivered_count

        if data.read_count is not None:
            cols.append("read_count")
            val_placeholders.append(":read_count")
            params["read_count"] = data.read_count

        if data.user_segment is not None:
            cols.append("user_segment")
            val_placeholders.append(":user_segment")
            params["user_segment"] = data.user_segment

        if data.user_behavior is not None:
            cols.append("user_behavior")
            val_placeholders.append(":user_behavior")
            params["user_behavior"] = data.user_behavior

        if data.created_by is not None:
            cols.append("created_by")
            val_placeholders.append(":created_by")
            params["created_by"] = data.created_by

        col_sql = ", ".join(cols)
        val_sql = ", ".join(val_placeholders)
        
        async with factory() as session:
            await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = (
                await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": external_id}
                )
            ).scalar()
            await session.commit()
            
        return await self.findById(int(new_id))

    async def update(self, id: Union[int, str], update_data: PushNotificationsInternalUpdate) -> Optional[PushNotificationsInternal]:
        factory = self._factory()
        updates = ["updated_at = :u"]
        params = {"u": now_utc()}

        if update_data.title is not None:
            updates.append("title = :title")
            params["title"] = update_data.title

        if update_data.message is not None:
            updates.append("message = :message")
            params["message"] = update_data.message

        if update_data.link is not None:
            updates.append("link = :link")
            params["link"] = update_data.link

        if update_data.image is not None:
            updates.append("image = :image")
            params["image"] = update_data.image

        if update_data.status is not None:
            updates.append("status = :status")
            params["status"] = update_data.status

        if update_data.scheduled_for is not None:
            updates.append("scheduled_for = :scheduled_for")
            params["scheduled_for"] = update_data.scheduled_for

        if update_data.delivered_count is not None:
            updates.append("delivered_count = :delivered_count")
            params["delivered_count"] = update_data.delivered_count

        if update_data.read_count is not None:
            updates.append("read_count = :read_count")
            params["read_count"] = update_data.read_count

        if update_data.user_segment is not None:
            updates.append("user_segment = :user_segment")
            params["user_segment"] = update_data.user_segment

        if update_data.user_behavior is not None:
            updates.append("user_behavior = :user_behavior")
            params["user_behavior"] = update_data.user_behavior

        if update_data.created_by is not None:
            updates.append("created_by = :created_by")
            params["created_by"] = update_data.created_by

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

            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE {del_where}"),
                params,
            )
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(self, r) -> PushNotificationsInternal:
        return PushNotificationsInternal(
            id=str(r.id),
            external_id=r.external_id,
            title=r.title,
            message=r.message,
            link=r.link,
            image=r.image,
            status=r.status,
            scheduled_for=r.scheduled_for,
            delivered_count=int(r.delivered_count) if r.delivered_count is not None else None,
            read_count=int(r.read_count) if r.read_count is not None else None,
            user_segment=r.user_segment,
            user_behavior=r.user_behavior,
            created_by=r.created_by,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
