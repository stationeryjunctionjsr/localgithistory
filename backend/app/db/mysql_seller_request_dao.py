from app.models.daos import SellerRequestInternalCreate, SellerRequestInternalUpdate
import logging
"""
MySQL DAO for sj_seller_requests. Implements FileStorage-like interface.
"""

import secrets
from datetime import datetime
from collections import defaultdict
from typing import List, Optional, Tuple, Union
from app.models.seller_request import SellerRequest, SellerRequestResponseItem
from app.models.schemas import TicketResponseItem

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

    def _map_row(self, r, attachments: List[str], responses: List[SellerRequestResponseItem]) -> SellerRequest:
        sr = SellerRequest.model_validate(r)
        sr.user = str(r.user_id) if r.user_id is not None else None
        sr.attachments = attachments
        sr.responses = responses
        return sr

    async def _fetch_children(self, session, req_ids: List[int]) -> Tuple[defaultdict[int, List[str]], defaultdict[int, List[SellerRequestResponseItem]]]:
        att_map: defaultdict[int, List[str]] = defaultdict(list)
        resp_map: defaultdict[int, List[SellerRequestResponseItem]] = defaultdict(list)
        if not req_ids:
            return att_map, resp_map
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
                att_map[r.request_id].append(r.url)

            # Responses
            resp_res = await session.execute(
                text(
                    f"SELECT request_id, admin_id, response_text, created_at FROM sj_seller_request_responses WHERE request_id IN ({placeholders}) ORDER BY id ASC"
                ),
                chunk_params,
            )
            for r in resp_res.fetchall():
                resp_map[r.request_id].append(
                    SellerRequestResponseItem(
                        admin_id=r.admin_id,
                        response=r.response_text,
                        created_at=r.created_at,
                    )
                )
        return att_map, resp_map

    async def _replace_children(self, session, req_id: int, data: Union['SellerRequestInternalCreate', 'SellerRequestInternalUpdate']):
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
            if isinstance(resp, TicketResponseItem):
                admin_id = resp.user
                response_text = resp.message
                created_at = resp.created_at or now_utc()
            else:
                admin_id = resp.admin_id
                response_text = resp.response
                created_at = resp.created_at or now_utc()
            await session.execute(
                text(
                    "INSERT INTO sj_seller_request_responses (request_id, admin_id, response_text, created_at) VALUES (:rid, :admin, :text, :c)"
                ),
                {
                    "rid": req_id,
                    "admin": admin_id,
                    "text": response_text,
                    "c": created_at,
                },
            )

    async def findAll(
        self,
        id: Optional[int] = None,
        user: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> List[SellerRequest]:
        factory = self._factory()
        if not factory:
            return []

        where_clauses = []
        params = {}
        if id is not None:
            where_clauses.append("id = :id")
            params["id"] = int(id)
        if user is not None:
            where_clauses.append("user_id = :user_id")
            params["user_id"] = str(user)
        if status is not None:
            where_clauses.append("status = :status")
            params["status"] = str(status)
        if priority is not None:
            where_clauses.append("priority = :priority")
            params["priority"] = str(priority)

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
            att_map, resp_map = await self._fetch_children(session, [int(r.id) for r in rows])
        return [self._map_row(r, att_map[int(r.id)], resp_map[int(r.id)]) for r in rows]

    async def findOne(
        self,
        id: Optional[int] = None,
        user: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> Optional[SellerRequest]:
        docs = await self.findAll(id=id, user=user, status=status, priority=priority)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[SellerRequest]:
        if str(id).isdigit():
            return await self.findOne(id=int(id))
        factory = self._factory()
        if not factory:
            return None
        async with factory() as session:
            result = await session.execute(
                text(f"""
                    SELECT id, external_id, request_number, user_id, subject, description, category,
                           priority, status, resolved_at, closed_at, created_at, updated_at
                    FROM {self.TABLE} WHERE external_id = :eid ORDER BY id ASC LIMIT 1
                """),
                {"eid": str(id)},
            )
            row = result.fetchone()
            if not row:
                return None
            att_map, resp_map = await self._fetch_children(session, [int(row.id)])
            return self._map_row(row, att_map[int(row.id)], resp_map[int(row.id)])

    async def create(self, data: 'SellerRequestInternalCreate') -> Optional[SellerRequest]:
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
                logging.warning("seller_request.to_dt: could not parse datetime %r: %s", val, e, exc_info=e)
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

    async def update(self, id: str, update_data: 'SellerRequestInternalUpdate') -> Optional[SellerRequest]:
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
                logging.warning("seller_request.to_dt: could not parse datetime %r: %s", val, e, exc_info=e)
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
                            "created_at": to_dt(comment.created_at) or now,
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

