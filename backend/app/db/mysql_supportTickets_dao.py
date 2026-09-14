"""
MySQL DAO for sj_support_tickets.
"""
from typing import Dict, Any, List, Optional
from app.models.schemas import SupportTicketResponse
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc
import logging

logger = logging.getLogger(__name__)

class MySQLSupportticketsDAO:
    @property
    def TABLE(self):
        suffix = (settings.table_suffix if settings.table_suffix is not None else "")
        return f"sj_support_tickets{suffix}"

    @property
    def RESPONSES_TABLE(self):
        suffix = (settings.table_suffix if settings.table_suffix is not None else "")
        return f"sj_support_ticket_responses{suffix}"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_model(self, r, responses_rows) -> SupportTicketResponse:
        responses_list = []
        i = 0
        while i < len(responses_rows):
            resp = responses_rows[i]
            try:
                ticket_id_val = r.id
            except AttributeError:
                ticket_id_val = None
                
            try:
                resp_ticket_id = resp.ticket_id
            except AttributeError:
                resp_ticket_id = None
                
            if resp_ticket_id == ticket_id_val:
                try:
                    r_uid = resp.user_id
                except AttributeError:
                    r_uid = None
                try:
                    r_msg = resp.message
                except AttributeError:
                    r_msg = None
                try:
                    r_time = resp.timestamp.isoformat() if resp.timestamp else None
                except AttributeError:
                    r_time = None
                    
                responses_list.append({
                    "userId": r_uid,
                    "message": r_msg,
                    "timestamp": r_time
                })
            i += 1
        
        try:
            r_user_id = r.user_id
        except AttributeError:
            r_user_id = None
            
        try:
            r_assigned_to = r.assigned_to
        except AttributeError:
            r_assigned_to = None
            
        try:
            r_subject = r.subject
        except AttributeError:
            r_subject = ""
            
        try:
            r_message = r.message
        except AttributeError:
            r_message = ""
            
        try:
            r_status = r.status
        except AttributeError:
            r_status = ""
            
        try:
            r_priority = r.priority
        except AttributeError:
            r_priority = ""
            
        try:
            r_resolved_at = r.resolved_at.isoformat() if r.resolved_at else None
        except AttributeError:
            r_resolved_at = None
            
        try:
            r_created_at = r.created_at.isoformat() if r.created_at else ""
        except AttributeError:
            r_created_at = ""
            
        try:
            r_updated_at = r.updated_at.isoformat() if r.updated_at else ""
        except AttributeError:
            r_updated_at = ""

        try:
            r_ticket_number = r.ticket_number
        except AttributeError:
            r_ticket_number = ""

        try:
            r_name = r.name
        except AttributeError:
            r_name = ""

        try:
            r_email = r.email
        except AttributeError:
            r_email = ""

        try:
            r_phone = r.phone
        except AttributeError:
            r_phone = ""

        try:
            r_id = r.id
        except AttributeError:
            r_id = None

        user_dict = {"_id": r_user_id} if r_user_id else {}
        assigned_to_dict = {"_id": r_assigned_to} if r_assigned_to else None
        
        data_dict = {
            "_id": str(r_id),
            "id": str(r_id),
            "userId": r_user_id,
            "subject": r_subject,
            "message": r_message,
            "status": r_status,
            "priority": r_priority,
            "assignedTo": assigned_to_dict,
            "resolvedAt": r_resolved_at,
            "createdAt": r_created_at,
            "updatedAt": r_updated_at,
            "ticketNumber": r_ticket_number or "",
            "user": user_dict,
            "name": r_name or "",
            "email": r_email or "",
            "phone": r_phone or "",
            "description": r_message or "",
            "responses": responses_list
        }
        return SupportTicketResponse.model_validate(data_dict)

    async def findAll(self, query: Optional[Dict] = None) -> List[SupportTicketResponse]:
        factory = self._factory()
        if not factory:
            return []
        async with factory() as session:
            result = await session.execute(
                text(
                    f"SELECT id, user_id, subject, message, status, priority, assigned_to, resolved_at, created_at, updated_at, ticket_number, name, email, phone FROM {self.TABLE}"
                )
            )
            rows = result.fetchall()
            
            responses_result = await session.execute(
                text(f"SELECT ticket_id, user_id, message, timestamp FROM {self.RESPONSES_TABLE}")
            )
            responses_rows = responses_result.fetchall()
            
        docs = [self._row_to_model(r, responses_rows) for r in rows]
        
        if not query:
            return docs
            
        filtered: List[SupportTicketResponse] = []
        i = 0
        while i < len(docs):
            d = docs[i]
            match = True
            for k, v in query.items():
                if k in ("_id", "id"):
                    try:
                        d_id = d.id
                    except AttributeError:
                        d_id = None
                    if str(d_id) != str(v):
                        match = False
                        break
                else:
                    try:
                        val = eval(f"d.{k}")
                    except (AttributeError, SyntaxError, NameError):
                        val = None
                    if val != v:
                        match = False
                        break
            if match:
                filtered.append(d)
            i += 1
        return filtered

    async def findOne(self, query: Dict) -> Optional[SupportTicketResponse]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[SupportTicketResponse]:
        factory = self._factory()
        if not factory:
            return None
        fid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            result = await session.execute(
                text(
                    f"SELECT id, user_id, subject, message, status, priority, assigned_to, resolved_at, created_at, updated_at, ticket_number, name, email, phone FROM {self.TABLE} WHERE id = :id"
                ),
                {"id": fid},
            )
            row = result.fetchone()
            if not row:
                return None
            
            responses_result = await session.execute(
                text(f"SELECT ticket_id, user_id, message, timestamp FROM {self.RESPONSES_TABLE} WHERE ticket_id = :id"),
                {"id": fid}
            )
            responses_rows = responses_result.fetchall()
            
        return self._row_to_model(row, responses_rows)

    async def create(self, data: Any) -> SupportTicketResponse:
        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        now = now_utc()
        
        try:
            user_id = data.userId
        except AttributeError:
            user_id = None
            
        try:
            subject = data.subject
        except AttributeError:
            subject = None
            
        try:
            message = data.message
        except AttributeError:
            message = None
            
        try:
            status = data.status
        except AttributeError:
            status = "open"
            
        try:
            priority = data.priority
        except AttributeError:
            priority = "medium"
            
        try:
            assigned_to = data.assignedTo
        except AttributeError:
            assigned_to = None
            
        try:
            resolved_at = data.resolvedAt
        except AttributeError:
            resolved_at = None

        ticket_number = f"TICK-{int(now.timestamp())}"
        
        try:
            name = data.name
        except AttributeError:
            name = ""
            
        try:
            email = data.email
        except AttributeError:
            email = ""
            
        try:
            phone = data.phone
        except AttributeError:
            phone = ""
            
        async with factory() as session:
            result = await session.execute(
                text(
                    f'''
                    INSERT INTO {self.TABLE} 
                    (user_id, subject, message, status, priority, assigned_to, resolved_at, created_at, updated_at, ticket_number, name, email, phone)
                    VALUES (:user_id, :subject, :message, :status, :priority, :assigned_to, :resolved_at, :created_at, :updated_at, :ticket_number, :name, :email, :phone)
                    '''
                ),
                {
                    "user_id": user_id,
                    "subject": subject,
                    "message": message,
                    "status": status,
                    "priority": priority,
                    "assigned_to": assigned_to,
                    "resolved_at": resolved_at,
                    "created_at": now,
                    "updated_at": now,
                    "ticket_number": ticket_number,
                    "name": name,
                    "email": email,
                    "phone": phone
                },
            )
            new_id = result.lastrowid
            
            try:
                data_responses = data.responses
            except AttributeError:
                data_responses = None
                
            if data_responses:
                i = 0
                while i < len(data_responses):
                    resp = data_responses[i]
                    try:
                        r_user_id = resp.userId
                    except AttributeError:
                        r_user_id = None
                    try:
                        r_message = resp.message
                    except AttributeError:
                        r_message = None
                    try:
                        r_timestamp = resp.timestamp
                    except AttributeError:
                        r_timestamp = now
                        
                    await session.execute(
                        text(
                            f'''
                            INSERT INTO {self.RESPONSES_TABLE} (ticket_id, user_id, message, timestamp)
                            VALUES (:ticket_id, :user_id, :message, :timestamp)
                            '''
                        ),
                        {
                            "ticket_id": new_id,
                            "user_id": r_user_id,
                            "message": r_message,
                            "timestamp": r_timestamp
                        }
                    )
                    i += 1
            
            await session.commit()
            
        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: Any) -> Optional[SupportTicketResponse]:
        factory = self._factory()
        if not factory:
            return None
        now = now_utc()
        fid = int(id) if str(id).isdigit() else None
        
        existing = await self.findById(id)
        if not existing:
            return None
            
        try:
            user_id = update_data.userId
        except AttributeError:
            try:
                user_id = existing.userId
            except AttributeError:
                user_id = None
                
        try:
            subject = update_data.subject
        except AttributeError:
            try:
                subject = existing.subject
            except AttributeError:
                subject = None
                
        try:
            message = update_data.message
        except AttributeError:
            try:
                message = existing.message
            except AttributeError:
                message = None
                
        try:
            status = update_data.status
        except AttributeError:
            try:
                status = existing.status
            except AttributeError:
                status = None
                
        try:
            priority = update_data.priority
        except AttributeError:
            try:
                priority = existing.priority
            except AttributeError:
                priority = None
                
        try:
            assigned_to = update_data.assignedTo
        except AttributeError:
            try:
                assigned_to = existing.assignedTo
            except AttributeError:
                assigned_to = None
                
        try:
            resolved_at = update_data.resolvedAt
        except AttributeError:
            try:
                resolved_at = existing.resolvedAt
            except AttributeError:
                resolved_at = None
                
        async with factory() as session:
            await session.execute(
                text(
                    f'''
                    UPDATE {self.TABLE} SET
                        user_id = :user_id,
                        subject = :subject,
                        message = :message,
                        status = :status,
                        priority = :priority,
                        assigned_to = :assigned_to,
                        resolved_at = :resolved_at,
                        updated_at = :updated_at
                    WHERE id = :id
                    '''
                ),
                {
                    "id": fid,
                    "user_id": user_id,
                    "subject": subject,
                    "message": message,
                    "status": status,
                    "priority": priority,
                    "assigned_to": assigned_to,
                    "resolved_at": resolved_at,
                    "updated_at": now,
                },
            )
            
            try:
                update_responses = update_data.responses
            except AttributeError:
                update_responses = None
                
            if update_responses is not None:
                await session.execute(
                    text(f"DELETE FROM {self.RESPONSES_TABLE} WHERE ticket_id = :id"),
                    {"id": fid}
                )
                i = 0
                while i < len(update_responses):
                    resp = update_responses[i]
                    try:
                        r_user_id = resp.userId
                    except AttributeError:
                        r_user_id = None
                    try:
                        r_message = resp.message
                    except AttributeError:
                        r_message = None
                    try:
                        r_timestamp = resp.timestamp
                    except AttributeError:
                        r_timestamp = now
                        
                    await session.execute(
                        text(
                            f'''
                            INSERT INTO {self.RESPONSES_TABLE} (ticket_id, user_id, message, timestamp)
                            VALUES (:ticket_id, :user_id, :message, :timestamp)
                            '''
                        ),
                        {
                            "ticket_id": fid,
                            "user_id": r_user_id,
                            "message": r_message,
                            "timestamp": r_timestamp
                        }
                    )
                    i += 1
            
            await session.commit()
            
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        fid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            await session.execute(
                text(f"DELETE FROM {self.RESPONSES_TABLE} WHERE ticket_id = :id"),
                {"id": fid},
            )
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": fid},
            )
            await session.commit()
            return result.rowcount > 0
            
    find_all = findAll
    find_by_id = findById
    find_one = findOne
