from typing import List, Optional, Dict, Any
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.schemas import NotificationCreate, NotificationUpdate, NotificationResponse

class MySQLNotificationsDAO:
    TABLE = "sj_notifications"

    def __init__(self):
        self._factory = get_async_session_factory

    async def create(self, data: NotificationCreate) -> NotificationResponse:
        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")

        async with factory() as session:
            res = await session.execute(
                text(f"""
                INSERT INTO {self.TABLE} (
                    user_id, title, message, type, is_read, action_url, related_entity_id, related_entity_type
                ) VALUES (
                    :user_id, :title, :message, :type, :is_read, :action_url, :related_entity_id, :related_entity_type
                )
                """),
                {
                    "user_id": data.userId,
                    "title": data.title,
                    "message": data.message,
                    "type": data.type,
                    "is_read": 1 if data.isRead else 0,
                    "action_url": data.actionUrl,
                    "related_entity_id": data.relatedEntityId,
                    "related_entity_type": data.relatedEntityType,
                }
            )
            inserted_id = res.lastrowid
            await session.commit()
            
        return await self.findById(inserted_id)

    async def update(self, notification_id: int, data: NotificationUpdate) -> Optional[NotificationResponse]:
        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")

        async with factory() as session:
            await session.execute(
                text(f"""
                UPDATE {self.TABLE}
                SET user_id = :user_id,
                    title = :title,
                    message = :message,
                    type = :type,
                    is_read = :is_read,
                    action_url = :action_url,
                    related_entity_id = :related_entity_id,
                    related_entity_type = :related_entity_type
                WHERE id = :id
                """),
                {
                    "user_id": data.userId,
                    "title": data.title,
                    "message": data.message,
                    "type": data.type,
                    "is_read": 1 if data.isRead else 0,
                    "action_url": data.actionUrl,
                    "related_entity_id": data.relatedEntityId,
                    "related_entity_type": data.relatedEntityType,
                    "id": notification_id
                }
            )
            await session.commit()
            
        return await self.findById(notification_id)

    async def findById(self, notification_id: int) -> Optional[NotificationResponse]:
        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")

        async with factory() as session:
            row = (await session.execute(
                text(f"""
                SELECT id, user_id, title, message, type, is_read, action_url, related_entity_id, related_entity_type
                FROM {self.TABLE}
                WHERE id = :id
                LIMIT 1
                """),
                {"id": notification_id}
            )).fetchone()
            
            if not row:
                return None
                
            return self._row_to_response(row)

    async def findOne(self, filters: Dict[str, Any]) -> Optional[NotificationResponse]:
        if not filters:
            return None
            
        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")

        conditions = []
        params = {}
        
        column_map = {
            "userId": "user_id",
            "title": "title",
            "message": "message",
            "type": "type",
            "isRead": "is_read",
            "actionUrl": "action_url",
            "relatedEntityId": "related_entity_id",
            "relatedEntityType": "related_entity_type",
            "id": "id"
        }
        
        for idx, (k, v) in enumerate(filters.items()):
            db_col = (column_map[k] if k in column_map else k)
            param_key = f"param_{idx}"
            conditions.append(f"{db_col} = :{param_key}")
            params[param_key] = 1 if k == "isRead" and v else (0 if k == "isRead" and not v else v)
            
        where_clause = " AND ".join(conditions)
        
        async with factory() as session:
            row = (await session.execute(
                text(f"""
                SELECT id, user_id, title, message, type, is_read, action_url, related_entity_id, related_entity_type
                FROM {self.TABLE}
                WHERE {where_clause}
                LIMIT 1
                """),
                params
            )).fetchone()
            
            if not row:
                return None
                
            return self._row_to_response(row)

    async def findAll(self, filters: Dict[str, Any] = None) -> List[NotificationResponse]:
        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")

        conditions = []
        params = {}
        
        if filters:
            column_map = {
                "userId": "user_id",
                "title": "title",
                "message": "message",
                "type": "type",
                "isRead": "is_read",
                "actionUrl": "action_url",
                "relatedEntityId": "related_entity_id",
                "relatedEntityType": "related_entity_type",
                "id": "id"
            }
            
            for idx, (k, v) in enumerate(filters.items()):
                db_col = (column_map[k] if k in column_map else k)
                param_key = f"param_{idx}"
                conditions.append(f"{db_col} = :{param_key}")
                params[param_key] = 1 if k == "isRead" and v else (0 if k == "isRead" and not v else v)
                
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        async with factory() as session:
            rows = (await session.execute(
                text(f"""
                SELECT id, user_id, title, message, type, is_read, action_url, related_entity_id, related_entity_type
                FROM {self.TABLE}
                {where_clause}
                """),
                params
            )).fetchall()
            
            return [self._row_to_response(row) for row in rows]

    def _row_to_response(self, row) -> NotificationResponse:
        data = {
            "id": str(row.id),
            "userId": str(row.user_id) if row.user_id is not None else "",
            "title": row.title,
            "message": row.message,
            "type": row.type,
            "isRead": bool(row.is_read),
            "actionUrl": row.action_url,
            "relatedEntityId": str(row.related_entity_id) if row.related_entity_id is not None else None,
            "relatedEntityType": row.related_entity_type
        }
        return NotificationResponse.model_validate(data)
