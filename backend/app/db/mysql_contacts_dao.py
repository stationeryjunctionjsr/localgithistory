import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.models.schemas import ContactCreate, ContactUpdate, ContactResponse


class MySQLContactsDAO:
    """
    MySQL DAO for sj_contacts.
    Standalone class using raw SQL statements without dictionary fallbacks.
    """

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    async def create(self, data: ContactCreate) -> ContactResponse:
        SessionLocal = get_async_session_factory()
        new_id = str(uuid.uuid4())
        now = self._now()
        async with SessionLocal() as session:
            await session.execute(
                text("""
                    INSERT INTO sj_contacts (
                        id, name, email, phone, subject, message, status, user_id, created_at, updated_at
                    ) VALUES (
                        :id, :name, :email, :phone, :subject, :message, :status, :userId, :created_at, :updated_at
                    )
                """),
                {
                    "id": new_id,
                    "name": data.name,
                    "email": data.email,
                    "phone": data.phone,
                    "subject": data.subject,
                    "message": data.message,
                    "status": data.status,
                    "userId": data.userId,
                    "created_at": now,
                    "updated_at": now
                }
            )
            await session.commit()
        return await self.findById(new_id)

    async def update(self, id: str, data: ContactUpdate) -> Optional[ContactResponse]:
        SessionLocal = get_async_session_factory()
        now = self._now()
        
        updates = []
        params = {"id": id, "updated_at": now}
        
        if data.name is not None:
            updates.append("name = :name")
            params["name"] = data.name
            
        if data.email is not None:
            updates.append("email = :email")
            params["email"] = data.email
            
        if data.phone is not None:
            updates.append("phone = :phone")
            params["phone"] = data.phone
            
        if data.subject is not None:
            updates.append("subject = :subject")
            params["subject"] = data.subject
            
        if data.message is not None:
            updates.append("message = :message")
            params["message"] = data.message
            
        if data.status is not None:
            updates.append("status = :status")
            params["status"] = data.status
            
        if data.userId is not None:
            updates.append("user_id = :userId")
            params["userId"] = data.userId
            
        if not updates:
            return await self.findById(id)
            
        updates.append("updated_at = :updated_at")
        set_clause = ", ".join(updates)
        
        async with SessionLocal() as session:
            await session.execute(
                text(f"UPDATE sj_contacts SET {set_clause} WHERE id = :id"),
                params
            )
            await session.commit()
            
        return await self.findById(id)

    async def findById(self, id: str) -> Optional[ContactResponse]:
        SessionLocal = get_async_session_factory()
        async with SessionLocal() as session:
            result = await session.execute(
                text("""
                    SELECT 
                        id, name, email, phone, subject, message, status, user_id, created_at, updated_at
                    FROM sj_contacts 
                    WHERE id = :id
                """),
                {"id": id}
            )
            row = result.fetchone()
            if not row:
                return None
                
            return ContactResponse(
                id=row.id,
                name=row.name,
                email=row.email,
                phone=row.phone,
                subject=row.subject,
                message=row.message,
                status=row.status,
                userId=row.user_id,
                createdAt=row.created_at.isoformat() if row.created_at else None,
                updatedAt=row.updated_at.isoformat() if row.updated_at else None
            )

    async def findOne(self, query: Dict[str, Any]) -> Optional[ContactResponse]:
        docs = await self.findAll(query, limit=1)
        return docs[0] if docs else None

    async def findAll(self, query: Optional[Dict[str, Any]] = None, skip: Optional[int] = None, limit: Optional[int] = None) -> List[ContactResponse]:
        SessionLocal = get_async_session_factory()
        
        where_clauses = []
        params = {}
        
        if query:
            if "name" in query:
                where_clauses.append("name = :name")
                params["name"] = query["name"]
            if "email" in query:
                where_clauses.append("email = :email")
                params["email"] = query["email"]
            if "phone" in query:
                where_clauses.append("phone = :phone")
                params["phone"] = query["phone"]
            if "status" in query:
                where_clauses.append("status = :status")
                params["status"] = query["status"]
            if "userId" in query:
                where_clauses.append("user_id = :userId")
                params["userId"] = query["userId"]

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        limit_sql = ""
        if limit is not None:
            limit_sql = f" LIMIT {limit}"
            if skip is not None:
                limit_sql = f" LIMIT {limit} OFFSET {skip}"
                
        sql = f"SELECT id, name, email, phone, subject, message, status, user_id, created_at, updated_at FROM sj_contacts WHERE {where_sql} ORDER BY created_at DESC{limit_sql}"
        
        async with SessionLocal() as session:
            result = await session.execute(text(sql), params)
            rows = result.fetchall()
            
            responses = []
            for row in rows:
                responses.append(ContactResponse(
                    id=row.id,
                    name=row.name,
                    email=row.email,
                    phone=row.phone,
                    subject=row.subject,
                    message=row.message,
                    status=row.status,
                    userId=row.user_id,
                    createdAt=row.created_at.isoformat() if row.created_at else None,
                    updatedAt=row.updated_at.isoformat() if row.updated_at else None
                ))
            return responses

    async def delete(self, id: str) -> bool:
        SessionLocal = get_async_session_factory()
        async with SessionLocal() as session:
            result = await session.execute(
                text("DELETE FROM sj_contacts WHERE id = :id"),
                {"id": id}
            )
            await session.commit()
            return result.rowcount > 0
