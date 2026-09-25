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

    def __map_to_schema(self, row) -> Dict:
        return {
            "_id": str(row.id),
            "id": row.id,
            "external_id": row.external_id,
            "returnDays": row.return_days,

            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        }

    async def findAll(self, query: Optional[Dict] = None) -> List[Google_reviewsInternal]:
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
        return [self.__map_to_schema(r) for r in rows]

    async def findOne(self, query: Dict) -> Any:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Any:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        return self.__map_to_schema(row) if row else None

    async def create(self, data: ReturnSettingsInternalCreate) -> Dict:

        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if data.return_days is not None:
            cols.append("return_days")
            vals.append(":returnDays")
            params["returnDays"] = data.return_days

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
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if data.return_days is not None:
            updates.append("return_days = :returnDays")
            params["returnDays"] = data.return_days

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

    def __map_to_schema(self, row) -> OrderFeedbackResponse:
        return OrderFeedbackResponse(
            _id=str(row.id),
            id=row.id,
            external_id=row.external_id,
            orderId=row.order_id,
            userId=row.user_id,
            rating=row.rating,
            comment=row.comments,
            deliveryRating=row.delivery_rating,
            deliveryComment=row.delivery_comment,
            feedbackType=row.feedback_type,

            createdAt=row.created_at.isoformat() if row.created_at else None,
            updatedAt=row.updated_at.isoformat() if row.updated_at else None,
        )

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
        return [self.__map_to_schema(r) for r in rows]

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
        return self.__map_to_schema(row) if row else None

    async def create(self, data: OrderFeedbackInternalCreate) -> OrderFeedbackResponse:

        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if data.order_id is not None:
            cols.append("order_id")
            vals.append(":orderId")
            params["orderId"] = data.order_id
        if data.userId is not None:
            cols.append("user_id")
            vals.append(":userId")
            params["userId"] = data.userId
        if data.rating is not None:
            cols.append("rating")
            vals.append(":rating")
            params["rating"] = data.rating
        if data.comment is not None:
            cols.append("comments")
            vals.append(":comment")
            params["comment"] = data.comment
        if data.delivery_rating is not None:
            cols.append("delivery_rating")
            vals.append(":deliveryRating")
            params["deliveryRating"] = data.delivery_rating
        if data.delivery_comment is not None:
            cols.append("delivery_comment")
            vals.append(":deliveryComment")
            params["deliveryComment"] = data.delivery_comment
        if data.feedback_type is not None:
            cols.append("feedback_type")
            vals.append(":feedbackType")
            params["feedbackType"] = data.feedback_type

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
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if data.order_id is not None:
            updates.append("order_id = :orderId")
            params["orderId"] = data.order_id
        if data.userId is not None:
            updates.append("user_id = :userId")
            params["userId"] = data.userId
        if data.rating is not None:
            updates.append("rating = :rating")
            params["rating"] = data.rating
        if data.comment is not None:
            updates.append("comments = :comment")
            params["comment"] = data.comment
        if data.delivery_rating is not None:
            updates.append("delivery_rating = :deliveryRating")
            params["deliveryRating"] = data.delivery_rating
        if data.delivery_comment is not None:
            updates.append("delivery_comment = :deliveryComment")
            params["deliveryComment"] = data.delivery_comment
        if data.feedback_type is not None:
            updates.append("feedback_type = :feedbackType")
            params["feedbackType"] = data.feedback_type

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

    def __map_to_schema(self, row) -> PromoStripResponse:
        return PromoStripResponse(
            _id=str(row.id),
            text=row.text,
            isActive=bool(row.is_active) if ("is_active" in row._mapping and row.is_active is not None) else False,
            createdAt=row.created_at.isoformat() if row.created_at else None,
            updatedAt=row.updated_at.isoformat() if row.updated_at else None,
        )

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
        return [self.__map_to_schema(r) for r in rows]

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
        return self.__map_to_schema(row) if row else None

    async def create(self, data: PromoStripsInternalCreate) -> PromoStripResponse:

        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if data.text is not None:
            cols.append("text")
            vals.append(":text")
            params["text"] = data.text
        if data.isActive is not None:
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

    async def update(self, id: str, data: PromoStripsInternalUpdate) -> Optional[Any]:

        existing = await self.findById(id)
        if not existing:
            return None
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if data.text is not None:
            updates.append("text = :text")
            params["text"] = data.text
        if data.isActive is not None:
            updates.append("is_active = :isActive")
            params["isActive"] = 1 if data.isActive else None

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

    def __map_to_schema(self, row) -> Dict:
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

    async def findAll(self, query: Optional[Dict] = None) -> List[Google_reviewsInternal]:
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
        return [self.__map_to_schema(r) for r in rows]

    async def findOne(self, query: Dict) -> Any:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Any:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        return self.__map_to_schema(row) if row else None

    async def create(self, data: PushNotificationsInternalCreate) -> Dict:

        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if data.title is not None:
            cols.append("title")
            vals.append(":title")
            params["title"] = data.title
        if data.message is not None:
            cols.append("message")
            vals.append(":message")
            params["message"] = data.message
        if data.link is not None:
            cols.append("link")
            vals.append(":link")
            params["link"] = data.link
        if data.image is not None:
            cols.append("image")
            vals.append(":image")
            params["image"] = data.image
        if data.status is not None:
            cols.append("status")
            vals.append(":status")
            params["status"] = data.status
        if data.scheduledFor is not None:
            cols.append("scheduled_for")
            vals.append(":scheduledFor")
            params["scheduledFor"] = data.scheduledFor
        if data.deliveredCount is not None:
            cols.append("delivered_count")
            vals.append(":deliveredCount")
            params["deliveredCount"] = data.deliveredCount
        if data.readCount is not None:
            cols.append("read_count")
            vals.append(":readCount")
            params["readCount"] = data.readCount
        if data.userSegment is not None:
            cols.append("user_segment")
            vals.append(":userSegment")
            params["userSegment"] = data.userSegment
        if data.userBehavior is not None:
            cols.append("user_behavior")
            vals.append(":userBehavior")
            params["userBehavior"] = data.userBehavior
        if data.createdBy is not None:
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

    async def update(self, id: str, data: PushNotificationsInternalUpdate) -> Optional[Any]:

        existing = await self.findById(id)
        if not existing:
            return None
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if data.title is not None:
            updates.append("title = :title")
            params["title"] = data.title
        if data.message is not None:
            updates.append("message = :message")
            params["message"] = data.message
        if data.link is not None:
            updates.append("link = :link")
            params["link"] = data.link
        if data.image is not None:
            updates.append("image = :image")
            params["image"] = data.image
        if data.status is not None:
            updates.append("status = :status")
            params["status"] = data.status
        if data.scheduledFor is not None:
            updates.append("scheduled_for = :scheduledFor")
            params["scheduledFor"] = data.scheduledFor
        if data.deliveredCount is not None:
            updates.append("delivered_count = :deliveredCount")
            params["deliveredCount"] = data.deliveredCount
        if data.readCount is not None:
            updates.append("read_count = :readCount")
            params["readCount"] = data.readCount
        if data.userSegment is not None:
            updates.append("user_segment = :userSegment")
            params["userSegment"] = data.userSegment
        if data.userBehavior is not None:
            updates.append("user_behavior = :userBehavior")
            params["userBehavior"] = data.userBehavior
        if data.createdBy is not None:
            updates.append("created_by = :createdBy")
            params["createdBy"] = data.createdBy

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

    def __map_to_schema(self, row) -> Dict:
        return {
            "_id": str(row.id),
            "id": row.id,
            "external_id": row.external_id,
            "anchorId": row.anchor_id,
            "title": row.title,
            "description": row.description,
            "screenName": row.screen_name,
            "sequenceOrder": row.sequence_order,
            "isActive": bool(row.is_active) if ("is_active" in row._mapping and row.is_active is not None) else False,

            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        }

    async def findAll(self, query: Optional[Dict] = None) -> List[Google_reviewsInternal]:
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
        return [self.__map_to_schema(r) for r in rows]

    async def findOne(self, query: Dict) -> Any:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Any:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        return self.__map_to_schema(row) if row else None

    async def create(self, data: CoachMarksInternalCreate) -> Dict:

        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if data.anchor_id is not None:
            cols.append("anchor_id")
            vals.append(":anchorId")
            params["anchorId"] = data.anchor_id
        if data.title is not None:
            cols.append("title")
            vals.append(":title")
            params["title"] = data.title
        if data.description is not None:
            cols.append("description")
            vals.append(":description")
            params["description"] = data.description
        if data.screen_name is not None:
            cols.append("screen_name")
            vals.append(":screenName")
            params["screenName"] = data.screen_name
        if data.sequence_order is not None:
            cols.append("sequence_order")
            vals.append(":sequenceOrder")
            params["sequenceOrder"] = data.sequence_order
        if data.isActive is not None:
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

    async def update(self, id: str, data: CoachMarksInternalUpdate) -> Optional[Any]:

        existing = await self.findById(id)
        if not existing:
            return None
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if data.anchor_id is not None:
            updates.append("anchor_id = :anchorId")
            params["anchorId"] = data.anchor_id
        if data.title is not None:
            updates.append("title = :title")
            params["title"] = data.title
        if data.description is not None:
            updates.append("description = :description")
            params["description"] = data.description
        if data.screen_name is not None:
            updates.append("screen_name = :screenName")
            params["screenName"] = data.screen_name
        if data.sequence_order is not None:
            updates.append("sequence_order = :sequenceOrder")
            params["sequenceOrder"] = data.sequence_order
        if data.isActive is not None:
            updates.append("is_active = :isActive")
            params["isActive"] = 1 if data.isActive else None

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

    def __map_to_schema(self, row) -> Any:
        return CategoryTagResponse(
            _id=str(row.id),
            id=row.id,
            external_id=row.external_id,
            name=row.name,
            description=row.description,
            isActive=bool(row.is_active) if ("is_active" in row._mapping and row.is_active is not None) else False,

            createdAt=row.created_at.isoformat() if row.created_at else None,
            updatedAt=row.updated_at.isoformat() if row.updated_at else None,
        )

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
        return [self.__map_to_schema(r) for r in rows]

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
        return self.__map_to_schema(row) if row else None

    async def create(self, data: CategoryTagsInternalCreate) -> Any:

        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if data.name is not None:
            cols.append("name")
            vals.append(":name")
            params["name"] = data.name
        if data.description is not None:
            cols.append("description")
            vals.append(":description")
            params["description"] = data.description
        if data.isActive is not None:
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

    async def update(self, id: str, data: CategoryTagsInternalUpdate) -> Optional[Any]:

        existing = await self.findById(id)
        if not existing:
            return None
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if data.name is not None:
            updates.append("name = :name")
            params["name"] = data.name
        if data.description is not None:
            updates.append("description = :description")
            params["description"] = data.description
        if data.isActive is not None:
            updates.append("is_active = :isActive")
            params["isActive"] = 1 if data.isActive else None

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

    def __map_to_schema(self, row) -> Google_reviewsInternal:
        return Google_reviewsInternal(
            id=str(row.id),
            externalId=row.external_id,
            rating=row.rating,
            reviewCount=str(row.review_count) if row.review_count is not None else None,
            lastUpdated=row.last_updated,
            method=row.method,
            createdAt=row.created_at.isoformat() if row.created_at else None,
            updatedAt=row.updated_at.isoformat() if row.updated_at else None,
        )

    async def findAll(self, query: Optional[Dict] = None) -> List[Google_reviewsInternal]:
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
        return [self.__map_to_schema(r) for r in rows]

    async def findOne(self, query: Dict) -> Any:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Any:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        return self.__map_to_schema(row) if row else None

    async def create(self, data: Google_reviewsInternalCreate) -> Google_reviewsInternal:

        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if data.rating is not None:
            cols.append("rating")
            vals.append(":rating")
            params["rating"] = data.rating
        if data.reviewCount is not None:
            cols.append("review_count")
            vals.append(":reviewCount")
            params["reviewCount"] = data.reviewCount
        if data.lastUpdated is not None:
            cols.append("last_updated")
            vals.append(":lastUpdated")
            params["lastUpdated"] = data.lastUpdated
        if data.method is not None:
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

    async def update(self, id: str, data: Google_reviewsInternalUpdate) -> Optional[Google_reviewsInternal]:

        existing = await self.findById(id)
        if not existing:
            return None

        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if data.rating is not None:
            updates.append("rating = :rating")
            params["rating"] = data.rating
        if data.reviewCount is not None:
            updates.append("review_count = :reviewCount")
            params["reviewCount"] = data.reviewCount
        if data.lastUpdated is not None:
            updates.append("last_updated = :lastUpdated")
            params["lastUpdated"] = data.lastUpdated
        if data.method is not None:
            updates.append("method = :method")
            params["method"] = data.method

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
        if data.product_id is not None:
            cols.append("product_id")
            vals.append(":productId")
            params["productId"] = data.product_id
        if data.userId is not None:
            cols.append("user_id")
            vals.append(":userId")
            params["userId"] = data.userId
        if data.quantity is not None:
            cols.append("quantity")
            vals.append(":quantity")
            params["quantity"] = data.quantity
        if data.status is not None:
            cols.append("status")
            vals.append(":status")
            params["status"] = data.status
        if data.expiresAt is not None:
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

    async def update(self, id: str, data: Any) -> Optional[StockReservation]:
        existing = await self.findById(id)
        if not existing:
            return None
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        
        product_id = data.product_id if data.product_id is not None else existing.product_id
        if product_id is not None:
            updates.append("product_id = :productId")
            params["productId"] = product_id
            
        user_id = data.userId if data.userId is not None else existing.user_id
        if user_id is not None:
            updates.append("user_id = :userId")
            params["userId"] = user_id
            
        quantity = data.quantity if data.quantity is not None else existing.quantity
        if quantity is not None:
            updates.append("quantity = :quantity")
            params["quantity"] = quantity
            
        status = data.status if data.status is not None else existing.status
        if status is not None:
            updates.append("status = :status")
            params["status"] = status
            
        expires_at = data.expiresAt if data.expiresAt is not None else existing.expires_at
        if expires_at is not None:
            updates.append("expires_at = :expiresAt")
            params["expiresAt"] = expires_at
        if not updates:
            return existing

        set_clause = ", ".join(updates)
        q = f"UPDATE {self.TABLE} SET {set_clause} WHERE id = :id"
        factory = self._factory()
        async with factory() as session:
            await session.execute(text(q), params)
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

    def __map_to_schema(self, row) -> Dict:
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

    async def findAll(self, query: Optional[Dict] = None) -> List[Google_reviewsInternal]:
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
        return [self.__map_to_schema(r) for r in rows]

    async def findOne(self, query: Dict) -> Any:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Any:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        return self.__map_to_schema(row) if row else None

    async def create(self, data: ProductNotificationsInternalCreate) -> Dict:

        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if data.product_id is not None:
            cols.append("product_id")
            vals.append(":productId")
            params["productId"] = data.product_id
        if data.userId is not None:
            cols.append("user_id")
            vals.append(":userId")
            params["userId"] = data.userId
        if data.email is not None:
            cols.append("email")
            vals.append(":email")
            params["email"] = data.email
        if data.phone is not None:
            cols.append("phone")
            vals.append(":phone")
            params["phone"] = data.phone
        if data.status is not None:
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

    async def update(self, id: str, data: ProductNotificationsInternalUpdate) -> Optional[Any]:

        existing = await self.findById(id)
        if not existing:
            return None
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if data.product_id is not None:
            updates.append("product_id = :productId")
            params["productId"] = data.product_id
        if data.userId is not None:
            updates.append("user_id = :userId")
            params["userId"] = data.userId
        if data.email is not None:
            updates.append("email = :email")
            params["email"] = data.email
        if data.phone is not None:
            updates.append("phone = :phone")
            params["phone"] = data.phone
        if data.status is not None:
            updates.append("status = :status")
            params["status"] = data.status

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

    def __map_to_schema(self, row) -> ProductReviewResponse:
        return ProductReviewResponse(
            _id=str(row.id),
            id=row.id,
            external_id=row.external_id,
            productId=row.product_id,
            userId=row.user_id,
            rating=row.rating,
            reviewText=row.review_text,
            status=row.status,
            userName=getattr(row, "user_name", None),
            classification=getattr(row, "classification", None),

            createdAt=row.created_at.isoformat() if row.created_at else None,
            updatedAt=row.updated_at.isoformat() if row.updated_at else None,
        )

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
        return [self.__map_to_schema(r) for r in rows]

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
        return self.__map_to_schema(row) if row else None

    async def create(self, data: ProductReviewsInternalCreate) -> ProductReviewResponse:

        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if data.product_id is not None:
            cols.append("product_id")
            vals.append(":productId")
            params["productId"] = data.product_id
        if data.userId is not None:
            cols.append("user_id")
            vals.append(":userId")
            params["userId"] = data.userId
        if data.rating is not None:
            cols.append("rating")
            vals.append(":rating")
            params["rating"] = data.rating
        if data.reviewText is not None:
            cols.append("review_text")
            vals.append(":reviewText")
            params["reviewText"] = data.reviewText
        if data.status is not None:
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

    async def update(self, id: str, data: ProductReviewsInternalUpdate) -> Optional[Any]:

        existing = await self.findById(id)
        if not existing:
            return None
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if data.product_id is not None:
            updates.append("product_id = :productId")
            params["productId"] = data.product_id
        if data.userId is not None:
            updates.append("user_id = :userId")
            params["userId"] = data.userId
        if data.rating is not None:
            updates.append("rating = :rating")
            params["rating"] = data.rating
        if data.reviewText is not None:
            updates.append("review_text = :reviewText")
            params["reviewText"] = data.reviewText
        if data.status is not None:
            updates.append("status = :status")
            params["status"] = data.status

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

    def __map_to_schema(self, row) -> ClassificationTagResponse:
        return ClassificationTagResponse(
            _id=str(row.id),
            id=row.id,
            external_id=row.external_id,
            name=row.name,
            isActive=bool(row.is_active),
            createdAt=row.created_at.isoformat() if row.created_at else None,
            updatedAt=row.updated_at.isoformat() if row.updated_at else None,
        )

    async def findAll(self, query: Optional[Dict] = None) -> List[ClassificationTagResponse]:
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
        return [self.__map_to_schema(r) for r in rows]

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
        return self.__map_to_schema(row) if row else None

    async def create(self, data: ClassificationTagsInternalCreate) -> ClassificationTagResponse:


        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if data.name is not None:
            cols.append("name")
            vals.append(":name")
            params["name"] = data.name
        if data.isActive is not None:
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

    async def update(self, id: str, data: ClassificationTagsInternalUpdate) -> Optional[Any]:


        existing = await self.findById(id)
        if not existing:
            return None
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if data.name is not None:
            updates.append("name = :name")
            params["name"] = data.name
        if data.isActive is not None:
            updates.append("is_active = :isActive")
            params["isActive"] = 1 if data.isActive else None

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

    def __map_to_schema(self, row) -> ClassificationTagResponse:
        return ClassificationTagResponse(
            _id=str(row.id),
            id=row.id,
            external_id=row.external_id,
            reviewId=row.review_id,
            category=row.category,
            confidenceScore=row.confidence_score,
            sentiment=row.sentiment,

            createdAt=row.created_at.isoformat() if row.created_at else None,
            updatedAt=row.updated_at.isoformat() if row.updated_at else None,
        )

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
        return [self.__map_to_schema(r) for r in rows]

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
        return self.__map_to_schema(row) if row else None

    async def create(self, data: ReviewClassificationsInternalCreate) -> ClassificationTagResponse:

        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if data.reviewId is not None:
            cols.append("review_id")
            vals.append(":reviewId")
            params["reviewId"] = data.reviewId
        if data.category is not None:
            cols.append("category")
            vals.append(":category")
            params["category"] = data.category
        if data.confidenceScore is not None:
            cols.append("confidence_score")
            vals.append(":confidenceScore")
            params["confidenceScore"] = data.confidenceScore
        if data.sentiment is not None:
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

    async def update(self, id: str, data: ReviewClassificationsInternalUpdate) -> Optional[Any]:

        existing = await self.findById(id)
        if not existing:
            return None
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if data.reviewId is not None:
            updates.append("review_id = :reviewId")
            params["reviewId"] = data.reviewId
        if data.category is not None:
            updates.append("category = :category")
            params["category"] = data.category
        if data.confidenceScore is not None:
            updates.append("confidence_score = :confidenceScore")
            params["confidenceScore"] = data.confidenceScore
        if data.sentiment is not None:
            updates.append("sentiment = :sentiment")
            params["sentiment"] = data.sentiment

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

    def __map_to_schema(self, row) -> AboutUs:
        return AboutUs(
            id=str(row.id),
            external_id=row.external_id,
            title=row.title,
            content=row.content,
            version=row.version,
            is_published=bool(row.is_published) if ("is_published" in row._mapping and row.is_published is not None) else False,
            created_at=row.created_at.isoformat() if row.created_at else None,
            updated_at=row.updated_at.isoformat() if row.updated_at else None,
        )

    async def findAll(self, query: Optional[Dict] = None) -> List[AboutUs]:
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
        return [self.__map_to_schema(r) for r in rows]

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
        return self.__map_to_schema(row) if row else None

    async def create(self, data: AboutUsInternalCreate) -> Any:

        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if data.title is not None:
            cols.append("title")
            vals.append(":title")
            params["title"] = data.title
        if data.content is not None:
            cols.append("content")
            vals.append(":content")
            params["content"] = data.content
        if data.version is not None:
            cols.append("version")
            vals.append(":version")
            params["version"] = data.version
        if data.is_published is not None:
            cols.append("is_published")
            vals.append(":isPublished")
            params["isPublished"] = 1 if data.is_published else 0

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
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if data.title is not None:
            updates.append("title = :title")
            params["title"] = data.title
        if data.content is not None:
            updates.append("content = :content")
            params["content"] = data.content
        if data.version is not None:
            updates.append("version = :version")
            params["version"] = data.version
        if data.is_published is not None:
            updates.append("is_published = :isPublished")
            params["isPublished"] = 1 if data.is_published else None

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

    def __map_to_schema(self, row) -> PrivacyPolicy:
        return PrivacyPolicy(
            id=str(row.id),
            external_id=row.external_id,
            version=row.version,
            content=row.content,
            effective_date=row.effective_date,
            is_active=bool(row.is_active) if ("is_active" in row._mapping and row.is_active is not None) else False,
            created_at=row.created_at.isoformat() if row.created_at else None,
            updated_at=row.updated_at.isoformat() if row.updated_at else None,
        )

    async def findAll(self, query: Optional[Dict] = None) -> List[PrivacyPolicy]:
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
        return [self.__map_to_schema(r) for r in rows]

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
        return self.__map_to_schema(row) if row else None

    async def create(self, data: PrivacyPolicyInternalCreate) -> Any:

        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if data.version is not None:
            cols.append("version")
            vals.append(":version")
            params["version"] = data.version
        if data.content is not None:
            cols.append("content")
            vals.append(":content")
            params["content"] = data.content
        if data.effectiveDate is not None:
            cols.append("effective_date")
            vals.append(":effectiveDate")
            params["effectiveDate"] = data.effectiveDate
        if data.isActive is not None:
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

    async def update(self, id: str, data: PrivacyPolicyInternalUpdate) -> Optional[Any]:

        existing = await self.findById(id)
        if not existing:
            return None
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if data.version is not None:
            updates.append("version = :version")
            params["version"] = data.version
        if data.content is not None:
            updates.append("content = :content")
            params["content"] = data.content
        if data.effectiveDate is not None:
            updates.append("effective_date = :effectiveDate")
            params["effectiveDate"] = data.effectiveDate
        if data.isActive is not None:
            updates.append("is_active = :isActive")
            params["isActive"] = 1 if data.isActive else None

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

    def __map_to_schema(self, row) -> AvailabilityRequestResponse:
        return AvailabilityRequestResponse(
            _id=str(row.id),
            id=row.id,
            external_id=row.external_id,
            productId=row.product_id,
            productName=row.product_name,
            pincode=row.pincode,
            userName=row.user_name,
            userEmail=row.user_email,

            createdAt=row.created_at.isoformat() if row.created_at else None,
            updatedAt=row.updated_at.isoformat() if row.updated_at else None,
        )

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
        return [self.__map_to_schema(r) for r in rows]

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
        return self.__map_to_schema(row) if row else None

    async def create(self, data: AvailabilityRequestsInternalCreate) -> AvailabilityRequestResponse:

        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if data.product_id is not None:
            cols.append("product_id")
            vals.append(":productId")
            params["productId"] = data.product_id
        if data.productName is not None:
            cols.append("product_name")
            vals.append(":productName")
            params["productName"] = data.productName
        if data.pincode is not None:
            cols.append("pincode")
            vals.append(":pincode")
            params["pincode"] = data.pincode
        if data.userName is not None:
            cols.append("user_name")
            vals.append(":userName")
            params["userName"] = data.userName
        if data.userEmail is not None:
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

    async def update(self, id: str, data: AvailabilityRequestsInternalUpdate) -> Optional[Any]:

        existing = await self.findById(id)
        if not existing:
            return None
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if data.product_id is not None:
            updates.append("product_id = :productId")
            params["productId"] = data.product_id
        if data.productName is not None:
            updates.append("product_name = :productName")
            params["productName"] = data.productName
        if data.pincode is not None:
            updates.append("pincode = :pincode")
            params["pincode"] = data.pincode
        if data.userName is not None:
            updates.append("user_name = :userName")
            params["userName"] = data.userName
        if data.userEmail is not None:
            updates.append("user_email = :userEmail")
            params["userEmail"] = data.userEmail

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

    def __map_to_schema(self, row) -> PincodeSearches:
        return PincodeSearches(
            id=str(row.id),
            external_id=row.external_id,
            pincode=row.pincode,
            query=row.query,
            is_serviceable=bool(row.is_serviceable) if ("is_serviceable" in row._mapping and row.is_serviceable is not None) else False,
            timestamp=row.timestamp,
            created_at=row.created_at.isoformat() if row.created_at else None,
            updated_at=row.updated_at.isoformat() if row.updated_at else None,
        )

    async def findAll(self, query: Optional[Dict] = None) -> List[PincodeSearches]:
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
        return [self.__map_to_schema(r) for r in rows]

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
        return self.__map_to_schema(row) if row else None

    async def create(self, data: PincodeSearchesInternalCreate) -> Any:

        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if data.pincode is not None:
            cols.append("pincode")
            vals.append(":pincode")
            params["pincode"] = data.pincode
        if data.query is not None:
            cols.append("query")
            vals.append(":query")
            params["query"] = data.query
        if data.isServiceable is not None:
            cols.append("is_serviceable")
            vals.append(":isServiceable")
            params["isServiceable"] = 1 if data.isServiceable else 0
        if data.timestamp is not None:
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

    async def update(self, id: str, data: PincodeSearchesInternalUpdate) -> Optional[Any]:

        existing = await self.findById(id)
        if not existing:
            return None
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if data.pincode is not None:
            updates.append("pincode = :pincode")
            params["pincode"] = data.pincode
        if data.query is not None:
            updates.append("query = :query")
            params["query"] = data.query
        if data.isServiceable is not None:
            updates.append("is_serviceable = :isServiceable")
            params["isServiceable"] = 1 if data.isServiceable else None
        if data.timestamp is not None:
            updates.append("timestamp = :timestamp")
            params["timestamp"] = data.timestamp

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

    def __map_to_schema(self, row) -> Any:
        return SystemSettingsResponse(
            _id=str(row.id),
            id=row.id,
            external_id=row.external_id,
            maintenanceMode=bool(row.maintenance_mode) if ("maintenance_mode" in row._mapping and row.maintenance_mode is not None) else False,
            allowSignups=bool(row.allow_signups) if ("allow_signups" in row._mapping and row.allow_signups is not None) else False,
            maxUploadSizeMb=row.max_upload_size_mb,
            defaultCurrency=row.default_currency,
            timezone=row.timezone,

            createdAt=row.created_at.isoformat() if row.created_at else None,
            updatedAt=row.updated_at.isoformat() if row.updated_at else None,
        )

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
        return [self.__map_to_schema(r) for r in rows]

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
        return self.__map_to_schema(row) if row else None

    async def create(self, data: SystemSettingsInternalCreate) -> Any:

        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if data.maintenanceMode is not None:
            cols.append("maintenance_mode")
            vals.append(":maintenanceMode")
            params["maintenanceMode"] = 1 if data.maintenanceMode else 0
        if data.allowSignups is not None:
            cols.append("allow_signups")
            vals.append(":allowSignups")
            params["allowSignups"] = 1 if data.allowSignups else 0
        if data.maxUploadSizeMb is not None:
            cols.append("max_upload_size_mb")
            vals.append(":maxUploadSizeMb")
            params["maxUploadSizeMb"] = data.maxUploadSizeMb
        if data.defaultCurrency is not None:
            cols.append("default_currency")
            vals.append(":defaultCurrency")
            params["defaultCurrency"] = data.defaultCurrency
        if data.timezone is not None:
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

    async def update(self, id: str, data: SystemSettingsInternalUpdate) -> Optional[Any]:

        existing = await self.findById(id)
        if not existing:
            return None
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if data.maintenanceMode is not None:
            updates.append("maintenance_mode = :maintenanceMode")
            params["maintenanceMode"] = 1 if data.maintenanceMode else None
        if data.allowSignups is not None:
            updates.append("allow_signups = :allowSignups")
            params["allowSignups"] = 1 if data.allowSignups else None
        if data.maxUploadSizeMb is not None:
            updates.append("max_upload_size_mb = :maxUploadSizeMb")
            params["maxUploadSizeMb"] = data.maxUploadSizeMb
        if data.defaultCurrency is not None:
            updates.append("default_currency = :defaultCurrency")
            params["defaultCurrency"] = data.defaultCurrency
        if data.timezone is not None:
            updates.append("timezone = :timezone")
            params["timezone"] = data.timezone

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

    def __map_to_schema(self, row) -> ValetPayoutSettings:
        return ValetPayoutSettings(
            id=str(row.id),
            external_id=row.external_id,
            delivery_charge_per_order=row.delivery_charge_per_order,
            return_pickup_charge_per_order=row.return_pickup_charge_per_order,
            created_at=row.created_at.isoformat() if row.created_at else None,
            updated_at=row.updated_at.isoformat() if row.updated_at else None,
        )

    async def findAll(self, query: Optional[Dict] = None) -> List[ValetPayoutSettings]:
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
        return [self.__map_to_schema(r) for r in rows]

    async def findOne(self, query: Dict) -> Any:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Any:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        return self.__map_to_schema(row) if row else None

    async def create(self, data: ValetPayoutSettingsInternalCreate) -> ValetPayoutSettings:

        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}
        if data.deliveryChargePerOrder is not None:
            cols.append("delivery_charge_per_order")
            vals.append(":deliveryChargePerOrder")
            params["deliveryChargePerOrder"] = data.deliveryChargePerOrder
        if data.returnPickupChargePerOrder is not None:
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

    async def update(self, id: str, data: ValetPayoutSettingsInternalUpdate) -> Optional[ValetPayoutSettings]:

        existing = await self.findById(id)
        if not existing:
            return None
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}
        if data.deliveryChargePerOrder is not None:
            updates.append("delivery_charge_per_order = :deliveryChargePerOrder")
            params["deliveryChargePerOrder"] = data.deliveryChargePerOrder
        if data.returnPickupChargePerOrder is not None:
            updates.append("return_pickup_charge_per_order = :returnPickupChargePerOrder")
            params["returnPickupChargePerOrder"] = data.returnPickupChargePerOrder

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



