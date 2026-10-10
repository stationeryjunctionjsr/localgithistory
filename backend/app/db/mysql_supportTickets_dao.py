from typing import Optional, Dict, List, Any, Union
from datetime import datetime, timezone
import secrets
import json
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.schemas import SupportTicketInternal
from app.models.daos_flat import SupportTicketInternalCreate, SupportTicketInternalUpdate

def now_utc():
    return datetime.now(timezone.utc)

class MySQLSupportTicketsDAO:
    def __init__(self):
        self.table_name = "sj_support_tickets"
    
    @property
    def TABLE(self):
        from app.config.settings import settings
        return self.table_name

    def _factory(self):
        return get_async_session_factory()
        
    async def findById(self, id: Union[int, str]) -> Optional['SupportTicketInternal']:
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
            children_map = await self._fetch_children(session, [int(row.id)])
            return self._map_to_schema(row, children_map.get(int(row.id), {}))

    async def findByTicketNumber(self, ticket_number: str) -> Optional['SupportTicketInternal']:
        factory = self._factory()
        if not factory or not ticket_number:
            return None
        async with factory() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE ticket_number = :tn LIMIT 1")
            result = await session.execute(q, {"tn": str(ticket_number)})
            row = result.fetchone()
            if not row:
                return None
            children_map = await self._fetch_children(session, [int(row.id)])
            return self._map_to_schema(row, children_map.get(int(row.id), {}))

    async def findOne(
        self,
        query: Optional[dict] = None,
        ticket_number: Optional[str] = None,
        status: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional['SupportTicketInternal']:
        if ticket_number:
            return await self.findByTicketNumber(ticket_number)
        if query:
            tn = query.get("ticket_number") or query.get("ticketNumber")
            if tn:
                return await self.findByTicketNumber(tn)
            if "_id" in query or "id" in query:
                return await self.findById(query.get("_id") or query.get("id"))
            if "externalId" in query and query["externalId"]:
                return await self.findById(query["externalId"])
        results = await self.findAll(query=query, status=status, user_id=user_id)
        return results[0] if results else None

    async def findAll(
        self,
        query: Optional[dict] = None,
        status: Optional[str] = None,
        user_id: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> List['SupportTicketInternal']:
        if query:
            if status is None and "status" in query:
                status = query["status"]
            if user_id is None:
                user_id = query.get("user") or query.get("user_id") or query.get("userId")
            if category is None and "category" in query:
                category = query["category"]
            if priority is None and "priority" in query:
                priority = query["priority"]

        clauses = []
        params = {}
        if status is not None:
            clauses.append("status = :status")
            params["status"] = status
        if user_id is not None:
            clauses.append("user_id = :uid")
            params["uid"] = str(user_id)
        if category is not None:
            clauses.append("category = :cat")
            params["cat"] = category
        if priority is not None:
            clauses.append("priority = :prio")
            params["prio"] = priority

        where_sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT * FROM {self.TABLE}{where_sql} ORDER BY id ASC"

        factory = self._factory()
        if not factory:
            return []
        async with factory() as session:
            result = await session.execute(text(sql), params)
            rows = result.fetchall()
            if not rows:
                return []
            children_map = await self._fetch_children(session, [int(r.id) for r in rows])
            return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]

    async def create(self, data: 'SupportTicketInternalCreate') -> 'SupportTicketInternal':
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        params = {"eid": external_id, "c": now, "u": now}

        if data.ticket_number is not None:
            cols.append("ticket_number")
            params["s_ticket_number"] = data.ticket_number

        if data.user is not None:
            cols.append("user_id")
            params["s_user"] = data.user

        if data.name is not None:
            cols.append("name")
            params["s_name"] = data.name

        if data.email is not None:
            cols.append("email")
            params["s_email"] = data.email

        if data.phone is not None:
            cols.append("phone")
            params["s_phone"] = data.phone

        if data.company is not None:
            cols.append("company")
            params["s_company"] = data.company

        if data.subject is not None:
            cols.append("subject")
            params["s_subject"] = data.subject

        if data.description is not None:
            cols.append("description")
            params["s_description"] = data.description

        if data.category is not None:
            cols.append("category")
            params["s_category"] = data.category

        if data.priority is not None:
            cols.append("priority")
            params["s_priority"] = data.priority

        if data.status is not None:
            cols.append("status")
            params["s_status"] = data.status

        if data.assigned_to is not None:
            cols.append("assigned_to")
            params["s_assigned_to"] = data.assigned_to

        if data.resolved_at is not None:
            cols.append("resolved_at")
            params["s_resolved_at"] = data.resolved_at

        if data.closed_at is not None:
            cols.append("closed_at")
            params["s_closed_at"] = data.closed_at

        col_sql = ", ".join(cols)
        val_sql = ", ".join([":eid", ":c", ":u"] + [f":s_{k}" for k in ['ticket_number', 'user', 'name', 'email', 'phone', 'company', 'subject', 'description', 'category', 'priority', 'status', 'assigned_to', 'resolved_at', 'closed_at'] if f"s_{k}" in params] + [f":c_{k}" for k in [] if f"c_{k}" in params])
        
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

    async def update(self, id: str, update_data: 'SupportTicketInternalUpdate') -> 'SupportTicketInternal':
        data = update_data
        factory = self._factory()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now_utc()}

        if data.ticket_number is not None:
            updates.append("ticket_number = :s_ticket_number")
            params["s_ticket_number"] = data.ticket_number

        if data.user is not None:
            updates.append("user_id = :s_user")
            params["s_user"] = data.user

        if data.name is not None:
            updates.append("name = :s_name")
            params["s_name"] = data.name

        if data.email is not None:
            updates.append("email = :s_email")
            params["s_email"] = data.email

        if data.phone is not None:
            updates.append("phone = :s_phone")
            params["s_phone"] = data.phone

        if data.company is not None:
            updates.append("company = :s_company")
            params["s_company"] = data.company

        if data.subject is not None:
            updates.append("subject = :s_subject")
            params["s_subject"] = data.subject

        if data.description is not None:
            updates.append("description = :s_description")
            params["s_description"] = data.description

        if data.category is not None:
            updates.append("category = :s_category")
            params["s_category"] = data.category

        if data.priority is not None:
            updates.append("priority = :s_priority")
            params["s_priority"] = data.priority

        if data.status is not None:
            updates.append("status = :s_status")
            params["s_status"] = data.status

        if data.assigned_to is not None:
            updates.append("assigned_to = :s_assigned_to")
            params["s_assigned_to"] = data.assigned_to

        if data.resolved_at is not None:
            updates.append("resolved_at = :s_resolved_at")
            params["s_resolved_at"] = data.resolved_at

        if data.closed_at is not None:
            updates.append("closed_at = :s_closed_at")
            params["s_closed_at"] = data.closed_at

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

            await session.execute(text("DELETE FROM sj_ticket_attachments WHERE parent_id = :id"), {"id": pk})
            await session.execute(text("DELETE FROM sj_ticket_responses WHERE parent_id = :id"), {"id": pk})

            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pk},
            )
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(self, r, children: Dict) -> 'SupportTicketInternal':
        from app.models.schemas import SupportTicketInternal
        user_val = str(r.user_id) if r.user_id is not None else None
        return SupportTicketInternal(
            id=str(r.id),
            external_id=r.external_id,
            ticket_number=r.ticket_number,
            user=user_val,
            name=r.name,
            email=r.email,
            phone=r.phone,
            company=r.company,
            subject=r.subject,
            description=r.description,
            category=r.category,
            priority=r.priority,
            status=r.status,
            assigned_to=r.assigned_to,
            attachments=children.get("attachments", []),
            responses=children.get("responses", []),
            resolved_at=str(r.resolved_at) if r.resolved_at else None,
            closed_at=str(r.closed_at) if r.closed_at else None,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:
        c_map = {rid: {} for rid in ids}
        if not ids:
            return c_map
            
        id_list = ",".join(map(str, ids))

        q_attachments = text(f"SELECT parent_id, url FROM sj_ticket_attachments WHERE parent_id IN ({id_list})")
        res_attachments = await session.execute(q_attachments)
        rows_attachments = res_attachments.fetchall()

        for r in rows_attachments:
            if "attachments" not in c_map[r.parent_id]:
                c_map[r.parent_id]["attachments"] = []
            c_map[r.parent_id]["attachments"].append(r[1])

        q_responses = text(f"SELECT parent_id, admin_id, message FROM sj_ticket_responses WHERE parent_id IN ({id_list})")
        res_responses = await session.execute(q_responses)
        rows_responses = res_responses.fetchall()

        for r in rows_responses:
            if "responses" not in c_map[r.parent_id]:
                c_map[r.parent_id]["responses"] = []
            obj = {}

            obj["user"] = r[1]
            obj["message"] = r[2]
            c_map[r.parent_id]["responses"].append(obj)

        return c_map

    async def _replace_children(self, session, row_id: int, data: 'CamelBaseModel'):

        if data.attachments is not None:
            await session.execute(text(f"DELETE FROM sj_ticket_attachments WHERE parent_id = :id"), {"id": row_id})
            child_list = data.attachments or []

            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_ticket_attachments (parent_id, url) VALUES (:id, :v)"), {"id": row_id, "v": item})

        if data.responses is not None:
            await session.execute(text(f"DELETE FROM sj_ticket_responses WHERE parent_id = :id"), {"id": row_id})
            child_list = data.responses or []

            if child_list:
                for item in child_list:
                    p = {"id": row_id}

                    p["v0"] = item.user
                    p["v1"] = item.message
                    await session.execute(text(f"INSERT INTO sj_ticket_responses (parent_id, admin_id, message) VALUES (:id, :v0, :v1)"), p)
