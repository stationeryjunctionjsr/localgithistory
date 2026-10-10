from typing import Optional, Dict, List, Any, Union
from datetime import datetime, timezone
import secrets
import json
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import OrderFeedbackInternal
from app.models.daos_flat import OrderFeedbackInternalCreate, OrderFeedbackInternalUpdate

def now_utc():
    return datetime.now(timezone.utc)

class MySQLOrderFeedbackDAO:
    def __init__(self):
        self.table_name = "sj_order_feedback"
    
    @property
    def TABLE(self):
        from app.config.settings import settings
        return self.table_name

    def _factory(self):
        return get_async_session_factory()
        
    async def findById(self, id: Union[int, str]) -> Optional['OrderFeedbackInternal']:
        factory = self._factory()
        if not factory or not id:
            return None
        async with factory() as session:
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

    async def findByOrderId(self, order_id: str) -> Optional['OrderFeedbackInternal']:
        factory = self._factory()
        if not factory or not order_id:
            return None
        async with factory() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE order_id = :oid LIMIT 1")
            result = await session.execute(q, {"oid": str(order_id)})
            row = result.fetchone()
            if not row:
                return None
            return self._map_to_schema(row)

    async def findOne(
        self,
        query: Optional[dict] = None,
        order_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional['OrderFeedbackInternal']:
        if order_id:
            return await self.findByOrderId(order_id)
        if query:
            oid = query.get("orderId") or query.get("order_id")
            if oid:
                return await self.findByOrderId(oid)
            if "_id" in query or "id" in query:
                return await self.findById(query.get("_id") or query.get("id"))
            if "externalId" in query and query["externalId"]:
                return await self.findById(query["externalId"])
        results = await self.findAll(query=query, order_id=order_id, user_id=user_id)
        return results[0] if results else None

    async def findAll(
        self,
        query: Optional[dict] = None,
        order_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List['OrderFeedbackInternal']:
        if query:
            if order_id is None:
                order_id = query.get("orderId") or query.get("order_id")
            if user_id is None:
                user_id = query.get("userId") or query.get("user_id")

        clauses = []
        params = {}
        if order_id is not None:
            clauses.append("order_id = :oid")
            params["oid"] = str(order_id)
        if user_id is not None:
            clauses.append("user_id = :uid")
            params["uid"] = str(user_id)

        where_sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT * FROM {self.TABLE}{where_sql} ORDER BY id ASC"

        factory = self._factory()
        if not factory:
            return []
        async with factory() as session:
            result = await session.execute(text(sql), params)
            rows = result.fetchall()
            return [self._map_to_schema(r) for r in rows]

    async def create(self, data: 'OrderFeedbackInternalCreate') -> 'OrderFeedbackInternal':
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        params = {"eid": external_id, "c": now, "u": now}

        if data.order_id is not None:
            cols.append("order_id")
            params["s_order_id"] = data.order_id

        if data.user_id is not None:
            cols.append("user_id")
            params["s_user_id"] = data.user_id

        if data.rating is not None:
            cols.append("rating")
            params["s_rating"] = data.rating

        if data.comment is not None:
            cols.append("comments")
            params["s_comment"] = data.comment

        if data.delivery_rating is not None:
            cols.append("delivery_rating")
            params["s_delivery_rating"] = data.delivery_rating

        if data.delivery_comment is not None:
            cols.append("delivery_comment")
            params["s_delivery_comment"] = data.delivery_comment

        if data.feedback_type is not None:
            cols.append("feedback_type")
            params["s_feedback_type"] = data.feedback_type

        col_sql = ", ".join(cols)
        val_sql = ", ".join([":eid", ":c", ":u"] + [f":s_{k}" for k in ['order_id', 'user_id', 'rating', 'comment', 'delivery_rating', 'delivery_comment', 'feedback_type'] if f"s_{k}" in params] + [f":c_{k}" for k in [] if f"c_{k}" in params])
        
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

    async def update(self, id: str, update_data: 'OrderFeedbackInternalUpdate') -> 'OrderFeedbackInternal':
        factory = self._factory()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now_utc()}

        if data.order_id is not None:
            updates.append("order_id = :s_orderId")
            params["s_order_id"] = data.order_id

        if data.user_id is not None:
            updates.append("user_id = :s_userId")
            params["s_user_id"] = data.user_id

        if data.rating is not None:
            updates.append("rating = :s_rating")
            params["s_rating"] = data.rating

        if data.comment is not None:
            updates.append("comments = :s_comment")
            params["s_comment"] = data.comment

        if data.delivery_rating is not None:
            updates.append("delivery_rating = :s_deliveryRating")
            params["s_delivery_rating"] = data.delivery_rating

        if data.delivery_comment is not None:
            updates.append("delivery_comment = :s_deliveryComment")
            params["s_delivery_comment"] = data.delivery_comment

        if data.feedback_type is not None:
            updates.append("feedback_type = :s_feedbackType")
            params["s_feedback_type"] = data.feedback_type

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

    async def delete(self, id: Union[int, str]) -> bool:
        factory = self._factory()
        if not factory or not id:
            return False
        async with factory() as session:
            if str(id).isdigit():
                pk = int(id)
            else:
                res = await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": str(id)}
                )
                pk = res.scalar()
                if not pk:
                    return False

            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pk},
            )
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(self, r, children: Dict = None) -> 'OrderFeedbackInternal':
        from app.models.daos_flat import OrderFeedbackInternal
        return OrderFeedbackInternal(
            id=str(r.id),
            external_id=r.external_id,
            order_id=r.order_id,
            user_id=r.user_id,
            rating=int(r.rating) if r.rating is not None else None,
            comment=getattr(r, "comments", None) or getattr(r, "comment", None),
            delivery_rating=int(r.delivery_rating) if getattr(r, "delivery_rating", None) is not None else None,
            delivery_comment=getattr(r, "delivery_comment", None),
            feedback_type=getattr(r, "feedback_type", None),
            created_at=r.created_at,
            updated_at=r.updated_at,
        )

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:
        return {}
        
    async def _replace_children(self, session, row_id: int, data: 'CamelBaseModel'):
        pass

