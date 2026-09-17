from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import secrets
import json
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import SupportTicketInternal
from app.models.daos_flat import SupportTicketInternalCreate, SupportTicketInternalUpdate

def now_utc():
    return datetime.now(timezone.utc)

class MySQLSupportTicketsDAO:
    def __init__(self):
        self.table_name = "sj_support_tickets"
    
    @property
    def TABLE(self):
        from app.config.settings import settings
        suffix = (settings.table_suffix if settings.table_suffix is not None else "")
        return f"{self.table_name}{suffix}"

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
            
            query_map = {'ticketNumber': 'ticket_number', 'user': 'user_id', 'name': 'name', 'email': 'email', 'phone': 'phone', 'company': 'company', 'subject': 'subject', 'description': 'description', 'category': 'category', 'priority': 'priority', 'status': 'status', 'assignedTo': 'assigned_to', 'resolvedAt': 'resolved_at', 'closedAt': 'closed_at'}
            query_map["_id"] = "id"
            query_map["externalId"] = "external_id"
            
            for k, v in kwargs.items():
                db_col = query_map.get(k, k)
                conditions.append(f"{db_col} = :{k}")
                params[k] = v
                
            where_clause = " AND ".join(conditions)
            q = text(f"SELECT * FROM {self.TABLE} WHERE {where_clause} LIMIT 1")
            result = await session.execute(q, params)
            row = result.fetchone()
            if not row:
                return None
                
            children_map = await self._fetch_children(session, [int(row.id)]) if True else {}
            return self._map_to_schema(row, children_map.get(int(row.id), {}))
            
    async def findAll(self, query: Optional[Dict[str, Any]] = None) -> List[Any]:
        query = query or {}
        async with self._factory()() as session:
            sql = f"SELECT * FROM {self.TABLE}"
            params = {}
            
            query_map = {'ticketNumber': 'ticket_number', 'user': 'user_id', 'name': 'name', 'email': 'email', 'phone': 'phone', 'company': 'company', 'subject': 'subject', 'description': 'description', 'category': 'category', 'priority': 'priority', 'status': 'status', 'assignedTo': 'assigned_to', 'resolvedAt': 'resolved_at', 'closedAt': 'closed_at'}
            query_map["_id"] = "id"
            query_map["externalId"] = "external_id"
            
            if query:
                conditions = []
                for k, v in query.items():
                    db_col = query_map.get(k, k)
                    conditions.append(f"{db_col} = :{k}")
                    params[k] = v
                if conditions:
                    sql += " WHERE " + " AND ".join(conditions)
                    
            q = text(sql)
            result = await session.execute(q, params)
            rows = result.fetchall()
            
            if not rows:
                return []
                
            children_map = await self._fetch_children(session, [int(r.id) for r in rows]) if True else {}
            
            return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]

    async def create(self, data: Any) -> Any:
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        params = {"eid": external_id, "c": now, "u": now}

        if data.ticketNumber is not None:
            cols.append("ticket_number")
            params["s_ticketNumber"] = data.ticketNumber

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

        if data.assignedTo is not None:
            cols.append("assigned_to")
            params["s_assignedTo"] = data.assignedTo

        if data.resolvedAt is not None:
            cols.append("resolved_at")
            params["s_resolvedAt"] = data.resolvedAt

        if data.closedAt is not None:
            cols.append("closed_at")
            params["s_closedAt"] = data.closedAt

        col_sql = ", ".join(cols)
        val_sql = ", ".join([":eid", ":c", ":u"] + [f":s_{k}" for k in ['ticketNumber', 'user', 'name', 'email', 'phone', 'company', 'subject', 'description', 'category', 'priority', 'status', 'assignedTo', 'resolvedAt', 'closedAt'] if f"s_{k}" in params] + [f":c_{k}" for k in [] if f"c_{k}" in params])
        
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

        if data.ticketNumber is not None:
            updates.append("ticket_number = :s_ticketNumber")
            params["s_ticketNumber"] = data.ticketNumber

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

        if data.assignedTo is not None:
            updates.append("assigned_to = :s_assignedTo")
            params["s_assignedTo"] = data.assignedTo

        if data.resolvedAt is not None:
            updates.append("resolved_at = :s_resolvedAt")
            params["s_resolvedAt"] = data.resolvedAt

        if data.closedAt is not None:
            updates.append("closed_at = :s_closedAt")
            params["s_closedAt"] = data.closedAt

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

            await session.execute(text(f"DELETE FROM sj_ticket_attachments WHERE parent_id = :id"), {"id": pk})

            await session.execute(text(f"DELETE FROM sj_ticket_responses WHERE parent_id = :id"), {"id": pk})

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
        rm = r._mapping
        out = {
            "_id": str(rm["id"]), 
            "externalId": rm["external_id"]
        }
        
        created_at = rm["created_at"]
        if created_at:
            out["createdAt"] = created_at.isoformat()
            
        updated_at = rm["updated_at"]
        if updated_at:
            out["updatedAt"] = updated_at.isoformat()

        out["ticketNumber"] = rm["ticket_number"]
        out["user"] = rm["user_id"]
        out["name"] = rm["name"]
        out["email"] = rm["email"]
        out["phone"] = rm["phone"]
        out["company"] = rm["company"]
        out["subject"] = rm["subject"]
        out["description"] = rm["description"]
        out["category"] = rm["category"]
        out["priority"] = rm["priority"]
        out["status"] = rm["status"]
        out["assignedTo"] = rm["assigned_to"]
        out["resolvedAt"] = rm["resolved_at"]
        out["closedAt"] = rm["closed_at"]
        for k, v in children.items():
            out[k] = v
            
        return SupportTicketInternal(**out)

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

    async def _replace_children(self, session, row_id: int, data: Any):

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
