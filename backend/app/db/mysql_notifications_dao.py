from typing import Optional, List
from datetime import datetime, timezone
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

    async def findById(self, id: int) -> Optional[NotificationInternal]:
        if not id:
            return None
        async_session = get_async_session_factory()
        async with async_session() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE id = :id LIMIT 1")
            result = await session.execute(q, {"id": id})
            row = result.fetchone()
            if not row:
                return None
                
            data_rows = await self._fetch_children(session, [row.id])
            return self._map_to_schema(row, data_rows)

    async def findOne(
        self,
        id: Optional[int] = None,
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
            params["user_id"] = user_id
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
        pagination_sql = ""
        if limit is not None:
            pagination_sql = " LIMIT :limit"
            params["limit"] = limit
        sql = f"SELECT * FROM {self.TABLE}{where_sql} ORDER BY id DESC{pagination_sql}"

        async_session = get_async_session_factory()
        async with async_session() as session:
            result = await session.execute(text(sql), params)
            rows = result.fetchall()
            if not rows:
                return []
            data_rows = await self._fetch_children(session, [r.id for r in rows])
            return [self._map_to_schema(r, data_rows) for r in rows]

    async def create(self, data: NotificationInternalCreate) -> NotificationInternal:
        now = now_utc()
        
        cols = ["created_at", "updated_at", "user_id", "type", "title", "message", "is_read", "is_acknowledged"]
        val_placeholders = [":c", ":u", ":user_id", ":type", ":title", ":message", ":is_read", ":is_ack"]
        params = {
            "c": now,
            "u": now,
            "user_id": data.user_id,
            "type": data.type,
            "title": data.title,
            "message": data.message,
            "is_read": 1 if data.is_read else 0,
            "is_ack": 1 if data.is_acknowledged else 0,
        }

        col_sql = ", ".join(cols)
        val_sql = ", ".join(val_placeholders)
        
        async_session = get_async_session_factory()
        async with async_session() as session:
            result = await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = result.lastrowid
            await self._replace_children(session, new_id, data)
            await session.commit()
            
        return await self.findById(new_id)

    async def update(self, id: int, update_data: NotificationInternalUpdate) -> Optional[NotificationInternal]:
        updates = ["updated_at = :u"]
        params = {"u": now_utc(), "pk": id}

        if update_data.is_read is not None:
            updates.append("is_read = :s_is_read")
            params["s_is_read"] = 1 if update_data.is_read else 0

        if update_data.is_acknowledged is not None:
            updates.append("is_acknowledged = :s_is_acknowledged")
            params["s_is_acknowledged"] = 1 if update_data.is_acknowledged else 0

        upd_sql = ", ".join(updates)
        async_session = get_async_session_factory()
        async with async_session() as session:
            await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE id = :pk"), params)
            await session.commit()

        return await self.findById(id)

    async def mark_all_as_read(self, user_id: Optional[str] = None) -> int:
        now = now_utc()
        where_clauses = ["(is_read = 0 OR is_acknowledged = 0)"]
        params = {"u": now}
        if user_id is not None:
            where_clauses.append("user_id = :uid")
            params["uid"] = user_id
        where_sql = " AND ".join(where_clauses)
        async_session = get_async_session_factory()
        async with async_session() as session:
            result = await session.execute(
                text(f"UPDATE {self.TABLE} SET is_read = 1, is_acknowledged = 1, updated_at = :u WHERE {where_sql}"),
                params,
            )
            await session.commit()
            return result.rowcount or 0

    async def delete(self, id: int) -> bool:
        if not id:
            return False
        async_session = get_async_session_factory()
        async with async_session() as session:
            await session.execute(text("DELETE FROM sj_notification_data WHERE parent_id = :id"), {"id": id})
            result = await session.execute(text(f"DELETE FROM {self.TABLE} WHERE id = :pk"), {"pk": id})
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(self, r, data_rows=None) -> NotificationInternal:
        matched = [dr for dr in (data_rows or []) if dr.parent_id == r.id]
        meta_obj = None
        if matched:
            meta_obj = NotificationMetadata()
            for dr in matched:
                k = dr.data_key
                v = dr.data_value
                if k in ("order_id", "orderId"):
                    meta_obj.order_id = v
                elif k in ("order_number", "orderNumber"):
                    meta_obj.order_number = v
                elif k in ("product_id", "productId"):
                    meta_obj.product_id = v
                elif k == "url":
                    meta_obj.url = v
                elif k == "type":
                    meta_obj.type = v
                elif k == "status":
                    meta_obj.status = v
                elif k == "amount":
                    meta_obj.amount = float(v) if v is not None else None
                elif k in ("user_id", "userId"):
                    meta_obj.user_id = v
                elif k in ("created_at", "createdAt"):
                    meta_obj.created_at = v
                elif k in ("payment_id", "paymentId"):
                    meta_obj.payment_id = v
                elif k in ("payment_id_formatted", "paymentIdFormatted"):
                    meta_obj.payment_id_formatted = v
                elif k in ("payment_method", "paymentMethod"):
                    meta_obj.payment_method = v
                elif k in ("sub_order_id", "subOrderId"):
                    meta_obj.sub_order_id = v
                elif k in ("sub_order_number", "subOrderNumber"):
                    meta_obj.sub_order_number = v
                elif k in ("parent_order_id", "parentOrderId"):
                    meta_obj.parent_order_id = v
                elif k in ("courier_partner", "courierPartner"):
                    meta_obj.courier_partner = v
        return NotificationInternal(
            id=r.id,
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

    async def _fetch_children(self, session, ids: List[int]):
        if not ids:
            return []
            
        params = {f"id_{i}": cid for i, cid in enumerate(ids)}
        placeholders = ", ".join(f":id_{i}" for i in range(len(ids)))
        q_data = text(f"SELECT parent_id, data_key, data_value FROM sj_notification_data WHERE parent_id IN ({placeholders})")
        res_data = await session.execute(q_data, params)
        return res_data.fetchall()

    async def _replace_children(self, session, row_id: int, data: NotificationInternalCreate):
        if data.metadata is not None:
            await session.execute(text("DELETE FROM sj_notification_data WHERE parent_id = :id"), {"id": row_id})
            m = data.metadata
            pairs = [
                ("order_id", m.order_id),
                ("order_number", m.order_number),
                ("product_id", m.product_id),
                ("url", m.url),
                ("type", m.type),
                ("status", m.status),
                ("amount", m.amount),
                ("user_id", m.user_id),
                ("created_at", m.created_at),
                ("payment_id", m.payment_id),
                ("payment_id_formatted", m.payment_id_formatted),
                ("payment_method", m.payment_method),
                ("sub_order_id", m.sub_order_id),
                ("sub_order_number", m.sub_order_number),
                ("parent_order_id", m.parent_order_id),
                ("courier_partner", m.courier_partner),
            ]
            for k, v in pairs:
                if v is not None:
                    await session.execute(
                        text("INSERT INTO sj_notification_data (parent_id, data_key, data_value) VALUES (:id, :k, :v)"),
                        {"id": row_id, "k": k, "v": str(v)},
                    )
