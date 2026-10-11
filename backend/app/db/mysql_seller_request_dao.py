from app.models.daos import SellerRequestInternalCreate, SellerRequestInternalUpdate
import logging
"""
MySQL DAO for sj_seller_requests. Implements FileStorage-like interface.
"""

import secrets
from datetime import datetime
from typing import Any, List, Optional, Tuple
from app.models.seller_request import SellerRequest, SellerRequestResponseItem

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

    async def _fetch_children(self, session, req_ids: List[int]) -> Tuple[List[Any], List[Any]]:
        if not req_ids:
            return [], []
        chunks = [req_ids[i : i + 999] for i in range(0, len(req_ids), 999)]
        all_att = []
        all_resp = []
        for chunk in chunks:
            chunk_params = {f"rid_{i}": rid for i, rid in enumerate(chunk)}
            placeholders = ", ".join([f":{k}" for k in chunk_params.keys()])

            # Attachments
            att_res = await session.execute(
                text(f"SELECT request_id, url FROM sj_seller_request_attachments WHERE request_id IN ({placeholders})"),
                chunk_params,
            )
            all_att.extend(att_res.fetchall())

            # Responses
            resp_res = await session.execute(
                text(
                    f"SELECT request_id, admin_id, response_text, created_at FROM sj_seller_request_responses WHERE request_id IN ({placeholders}) ORDER BY id ASC"
                ),
                chunk_params,
            )
            all_resp.extend(resp_res.fetchall())
        return all_att, all_resp

    async def _replace_children(
        self,
        session,
        req_id: int,
        attachments: Optional[List[str]] = None,
        responses: Optional[List[SellerRequestResponseItem]] = None,
    ) -> None:
        if attachments is not None:
            await session.execute(
                text("DELETE FROM sj_seller_request_attachments WHERE request_id = :rid"), {"rid": req_id}
            )
            for url in attachments:
                await session.execute(
                    text("INSERT INTO sj_seller_request_attachments (request_id, url) VALUES (:rid, :url)"),
                    {"rid": req_id, "url": url},
                )

        if responses is not None:
            await session.execute(text("DELETE FROM sj_seller_request_responses WHERE request_id = :rid"), {"rid": req_id})
            for resp in responses:
                await session.execute(
                    text(
                        "INSERT INTO sj_seller_request_responses (request_id, admin_id, response_text, created_at) VALUES (:rid, :admin, :text, :c)"
                    ),
                    {
                        "rid": req_id,
                        "admin": resp.admin_id,
                        "text": resp.response,
                        "c": resp.created_at or now_utc(),
                    },
                )

    async def findAll(
        self,
        id: Optional[int] = None,
        user: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        subject: Optional[str] = None,
        request_number: Optional[str] = None,
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
        if category is not None:
            where_clauses.append("category = :category")
            params["category"] = str(category)
        if subject is not None:
            where_clauses.append("subject = :subject")
            params["subject"] = str(subject)
        if request_number is not None:
            where_clauses.append("request_number = :request_number")
            params["request_number"] = str(request_number)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        async with factory() as session:
            result = await session.execute(
                text(f"""
                    SELECT id, external_id, request_number, user_id, subject, description, category,
                           priority, status, resolved_at, closed_at, created_at, updated_at
                    FROM {self.TABLE} WHERE {where_sql} ORDER BY created_at DESC, id DESC
                """),
                params,
            )
            rows = result.fetchall()
            att_rows, resp_rows = await self._fetch_children(session, [int(r.id) for r in rows])
        return [
            self._map_row(
                r,
                attachments=[str(a.url) for a in att_rows if int(a.request_id) == int(r.id)],
                responses=[
                    SellerRequestResponseItem(
                        admin_id=resp.admin_id,
                        response=resp.response_text,
                        created_at=resp.created_at,
                    )
                    for resp in resp_rows
                    if int(resp.request_id) == int(r.id)
                ],
            )
            for r in rows
        ]

    async def findOne(
        self,
        id: Optional[int] = None,
        user: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> Optional[SellerRequest]:
        records = await self.findAll(id=id, user=user, status=status, priority=priority)
        return records[0] if records else None

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
            att_rows, resp_rows = await self._fetch_children(session, [int(row.id)])
            return self._map_row(
                row,
                attachments=[str(a.url) for a in att_rows if int(a.request_id) == int(row.id)],
                responses=[
                    SellerRequestResponseItem(
                        admin_id=resp.admin_id,
                        response=resp.response_text,
                        created_at=resp.created_at,
                    )
                    for resp in resp_rows
                    if int(resp.request_id) == int(row.id)
                ],
            )

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
            await self._replace_children(
                session,
                int(new_id),
                attachments=data.attachments or [],
                responses=data.responses or [],
            )
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

        oid = int(existing.id) if existing.id and str(existing.id).isdigit() else (int(id) if str(id).isdigit() else None)
        updates = ["updated_at = :updated_at"]
        params = {"id": oid, "updated_at": now}

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
            if update_data.attachments is not None or update_data.responses is not None:
                await self._replace_children(
                    session,
                    params["id"],
                    attachments=update_data.attachments,
                    responses=update_data.responses,
                )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        is_digit = str(id).isdigit()
        async with factory() as session:
            if is_digit:
                req_id = int(id)
            else:
                find_res = await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"),
                    {"eid": str(id)},
                )
                row = find_res.fetchone()
                if not row:
                    return False
                req_id = int(row.id)

            await session.execute(
                text("DELETE FROM sj_seller_request_attachments WHERE request_id = :rid"),
                {"rid": req_id},
            )
            await session.execute(
                text("DELETE FROM sj_seller_request_responses WHERE request_id = :rid"),
                {"rid": req_id},
            )
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :rid"),
                {"rid": req_id},
            )
            await session.commit()
            return result.rowcount > 0

