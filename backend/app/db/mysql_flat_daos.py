"""
Strict SQLAlchemy DAOs replacing MySQLTypedDocDAO and DocStore patterns.
"""

import secrets
from typing import Dict, List, Optional
from app.models.schemas import PromoStripResponse, OrderFeedbackResponse, ProductReviewResponse, ClassificationTagResponse, AvailabilityRequestResponse
from app.routers.category_tags import CategoryTagResponse
from app.routers.system_settings import SystemSettingsResponse
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

    async def create(self, data: Dict) -> Dict:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if "returnDays" in data:
            cols.append("return_days")
            vals.append(":returnDays")
            params["returnDays"] = data.returnDays

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
        merged = {**existing, **data}
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if "returnDays" in merged:
            updates.append("return_days = :returnDays")
            params["returnDays"] = merged.returnDays

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

    async def create(self, data: Dict) -> OrderFeedbackResponse:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if "orderId" in data:
            cols.append("order_id")
            vals.append(":orderId")
            params["orderId"] = data.orderId
        if "userId" in data:
            cols.append("user_id")
            vals.append(":userId")
            params["userId"] = data.userId
        if "rating" in data:
            cols.append("rating")
            vals.append(":rating")
            params["rating"] = data.rating
        if "comment" in data:
            cols.append("comments")
            vals.append(":comment")
            params["comment"] = data.comment
        if "deliveryRating" in data:
            cols.append("delivery_rating")
            vals.append(":deliveryRating")
            params["deliveryRating"] = data.deliveryRating
        if "deliveryComment" in data:
            cols.append("delivery_comment")
            vals.append(":deliveryComment")
            params["deliveryComment"] = data.deliveryComment
        if "feedbackType" in data:
            cols.append("feedback_type")
            vals.append(":feedbackType")
            params["feedbackType"] = data.feedbackType

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

    async def update(self, id: str, data: Dict) -> Optional[OrderFeedbackResponse]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = {**existing, **data}
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if "orderId" in merged:
            updates.append("order_id = :orderId")
            params["orderId"] = merged.orderId
        if "userId" in merged:
            updates.append("user_id = :userId")
            params["userId"] = merged.userId
        if "rating" in merged:
            updates.append("rating = :rating")
            params["rating"] = merged.rating
        if "comment" in merged:
            updates.append("comments = :comment")
            params["comment"] = merged.comment
        if "deliveryRating" in merged:
            updates.append("delivery_rating = :deliveryRating")
            params["deliveryRating"] = merged.deliveryRating
        if "deliveryComment" in merged:
            updates.append("delivery_comment = :deliveryComment")
            params["deliveryComment"] = merged.deliveryComment
        if "feedbackType" in merged:
            updates.append("feedback_type = :feedbackType")
            params["feedbackType"] = merged.feedbackType

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

    async def create(self, data: Dict) -> PromoStripResponse:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if "text" in data:
            cols.append("text")
            vals.append(":text")
            params["text"] = data.text
        if "isActive" in data:
            cols.append("is_active")
            vals.append(":isActive")
            params["isActive"] = 1 if data.isActive else 0

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

    async def update(self, id: str, data: Dict) -> Optional[PromoStripResponse]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = {**existing, **data}
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if "text" in merged:
            updates.append("text = :text")
            params["text"] = merged.text
        if "isActive" in merged:
            updates.append("is_active = :isActive")
            params["isActive"] = 1 if merged.isActive else None

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

    async def create(self, data: Dict) -> Dict:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if "title" in data:
            cols.append("title")
            vals.append(":title")
            params["title"] = data.title
        if "message" in data:
            cols.append("message")
            vals.append(":message")
            params["message"] = data.message
        if "link" in data:
            cols.append("link")
            vals.append(":link")
            params["link"] = data.link
        if "image" in data:
            cols.append("image")
            vals.append(":image")
            params["image"] = data.image
        if "status" in data:
            cols.append("status")
            vals.append(":status")
            params["status"] = data.status
        if "scheduledFor" in data:
            cols.append("scheduled_for")
            vals.append(":scheduledFor")
            params["scheduledFor"] = data.scheduledFor
        if "deliveredCount" in data:
            cols.append("delivered_count")
            vals.append(":deliveredCount")
            params["deliveredCount"] = data.deliveredCount
        if "readCount" in data:
            cols.append("read_count")
            vals.append(":readCount")
            params["readCount"] = data.readCount
        if "userSegment" in data:
            cols.append("user_segment")
            vals.append(":userSegment")
            params["userSegment"] = data.userSegment
        if "userBehavior" in data:
            cols.append("user_behavior")
            vals.append(":userBehavior")
            params["userBehavior"] = data.userBehavior
        if "createdBy" in data:
            cols.append("created_by")
            vals.append(":createdBy")
            params["createdBy"] = data.createdBy

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
        merged = {**existing, **data}
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if "title" in merged:
            updates.append("title = :title")
            params["title"] = merged.title
        if "message" in merged:
            updates.append("message = :message")
            params["message"] = merged.message
        if "link" in merged:
            updates.append("link = :link")
            params["link"] = merged.link
        if "image" in merged:
            updates.append("image = :image")
            params["image"] = merged.image
        if "status" in merged:
            updates.append("status = :status")
            params["status"] = merged.status
        if "scheduledFor" in merged:
            updates.append("scheduled_for = :scheduledFor")
            params["scheduledFor"] = merged.scheduledFor
        if "deliveredCount" in merged:
            updates.append("delivered_count = :deliveredCount")
            params["deliveredCount"] = merged.deliveredCount
        if "readCount" in merged:
            updates.append("read_count = :readCount")
            params["readCount"] = merged.readCount
        if "userSegment" in merged:
            updates.append("user_segment = :userSegment")
            params["userSegment"] = merged.userSegment
        if "userBehavior" in merged:
            updates.append("user_behavior = :userBehavior")
            params["userBehavior"] = merged.userBehavior
        if "createdBy" in merged:
            updates.append("created_by = :createdBy")
            params["createdBy"] = merged.createdBy

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

    async def create(self, data: Dict) -> Dict:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if "anchorId" in data:
            cols.append("anchor_id")
            vals.append(":anchorId")
            params["anchorId"] = data.anchorId
        if "title" in data:
            cols.append("title")
            vals.append(":title")
            params["title"] = data.title
        if "description" in data:
            cols.append("description")
            vals.append(":description")
            params["description"] = data.description
        if "screenName" in data:
            cols.append("screen_name")
            vals.append(":screenName")
            params["screenName"] = data.screenName
        if "sequenceOrder" in data:
            cols.append("sequence_order")
            vals.append(":sequenceOrder")
            params["sequenceOrder"] = data.sequenceOrder
        if "isActive" in data:
            cols.append("is_active")
            vals.append(":isActive")
            params["isActive"] = 1 if data.isActive else 0

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
        merged = {**existing, **data}
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if "anchorId" in merged:
            updates.append("anchor_id = :anchorId")
            params["anchorId"] = merged.anchorId
        if "title" in merged:
            updates.append("title = :title")
            params["title"] = merged.title
        if "description" in merged:
            updates.append("description = :description")
            params["description"] = merged.description
        if "screenName" in merged:
            updates.append("screen_name = :screenName")
            params["screenName"] = merged.screenName
        if "sequenceOrder" in merged:
            updates.append("sequence_order = :sequenceOrder")
            params["sequenceOrder"] = merged.sequenceOrder
        if "isActive" in merged:
            updates.append("is_active = :isActive")
            params["isActive"] = 1 if merged.isActive else None

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

    def _row_to_dict(self, row) -> CategoryTagResponse:
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

    async def create(self, data: Dict) -> CategoryTagResponse:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if "name" in data:
            cols.append("name")
            vals.append(":name")
            params["name"] = data.name
        if "description" in data:
            cols.append("description")
            vals.append(":description")
            params["description"] = data.description
        if "isActive" in data:
            cols.append("is_active")
            vals.append(":isActive")
            params["isActive"] = 1 if data.isActive else 0

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

    async def update(self, id: str, data: Dict) -> Optional[CategoryTagResponse]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = {**existing, **data}
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if "name" in merged:
            updates.append("name = :name")
            params["name"] = merged.name
        if "description" in merged:
            updates.append("description = :description")
            params["description"] = merged.description
        if "isActive" in merged:
            updates.append("is_active = :isActive")
            params["isActive"] = 1 if merged.isActive else None

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

    async def create(self, data: Dict) -> Dict:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if "rating" in data:
            cols.append("rating")
            vals.append(":rating")
            params["rating"] = data.rating
        if "reviewCount" in data:
            cols.append("review_count")
            vals.append(":reviewCount")
            params["reviewCount"] = data.reviewCount
        if "lastUpdated" in data:
            cols.append("last_updated")
            vals.append(":lastUpdated")
            params["lastUpdated"] = data.lastUpdated
        if "method" in data:
            cols.append("method")
            vals.append(":method")
            params["method"] = data.method

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
        merged = {**existing, **data}
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if "rating" in merged:
            updates.append("rating = :rating")
            params["rating"] = merged.rating
        if "reviewCount" in merged:
            updates.append("review_count = :reviewCount")
            params["reviewCount"] = merged.reviewCount
        if "lastUpdated" in merged:
            updates.append("last_updated = :lastUpdated")
            params["lastUpdated"] = merged.lastUpdated
        if "method" in merged:
            updates.append("method = :method")
            params["method"] = merged.method

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

    async def create(self, data: Dict) -> StockReservation:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if "productId" in data:
            cols.append("product_id")
            vals.append(":productId")
            params["productId"] = data.productId
        if "userId" in data:
            cols.append("user_id")
            vals.append(":userId")
            params["userId"] = data.userId
        if "quantity" in data:
            cols.append("quantity")
            vals.append(":quantity")
            params["quantity"] = data.quantity
        if "status" in data:
            cols.append("status")
            vals.append(":status")
            params["status"] = data.status
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

    async def update(self, id: str, data: Dict) -> Optional[StockReservation]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = {**existing.model_dump(by_alias=True), **data}
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if "productId" in merged:
            updates.append("product_id = :productId")
            params["productId"] = merged.productId
        if "userId" in merged:
            updates.append("user_id = :userId")
            params["userId"] = merged.userId
        if "quantity" in merged:
            updates.append("quantity = :quantity")
            params["quantity"] = merged.quantity
        if "status" in merged:
            updates.append("status = :status")
            params["status"] = merged.status
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

    async def create(self, data: Dict) -> Dict:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if "productId" in data:
            cols.append("product_id")
            vals.append(":productId")
            params["productId"] = data.productId
        if "userId" in data:
            cols.append("user_id")
            vals.append(":userId")
            params["userId"] = data.userId
        if "email" in data:
            cols.append("email")
            vals.append(":email")
            params["email"] = data.email
        if "phone" in data:
            cols.append("phone")
            vals.append(":phone")
            params["phone"] = data.phone
        if "status" in data:
            cols.append("status")
            vals.append(":status")
            params["status"] = data.status

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
        merged = {**existing, **data}
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if "productId" in merged:
            updates.append("product_id = :productId")
            params["productId"] = merged.productId
        if "userId" in merged:
            updates.append("user_id = :userId")
            params["userId"] = merged.userId
        if "email" in merged:
            updates.append("email = :email")
            params["email"] = merged.email
        if "phone" in merged:
            updates.append("phone = :phone")
            params["phone"] = merged.phone
        if "status" in merged:
            updates.append("status = :status")
            params["status"] = merged.status

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

    async def create(self, data: Dict) -> ProductReviewResponse:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if "productId" in data:
            cols.append("product_id")
            vals.append(":productId")
            params["productId"] = data.productId
        if "userId" in data:
            cols.append("user_id")
            vals.append(":userId")
            params["userId"] = data.userId
        if "rating" in data:
            cols.append("rating")
            vals.append(":rating")
            params["rating"] = data.rating
        if "reviewText" in data:
            cols.append("review_text")
            vals.append(":reviewText")
            params["reviewText"] = data.reviewText
        if "status" in data:
            cols.append("status")
            vals.append(":status")
            params["status"] = data.status

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

    async def update(self, id: str, data: Dict) -> Optional[ProductReviewResponse]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = {**existing, **data}
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if "productId" in merged:
            updates.append("product_id = :productId")
            params["productId"] = merged.productId
        if "userId" in merged:
            updates.append("user_id = :userId")
            params["userId"] = merged.userId
        if "rating" in merged:
            updates.append("rating = :rating")
            params["rating"] = merged.rating
        if "reviewText" in merged:
            updates.append("review_text = :reviewText")
            params["reviewText"] = merged.reviewText
        if "status" in merged:
            updates.append("status = :status")
            params["status"] = merged.status

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

    async def create(self, data: Dict) -> ProductReviewResponse:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if "name" in data:
            cols.append("name")
            vals.append(":name")
            params["name"] = data.name
        if "isActive" in data:
            cols.append("is_active")
            vals.append(":isActive")
            params["isActive"] = 1 if data.isActive else 0

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

    async def update(self, id: str, data: Dict) -> Optional[ProductReviewResponse]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = {**existing, **data}
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if "name" in merged:
            updates.append("name = :name")
            params["name"] = merged.name
        if "isActive" in merged:
            updates.append("is_active = :isActive")
            params["isActive"] = 1 if merged.isActive else None

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

    async def create(self, data: Dict) -> ClassificationTagResponse:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if "reviewId" in data:
            cols.append("review_id")
            vals.append(":reviewId")
            params["reviewId"] = data.reviewId
        if "category" in data:
            cols.append("category")
            vals.append(":category")
            params["category"] = data.category
        if "confidenceScore" in data:
            cols.append("confidence_score")
            vals.append(":confidenceScore")
            params["confidenceScore"] = data.confidenceScore
        if "sentiment" in data:
            cols.append("sentiment")
            vals.append(":sentiment")
            params["sentiment"] = data.sentiment

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

    async def update(self, id: str, data: Dict) -> Optional[ClassificationTagResponse]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = {**existing, **data}
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if "reviewId" in merged:
            updates.append("review_id = :reviewId")
            params["reviewId"] = merged.reviewId
        if "category" in merged:
            updates.append("category = :category")
            params["category"] = merged.category
        if "confidenceScore" in merged:
            updates.append("confidence_score = :confidenceScore")
            params["confidenceScore"] = merged.confidenceScore
        if "sentiment" in merged:
            updates.append("sentiment = :sentiment")
            params["sentiment"] = merged.sentiment

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

    async def create(self, data: Dict) -> Any:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if "title" in data:
            cols.append("title")
            vals.append(":title")
            params["title"] = data.title
        if "content" in data:
            cols.append("content")
            vals.append(":content")
            params["content"] = data.content
        if "version" in data:
            cols.append("version")
            vals.append(":version")
            params["version"] = data.version
        if "isPublished" in data:
            cols.append("is_published")
            vals.append(":isPublished")
            params["isPublished"] = 1 if data.isPublished else 0

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

    async def update(self, id: str, data: Dict) -> Optional[Any]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = {**existing, **data}
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if "title" in merged:
            updates.append("title = :title")
            params["title"] = merged.title
        if "content" in merged:
            updates.append("content = :content")
            params["content"] = merged.content
        if "version" in merged:
            updates.append("version = :version")
            params["version"] = merged.version
        if "isPublished" in merged:
            updates.append("is_published = :isPublished")
            params["isPublished"] = 1 if merged.isPublished else None

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

    async def create(self, data: Dict) -> Any:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if "version" in data:
            cols.append("version")
            vals.append(":version")
            params["version"] = data.version
        if "content" in data:
            cols.append("content")
            vals.append(":content")
            params["content"] = data.content
        if "effectiveDate" in data:
            cols.append("effective_date")
            vals.append(":effectiveDate")
            params["effectiveDate"] = data.effectiveDate
        if "isActive" in data:
            cols.append("is_active")
            vals.append(":isActive")
            params["isActive"] = 1 if data.isActive else 0

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

    async def update(self, id: str, data: Dict) -> Optional[Any]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = {**existing, **data}
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if "version" in merged:
            updates.append("version = :version")
            params["version"] = merged.version
        if "content" in merged:
            updates.append("content = :content")
            params["content"] = merged.content
        if "effectiveDate" in merged:
            updates.append("effective_date = :effectiveDate")
            params["effectiveDate"] = merged.effectiveDate
        if "isActive" in merged:
            updates.append("is_active = :isActive")
            params["isActive"] = 1 if merged.isActive else None

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

    async def create(self, data: Dict) -> AvailabilityRequestResponse:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if "productId" in data:
            cols.append("product_id")
            vals.append(":productId")
            params["productId"] = data.productId
        if "productName" in data:
            cols.append("product_name")
            vals.append(":productName")
            params["productName"] = data.productName
        if "pincode" in data:
            cols.append("pincode")
            vals.append(":pincode")
            params["pincode"] = data.pincode
        if "userName" in data:
            cols.append("user_name")
            vals.append(":userName")
            params["userName"] = data.userName
        if "userEmail" in data:
            cols.append("user_email")
            vals.append(":userEmail")
            params["userEmail"] = data.userEmail

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

    async def update(self, id: str, data: Dict) -> Optional[AvailabilityRequestResponse]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = {**existing, **data}
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if "productId" in merged:
            updates.append("product_id = :productId")
            params["productId"] = merged.productId
        if "productName" in merged:
            updates.append("product_name = :productName")
            params["productName"] = merged.productName
        if "pincode" in merged:
            updates.append("pincode = :pincode")
            params["pincode"] = merged.pincode
        if "userName" in merged:
            updates.append("user_name = :userName")
            params["userName"] = merged.userName
        if "userEmail" in merged:
            updates.append("user_email = :userEmail")
            params["userEmail"] = merged.userEmail

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

    async def create(self, data: Dict) -> Any:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if "pincode" in data:
            cols.append("pincode")
            vals.append(":pincode")
            params["pincode"] = data.pincode
        if "query" in data:
            cols.append("query")
            vals.append(":query")
            params["query"] = data.query
        if "isServiceable" in data:
            cols.append("is_serviceable")
            vals.append(":isServiceable")
            params["isServiceable"] = 1 if data.isServiceable else 0
        if "timestamp" in data:
            cols.append("timestamp")
            vals.append(":timestamp")
            params["timestamp"] = data.timestamp

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

    async def update(self, id: str, data: Dict) -> Optional[Any]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = {**existing, **data}
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if "pincode" in merged:
            updates.append("pincode = :pincode")
            params["pincode"] = merged.pincode
        if "query" in merged:
            updates.append("query = :query")
            params["query"] = merged.query
        if "isServiceable" in merged:
            updates.append("is_serviceable = :isServiceable")
            params["isServiceable"] = 1 if merged.isServiceable else None
        if "timestamp" in merged:
            updates.append("timestamp = :timestamp")
            params["timestamp"] = merged.timestamp

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

    def _row_to_dict(self, row) -> SystemSettingsResponse:
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

    async def create(self, data: Dict) -> SystemSettingsResponse:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if "maintenanceMode" in data:
            cols.append("maintenance_mode")
            vals.append(":maintenanceMode")
            params["maintenanceMode"] = 1 if data.maintenanceMode else 0
        if "allowSignups" in data:
            cols.append("allow_signups")
            vals.append(":allowSignups")
            params["allowSignups"] = 1 if data.allowSignups else 0
        if "maxUploadSizeMb" in data:
            cols.append("max_upload_size_mb")
            vals.append(":maxUploadSizeMb")
            params["maxUploadSizeMb"] = data.maxUploadSizeMb
        if "defaultCurrency" in data:
            cols.append("default_currency")
            vals.append(":defaultCurrency")
            params["defaultCurrency"] = data.defaultCurrency
        if "timezone" in data:
            cols.append("timezone")
            vals.append(":timezone")
            params["timezone"] = data.timezone

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

    async def update(self, id: str, data: Dict) -> Optional[SystemSettingsResponse]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = {**existing, **data}
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if "maintenanceMode" in merged:
            updates.append("maintenance_mode = :maintenanceMode")
            params["maintenanceMode"] = 1 if merged.maintenanceMode else None
        if "allowSignups" in merged:
            updates.append("allow_signups = :allowSignups")
            params["allowSignups"] = 1 if merged.allowSignups else None
        if "maxUploadSizeMb" in merged:
            updates.append("max_upload_size_mb = :maxUploadSizeMb")
            params["maxUploadSizeMb"] = merged.maxUploadSizeMb
        if "defaultCurrency" in merged:
            updates.append("default_currency = :defaultCurrency")
            params["defaultCurrency"] = merged.defaultCurrency
        if "timezone" in merged:
            updates.append("timezone = :timezone")
            params["timezone"] = merged.timezone

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

    async def create(self, data: Dict) -> Dict:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if "deliveryChargePerOrder" in data:
            cols.append("delivery_charge_per_order")
            vals.append(":deliveryChargePerOrder")
            params["deliveryChargePerOrder"] = data.deliveryChargePerOrder
        if "returnPickupChargePerOrder" in data:
            cols.append("return_pickup_charge_per_order")
            vals.append(":returnPickupChargePerOrder")
            params["returnPickupChargePerOrder"] = data.returnPickupChargePerOrder

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
        merged = {**existing, **data}
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if "deliveryChargePerOrder" in merged:
            updates.append("delivery_charge_per_order = :deliveryChargePerOrder")
            params["deliveryChargePerOrder"] = merged.deliveryChargePerOrder
        if "returnPickupChargePerOrder" in merged:
            updates.append("return_pickup_charge_per_order = :returnPickupChargePerOrder")
            params["returnPickupChargePerOrder"] = merged.returnPickupChargePerOrder

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

