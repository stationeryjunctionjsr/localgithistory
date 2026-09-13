from app.models.daos_flat import *
from typing import Any
"""
Strict SQLAlchemy DAOs replacing MySQLTypedDocDAO and DocStore patterns.
"""

import secrets
from typing import Dict, List, Optional
from app.models.schemas import PromoStripResponse, OrderFeedbackResponse, ProductReviewResponse, ClassificationTagResponse
from app.models.availability_requests import AvailabilityRequestResponse


from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc


class MySQLReturnSettingsDAO:
    TABLE = "sj_return_settings"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_dict(self, row) -> Dict:
        return {
            "_id": str(row.id),
            "id": row.id,
            "external_id": row.external_id,
            "returnDays": row.return_days,

            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        }

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        query = query or {}
        where_clauses = []
        params = {}
        if "returnDays" in query:
            where_clauses.append("return_days = :returnDays")
            params["returnDays"] = query["returnDays"]

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        factory = self._factory()
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"),
                    params,
                )
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    async def findOne(self, query: Dict) -> Optional[Dict]:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        return self._row_to_dict(row) if row else None

    async def create(self, data: ReturnSettingsInternalCreate) -> Dict:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if ((hasattr(data, "returnDays") and (getattr(data, "returnDays") if hasattr(data, "returnDays") else (data.get("returnDays") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("returnDays") is not None)):
            cols.append("return_days")
            vals.append(":returnDays")
            params["returnDays"] = (getattr(data, "returnDays") if hasattr(data, "returnDays") else (data.get("returnDays") if isinstance(data, dict) else None))

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        async with factory() as session:
            await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = (await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": ext_id})).scalar()
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, data: ReturnSettingsInternalUpdate) -> Optional[Any]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = ReturnSettingsInternalUpdate(**{**(existing.model_dump(by_alias=True) if hasattr(existing, "model_dump") else existing), **(data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data)})
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if ((hasattr(merged, "returnDays") and (getattr(merged, "returnDays") if hasattr(merged, "returnDays") else (merged.get("returnDays") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("returnDays") is not None)):
            updates.append("return_days = :returnDays")
            params["returnDays"] = (getattr(merged, "returnDays") if hasattr(merged, "returnDays") else (merged.get("returnDays") if isinstance(merged, dict) else None))

        set_sql = ", ".join(updates)
        factory = self._factory()
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pid},
            )
            await session.commit()
            return res.rowcount > 0

class MySQLOrderFeedbackDAO:
    TABLE = "sj_order_feedback"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_dict(self, row) -> OrderFeedbackResponse:
        return OrderFeedbackResponse(**{
            "_id": str(row.id),
            "id": row.id,
            "external_id": row.external_id,
            "orderId": row.order_id,
            "userId": row.user_id,
            "rating": row.rating,
            "comment": row.comments,
            "deliveryRating": row.delivery_rating,
            "deliveryComment": row.delivery_comment,
            "feedbackType": row.feedback_type,

            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        })

    async def findAll(self, query: Optional[Dict] = None) -> List[OrderFeedbackResponse]:
        query = query or {}
        where_clauses = []
        params = {}
        if "orderId" in query:
            where_clauses.append("order_id = :orderId")
            params["orderId"] = query["orderId"]
        if "userId" in query:
            where_clauses.append("user_id = :userId")
            params["userId"] = query["userId"]
        if "rating" in query:
            where_clauses.append("rating = :rating")
            params["rating"] = query["rating"]
        if "comment" in query:
            where_clauses.append("comments = :comment")
            params["comment"] = query["comment"]
        if "deliveryRating" in query:
            where_clauses.append("delivery_rating = :deliveryRating")
            params["deliveryRating"] = query["deliveryRating"]
        if "deliveryComment" in query:
            where_clauses.append("delivery_comment = :deliveryComment")
            params["deliveryComment"] = query["deliveryComment"]
        if "feedbackType" in query:
            where_clauses.append("feedback_type = :feedbackType")
            params["feedbackType"] = query["feedbackType"]

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        factory = self._factory()
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"),
                    params,
                )
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    async def findOne(self, query: Dict) -> Optional[OrderFeedbackResponse]:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[OrderFeedbackResponse]:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        return self._row_to_dict(row) if row else None

    async def create(self, data: OrderFeedbackInternalCreate) -> OrderFeedbackResponse:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if ((hasattr(data, "orderId") and (getattr(data, "orderId") if hasattr(data, "orderId") else (data.get("orderId") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("orderId") is not None)):
            cols.append("order_id")
            vals.append(":orderId")
            params["orderId"] = (getattr(data, "orderId") if hasattr(data, "orderId") else (data.get("orderId") if isinstance(data, dict) else None))
        if ((hasattr(data, "userId") and (getattr(data, "userId") if hasattr(data, "userId") else (data.get("userId") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("userId") is not None)):
            cols.append("user_id")
            vals.append(":userId")
            params["userId"] = (getattr(data, "userId") if hasattr(data, "userId") else (data.get("userId") if isinstance(data, dict) else None))
        if ((hasattr(data, "rating") and (getattr(data, "rating") if hasattr(data, "rating") else (data.get("rating") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("rating") is not None)):
            cols.append("rating")
            vals.append(":rating")
            params["rating"] = (getattr(data, "rating") if hasattr(data, "rating") else (data.get("rating") if isinstance(data, dict) else None))
        if ((hasattr(data, "comment") and (getattr(data, "comment") if hasattr(data, "comment") else (data.get("comment") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("comment") is not None)):
            cols.append("comments")
            vals.append(":comment")
            params["comment"] = (getattr(data, "comment") if hasattr(data, "comment") else (data.get("comment") if isinstance(data, dict) else None))
        if ((hasattr(data, "deliveryRating") and (getattr(data, "deliveryRating") if hasattr(data, "deliveryRating") else (data.get("deliveryRating") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("deliveryRating") is not None)):
            cols.append("delivery_rating")
            vals.append(":deliveryRating")
            params["deliveryRating"] = (getattr(data, "deliveryRating") if hasattr(data, "deliveryRating") else (data.get("deliveryRating") if isinstance(data, dict) else None))
        if ((hasattr(data, "deliveryComment") and (getattr(data, "deliveryComment") if hasattr(data, "deliveryComment") else (data.get("deliveryComment") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("deliveryComment") is not None)):
            cols.append("delivery_comment")
            vals.append(":deliveryComment")
            params["deliveryComment"] = (getattr(data, "deliveryComment") if hasattr(data, "deliveryComment") else (data.get("deliveryComment") if isinstance(data, dict) else None))
        if ((hasattr(data, "feedbackType") and (getattr(data, "feedbackType") if hasattr(data, "feedbackType") else (data.get("feedbackType") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("feedbackType") is not None)):
            cols.append("feedback_type")
            vals.append(":feedbackType")
            params["feedbackType"] = (getattr(data, "feedbackType") if hasattr(data, "feedbackType") else (data.get("feedbackType") if isinstance(data, dict) else None))

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        async with factory() as session:
            await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = (await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": ext_id})).scalar()
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, data: OrderFeedbackInternalUpdate) -> Optional[Any]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = OrderFeedbackInternalUpdate(**{**(existing.model_dump(by_alias=True) if hasattr(existing, "model_dump") else existing), **(data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data)})
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if ((hasattr(merged, "orderId") and (getattr(merged, "orderId") if hasattr(merged, "orderId") else (merged.get("orderId") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("orderId") is not None)):
            updates.append("order_id = :orderId")
            params["orderId"] = (getattr(merged, "orderId") if hasattr(merged, "orderId") else (merged.get("orderId") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "userId") and (getattr(merged, "userId") if hasattr(merged, "userId") else (merged.get("userId") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("userId") is not None)):
            updates.append("user_id = :userId")
            params["userId"] = (getattr(merged, "userId") if hasattr(merged, "userId") else (merged.get("userId") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "rating") and (getattr(merged, "rating") if hasattr(merged, "rating") else (merged.get("rating") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("rating") is not None)):
            updates.append("rating = :rating")
            params["rating"] = (getattr(merged, "rating") if hasattr(merged, "rating") else (merged.get("rating") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "comment") and (getattr(merged, "comment") if hasattr(merged, "comment") else (merged.get("comment") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("comment") is not None)):
            updates.append("comments = :comment")
            params["comment"] = (getattr(merged, "comment") if hasattr(merged, "comment") else (merged.get("comment") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "deliveryRating") and (getattr(merged, "deliveryRating") if hasattr(merged, "deliveryRating") else (merged.get("deliveryRating") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("deliveryRating") is not None)):
            updates.append("delivery_rating = :deliveryRating")
            params["deliveryRating"] = (getattr(merged, "deliveryRating") if hasattr(merged, "deliveryRating") else (merged.get("deliveryRating") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "deliveryComment") and (getattr(merged, "deliveryComment") if hasattr(merged, "deliveryComment") else (merged.get("deliveryComment") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("deliveryComment") is not None)):
            updates.append("delivery_comment = :deliveryComment")
            params["deliveryComment"] = (getattr(merged, "deliveryComment") if hasattr(merged, "deliveryComment") else (merged.get("deliveryComment") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "feedbackType") and (getattr(merged, "feedbackType") if hasattr(merged, "feedbackType") else (merged.get("feedbackType") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("feedbackType") is not None)):
            updates.append("feedback_type = :feedbackType")
            params["feedbackType"] = (getattr(merged, "feedbackType") if hasattr(merged, "feedbackType") else (merged.get("feedbackType") if isinstance(merged, dict) else None))

        set_sql = ", ".join(updates)
        factory = self._factory()
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pid},
            )
            await session.commit()
            return res.rowcount > 0

class MySQLPromoStripsDAO:
    TABLE = "sj_promo_strips"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_dict(self, row) -> PromoStripResponse:
        return PromoStripResponse(**{
            "_id": str(row.id),
            "text": row.text,
            "isActive": bool(row.is_active) if getattr(row, "is_active", None) is not None else False,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        })

    async def findAll(self, query: Optional[Dict] = None) -> List[PromoStripResponse]:
        query = query or {}
        where_clauses = []
        params = {}
        if "text" in query:
            where_clauses.append("text = :text")
            params["text"] = query["text"]
        if "isActive" in query:
            where_clauses.append("is_active = :isActive")
            params["isActive"] = 1 if query["isActive"] else None

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        factory = self._factory()
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"),
                    params,
                )
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    async def findOne(self, query: Dict) -> Optional[PromoStripResponse]:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[PromoStripResponse]:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        return self._row_to_dict(row) if row else None

    async def create(self, data: PromoStripsInternalCreate) -> PromoStripResponse:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if ((hasattr(data, "text") and (getattr(data, "text") if hasattr(data, "text") else (data.get("text") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("text") is not None)):
            cols.append("text")
            vals.append(":text")
            params["text"] = (getattr(data, "text") if hasattr(data, "text") else (data.get("text") if isinstance(data, dict) else None))
        if ((hasattr(data, "isActive") and (getattr(data, "isActive") if hasattr(data, "isActive") else (data.get("isActive") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("isActive") is not None)):
            cols.append("is_active")
            vals.append(":isActive")
            params["isActive"] = 1 if (getattr(data, "isActive") if hasattr(data, "isActive") else (data.get("isActive") if isinstance(data, dict) else None)) else 0

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        async with factory() as session:
            await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = (await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": ext_id})).scalar()
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, data: PromoStripsInternalUpdate) -> Optional[Any]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = PromoStripsInternalUpdate(**{**(existing.model_dump(by_alias=True) if hasattr(existing, "model_dump") else existing), **(data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data)})
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if ((hasattr(merged, "text") and (getattr(merged, "text") if hasattr(merged, "text") else (merged.get("text") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("text") is not None)):
            updates.append("text = :text")
            params["text"] = (getattr(merged, "text") if hasattr(merged, "text") else (merged.get("text") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "isActive") and (getattr(merged, "isActive") if hasattr(merged, "isActive") else (merged.get("isActive") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("isActive") is not None)):
            updates.append("is_active = :isActive")
            params["isActive"] = 1 if (getattr(merged, "isActive") if hasattr(merged, "isActive") else (merged.get("isActive") if isinstance(merged, dict) else None)) else None

        set_sql = ", ".join(updates)
        factory = self._factory()
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pid},
            )
            await session.commit()
            return res.rowcount > 0

class MySQLPushNotificationsDAO:
    TABLE = "sj_push_notifications"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_dict(self, row) -> Dict:
        return {
            "_id": str(row.id),
            "id": row.id,
            "external_id": row.external_id,
            "title": row.title,
            "message": row.message,
            "link": row.link,
            "image": row.image,
            "status": row.status,
            "scheduledFor": row.scheduled_for,
            "deliveredCount": row.delivered_count,
            "readCount": row.read_count,
            "userSegment": row.user_segment,
            "userBehavior": row.user_behavior,
            "createdBy": row.created_by,

            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        }

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        query = query or {}
        where_clauses = []
        params = {}
        if "title" in query:
            where_clauses.append("title = :title")
            params["title"] = query["title"]
        if "message" in query:
            where_clauses.append("message = :message")
            params["message"] = query["message"]
        if "link" in query:
            where_clauses.append("link = :link")
            params["link"] = query["link"]
        if "image" in query:
            where_clauses.append("image = :image")
            params["image"] = query["image"]
        if "status" in query:
            where_clauses.append("status = :status")
            params["status"] = query["status"]
        if "scheduledFor" in query:
            where_clauses.append("scheduled_for = :scheduledFor")
            params["scheduledFor"] = query["scheduledFor"]
        if "deliveredCount" in query:
            where_clauses.append("delivered_count = :deliveredCount")
            params["deliveredCount"] = query["deliveredCount"]
        if "readCount" in query:
            where_clauses.append("read_count = :readCount")
            params["readCount"] = query["readCount"]
        if "userSegment" in query:
            where_clauses.append("user_segment = :userSegment")
            params["userSegment"] = query["userSegment"]
        if "userBehavior" in query:
            where_clauses.append("user_behavior = :userBehavior")
            params["userBehavior"] = query["userBehavior"]
        if "createdBy" in query:
            where_clauses.append("created_by = :createdBy")
            params["createdBy"] = query["createdBy"]

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        factory = self._factory()
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"),
                    params,
                )
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    async def findOne(self, query: Dict) -> Optional[Dict]:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        return self._row_to_dict(row) if row else None

    async def create(self, data: PushNotificationsInternalCreate) -> Dict:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if ((hasattr(data, "title") and (getattr(data, "title") if hasattr(data, "title") else (data.get("title") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("title") is not None)):
            cols.append("title")
            vals.append(":title")
            params["title"] = (getattr(data, "title") if hasattr(data, "title") else (data.get("title") if isinstance(data, dict) else None))
        if ((hasattr(data, "message") and (getattr(data, "message") if hasattr(data, "message") else (data.get("message") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("message") is not None)):
            cols.append("message")
            vals.append(":message")
            params["message"] = (getattr(data, "message") if hasattr(data, "message") else (data.get("message") if isinstance(data, dict) else None))
        if ((hasattr(data, "link") and (getattr(data, "link") if hasattr(data, "link") else (data.get("link") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("link") is not None)):
            cols.append("link")
            vals.append(":link")
            params["link"] = (getattr(data, "link") if hasattr(data, "link") else (data.get("link") if isinstance(data, dict) else None))
        if ((hasattr(data, "image") and (getattr(data, "image") if hasattr(data, "image") else (data.get("image") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("image") is not None)):
            cols.append("image")
            vals.append(":image")
            params["image"] = (getattr(data, "image") if hasattr(data, "image") else (data.get("image") if isinstance(data, dict) else None))
        if ((hasattr(data, "status") and (getattr(data, "status") if hasattr(data, "status") else (data.get("status") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("status") is not None)):
            cols.append("status")
            vals.append(":status")
            params["status"] = (getattr(data, "status") if hasattr(data, "status") else (data.get("status") if isinstance(data, dict) else None))
        if ((hasattr(data, "scheduledFor") and (getattr(data, "scheduledFor") if hasattr(data, "scheduledFor") else (data.get("scheduledFor") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("scheduledFor") is not None)):
            cols.append("scheduled_for")
            vals.append(":scheduledFor")
            params["scheduledFor"] = (getattr(data, "scheduledFor") if hasattr(data, "scheduledFor") else (data.get("scheduledFor") if isinstance(data, dict) else None))
        if ((hasattr(data, "deliveredCount") and (getattr(data, "deliveredCount") if hasattr(data, "deliveredCount") else (data.get("deliveredCount") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("deliveredCount") is not None)):
            cols.append("delivered_count")
            vals.append(":deliveredCount")
            params["deliveredCount"] = (getattr(data, "deliveredCount") if hasattr(data, "deliveredCount") else (data.get("deliveredCount") if isinstance(data, dict) else None))
        if ((hasattr(data, "readCount") and (getattr(data, "readCount") if hasattr(data, "readCount") else (data.get("readCount") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("readCount") is not None)):
            cols.append("read_count")
            vals.append(":readCount")
            params["readCount"] = (getattr(data, "readCount") if hasattr(data, "readCount") else (data.get("readCount") if isinstance(data, dict) else None))
        if ((hasattr(data, "userSegment") and (getattr(data, "userSegment") if hasattr(data, "userSegment") else (data.get("userSegment") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("userSegment") is not None)):
            cols.append("user_segment")
            vals.append(":userSegment")
            params["userSegment"] = (getattr(data, "userSegment") if hasattr(data, "userSegment") else (data.get("userSegment") if isinstance(data, dict) else None))
        if ((hasattr(data, "userBehavior") and (getattr(data, "userBehavior") if hasattr(data, "userBehavior") else (data.get("userBehavior") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("userBehavior") is not None)):
            cols.append("user_behavior")
            vals.append(":userBehavior")
            params["userBehavior"] = (getattr(data, "userBehavior") if hasattr(data, "userBehavior") else (data.get("userBehavior") if isinstance(data, dict) else None))
        if ((hasattr(data, "createdBy") and (getattr(data, "createdBy") if hasattr(data, "createdBy") else (data.get("createdBy") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("createdBy") is not None)):
            cols.append("created_by")
            vals.append(":createdBy")
            params["createdBy"] = (getattr(data, "createdBy") if hasattr(data, "createdBy") else (data.get("createdBy") if isinstance(data, dict) else None))

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        async with factory() as session:
            await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = (await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": ext_id})).scalar()
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, data: PushNotificationsInternalUpdate) -> Optional[Any]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = PushNotificationsInternalUpdate(**{**(existing.model_dump(by_alias=True) if hasattr(existing, "model_dump") else existing), **(data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data)})
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if ((hasattr(merged, "title") and (getattr(merged, "title") if hasattr(merged, "title") else (merged.get("title") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("title") is not None)):
            updates.append("title = :title")
            params["title"] = (getattr(merged, "title") if hasattr(merged, "title") else (merged.get("title") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "message") and (getattr(merged, "message") if hasattr(merged, "message") else (merged.get("message") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("message") is not None)):
            updates.append("message = :message")
            params["message"] = (getattr(merged, "message") if hasattr(merged, "message") else (merged.get("message") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "link") and (getattr(merged, "link") if hasattr(merged, "link") else (merged.get("link") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("link") is not None)):
            updates.append("link = :link")
            params["link"] = (getattr(merged, "link") if hasattr(merged, "link") else (merged.get("link") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "image") and (getattr(merged, "image") if hasattr(merged, "image") else (merged.get("image") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("image") is not None)):
            updates.append("image = :image")
            params["image"] = (getattr(merged, "image") if hasattr(merged, "image") else (merged.get("image") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "status") and (getattr(merged, "status") if hasattr(merged, "status") else (merged.get("status") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("status") is not None)):
            updates.append("status = :status")
            params["status"] = (getattr(merged, "status") if hasattr(merged, "status") else (merged.get("status") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "scheduledFor") and (getattr(merged, "scheduledFor") if hasattr(merged, "scheduledFor") else (merged.get("scheduledFor") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("scheduledFor") is not None)):
            updates.append("scheduled_for = :scheduledFor")
            params["scheduledFor"] = (getattr(merged, "scheduledFor") if hasattr(merged, "scheduledFor") else (merged.get("scheduledFor") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "deliveredCount") and (getattr(merged, "deliveredCount") if hasattr(merged, "deliveredCount") else (merged.get("deliveredCount") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("deliveredCount") is not None)):
            updates.append("delivered_count = :deliveredCount")
            params["deliveredCount"] = (getattr(merged, "deliveredCount") if hasattr(merged, "deliveredCount") else (merged.get("deliveredCount") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "readCount") and (getattr(merged, "readCount") if hasattr(merged, "readCount") else (merged.get("readCount") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("readCount") is not None)):
            updates.append("read_count = :readCount")
            params["readCount"] = (getattr(merged, "readCount") if hasattr(merged, "readCount") else (merged.get("readCount") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "userSegment") and (getattr(merged, "userSegment") if hasattr(merged, "userSegment") else (merged.get("userSegment") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("userSegment") is not None)):
            updates.append("user_segment = :userSegment")
            params["userSegment"] = (getattr(merged, "userSegment") if hasattr(merged, "userSegment") else (merged.get("userSegment") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "userBehavior") and (getattr(merged, "userBehavior") if hasattr(merged, "userBehavior") else (merged.get("userBehavior") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("userBehavior") is not None)):
            updates.append("user_behavior = :userBehavior")
            params["userBehavior"] = (getattr(merged, "userBehavior") if hasattr(merged, "userBehavior") else (merged.get("userBehavior") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "createdBy") and (getattr(merged, "createdBy") if hasattr(merged, "createdBy") else (merged.get("createdBy") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("createdBy") is not None)):
            updates.append("created_by = :createdBy")
            params["createdBy"] = (getattr(merged, "createdBy") if hasattr(merged, "createdBy") else (merged.get("createdBy") if isinstance(merged, dict) else None))

        set_sql = ", ".join(updates)
        factory = self._factory()
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pid},
            )
            await session.commit()
            return res.rowcount > 0

class MySQLCoachMarksDAO:
    TABLE = "sj_coach_marks"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_dict(self, row) -> Dict:
        return {
            "_id": str(row.id),
            "id": row.id,
            "external_id": row.external_id,
            "anchorId": row.anchor_id,
            "title": row.title,
            "description": row.description,
            "screenName": row.screen_name,
            "sequenceOrder": row.sequence_order,
            "isActive": bool(row.is_active) if getattr(row, "is_active", None) is not None else False,

            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        }

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        query = query or {}
        where_clauses = []
        params = {}
        if "anchorId" in query:
            where_clauses.append("anchor_id = :anchorId")
            params["anchorId"] = query["anchorId"]
        if "title" in query:
            where_clauses.append("title = :title")
            params["title"] = query["title"]
        if "description" in query:
            where_clauses.append("description = :description")
            params["description"] = query["description"]
        if "screenName" in query:
            where_clauses.append("screen_name = :screenName")
            params["screenName"] = query["screenName"]
        if "sequenceOrder" in query:
            where_clauses.append("sequence_order = :sequenceOrder")
            params["sequenceOrder"] = query["sequenceOrder"]
        if "isActive" in query:
            where_clauses.append("is_active = :isActive")
            params["isActive"] = 1 if query["isActive"] else None

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        factory = self._factory()
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"),
                    params,
                )
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    async def findOne(self, query: Dict) -> Optional[Dict]:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        return self._row_to_dict(row) if row else None

    async def create(self, data: CoachMarksInternalCreate) -> Dict:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if ((hasattr(data, "anchorId") and (getattr(data, "anchorId") if hasattr(data, "anchorId") else (data.get("anchorId") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("anchorId") is not None)):
            cols.append("anchor_id")
            vals.append(":anchorId")
            params["anchorId"] = (getattr(data, "anchorId") if hasattr(data, "anchorId") else (data.get("anchorId") if isinstance(data, dict) else None))
        if ((hasattr(data, "title") and (getattr(data, "title") if hasattr(data, "title") else (data.get("title") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("title") is not None)):
            cols.append("title")
            vals.append(":title")
            params["title"] = (getattr(data, "title") if hasattr(data, "title") else (data.get("title") if isinstance(data, dict) else None))
        if ((hasattr(data, "description") and (getattr(data, "description") if hasattr(data, "description") else (data.get("description") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("description") is not None)):
            cols.append("description")
            vals.append(":description")
            params["description"] = (getattr(data, "description") if hasattr(data, "description") else (data.get("description") if isinstance(data, dict) else None))
        if ((hasattr(data, "screenName") and (getattr(data, "screenName") if hasattr(data, "screenName") else (data.get("screenName") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("screenName") is not None)):
            cols.append("screen_name")
            vals.append(":screenName")
            params["screenName"] = (getattr(data, "screenName") if hasattr(data, "screenName") else (data.get("screenName") if isinstance(data, dict) else None))
        if ((hasattr(data, "sequenceOrder") and (getattr(data, "sequenceOrder") if hasattr(data, "sequenceOrder") else (data.get("sequenceOrder") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("sequenceOrder") is not None)):
            cols.append("sequence_order")
            vals.append(":sequenceOrder")
            params["sequenceOrder"] = (getattr(data, "sequenceOrder") if hasattr(data, "sequenceOrder") else (data.get("sequenceOrder") if isinstance(data, dict) else None))
        if ((hasattr(data, "isActive") and (getattr(data, "isActive") if hasattr(data, "isActive") else (data.get("isActive") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("isActive") is not None)):
            cols.append("is_active")
            vals.append(":isActive")
            params["isActive"] = 1 if (getattr(data, "isActive") if hasattr(data, "isActive") else (data.get("isActive") if isinstance(data, dict) else None)) else 0

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        async with factory() as session:
            await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = (await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": ext_id})).scalar()
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, data: CoachMarksInternalUpdate) -> Optional[Any]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = CoachMarksInternalUpdate(**{**(existing.model_dump(by_alias=True) if hasattr(existing, "model_dump") else existing), **(data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data)})
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if ((hasattr(merged, "anchorId") and (getattr(merged, "anchorId") if hasattr(merged, "anchorId") else (merged.get("anchorId") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("anchorId") is not None)):
            updates.append("anchor_id = :anchorId")
            params["anchorId"] = (getattr(merged, "anchorId") if hasattr(merged, "anchorId") else (merged.get("anchorId") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "title") and (getattr(merged, "title") if hasattr(merged, "title") else (merged.get("title") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("title") is not None)):
            updates.append("title = :title")
            params["title"] = (getattr(merged, "title") if hasattr(merged, "title") else (merged.get("title") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "description") and (getattr(merged, "description") if hasattr(merged, "description") else (merged.get("description") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("description") is not None)):
            updates.append("description = :description")
            params["description"] = (getattr(merged, "description") if hasattr(merged, "description") else (merged.get("description") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "screenName") and (getattr(merged, "screenName") if hasattr(merged, "screenName") else (merged.get("screenName") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("screenName") is not None)):
            updates.append("screen_name = :screenName")
            params["screenName"] = (getattr(merged, "screenName") if hasattr(merged, "screenName") else (merged.get("screenName") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "sequenceOrder") and (getattr(merged, "sequenceOrder") if hasattr(merged, "sequenceOrder") else (merged.get("sequenceOrder") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("sequenceOrder") is not None)):
            updates.append("sequence_order = :sequenceOrder")
            params["sequenceOrder"] = (getattr(merged, "sequenceOrder") if hasattr(merged, "sequenceOrder") else (merged.get("sequenceOrder") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "isActive") and (getattr(merged, "isActive") if hasattr(merged, "isActive") else (merged.get("isActive") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("isActive") is not None)):
            updates.append("is_active = :isActive")
            params["isActive"] = 1 if (getattr(merged, "isActive") if hasattr(merged, "isActive") else (merged.get("isActive") if isinstance(merged, dict) else None)) else None

        set_sql = ", ".join(updates)
        factory = self._factory()
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pid},
            )
            await session.commit()
            return res.rowcount > 0

class MySQLCategoryTagsDAO:
    TABLE = "sj_category_tags"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_dict(self, row) -> Any:
        return CategoryTagResponse(**{
            "_id": str(row.id),
            "id": row.id,
            "external_id": row.external_id,
            "name": row.name,
            "description": row.description,
            "isActive": bool(row.is_active) if getattr(row, "is_active", None) is not None else False,

            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        })

    async def findAll(self, query: Optional[Dict] = None) -> List[CategoryTagResponse]:
        query = query or {}
        where_clauses = []
        params = {}
        if "name" in query:
            where_clauses.append("name = :name")
            params["name"] = query["name"]
        if "description" in query:
            where_clauses.append("description = :description")
            params["description"] = query["description"]
        if "isActive" in query:
            where_clauses.append("is_active = :isActive")
            params["isActive"] = 1 if query["isActive"] else None

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        factory = self._factory()
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"),
                    params,
                )
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    async def findOne(self, query: Dict) -> Optional[CategoryTagResponse]:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[CategoryTagResponse]:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        return self._row_to_dict(row) if row else None

    async def create(self, data: CategoryTagsInternalCreate) -> Any:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if ((hasattr(data, "name") and (getattr(data, "name") if hasattr(data, "name") else (data.get("name") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("name") is not None)):
            cols.append("name")
            vals.append(":name")
            params["name"] = (getattr(data, "name") if hasattr(data, "name") else (data.get("name") if isinstance(data, dict) else None))
        if ((hasattr(data, "description") and (getattr(data, "description") if hasattr(data, "description") else (data.get("description") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("description") is not None)):
            cols.append("description")
            vals.append(":description")
            params["description"] = (getattr(data, "description") if hasattr(data, "description") else (data.get("description") if isinstance(data, dict) else None))
        if ((hasattr(data, "isActive") and (getattr(data, "isActive") if hasattr(data, "isActive") else (data.get("isActive") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("isActive") is not None)):
            cols.append("is_active")
            vals.append(":isActive")
            params["isActive"] = 1 if (getattr(data, "isActive") if hasattr(data, "isActive") else (data.get("isActive") if isinstance(data, dict) else None)) else 0

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        async with factory() as session:
            await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = (await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": ext_id})).scalar()
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, data: CategoryTagsInternalUpdate) -> Optional[Any]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = CategoryTagsInternalUpdate(**{**(existing.model_dump(by_alias=True) if hasattr(existing, "model_dump") else existing), **(data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data)})
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if ((hasattr(merged, "name") and (getattr(merged, "name") if hasattr(merged, "name") else (merged.get("name") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("name") is not None)):
            updates.append("name = :name")
            params["name"] = (getattr(merged, "name") if hasattr(merged, "name") else (merged.get("name") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "description") and (getattr(merged, "description") if hasattr(merged, "description") else (merged.get("description") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("description") is not None)):
            updates.append("description = :description")
            params["description"] = (getattr(merged, "description") if hasattr(merged, "description") else (merged.get("description") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "isActive") and (getattr(merged, "isActive") if hasattr(merged, "isActive") else (merged.get("isActive") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("isActive") is not None)):
            updates.append("is_active = :isActive")
            params["isActive"] = 1 if (getattr(merged, "isActive") if hasattr(merged, "isActive") else (merged.get("isActive") if isinstance(merged, dict) else None)) else None

        set_sql = ", ".join(updates)
        factory = self._factory()
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pid},
            )
            await session.commit()
            return res.rowcount > 0

class MySQLGoogle_reviewsDAO:
    TABLE = "sj_google_reviews"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_dict(self, row) -> Dict:
        return {
            "_id": str(row.id),
            "id": row.id,
            "external_id": row.external_id,
            "rating": row.rating,
            "reviewCount": row.review_count,
            "lastUpdated": row.last_updated,
            "method": row.method,

            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        }

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        query = query or {}
        where_clauses = []
        params = {}
        if "rating" in query:
            where_clauses.append("rating = :rating")
            params["rating"] = query["rating"]
        if "reviewCount" in query:
            where_clauses.append("review_count = :reviewCount")
            params["reviewCount"] = query["reviewCount"]
        if "lastUpdated" in query:
            where_clauses.append("last_updated = :lastUpdated")
            params["lastUpdated"] = query["lastUpdated"]
        if "method" in query:
            where_clauses.append("method = :method")
            params["method"] = query["method"]

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        factory = self._factory()
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"),
                    params,
                )
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    async def findOne(self, query: Dict) -> Optional[Dict]:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        return self._row_to_dict(row) if row else None

    async def create(self, data: Google_reviewsInternalCreate) -> Dict:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if ((hasattr(data, "rating") and (getattr(data, "rating") if hasattr(data, "rating") else (data.get("rating") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("rating") is not None)):
            cols.append("rating")
            vals.append(":rating")
            params["rating"] = (getattr(data, "rating") if hasattr(data, "rating") else (data.get("rating") if isinstance(data, dict) else None))
        if ((hasattr(data, "reviewCount") and (getattr(data, "reviewCount") if hasattr(data, "reviewCount") else (data.get("reviewCount") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("reviewCount") is not None)):
            cols.append("review_count")
            vals.append(":reviewCount")
            params["reviewCount"] = (getattr(data, "reviewCount") if hasattr(data, "reviewCount") else (data.get("reviewCount") if isinstance(data, dict) else None))
        if ((hasattr(data, "lastUpdated") and (getattr(data, "lastUpdated") if hasattr(data, "lastUpdated") else (data.get("lastUpdated") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("lastUpdated") is not None)):
            cols.append("last_updated")
            vals.append(":lastUpdated")
            params["lastUpdated"] = (getattr(data, "lastUpdated") if hasattr(data, "lastUpdated") else (data.get("lastUpdated") if isinstance(data, dict) else None))
        if ((hasattr(data, "method") and (getattr(data, "method") if hasattr(data, "method") else (data.get("method") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("method") is not None)):
            cols.append("method")
            vals.append(":method")
            params["method"] = (getattr(data, "method") if hasattr(data, "method") else (data.get("method") if isinstance(data, dict) else None))

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        async with factory() as session:
            await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = (await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": ext_id})).scalar()
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, data: Google_reviewsInternalUpdate) -> Optional[Any]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = Google_reviewsInternalUpdate(**{**(existing.model_dump(by_alias=True) if hasattr(existing, "model_dump") else existing), **(data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data)})
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if ((hasattr(merged, "rating") and (getattr(merged, "rating") if hasattr(merged, "rating") else (merged.get("rating") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("rating") is not None)):
            updates.append("rating = :rating")
            params["rating"] = (getattr(merged, "rating") if hasattr(merged, "rating") else (merged.get("rating") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "reviewCount") and (getattr(merged, "reviewCount") if hasattr(merged, "reviewCount") else (merged.get("reviewCount") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("reviewCount") is not None)):
            updates.append("review_count = :reviewCount")
            params["reviewCount"] = (getattr(merged, "reviewCount") if hasattr(merged, "reviewCount") else (merged.get("reviewCount") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "lastUpdated") and (getattr(merged, "lastUpdated") if hasattr(merged, "lastUpdated") else (merged.get("lastUpdated") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("lastUpdated") is not None)):
            updates.append("last_updated = :lastUpdated")
            params["lastUpdated"] = (getattr(merged, "lastUpdated") if hasattr(merged, "lastUpdated") else (merged.get("lastUpdated") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "method") and (getattr(merged, "method") if hasattr(merged, "method") else (merged.get("method") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("method") is not None)):
            updates.append("method = :method")
            params["method"] = (getattr(merged, "method") if hasattr(merged, "method") else (merged.get("method") if isinstance(merged, dict) else None))

        set_sql = ", ".join(updates)
        factory = self._factory()
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pid},
            )
            await session.commit()
            return res.rowcount > 0

from app.models.stock_reservation import StockReservation

class MySQLStockReservationsDAO:
    TABLE = "sj_stock_reservations"

    def _factory(self):
        return get_async_session_factory()

    async def findAll(self, query: Optional[Dict] = None) -> List[StockReservation]:
        query = query or {}
        where_clauses = []
        params = {}
        if "productId" in query:
            where_clauses.append("product_id = :productId")
            params["productId"] = query["productId"]
        if "userId" in query:
            where_clauses.append("user_id = :userId")
            params["userId"] = query["userId"]
        if "quantity" in query:
            where_clauses.append("quantity = :quantity")
            params["quantity"] = query["quantity"]
        if "status" in query:
            where_clauses.append("status = :status")
            params["status"] = query["status"]
        if "expiresAt" in query:
            where_clauses.append("expires_at = :expiresAt")
            params["expiresAt"] = query["expiresAt"]

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        factory = self._factory()
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"),
                    params,
                )
            ).fetchall()
        return [StockReservation.model_validate(r) for r in rows]

    async def findOne(self, query: Dict) -> Optional[StockReservation]:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[StockReservation]:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        return StockReservation.model_validate(row) if row else None

    async def create(self, data: StockReservationsInternalCreate) -> StockReservation:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if ((hasattr(data, "productId") and (getattr(data, "productId") if hasattr(data, "productId") else (data.get("productId") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("productId") is not None)):
            cols.append("product_id")
            vals.append(":productId")
            params["productId"] = (getattr(data, "productId") if hasattr(data, "productId") else (data.get("productId") if isinstance(data, dict) else None))
        if ((hasattr(data, "userId") and (getattr(data, "userId") if hasattr(data, "userId") else (data.get("userId") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("userId") is not None)):
            cols.append("user_id")
            vals.append(":userId")
            params["userId"] = (getattr(data, "userId") if hasattr(data, "userId") else (data.get("userId") if isinstance(data, dict) else None))
        if ((hasattr(data, "quantity") and (getattr(data, "quantity") if hasattr(data, "quantity") else (data.get("quantity") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("quantity") is not None)):
            cols.append("quantity")
            vals.append(":quantity")
            params["quantity"] = (getattr(data, "quantity") if hasattr(data, "quantity") else (data.get("quantity") if isinstance(data, dict) else None))
        if ((hasattr(data, "status") and (getattr(data, "status") if hasattr(data, "status") else (data.get("status") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("status") is not None)):
            cols.append("status")
            vals.append(":status")
            params["status"] = (getattr(data, "status") if hasattr(data, "status") else (data.get("status") if isinstance(data, dict) else None))
        if "expiresAt" in data:
            cols.append("expires_at")
            vals.append(":expiresAt")
            # Convert 'Z' format to datetime object
            exp = str(data.expiresAt)
            if exp.endswith("Z"):
                exp = exp[:-1]
                if not exp.endswith("+00:00") and "+" not in exp[-6:] and "-" not in exp[-6:]:
                    exp += "+00:00"
            from datetime import datetime
            params["expiresAt"] = datetime.fromisoformat(exp).replace(tzinfo=None)

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        async with factory() as session:
            await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = (await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": ext_id})).scalar()
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, data: StockReservationsInternalUpdate) -> Optional[StockReservation]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = {**(existing.model_dump(by_alias=True) if hasattr(existing, "model_dump") else existing), **(data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data)}
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if ((hasattr(merged, "productId") and (getattr(merged, "productId") if hasattr(merged, "productId") else (merged.get("productId") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("productId") is not None)):
            updates.append("product_id = :productId")
            params["productId"] = (getattr(merged, "productId") if hasattr(merged, "productId") else (merged.get("productId") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "userId") and (getattr(merged, "userId") if hasattr(merged, "userId") else (merged.get("userId") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("userId") is not None)):
            updates.append("user_id = :userId")
            params["userId"] = (getattr(merged, "userId") if hasattr(merged, "userId") else (merged.get("userId") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "quantity") and (getattr(merged, "quantity") if hasattr(merged, "quantity") else (merged.get("quantity") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("quantity") is not None)):
            updates.append("quantity = :quantity")
            params["quantity"] = (getattr(merged, "quantity") if hasattr(merged, "quantity") else (merged.get("quantity") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "status") and (getattr(merged, "status") if hasattr(merged, "status") else (merged.get("status") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("status") is not None)):
            updates.append("status = :status")
            params["status"] = (getattr(merged, "status") if hasattr(merged, "status") else (merged.get("status") if isinstance(merged, dict) else None))
        if "expiresAt" in merged:
            updates.append("expires_at = :expiresAt")
            exp = str(merged.expiresAt)
            if exp.endswith("Z"):
                exp = exp[:-1]
                if not exp.endswith("+00:00") and "+" not in exp[-6:] and "-" not in exp[-6:]:
                    exp += "+00:00"
            from datetime import datetime
            params["expiresAt"] = datetime.fromisoformat(exp).replace(tzinfo=None)

        set_sql = ", ".join(updates)
        factory = self._factory()
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pid},
            )
            await session.commit()
            return res.rowcount > 0

class MySQLProductNotificationsDAO:
    TABLE = "sj_product_notifications"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_dict(self, row) -> Dict:
        return {
            "_id": str(row.id),
            "id": row.id,
            "external_id": row.external_id,
            "productId": row.product_id,
            "userId": row.user_id,
            "email": row.email,
            "phone": row.phone,
            "status": row.status,

            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        }

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        query = query or {}
        where_clauses = []
        params = {}
        if "productId" in query:
            where_clauses.append("product_id = :productId")
            params["productId"] = query["productId"]
        if "userId" in query:
            where_clauses.append("user_id = :userId")
            params["userId"] = query["userId"]
        if "email" in query:
            where_clauses.append("email = :email")
            params["email"] = query["email"]
        if "phone" in query:
            where_clauses.append("phone = :phone")
            params["phone"] = query["phone"]
        if "status" in query:
            where_clauses.append("status = :status")
            params["status"] = query["status"]

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        factory = self._factory()
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"),
                    params,
                )
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    async def findOne(self, query: Dict) -> Optional[Dict]:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        return self._row_to_dict(row) if row else None

    async def create(self, data: ProductNotificationsInternalCreate) -> Dict:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if ((hasattr(data, "productId") and (getattr(data, "productId") if hasattr(data, "productId") else (data.get("productId") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("productId") is not None)):
            cols.append("product_id")
            vals.append(":productId")
            params["productId"] = (getattr(data, "productId") if hasattr(data, "productId") else (data.get("productId") if isinstance(data, dict) else None))
        if ((hasattr(data, "userId") and (getattr(data, "userId") if hasattr(data, "userId") else (data.get("userId") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("userId") is not None)):
            cols.append("user_id")
            vals.append(":userId")
            params["userId"] = (getattr(data, "userId") if hasattr(data, "userId") else (data.get("userId") if isinstance(data, dict) else None))
        if ((hasattr(data, "email") and (getattr(data, "email") if hasattr(data, "email") else (data.get("email") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("email") is not None)):
            cols.append("email")
            vals.append(":email")
            params["email"] = (getattr(data, "email") if hasattr(data, "email") else (data.get("email") if isinstance(data, dict) else None))
        if ((hasattr(data, "phone") and (getattr(data, "phone") if hasattr(data, "phone") else (data.get("phone") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("phone") is not None)):
            cols.append("phone")
            vals.append(":phone")
            params["phone"] = (getattr(data, "phone") if hasattr(data, "phone") else (data.get("phone") if isinstance(data, dict) else None))
        if ((hasattr(data, "status") and (getattr(data, "status") if hasattr(data, "status") else (data.get("status") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("status") is not None)):
            cols.append("status")
            vals.append(":status")
            params["status"] = (getattr(data, "status") if hasattr(data, "status") else (data.get("status") if isinstance(data, dict) else None))

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        async with factory() as session:
            await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = (await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": ext_id})).scalar()
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, data: ProductNotificationsInternalUpdate) -> Optional[Any]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = ProductNotificationsInternalUpdate(**{**(existing.model_dump(by_alias=True) if hasattr(existing, "model_dump") else existing), **(data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data)})
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if ((hasattr(merged, "productId") and (getattr(merged, "productId") if hasattr(merged, "productId") else (merged.get("productId") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("productId") is not None)):
            updates.append("product_id = :productId")
            params["productId"] = (getattr(merged, "productId") if hasattr(merged, "productId") else (merged.get("productId") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "userId") and (getattr(merged, "userId") if hasattr(merged, "userId") else (merged.get("userId") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("userId") is not None)):
            updates.append("user_id = :userId")
            params["userId"] = (getattr(merged, "userId") if hasattr(merged, "userId") else (merged.get("userId") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "email") and (getattr(merged, "email") if hasattr(merged, "email") else (merged.get("email") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("email") is not None)):
            updates.append("email = :email")
            params["email"] = (getattr(merged, "email") if hasattr(merged, "email") else (merged.get("email") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "phone") and (getattr(merged, "phone") if hasattr(merged, "phone") else (merged.get("phone") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("phone") is not None)):
            updates.append("phone = :phone")
            params["phone"] = (getattr(merged, "phone") if hasattr(merged, "phone") else (merged.get("phone") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "status") and (getattr(merged, "status") if hasattr(merged, "status") else (merged.get("status") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("status") is not None)):
            updates.append("status = :status")
            params["status"] = (getattr(merged, "status") if hasattr(merged, "status") else (merged.get("status") if isinstance(merged, dict) else None))

        set_sql = ", ".join(updates)
        factory = self._factory()
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pid},
            )
            await session.commit()
            return res.rowcount > 0

class MySQLProductReviewsDAO:
    TABLE = "sj_product_reviews"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_dict(self, row) -> ProductReviewResponse:
        return ProductReviewResponse(**{
            "_id": str(row.id),
            "id": row.id,
            "external_id": row.external_id,
            "productId": row.product_id,
            "userId": row.user_id,
            "rating": row.rating,
            "reviewText": row.review_text,
            "status": row.status,

            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        })

    async def findAll(self, query: Optional[Dict] = None) -> List[ProductReviewResponse]:
        query = query or {}
        where_clauses = []
        params = {}
        if "productId" in query:
            where_clauses.append("product_id = :productId")
            params["productId"] = query["productId"]
        if "userId" in query:
            where_clauses.append("user_id = :userId")
            params["userId"] = query["userId"]
        if "rating" in query:
            where_clauses.append("rating = :rating")
            params["rating"] = query["rating"]
        if "reviewText" in query:
            where_clauses.append("review_text = :reviewText")
            params["reviewText"] = query["reviewText"]
        if "status" in query:
            where_clauses.append("status = :status")
            params["status"] = query["status"]

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        factory = self._factory()
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"),
                    params,
                )
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    async def findOne(self, query: Dict) -> Optional[ProductReviewResponse]:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[ProductReviewResponse]:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        return self._row_to_dict(row) if row else None

    async def create(self, data: ProductReviewsInternalCreate) -> ProductReviewResponse:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if ((hasattr(data, "productId") and (getattr(data, "productId") if hasattr(data, "productId") else (data.get("productId") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("productId") is not None)):
            cols.append("product_id")
            vals.append(":productId")
            params["productId"] = (getattr(data, "productId") if hasattr(data, "productId") else (data.get("productId") if isinstance(data, dict) else None))
        if ((hasattr(data, "userId") and (getattr(data, "userId") if hasattr(data, "userId") else (data.get("userId") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("userId") is not None)):
            cols.append("user_id")
            vals.append(":userId")
            params["userId"] = (getattr(data, "userId") if hasattr(data, "userId") else (data.get("userId") if isinstance(data, dict) else None))
        if ((hasattr(data, "rating") and (getattr(data, "rating") if hasattr(data, "rating") else (data.get("rating") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("rating") is not None)):
            cols.append("rating")
            vals.append(":rating")
            params["rating"] = (getattr(data, "rating") if hasattr(data, "rating") else (data.get("rating") if isinstance(data, dict) else None))
        if ((hasattr(data, "reviewText") and (getattr(data, "reviewText") if hasattr(data, "reviewText") else (data.get("reviewText") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("reviewText") is not None)):
            cols.append("review_text")
            vals.append(":reviewText")
            params["reviewText"] = (getattr(data, "reviewText") if hasattr(data, "reviewText") else (data.get("reviewText") if isinstance(data, dict) else None))
        if ((hasattr(data, "status") and (getattr(data, "status") if hasattr(data, "status") else (data.get("status") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("status") is not None)):
            cols.append("status")
            vals.append(":status")
            params["status"] = (getattr(data, "status") if hasattr(data, "status") else (data.get("status") if isinstance(data, dict) else None))

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        async with factory() as session:
            await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = (await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": ext_id})).scalar()
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, data: ProductReviewsInternalUpdate) -> Optional[Any]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = ProductReviewsInternalUpdate(**{**(existing.model_dump(by_alias=True) if hasattr(existing, "model_dump") else existing), **(data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data)})
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if ((hasattr(merged, "productId") and (getattr(merged, "productId") if hasattr(merged, "productId") else (merged.get("productId") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("productId") is not None)):
            updates.append("product_id = :productId")
            params["productId"] = (getattr(merged, "productId") if hasattr(merged, "productId") else (merged.get("productId") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "userId") and (getattr(merged, "userId") if hasattr(merged, "userId") else (merged.get("userId") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("userId") is not None)):
            updates.append("user_id = :userId")
            params["userId"] = (getattr(merged, "userId") if hasattr(merged, "userId") else (merged.get("userId") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "rating") and (getattr(merged, "rating") if hasattr(merged, "rating") else (merged.get("rating") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("rating") is not None)):
            updates.append("rating = :rating")
            params["rating"] = (getattr(merged, "rating") if hasattr(merged, "rating") else (merged.get("rating") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "reviewText") and (getattr(merged, "reviewText") if hasattr(merged, "reviewText") else (merged.get("reviewText") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("reviewText") is not None)):
            updates.append("review_text = :reviewText")
            params["reviewText"] = (getattr(merged, "reviewText") if hasattr(merged, "reviewText") else (merged.get("reviewText") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "status") and (getattr(merged, "status") if hasattr(merged, "status") else (merged.get("status") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("status") is not None)):
            updates.append("status = :status")
            params["status"] = (getattr(merged, "status") if hasattr(merged, "status") else (merged.get("status") if isinstance(merged, dict) else None))

        set_sql = ", ".join(updates)
        factory = self._factory()
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pid},
            )
            await session.commit()
            return res.rowcount > 0

class MySQLClassificationTagsDAO:
    TABLE = "sj_classification_tags"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_dict(self, row) -> ProductReviewResponse:
        return ProductReviewResponse(**{
            "_id": str(row.id),
            "id": row.id,
            "external_id": row.external_id,
            "name": row.name,
            "isActive": bool(row.is_active),
            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        })

    async def findAll(self, query: Optional[Dict] = None) -> List[ProductReviewResponse]:
        query = query or {}
        where_clauses = []
        params = {}
        if "name" in query:
            where_clauses.append("name = :name")
            params["name"] = query["name"]
        if "isActive" in query:
            where_clauses.append("is_active = :isActive")
            params["isActive"] = 1 if query["isActive"] else None

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        factory = self._factory()
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"),
                    params,
                )
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    async def findOne(self, query: Dict) -> Optional[ProductReviewResponse]:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[ProductReviewResponse]:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        return self._row_to_dict(row) if row else None

    async def create(self, data: ClassificationTagsInternalCreate) -> ProductReviewResponse:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if ((hasattr(data, "name") and (getattr(data, "name") if hasattr(data, "name") else (data.get("name") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("name") is not None)):
            cols.append("name")
            vals.append(":name")
            params["name"] = (getattr(data, "name") if hasattr(data, "name") else (data.get("name") if isinstance(data, dict) else None))
        if ((hasattr(data, "isActive") and (getattr(data, "isActive") if hasattr(data, "isActive") else (data.get("isActive") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("isActive") is not None)):
            cols.append("is_active")
            vals.append(":isActive")
            params["isActive"] = 1 if (getattr(data, "isActive") if hasattr(data, "isActive") else (data.get("isActive") if isinstance(data, dict) else None)) else 0

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        async with factory() as session:
            await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = (await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": ext_id})).scalar()
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, data: ClassificationTagsInternalUpdate) -> Optional[Any]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = ClassificationTagsInternalUpdate(**{**(existing.model_dump(by_alias=True) if hasattr(existing, "model_dump") else existing), **(data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data)})
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if ((hasattr(merged, "name") and (getattr(merged, "name") if hasattr(merged, "name") else (merged.get("name") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("name") is not None)):
            updates.append("name = :name")
            params["name"] = (getattr(merged, "name") if hasattr(merged, "name") else (merged.get("name") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "isActive") and (getattr(merged, "isActive") if hasattr(merged, "isActive") else (merged.get("isActive") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("isActive") is not None)):
            updates.append("is_active = :isActive")
            params["isActive"] = 1 if (getattr(merged, "isActive") if hasattr(merged, "isActive") else (merged.get("isActive") if isinstance(merged, dict) else None)) else None

        set_sql = ", ".join(updates)
        factory = self._factory()
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pid},
            )
            await session.commit()
            return result.rowcount > 0

class MySQLReviewClassificationsDAO:
    TABLE = "sj_review_classifications"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_dict(self, row) -> ClassificationTagResponse:
        return ClassificationTagResponse(**{
            "_id": str(row.id),
            "id": row.id,
            "external_id": row.external_id,
            "reviewId": row.review_id,
            "category": row.category,
            "confidenceScore": row.confidence_score,
            "sentiment": row.sentiment,

            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        })

    async def findAll(self, query: Optional[Dict] = None) -> List[ClassificationTagResponse]:
        query = query or {}
        where_clauses = []
        params = {}
        if "reviewId" in query:
            where_clauses.append("review_id = :reviewId")
            params["reviewId"] = query["reviewId"]
        if "category" in query:
            where_clauses.append("category = :category")
            params["category"] = query["category"]
        if "confidenceScore" in query:
            where_clauses.append("confidence_score = :confidenceScore")
            params["confidenceScore"] = query["confidenceScore"]
        if "sentiment" in query:
            where_clauses.append("sentiment = :sentiment")
            params["sentiment"] = query["sentiment"]

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        factory = self._factory()
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"),
                    params,
                )
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    async def findOne(self, query: Dict) -> Optional[ClassificationTagResponse]:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[ClassificationTagResponse]:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        return self._row_to_dict(row) if row else None

    async def create(self, data: ReviewClassificationsInternalCreate) -> ClassificationTagResponse:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if ((hasattr(data, "reviewId") and (getattr(data, "reviewId") if hasattr(data, "reviewId") else (data.get("reviewId") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("reviewId") is not None)):
            cols.append("review_id")
            vals.append(":reviewId")
            params["reviewId"] = (getattr(data, "reviewId") if hasattr(data, "reviewId") else (data.get("reviewId") if isinstance(data, dict) else None))
        if ((hasattr(data, "category") and (getattr(data, "category") if hasattr(data, "category") else (data.get("category") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("category") is not None)):
            cols.append("category")
            vals.append(":category")
            params["category"] = (getattr(data, "category") if hasattr(data, "category") else (data.get("category") if isinstance(data, dict) else None))
        if ((hasattr(data, "confidenceScore") and (getattr(data, "confidenceScore") if hasattr(data, "confidenceScore") else (data.get("confidenceScore") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("confidenceScore") is not None)):
            cols.append("confidence_score")
            vals.append(":confidenceScore")
            params["confidenceScore"] = (getattr(data, "confidenceScore") if hasattr(data, "confidenceScore") else (data.get("confidenceScore") if isinstance(data, dict) else None))
        if ((hasattr(data, "sentiment") and (getattr(data, "sentiment") if hasattr(data, "sentiment") else (data.get("sentiment") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("sentiment") is not None)):
            cols.append("sentiment")
            vals.append(":sentiment")
            params["sentiment"] = (getattr(data, "sentiment") if hasattr(data, "sentiment") else (data.get("sentiment") if isinstance(data, dict) else None))

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        async with factory() as session:
            await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = (await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": ext_id})).scalar()
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, data: ReviewClassificationsInternalUpdate) -> Optional[Any]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = ReviewClassificationsInternalUpdate(**{**(existing.model_dump(by_alias=True) if hasattr(existing, "model_dump") else existing), **(data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data)})
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if ((hasattr(merged, "reviewId") and (getattr(merged, "reviewId") if hasattr(merged, "reviewId") else (merged.get("reviewId") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("reviewId") is not None)):
            updates.append("review_id = :reviewId")
            params["reviewId"] = (getattr(merged, "reviewId") if hasattr(merged, "reviewId") else (merged.get("reviewId") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "category") and (getattr(merged, "category") if hasattr(merged, "category") else (merged.get("category") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("category") is not None)):
            updates.append("category = :category")
            params["category"] = (getattr(merged, "category") if hasattr(merged, "category") else (merged.get("category") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "confidenceScore") and (getattr(merged, "confidenceScore") if hasattr(merged, "confidenceScore") else (merged.get("confidenceScore") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("confidenceScore") is not None)):
            updates.append("confidence_score = :confidenceScore")
            params["confidenceScore"] = (getattr(merged, "confidenceScore") if hasattr(merged, "confidenceScore") else (merged.get("confidenceScore") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "sentiment") and (getattr(merged, "sentiment") if hasattr(merged, "sentiment") else (merged.get("sentiment") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("sentiment") is not None)):
            updates.append("sentiment = :sentiment")
            params["sentiment"] = (getattr(merged, "sentiment") if hasattr(merged, "sentiment") else (merged.get("sentiment") if isinstance(merged, dict) else None))

        set_sql = ", ".join(updates)
        factory = self._factory()
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pid},
            )
            await session.commit()
            return res.rowcount > 0

class MySQLAboutUsDAO:
    TABLE = "sj_about_us"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_dict(self, row) -> Any:
        return {
            "_id": str(row.id),
            "id": row.id,
            "external_id": row.external_id,
            "title": row.title,
            "content": row.content,
            "version": row.version,
            "isPublished": bool(row.is_published) if getattr(row, "is_published", None) is not None else False,

            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        }

    async def findAll(self, query: Optional[Dict] = None) -> List[Any]:
        query = query or {}
        where_clauses = []
        params = {}
        if "title" in query:
            where_clauses.append("title = :title")
            params["title"] = query["title"]
        if "content" in query:
            where_clauses.append("content = :content")
            params["content"] = query["content"]
        if "version" in query:
            where_clauses.append("version = :version")
            params["version"] = query["version"]
        if "isPublished" in query:
            where_clauses.append("is_published = :isPublished")
            params["isPublished"] = 1 if query["isPublished"] else None

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        factory = self._factory()
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"),
                    params,
                )
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    async def findOne(self, query: Dict) -> Optional[Any]:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Any]:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        return self._row_to_dict(row) if row else None

    async def create(self, data: AboutUsInternalCreate) -> Any:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if ((hasattr(data, "title") and (getattr(data, "title") if hasattr(data, "title") else (data.get("title") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("title") is not None)):
            cols.append("title")
            vals.append(":title")
            params["title"] = (getattr(data, "title") if hasattr(data, "title") else (data.get("title") if isinstance(data, dict) else None))
        if ((hasattr(data, "content") and (getattr(data, "content") if hasattr(data, "content") else (data.get("content") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("content") is not None)):
            cols.append("content")
            vals.append(":content")
            params["content"] = (getattr(data, "content") if hasattr(data, "content") else (data.get("content") if isinstance(data, dict) else None))
        if ((hasattr(data, "version") and (getattr(data, "version") if hasattr(data, "version") else (data.get("version") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("version") is not None)):
            cols.append("version")
            vals.append(":version")
            params["version"] = (getattr(data, "version") if hasattr(data, "version") else (data.get("version") if isinstance(data, dict) else None))
        if ((hasattr(data, "isPublished") and (getattr(data, "isPublished") if hasattr(data, "isPublished") else (data.get("isPublished") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("isPublished") is not None)):
            cols.append("is_published")
            vals.append(":isPublished")
            params["isPublished"] = 1 if (getattr(data, "isPublished") if hasattr(data, "isPublished") else (data.get("isPublished") if isinstance(data, dict) else None)) else 0

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        async with factory() as session:
            await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = (await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": ext_id})).scalar()
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, data: AboutUsInternalUpdate) -> Optional[Any]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = AboutUsInternalUpdate(**{**(existing.model_dump(by_alias=True) if hasattr(existing, "model_dump") else existing), **(data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data)})
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if ((hasattr(merged, "title") and (getattr(merged, "title") if hasattr(merged, "title") else (merged.get("title") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("title") is not None)):
            updates.append("title = :title")
            params["title"] = (getattr(merged, "title") if hasattr(merged, "title") else (merged.get("title") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "content") and (getattr(merged, "content") if hasattr(merged, "content") else (merged.get("content") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("content") is not None)):
            updates.append("content = :content")
            params["content"] = (getattr(merged, "content") if hasattr(merged, "content") else (merged.get("content") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "version") and (getattr(merged, "version") if hasattr(merged, "version") else (merged.get("version") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("version") is not None)):
            updates.append("version = :version")
            params["version"] = (getattr(merged, "version") if hasattr(merged, "version") else (merged.get("version") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "isPublished") and (getattr(merged, "isPublished") if hasattr(merged, "isPublished") else (merged.get("isPublished") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("isPublished") is not None)):
            updates.append("is_published = :isPublished")
            params["isPublished"] = 1 if (getattr(merged, "isPublished") if hasattr(merged, "isPublished") else (merged.get("isPublished") if isinstance(merged, dict) else None)) else None

        set_sql = ", ".join(updates)
        factory = self._factory()
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pid},
            )
            await session.commit()
            return res.rowcount > 0

class MySQLPrivacyPolicyDAO:
    TABLE = "sj_privacy_policy"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_dict(self, row) -> Any:
        return {
            "_id": str(row.id),
            "id": row.id,
            "external_id": row.external_id,
            "version": row.version,
            "content": row.content,
            "effectiveDate": row.effective_date,
            "isActive": bool(row.is_active) if getattr(row, "is_active", None) is not None else False,

            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        }

    async def findAll(self, query: Optional[Dict] = None) -> List[Any]:
        query = query or {}
        where_clauses = []
        params = {}
        if "version" in query:
            where_clauses.append("version = :version")
            params["version"] = query["version"]
        if "content" in query:
            where_clauses.append("content = :content")
            params["content"] = query["content"]
        if "effectiveDate" in query:
            where_clauses.append("effective_date = :effectiveDate")
            params["effectiveDate"] = query["effectiveDate"]
        if "isActive" in query:
            where_clauses.append("is_active = :isActive")
            params["isActive"] = 1 if query["isActive"] else None

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        factory = self._factory()
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"),
                    params,
                )
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    async def findOne(self, query: Dict) -> Optional[Any]:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Any]:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        return self._row_to_dict(row) if row else None

    async def create(self, data: PrivacyPolicyInternalCreate) -> Any:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if ((hasattr(data, "version") and (getattr(data, "version") if hasattr(data, "version") else (data.get("version") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("version") is not None)):
            cols.append("version")
            vals.append(":version")
            params["version"] = (getattr(data, "version") if hasattr(data, "version") else (data.get("version") if isinstance(data, dict) else None))
        if ((hasattr(data, "content") and (getattr(data, "content") if hasattr(data, "content") else (data.get("content") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("content") is not None)):
            cols.append("content")
            vals.append(":content")
            params["content"] = (getattr(data, "content") if hasattr(data, "content") else (data.get("content") if isinstance(data, dict) else None))
        if ((hasattr(data, "effectiveDate") and (getattr(data, "effectiveDate") if hasattr(data, "effectiveDate") else (data.get("effectiveDate") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("effectiveDate") is not None)):
            cols.append("effective_date")
            vals.append(":effectiveDate")
            params["effectiveDate"] = (getattr(data, "effectiveDate") if hasattr(data, "effectiveDate") else (data.get("effectiveDate") if isinstance(data, dict) else None))
        if ((hasattr(data, "isActive") and (getattr(data, "isActive") if hasattr(data, "isActive") else (data.get("isActive") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("isActive") is not None)):
            cols.append("is_active")
            vals.append(":isActive")
            params["isActive"] = 1 if (getattr(data, "isActive") if hasattr(data, "isActive") else (data.get("isActive") if isinstance(data, dict) else None)) else 0

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        async with factory() as session:
            await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = (await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": ext_id})).scalar()
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, data: PrivacyPolicyInternalUpdate) -> Optional[Any]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = PrivacyPolicyInternalUpdate(**{**(existing.model_dump(by_alias=True) if hasattr(existing, "model_dump") else existing), **(data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data)})
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if ((hasattr(merged, "version") and (getattr(merged, "version") if hasattr(merged, "version") else (merged.get("version") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("version") is not None)):
            updates.append("version = :version")
            params["version"] = (getattr(merged, "version") if hasattr(merged, "version") else (merged.get("version") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "content") and (getattr(merged, "content") if hasattr(merged, "content") else (merged.get("content") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("content") is not None)):
            updates.append("content = :content")
            params["content"] = (getattr(merged, "content") if hasattr(merged, "content") else (merged.get("content") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "effectiveDate") and (getattr(merged, "effectiveDate") if hasattr(merged, "effectiveDate") else (merged.get("effectiveDate") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("effectiveDate") is not None)):
            updates.append("effective_date = :effectiveDate")
            params["effectiveDate"] = (getattr(merged, "effectiveDate") if hasattr(merged, "effectiveDate") else (merged.get("effectiveDate") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "isActive") and (getattr(merged, "isActive") if hasattr(merged, "isActive") else (merged.get("isActive") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("isActive") is not None)):
            updates.append("is_active = :isActive")
            params["isActive"] = 1 if (getattr(merged, "isActive") if hasattr(merged, "isActive") else (merged.get("isActive") if isinstance(merged, dict) else None)) else None

        set_sql = ", ".join(updates)
        factory = self._factory()
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pid},
            )
            await session.commit()
            return res.rowcount > 0

class MySQLAvailabilityRequestsDAO:
    TABLE = "sj_availability_requests"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_dict(self, row) -> AvailabilityRequestResponse:
        return AvailabilityRequestResponse(**{
            "_id": str(row.id),
            "id": row.id,
            "external_id": row.external_id,
            "productId": row.product_id,
            "productName": row.product_name,
            "pincode": row.pincode,
            "userName": row.user_name,
            "userEmail": row.user_email,

            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        })

    async def findAll(self, query: Optional[Dict] = None) -> List[AvailabilityRequestResponse]:
        query = query or {}
        where_clauses = []
        params = {}
        if "productId" in query:
            where_clauses.append("product_id = :productId")
            params["productId"] = query["productId"]
        if "productName" in query:
            where_clauses.append("product_name = :productName")
            params["productName"] = query["productName"]
        if "pincode" in query:
            where_clauses.append("pincode = :pincode")
            params["pincode"] = query["pincode"]
        if "userName" in query:
            where_clauses.append("user_name = :userName")
            params["userName"] = query["userName"]
        if "userEmail" in query:
            where_clauses.append("user_email = :userEmail")
            params["userEmail"] = query["userEmail"]

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        factory = self._factory()
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"),
                    params,
                )
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    async def findOne(self, query: Dict) -> Optional[AvailabilityRequestResponse]:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[AvailabilityRequestResponse]:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        return self._row_to_dict(row) if row else None

    async def create(self, data: AvailabilityRequestsInternalCreate) -> AvailabilityRequestResponse:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if ((hasattr(data, "productId") and (getattr(data, "productId") if hasattr(data, "productId") else (data.get("productId") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("productId") is not None)):
            cols.append("product_id")
            vals.append(":productId")
            params["productId"] = (getattr(data, "productId") if hasattr(data, "productId") else (data.get("productId") if isinstance(data, dict) else None))
        if ((hasattr(data, "productName") and (getattr(data, "productName") if hasattr(data, "productName") else (data.get("productName") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("productName") is not None)):
            cols.append("product_name")
            vals.append(":productName")
            params["productName"] = (getattr(data, "productName") if hasattr(data, "productName") else (data.get("productName") if isinstance(data, dict) else None))
        if ((hasattr(data, "pincode") and (getattr(data, "pincode") if hasattr(data, "pincode") else (data.get("pincode") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("pincode") is not None)):
            cols.append("pincode")
            vals.append(":pincode")
            params["pincode"] = (getattr(data, "pincode") if hasattr(data, "pincode") else (data.get("pincode") if isinstance(data, dict) else None))
        if ((hasattr(data, "userName") and (getattr(data, "userName") if hasattr(data, "userName") else (data.get("userName") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("userName") is not None)):
            cols.append("user_name")
            vals.append(":userName")
            params["userName"] = (getattr(data, "userName") if hasattr(data, "userName") else (data.get("userName") if isinstance(data, dict) else None))
        if ((hasattr(data, "userEmail") and (getattr(data, "userEmail") if hasattr(data, "userEmail") else (data.get("userEmail") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("userEmail") is not None)):
            cols.append("user_email")
            vals.append(":userEmail")
            params["userEmail"] = (getattr(data, "userEmail") if hasattr(data, "userEmail") else (data.get("userEmail") if isinstance(data, dict) else None))

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        async with factory() as session:
            await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = (await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": ext_id})).scalar()
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, data: AvailabilityRequestsInternalUpdate) -> Optional[Any]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = AvailabilityRequestsInternalUpdate(**{**(existing.model_dump(by_alias=True) if hasattr(existing, "model_dump") else existing), **(data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data)})
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if ((hasattr(merged, "productId") and (getattr(merged, "productId") if hasattr(merged, "productId") else (merged.get("productId") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("productId") is not None)):
            updates.append("product_id = :productId")
            params["productId"] = (getattr(merged, "productId") if hasattr(merged, "productId") else (merged.get("productId") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "productName") and (getattr(merged, "productName") if hasattr(merged, "productName") else (merged.get("productName") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("productName") is not None)):
            updates.append("product_name = :productName")
            params["productName"] = (getattr(merged, "productName") if hasattr(merged, "productName") else (merged.get("productName") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "pincode") and (getattr(merged, "pincode") if hasattr(merged, "pincode") else (merged.get("pincode") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("pincode") is not None)):
            updates.append("pincode = :pincode")
            params["pincode"] = (getattr(merged, "pincode") if hasattr(merged, "pincode") else (merged.get("pincode") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "userName") and (getattr(merged, "userName") if hasattr(merged, "userName") else (merged.get("userName") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("userName") is not None)):
            updates.append("user_name = :userName")
            params["userName"] = (getattr(merged, "userName") if hasattr(merged, "userName") else (merged.get("userName") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "userEmail") and (getattr(merged, "userEmail") if hasattr(merged, "userEmail") else (merged.get("userEmail") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("userEmail") is not None)):
            updates.append("user_email = :userEmail")
            params["userEmail"] = (getattr(merged, "userEmail") if hasattr(merged, "userEmail") else (merged.get("userEmail") if isinstance(merged, dict) else None))

        set_sql = ", ".join(updates)
        factory = self._factory()
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pid},
            )
            await session.commit()
            return res.rowcount > 0

class MySQLPincodeSearchesDAO:
    TABLE = "sj_pincode_searches"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_dict(self, row) -> Any:
        return {
            "_id": str(row.id),
            "id": row.id,
            "external_id": row.external_id,
            "pincode": row.pincode,
            "query": row.query,
            "isServiceable": bool(row.is_serviceable) if getattr(row, "is_serviceable", None) is not None else False,
            "timestamp": row.timestamp,

            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        }

    async def findAll(self, query: Optional[Dict] = None) -> List[Any]:
        query = query or {}
        where_clauses = []
        params = {}
        if "pincode" in query:
            where_clauses.append("pincode = :pincode")
            params["pincode"] = query["pincode"]
        if "query" in query:
            where_clauses.append("query = :query")
            params["query"] = query["query"]
        if "isServiceable" in query:
            where_clauses.append("is_serviceable = :isServiceable")
            params["isServiceable"] = 1 if query["isServiceable"] else None
        if "timestamp" in query:
            where_clauses.append("timestamp = :timestamp")
            params["timestamp"] = query["timestamp"]

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        factory = self._factory()
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"),
                    params,
                )
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    async def findOne(self, query: Dict) -> Optional[Any]:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Any]:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        return self._row_to_dict(row) if row else None

    async def create(self, data: PincodeSearchesInternalCreate) -> Any:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if ((hasattr(data, "pincode") and (getattr(data, "pincode") if hasattr(data, "pincode") else (data.get("pincode") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("pincode") is not None)):
            cols.append("pincode")
            vals.append(":pincode")
            params["pincode"] = (getattr(data, "pincode") if hasattr(data, "pincode") else (data.get("pincode") if isinstance(data, dict) else None))
        if ((hasattr(data, "query") and (getattr(data, "query") if hasattr(data, "query") else (data.get("query") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("query") is not None)):
            cols.append("query")
            vals.append(":query")
            params["query"] = (getattr(data, "query") if hasattr(data, "query") else (data.get("query") if isinstance(data, dict) else None))
        if ((hasattr(data, "isServiceable") and (getattr(data, "isServiceable") if hasattr(data, "isServiceable") else (data.get("isServiceable") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("isServiceable") is not None)):
            cols.append("is_serviceable")
            vals.append(":isServiceable")
            params["isServiceable"] = 1 if (getattr(data, "isServiceable") if hasattr(data, "isServiceable") else (data.get("isServiceable") if isinstance(data, dict) else None)) else 0
        if ((hasattr(data, "timestamp") and (getattr(data, "timestamp") if hasattr(data, "timestamp") else (data.get("timestamp") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("timestamp") is not None)):
            cols.append("timestamp")
            vals.append(":timestamp")
            params["timestamp"] = (getattr(data, "timestamp") if hasattr(data, "timestamp") else (data.get("timestamp") if isinstance(data, dict) else None))

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        async with factory() as session:
            await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = (await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": ext_id})).scalar()
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, data: PincodeSearchesInternalUpdate) -> Optional[Any]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = PincodeSearchesInternalUpdate(**{**(existing.model_dump(by_alias=True) if hasattr(existing, "model_dump") else existing), **(data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data)})
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if ((hasattr(merged, "pincode") and (getattr(merged, "pincode") if hasattr(merged, "pincode") else (merged.get("pincode") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("pincode") is not None)):
            updates.append("pincode = :pincode")
            params["pincode"] = (getattr(merged, "pincode") if hasattr(merged, "pincode") else (merged.get("pincode") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "query") and (getattr(merged, "query") if hasattr(merged, "query") else (merged.get("query") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("query") is not None)):
            updates.append("query = :query")
            params["query"] = (getattr(merged, "query") if hasattr(merged, "query") else (merged.get("query") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "isServiceable") and (getattr(merged, "isServiceable") if hasattr(merged, "isServiceable") else (merged.get("isServiceable") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("isServiceable") is not None)):
            updates.append("is_serviceable = :isServiceable")
            params["isServiceable"] = 1 if (getattr(merged, "isServiceable") if hasattr(merged, "isServiceable") else (merged.get("isServiceable") if isinstance(merged, dict) else None)) else None
        if ((hasattr(merged, "timestamp") and (getattr(merged, "timestamp") if hasattr(merged, "timestamp") else (merged.get("timestamp") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("timestamp") is not None)):
            updates.append("timestamp = :timestamp")
            params["timestamp"] = (getattr(merged, "timestamp") if hasattr(merged, "timestamp") else (merged.get("timestamp") if isinstance(merged, dict) else None))

        set_sql = ", ".join(updates)
        factory = self._factory()
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pid},
            )
            await session.commit()
            return res.rowcount > 0

class MySQLSystemSettingsDAO:
    TABLE = "sj_system_settings"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_dict(self, row) -> Any:
        return SystemSettingsResponse(**{
            "_id": str(row.id),
            "id": row.id,
            "external_id": row.external_id,
            "maintenanceMode": bool(row.maintenance_mode) if getattr(row, "maintenance_mode", None) is not None else False,
            "allowSignups": bool(row.allow_signups) if getattr(row, "allow_signups", None) is not None else False,
            "maxUploadSizeMb": row.max_upload_size_mb,
            "defaultCurrency": row.default_currency,
            "timezone": row.timezone,

            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        })

    async def findAll(self, query: Optional[Dict] = None) -> List[SystemSettingsResponse]:
        query = query or {}
        where_clauses = []
        params = {}
        if "maintenanceMode" in query:
            where_clauses.append("maintenance_mode = :maintenanceMode")
            params["maintenanceMode"] = 1 if query["maintenanceMode"] else None
        if "allowSignups" in query:
            where_clauses.append("allow_signups = :allowSignups")
            params["allowSignups"] = 1 if query["allowSignups"] else None
        if "maxUploadSizeMb" in query:
            where_clauses.append("max_upload_size_mb = :maxUploadSizeMb")
            params["maxUploadSizeMb"] = query["maxUploadSizeMb"]
        if "defaultCurrency" in query:
            where_clauses.append("default_currency = :defaultCurrency")
            params["defaultCurrency"] = query["defaultCurrency"]
        if "timezone" in query:
            where_clauses.append("timezone = :timezone")
            params["timezone"] = query["timezone"]

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        factory = self._factory()
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"),
                    params,
                )
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    async def findOne(self, query: Dict) -> Optional[SystemSettingsResponse]:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[SystemSettingsResponse]:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        return self._row_to_dict(row) if row else None

    async def create(self, data: SystemSettingsInternalCreate) -> Any:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if ((hasattr(data, "maintenanceMode") and (getattr(data, "maintenanceMode") if hasattr(data, "maintenanceMode") else (data.get("maintenanceMode") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("maintenanceMode") is not None)):
            cols.append("maintenance_mode")
            vals.append(":maintenanceMode")
            params["maintenanceMode"] = 1 if (getattr(data, "maintenanceMode") if hasattr(data, "maintenanceMode") else (data.get("maintenanceMode") if isinstance(data, dict) else None)) else 0
        if ((hasattr(data, "allowSignups") and (getattr(data, "allowSignups") if hasattr(data, "allowSignups") else (data.get("allowSignups") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("allowSignups") is not None)):
            cols.append("allow_signups")
            vals.append(":allowSignups")
            params["allowSignups"] = 1 if (getattr(data, "allowSignups") if hasattr(data, "allowSignups") else (data.get("allowSignups") if isinstance(data, dict) else None)) else 0
        if ((hasattr(data, "maxUploadSizeMb") and (getattr(data, "maxUploadSizeMb") if hasattr(data, "maxUploadSizeMb") else (data.get("maxUploadSizeMb") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("maxUploadSizeMb") is not None)):
            cols.append("max_upload_size_mb")
            vals.append(":maxUploadSizeMb")
            params["maxUploadSizeMb"] = (getattr(data, "maxUploadSizeMb") if hasattr(data, "maxUploadSizeMb") else (data.get("maxUploadSizeMb") if isinstance(data, dict) else None))
        if ((hasattr(data, "defaultCurrency") and (getattr(data, "defaultCurrency") if hasattr(data, "defaultCurrency") else (data.get("defaultCurrency") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("defaultCurrency") is not None)):
            cols.append("default_currency")
            vals.append(":defaultCurrency")
            params["defaultCurrency"] = (getattr(data, "defaultCurrency") if hasattr(data, "defaultCurrency") else (data.get("defaultCurrency") if isinstance(data, dict) else None))
        if ((hasattr(data, "timezone") and (getattr(data, "timezone") if hasattr(data, "timezone") else (data.get("timezone") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("timezone") is not None)):
            cols.append("timezone")
            vals.append(":timezone")
            params["timezone"] = (getattr(data, "timezone") if hasattr(data, "timezone") else (data.get("timezone") if isinstance(data, dict) else None))

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        async with factory() as session:
            await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = (await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": ext_id})).scalar()
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, data: SystemSettingsInternalUpdate) -> Optional[Any]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = SystemSettingsInternalUpdate(**{**(existing.model_dump(by_alias=True) if hasattr(existing, "model_dump") else existing), **(data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data)})
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if ((hasattr(merged, "maintenanceMode") and (getattr(merged, "maintenanceMode") if hasattr(merged, "maintenanceMode") else (merged.get("maintenanceMode") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("maintenanceMode") is not None)):
            updates.append("maintenance_mode = :maintenanceMode")
            params["maintenanceMode"] = 1 if (getattr(merged, "maintenanceMode") if hasattr(merged, "maintenanceMode") else (merged.get("maintenanceMode") if isinstance(merged, dict) else None)) else None
        if ((hasattr(merged, "allowSignups") and (getattr(merged, "allowSignups") if hasattr(merged, "allowSignups") else (merged.get("allowSignups") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("allowSignups") is not None)):
            updates.append("allow_signups = :allowSignups")
            params["allowSignups"] = 1 if (getattr(merged, "allowSignups") if hasattr(merged, "allowSignups") else (merged.get("allowSignups") if isinstance(merged, dict) else None)) else None
        if ((hasattr(merged, "maxUploadSizeMb") and (getattr(merged, "maxUploadSizeMb") if hasattr(merged, "maxUploadSizeMb") else (merged.get("maxUploadSizeMb") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("maxUploadSizeMb") is not None)):
            updates.append("max_upload_size_mb = :maxUploadSizeMb")
            params["maxUploadSizeMb"] = (getattr(merged, "maxUploadSizeMb") if hasattr(merged, "maxUploadSizeMb") else (merged.get("maxUploadSizeMb") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "defaultCurrency") and (getattr(merged, "defaultCurrency") if hasattr(merged, "defaultCurrency") else (merged.get("defaultCurrency") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("defaultCurrency") is not None)):
            updates.append("default_currency = :defaultCurrency")
            params["defaultCurrency"] = (getattr(merged, "defaultCurrency") if hasattr(merged, "defaultCurrency") else (merged.get("defaultCurrency") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "timezone") and (getattr(merged, "timezone") if hasattr(merged, "timezone") else (merged.get("timezone") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("timezone") is not None)):
            updates.append("timezone = :timezone")
            params["timezone"] = (getattr(merged, "timezone") if hasattr(merged, "timezone") else (merged.get("timezone") if isinstance(merged, dict) else None))

        set_sql = ", ".join(updates)
        factory = self._factory()
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pid},
            )
            await session.commit()
            return res.rowcount > 0

class MySQLValetPayoutSettingsDAO:
    TABLE = "sj_valet_payout_settings"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_dict(self, row) -> Dict:
        return {
            "_id": str(row.id),
            "id": row.id,
            "external_id": row.external_id,
            "deliveryChargePerOrder": row.delivery_charge_per_order,
            "returnPickupChargePerOrder": row.return_pickup_charge_per_order,

            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        }

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        query = query or {}
        where_clauses = []
        params = {}
        if "deliveryChargePerOrder" in query:
            where_clauses.append("delivery_charge_per_order = :deliveryChargePerOrder")
            params["deliveryChargePerOrder"] = query["deliveryChargePerOrder"]
        if "returnPickupChargePerOrder" in query:
            where_clauses.append("return_pickup_charge_per_order = :returnPickupChargePerOrder")
            params["returnPickupChargePerOrder"] = query["returnPickupChargePerOrder"]

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        factory = self._factory()
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"),
                    params,
                )
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    async def findOne(self, query: Dict) -> Optional[Dict]:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        return self._row_to_dict(row) if row else None

    async def create(self, data: ValetPayoutSettingsInternalCreate) -> Dict:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if ((hasattr(data, "deliveryChargePerOrder") and (getattr(data, "deliveryChargePerOrder") if hasattr(data, "deliveryChargePerOrder") else (data.get("deliveryChargePerOrder") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("deliveryChargePerOrder") is not None)):
            cols.append("delivery_charge_per_order")
            vals.append(":deliveryChargePerOrder")
            params["deliveryChargePerOrder"] = (getattr(data, "deliveryChargePerOrder") if hasattr(data, "deliveryChargePerOrder") else (data.get("deliveryChargePerOrder") if isinstance(data, dict) else None))
        if ((hasattr(data, "returnPickupChargePerOrder") and (getattr(data, "returnPickupChargePerOrder") if hasattr(data, "returnPickupChargePerOrder") else (data.get("returnPickupChargePerOrder") if isinstance(data, dict) else None)) is not None) or (isinstance(data, dict) and data.get("returnPickupChargePerOrder") is not None)):
            cols.append("return_pickup_charge_per_order")
            vals.append(":returnPickupChargePerOrder")
            params["returnPickupChargePerOrder"] = (getattr(data, "returnPickupChargePerOrder") if hasattr(data, "returnPickupChargePerOrder") else (data.get("returnPickupChargePerOrder") if isinstance(data, dict) else None))

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        async with factory() as session:
            await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = (await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": ext_id})).scalar()
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, data: Dict) -> Optional[Dict]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = SystemSettingsInternalUpdate(**{**existing, **(data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data)})
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if ((hasattr(merged, "deliveryChargePerOrder") and (getattr(merged, "deliveryChargePerOrder") if hasattr(merged, "deliveryChargePerOrder") else (merged.get("deliveryChargePerOrder") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("deliveryChargePerOrder") is not None)):
            updates.append("delivery_charge_per_order = :deliveryChargePerOrder")
            params["deliveryChargePerOrder"] = (getattr(merged, "deliveryChargePerOrder") if hasattr(merged, "deliveryChargePerOrder") else (merged.get("deliveryChargePerOrder") if isinstance(merged, dict) else None))
        if ((hasattr(merged, "returnPickupChargePerOrder") and (getattr(merged, "returnPickupChargePerOrder") if hasattr(merged, "returnPickupChargePerOrder") else (merged.get("returnPickupChargePerOrder") if isinstance(merged, dict) else None)) is not None) or (isinstance(merged, dict) and merged.get("returnPickupChargePerOrder") is not None)):
            updates.append("return_pickup_charge_per_order = :returnPickupChargePerOrder")
            params["returnPickupChargePerOrder"] = (getattr(merged, "returnPickupChargePerOrder") if hasattr(merged, "returnPickupChargePerOrder") else (merged.get("returnPickupChargePerOrder") if isinstance(merged, dict) else None))

        set_sql = ", ".join(updates)
        factory = self._factory()
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pid},
            )
            await session.commit()
            return res.rowcount > 0

# Collection name -> Strict DAO instance
FLAT_DAOS = {
    "returnSettings": MySQLReturnSettingsDAO(),
    "orderFeedback": MySQLOrderFeedbackDAO(),
    "promoStrips": MySQLPromoStripsDAO(),
    "pushNotifications": MySQLPushNotificationsDAO(),
    "coachMarks": MySQLCoachMarksDAO(),
    "categoryTags": MySQLCategoryTagsDAO(),
    "google_reviews": MySQLGoogle_reviewsDAO(),
    "stockReservations": MySQLStockReservationsDAO(),
    "productNotifications": MySQLProductNotificationsDAO(),
    "productReviews": MySQLProductReviewsDAO(),
    "classificationTags": MySQLClassificationTagsDAO(),
    "reviewClassifications": MySQLReviewClassificationsDAO(),
    "aboutUs": MySQLAboutUsDAO(),
    "privacyPolicy": MySQLPrivacyPolicyDAO(),
    "availabilityRequests": MySQLAvailabilityRequestsDAO(),
    "pincodeSearches": MySQLPincodeSearchesDAO(),
    "systemSettings": MySQLSystemSettingsDAO(),
    "valetPayoutSettings": MySQLValetPayoutSettingsDAO(),
}



