import uuid
from typing import List, Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.models.schemas import ActivityCreate, ActivityUpdate, ActivityResponse

class MySQLActivitiesDAO:
    def __init__(self):
        self.TABLE = "sj_activities"
        
    async def create(self, session: AsyncSession, data: ActivityCreate) -> str:
        new_id = str(uuid.uuid4())
        
        insert_sql = f"""
            INSERT INTO {self.TABLE} (
                id, user_id, action, entity_type, entity_id, session_id
            ) VALUES (
                :id, :user_id, :action, :entity_type, :entity_id, :session_id
            )
        """
        params = {
            "id": new_id,
            "user_id": data.userId,
            "action": data.action,
            "entity_type": data.entityType,
            "entity_id": data.entityId,
            "session_id": data.sessionId,
        }
        await session.execute(text(insert_sql), params)
        
        if data.metadata:
            for k, v in data.metadata.items():
                meta_sql = """
                    INSERT INTO sj_activity_metadata (activity_id, meta_key, meta_value)
                    VALUES (:activity_id, :meta_key, :meta_value)
                """
                await session.execute(text(meta_sql), {
                    "activity_id": new_id,
                    "meta_key": str(k),
                    "meta_value": str(v)
                })
                
        return new_id

    async def update(self, session: AsyncSession, id: str, data: ActivityUpdate) -> Optional[str]:
        check = await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE id = :id"), {"id": id})
        if not check.scalar():
            return None
            
        update_sql = f"""
            UPDATE {self.TABLE}
            SET user_id = :user_id,
                action = :action,
                entity_type = :entity_type,
                entity_id = :entity_id,
                session_id = :session_id
            WHERE id = :id
        """
        params = {
            "id": id,
            "user_id": data.userId,
            "action": data.action,
            "entity_type": data.entityType,
            "entity_id": data.entityId,
            "session_id": data.sessionId,
        }
        await session.execute(text(update_sql), params)
        
        await session.execute(
            text("DELETE FROM sj_activity_metadata WHERE activity_id = :id"),
            {"id": id}
        )
        if data.metadata:
            for k, v in data.metadata.items():
                meta_sql = """
                    INSERT INTO sj_activity_metadata (activity_id, meta_key, meta_value)
                    VALUES (:activity_id, :meta_key, :meta_value)
                """
                await session.execute(text(meta_sql), {
                    "activity_id": id,
                    "meta_key": str(k),
                    "meta_value": str(v)
                })
                
        return id

    async def findById(self, session: AsyncSession, id: str) -> Optional[ActivityResponse]:
        query = f"""
            SELECT id, user_id, action, entity_type, entity_id, session_id
            FROM {self.TABLE}
            WHERE id = :id
        """
        result = await session.execute(text(query), {"id": id})
        row = result.fetchone()
        if not row:
            return None
            
        meta_query = """
            SELECT meta_key, meta_value
            FROM sj_activity_metadata
            WHERE activity_id = :id
        """
        meta_result = await session.execute(text(meta_query), {"id": id})
        metadata = {}
        for m_row in meta_result.fetchall():
            metadata[m_row.meta_key] = m_row.meta_value
            
        return ActivityResponse(
            id=row.id,
            userId=row.user_id,
            action=row.action,
            entityType=row.entity_type,
            entityId=row.entity_id,
            sessionId=row.session_id,
            metadata=metadata
        )

    async def findOne(self, session: AsyncSession, filters: dict) -> Optional[ActivityResponse]:
        if not filters:
            return None
            
        conditions = []
        params = {}
        for k, v in filters.items():
            db_col = self._map_key_to_col(k)
            if db_col:
                conditions.append(f"{db_col} = :{k}")
                params[k] = v
                
        if not conditions:
            return None
            
        where_clause = " AND ".join(conditions)
        query = f"""
            SELECT id, user_id, action, entity_type, entity_id, session_id
            FROM {self.TABLE}
            WHERE {where_clause}
            LIMIT 1
        """
        result = await session.execute(text(query), params)
        row = result.fetchone()
        if not row:
            return None
            
        meta_query = """
            SELECT meta_key, meta_value
            FROM sj_activity_metadata
            WHERE activity_id = :id
        """
        meta_result = await session.execute(text(meta_query), {"id": row.id})
        metadata = {}
        for m_row in meta_result.fetchall():
            metadata[m_row.meta_key] = m_row.meta_value
            
        return ActivityResponse(
            id=row.id,
            userId=row.user_id,
            action=row.action,
            entityType=row.entity_type,
            entityId=row.entity_id,
            sessionId=row.session_id,
            metadata=metadata
        )

    async def findAll(self, session: AsyncSession, filters: Optional[dict] = None) -> List[ActivityResponse]:
        query = f"""
            SELECT id, user_id, action, entity_type, entity_id, session_id
            FROM {self.TABLE}
        """
        params = {}
        if filters:
            conditions = []
            for k, v in filters.items():
                db_col = self._map_key_to_col(k)
                if db_col:
                    conditions.append(f"{db_col} = :{k}")
                    params[k] = v
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
        result = await session.execute(text(query), params)
        rows = result.fetchall()
        
        if not rows:
            return []
            
        ids = [r.id for r in rows]
        
        meta_query = """
            SELECT activity_id, meta_key, meta_value
            FROM sj_activity_metadata
            WHERE activity_id IN :ids
        """
        meta_result = await session.execute(text(meta_query), {"ids": tuple(ids)})
        
        metadata_map = {r_id: {} for r_id in ids}
        for m_row in meta_result.fetchall():
            metadata_map[m_row.activity_id][m_row.meta_key] = m_row.meta_value
            
        responses = []
        for row in rows:
            responses.append(ActivityResponse(
                id=row.id,
                userId=row.user_id,
                action=row.action,
                entityType=row.entity_type,
                entityId=row.entity_id,
                sessionId=row.session_id,
                metadata=metadata_map[row.id]
            ))
            
        return responses

    def _map_key_to_col(self, key: str) -> Optional[str]:
        mapping = {
            "userId": "user_id",
            "action": "action",
            "entityType": "entity_type",
            "entityId": "entity_id",
            "sessionId": "session_id",
            "id": "id"
        }
        return (mapping[key] if key in mapping else None)
