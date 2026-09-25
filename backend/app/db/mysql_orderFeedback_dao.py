from typing import Optional, Dict, List, Any
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
            
            query_map = {'order_id': 'order_id', 'user_id': 'user_id', 'rating': 'rating', 'comment': 'comments', 'delivery_rating': 'delivery_rating', 'delivery_comment': 'delivery_comment', 'feedback_type': 'feedback_type'}
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
            
            query_map = {'order_id': 'order_id', 'user_id': 'user_id', 'rating': 'rating', 'comment': 'comments', 'delivery_rating': 'delivery_rating', 'delivery_comment': 'delivery_comment', 'feedback_type': 'feedback_type'}
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

    async def update(self, id: str, data: Any) -> Any:
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
        obj = OrderFeedbackInternal.model_validate(r)
        if getattr(r, "comments", None):
            obj.comment = getattr(r, "comments", None)
        for k, v in children.items():
            setattr(obj, k, v)
        return obj

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:
        return {}
        
    async def _replace_children(self, session, row_id: int, data: Any):
        pass

