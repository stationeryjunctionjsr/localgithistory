from app.models.daos import SellerRequestInternalCreate, SellerRequestInternalUpdate
import logging
"""
MySQL DAO for sj_seller_requests. Implements FileStorage-like interface.
"""

import secrets
from datetime import datetime
from typing import Dict
from app.models.seller_request import SellerRequest, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc


class MySQLSellerRequestDAO:
    @property
    def TABLE(self):
        return "sj_seller_requests"

    def _factory(self):
        return get_async_session_factory()

    def _map_row(self, r, children: Dict) -> Dict:
        d = dict(r._mapping)
        d["user"] = d.pop("user_id")
        d["attachments"] = children.get("attachments", [])
        d["responses"] = children.get("responses", [])
        return d

    async def _fetch_children(self, session, req_ids: List[int]) -> Dict[int, Dict]:
        children_map = {rid: {"attachments": [], "responses": []} for rid in req_ids}
        if not req_ids:
            return children_map
        chunks = [req_ids[i : i + 999] for i in range(0, len(req_ids), 999)]
        for chunk in chunks:
            chunk_params = {f"rid_{i}": rid for i, rid in enumerate(chunk)}
            placeholders = ", ".join([f":{k}" for k in chunk_params.keys()])

            # Attachments
            att_res = await session.execute(
                text(f"SELECT request_id, url FROM sj_seller_request_attachments WHERE request_id IN ({placeholders})"),
                chunk_params,
            )
            for r in att_res.fetchall():
                children_map[r.request_id]["attachments"].append(r.url)

            # Responses
            resp_res = await session.execute(
                text(
                    f"SELECT request_id, admin_id, response_text, created_at FROM sj_seller_request_responses WHERE request_id IN ({placeholders}) ORDER BY id ASC"
                ),
                chunk_params,
            )
            for r in resp_res.fetchall():
                children_map[r.request_id]["responses"].append(
                    {
                        "adminId": r.admin_id,
                        "response": r.response_text,
                        "createdAt": r.created_at.isoformat() if r.created_at else None,
                    }
                )
        return children_map

    async def _replace_children(self, session, req_id: int, data: Dict):
        await session.execute(
            text("DELETE FROM sj_seller_request_attachments WHERE request_id = :rid"), {"rid": req_id}
        )
        await session.execute(text("DELETE FROM sj_seller_request_responses WHERE request_id = :rid"), {"rid": req_id})

        for url in (data.attachments if data.attachments is not None else []):
            await session.execute(
                text("INSERT INTO sj_seller_request_attachments (request_id, url) VALUES (:rid, :url)"),
                {"rid": req_id, "url": url},
            )

        for resp in (data.responses if data.responses is not None else []):
            created_at = None
            if (resp["createdAt"] if "createdAt" in resp else None):
                try:
                    created_at = datetime.fromisoformat(resp["createdAt"].replace("Z", "+00:00"))
                except Exception as e:
                    logging.warning("Background task failed", exc_info=e)
            if not created_at:
                created_at = now_utc()
            await session.execute(
                text(
                    "INSERT INTO sj_seller_request_responses (request_id, admin_id, response_text, created_at) VALUES (:rid, :admin, :text, :c)"
                ),
                {
                    "rid": req_id,
                    "admin": (resp["adminId"] if "adminId" in resp else None),
                    "text": (resp["response"] if "response" in resp else None) or (resp["text"] if "text" in resp else None),
                    "c": created_at,
                },
            )

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        factory = self._factory()
        if not factory:
            return []

        where_clauses = []
        params = {}
        if query:
            for k, v in query.items():
                if k in ("_id", "id"):
                    where_clauses.append("id = :id")
                    params["id"] = int(v) if str(v).isdigit() else None
                elif k == "user":
                    where_clauses.append("user_id = :user_id")
                    params["user_id"] = str(v)
                elif k == "status":
                    where_clauses.append("status = :status")
                    params["status"] = str(v)
                elif k == "priority":
                    where_clauses.append("priority = :priority")
                    params["priority"] = str(v)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        async with factory() as session:
            result = await session.execute(
                text(f"""
                    SELECT id, external_id, request_number, user_id, subject, description, category,
                           priority, status, resolved_at, closed_at, created_at, updated_at
                    FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC
                """),
                params,
            )
            rows = result.fetchall()
            children_map = await self._fetch_children(session, [int(r.id) for r in rows])
        return [SellerRequest.model_validate(self._map_row(r, children_map[int(r.id)]) ) for r in rows]

    async def findOne(self, query: Dict) -> Optional[Dict]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        return await self.findOne({"_id": id})

    async def create(self, data: 'SellerRequestInternalCreate') -> Dict:
        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        now = now_utc()
        external_id = secrets.token_hex(16)
        req_number = f"REQ-{now.strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"

        def to_dt(val):
            if not val:
                return None
            try:
                return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
            except Exception as e:
                logging.warning("Background task failed", exc_info=e)
                return None

        async with factory() as session:
            await session.execute(
                text(f"""
                    INSERT INTO {self.TABLE} (
                        external_id, request_number, user_id, subject, description, category, priority, status,
                        resolved_at, closed_at, created_at, updated_at
                    ) VALUES (
                        :external_id, :request_number, :user_id, :subject, :description, :category, :priority, :status,
                        :resolved_at, :closed_at, :created_at, :updated_at
                    )
                """),
                {
                    "external_id": external_id,
                    "request_number": req_number,
                    "user_id": data.user,
                    "subject": (data.subject if data.subject is not None else ""),
                    "description": (data.description if data.description is not None else ""),
                    "category": (data.category if data.category is not None else "general"),
                    "priority": (data.priority if data.priority is not None else "medium"),
                    "status": (data.status if data.status is not None else "open"),
                    "resolved_at": to_dt(data.resolved_at),
                    "closed_at": to_dt(data.closed_at),
                    "created_at": now,
                    "updated_at": now,
                },
            )
            new_id = (
                await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": external_id}
                )
            ).scalar()
            await self._replace_children(session, new_id, data)
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: 'SellerRequestInternalUpdate') -> Optional[Dict]:
        existing = await self.findById(id)
        if not existing:
            return None

        now = now_utc()
        factory = self._factory()

        def to_dt(val):
            if not val:
                return None
            try:
                return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
            except Exception as e:
                logging.warning("Background task failed", exc_info=e)
                return None

        updates = ["updated_at = :updated_at"]
        params = {"id": int(id) if str(id).isdigit() else None, "updated_at": now}

        if update_data.user is not None:
            updates.append("user_id = :user_id")
            params["user_id"] = update_data.user
        if update_data.subject is not None:
            updates.append("subject = :subject")
            params["subject"] = update_data.subject
        if update_data.description is not None:
            updates.append("description = :description")
            params["description"] = update_data.description
        if update_data.category is not None:
            updates.append("category = :category")
            params["category"] = update_data.category
        if update_data.priority is not None:
            updates.append("priority = :priority")
            params["priority"] = update_data.priority
        if update_data.status is not None:
            updates.append("status = :status")
            params["status"] = update_data.status
        if update_data.resolved_at is not None:
            updates.append("resolved_at = :resolved_at")
            params["resolved_at"] = to_dt(update_data.resolved_at)
        if update_data.closed_at is not None:
            updates.append("closed_at = :closed_at")
            params["closed_at"] = to_dt(update_data.closed_at)
            
        set_sql = ", ".join(updates)

        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            if update_data.comments is not None:
                await session.execute(
                    text(f"DELETE FROM {self.CHILD_TABLE} WHERE parent_id = :id"),
                    {"id": params["id"]},
                )
                for comment in update_data.comments:
                    await session.execute(
                        text(f"INSERT INTO {self.CHILD_TABLE} (parent_id, user_id, message, created_at) VALUES (:parent_id, :user_id, :message, :created_at)"),
                        {
                            "parent_id": params["id"],
                            "user_id": comment.user,
                            "message": comment.message,
                            "created_at": to_dt(getattr(comment, "created_at", None)) or now,
                        },
                    )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"), {"id": int(id) if str(id).isdigit() else None}
            )
            await session.commit()
            return result.rowcount > 0

    async def deleteMany(self, query: Dict) -> Dict:
        docs = await self.findAll(query)
        deleted = 0
        for d in docs:
            if await self.delete(d._id):
                deleted += 1
        return {"deletedCount": deleted}

    async def count(self, query: Optional[Dict] = None) -> int:
        return len(await self.findAll(query))
