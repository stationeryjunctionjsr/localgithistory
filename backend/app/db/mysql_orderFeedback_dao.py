from typing import Optional, List, Union
from datetime import datetime, timezone
import secrets
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import OrderFeedbackInternal, OrderFeedbackInternalCreate, OrderFeedbackInternalUpdate

def now_utc():
    return datetime.now(timezone.utc)

class MySQLOrderFeedbackDAO:
    def __init__(self):
        self.table_name = "sj_order_feedback"
    
    @property
    def TABLE(self):
        return self.table_name

    def _factory(self):
        return get_async_session_factory()
        
    async def findById(self, id: Union[int, str]) -> Optional[OrderFeedbackInternal]:
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

    async def findByOrderId(self, order_id: str) -> Optional[OrderFeedbackInternal]:
        if not order_id:
            return None
        async with self._factory()() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE order_id = :order_id LIMIT 1")
            result = await session.execute(q, {"order_id": str(order_id)})
            row = result.fetchone()
            if not row:
                return None
            return self._map_to_schema(row)

    async def findOne(
        self,
        order_id: Optional[str] = None,
        id: Optional[Union[int, str]] = None,
        query: Optional[dict] = None,
    ) -> Optional[OrderFeedbackInternal]:
        if query:
            order_id = query.get("order_id") or query.get("orderId") or order_id
            id = query.get("id") or query.get("_id") or id
        if order_id:
            return await self.findByOrderId(order_id)
        if id:
            return await self.findById(id)
        all_feedback = await self.findAll()
        return all_feedback[0] if all_feedback else None
            
    async def findAll(
        self,
        order_id: Optional[str] = None,
        user_id: Optional[str] = None,
        feedback_type: Optional[str] = None,
        query: Optional[dict] = None,
    ) -> List[OrderFeedbackInternal]:
        if query:
            if order_id is None:
                order_id = query.get("order_id") or query.get("orderId")
            if user_id is None:
                user_id = query.get("user_id") or query.get("userId")
            if feedback_type is None:
                feedback_type = query.get("feedback_type") or query.get("feedbackType")

        async with self._factory()() as session:
            clauses = []
            params = {}

            if order_id is not None:
                clauses.append("order_id = :oid")
                params["oid"] = str(order_id)
            if user_id is not None:
                clauses.append("user_id = :uid")
                params["uid"] = str(user_id)
            if feedback_type is not None:
                clauses.append("feedback_type = :ft")
                params["ft"] = str(feedback_type)

            sql = f"SELECT * FROM {self.TABLE}"
            if clauses:
                sql += " WHERE " + " AND ".join(clauses)
            sql += " ORDER BY id DESC"
                    
            result = await session.execute(text(sql), params)
            rows = result.fetchall()
            return [self._map_to_schema(r) for r in rows]

    async def create(self, data: OrderFeedbackInternalCreate) -> OrderFeedbackInternal:
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        val_placeholders = [":eid", ":c", ":u"]
        params = {"eid": external_id, "c": now, "u": now}

        if data.order_id is not None:
            cols.append("order_id")
            val_placeholders.append(":order_id")
            params["order_id"] = data.order_id

        if data.user_id is not None:
            cols.append("user_id")
            val_placeholders.append(":user_id")
            params["user_id"] = data.user_id

        if data.rating is not None:
            cols.append("rating")
            val_placeholders.append(":rating")
            params["rating"] = data.rating

        if data.comment is not None:
            cols.append("comments")
            val_placeholders.append(":comments")
            params["comments"] = data.comment

        if data.delivery_rating is not None:
            cols.append("delivery_rating")
            val_placeholders.append(":delivery_rating")
            params["delivery_rating"] = data.delivery_rating

        if data.delivery_comment is not None:
            cols.append("delivery_comment")
            val_placeholders.append(":delivery_comment")
            params["delivery_comment"] = data.delivery_comment

        if data.feedback_type is not None:
            cols.append("feedback_type")
            val_placeholders.append(":feedback_type")
            params["feedback_type"] = data.feedback_type

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

    async def update(self, id: Union[int, str], update_data: OrderFeedbackInternalUpdate) -> Optional[OrderFeedbackInternal]:
        factory = self._factory()
        updates = ["updated_at = :u"]
        params = {"u": now_utc()}

        if update_data.rating is not None:
            updates.append("rating = :rating")
            params["rating"] = update_data.rating

        if update_data.comment is not None:
            updates.append("comments = :comments")
            params["comments"] = update_data.comment

        if update_data.delivery_rating is not None:
            updates.append("delivery_rating = :delivery_rating")
            params["delivery_rating"] = update_data.delivery_rating

        if update_data.delivery_comment is not None:
            updates.append("delivery_comment = :delivery_comment")
            params["delivery_comment"] = update_data.delivery_comment

        if update_data.feedback_type is not None:
            updates.append("feedback_type = :feedback_type")
            params["feedback_type"] = update_data.feedback_type

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
                del_where = "id = :pk"
                params = {"pk": int(id)}
            else:
                del_where = "external_id = :eid"
                params = {"eid": str(id)}

            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE {del_where}"),
                params,
            )
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(self, r) -> OrderFeedbackInternal:
        return OrderFeedbackInternal(
            id=str(r.id),
            external_id=r.external_id,
            order_id=r.order_id,
            user_id=r.user_id,
            rating=int(r.rating) if r.rating is not None else None,
            comment=r.comments,
            delivery_rating=int(r.delivery_rating) if r.delivery_rating is not None else None,
            delivery_comment=r.delivery_comment,
            feedback_type=r.feedback_type,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
