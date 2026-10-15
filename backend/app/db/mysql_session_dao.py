from app.models.daos import SessionInternalCreate, SessionInternalUpdate, DeviceSnippet
from app.models.analytics_schemas import SessionsByDeviceResponse
import logging
"""
MySQL DAO for sj_sessions. Implements FileStorage-like interface for 'sessions'.
"""

from datetime import datetime
from typing import List, Optional
from app.models.session import Session

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc


class MySQLSessionDAO:
    @property
    def TABLE(self):
        return "sj_sessions"

    def _map_to_schema(self, r) -> Session:
        return Session.model_validate(r)

    async def findAll(
        self,
        id: Optional[int] = None,
        user_id: Optional[int] = None,
        refresh_token_id: Optional[str] = None,
        status: Optional[str] = None,
        is_guest: Optional[bool] = None,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Session]:
        where_clauses = []
        params = {}
        if id is not None:
            where_clauses.append("id = :id")
            params["id"] = id
        if user_id is not None:
            where_clauses.append("user_id = :user_id")
            params["user_id"] = user_id
        if refresh_token_id is not None:
            where_clauses.append("refresh_token_id = :refresh_token_id")
            params["refresh_token_id"] = str(refresh_token_id)
        if status is not None:
            where_clauses.append("status = :status")
            params["status"] = str(status)
        if is_guest is not None:
            where_clauses.append("is_guest = :is_guest")
            params["is_guest"] = 1 if is_guest else 0

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        pagination_sql = ""
        if limit is not None:
            pagination_sql += f" LIMIT {limit}"
        if skip is not None:
            pagination_sql += f" OFFSET {skip}"

        async_session = get_async_session_factory()
        async with async_session() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id, user_id, refresh_token_id, status, last_active_at,
                           revoked_at, revoked_reason, is_guest, comments, created_at, updated_at
                    FROM {self.TABLE} {where_sql} ORDER BY id DESC {pagination_sql}
                    """
                ),
                params,
            )
            rows = result.fetchall()
        return [self._map_to_schema(r) for r in rows]

    async def findOne(
        self,
        id: Optional[int] = None,
        user_id: Optional[int] = None,
        refresh_token_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Optional[Session]:
        where_clauses = []
        params = {}
        if id is not None:
            where_clauses.append("id = :id")
            params["id"] = id
        if user_id is not None:
            where_clauses.append("user_id = :user_id")
            params["user_id"] = user_id
        if refresh_token_id is not None:
            where_clauses.append("refresh_token_id = :refresh_token_id")
            params["refresh_token_id"] = str(refresh_token_id)
        if status is not None:
            where_clauses.append("status = :status")
            params["status"] = str(status)

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        async_session = get_async_session_factory()
        async with async_session() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id, user_id, refresh_token_id, status, last_active_at,
                           revoked_at, revoked_reason, is_guest, comments, created_at, updated_at
                    FROM {self.TABLE} {where_sql} LIMIT 1
                    """
                ),
                params,
            )
            row = result.fetchone()
        return self._map_to_schema(row) if row else None

    async def findById(self, id: int) -> Optional['Session']:
        if not id:
            return None
        async_session = get_async_session_factory()
        async with async_session() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id, user_id, refresh_token_id, status, last_active_at,
                           revoked_at, revoked_reason, is_guest, comments, created_at, updated_at
                    FROM {self.TABLE} WHERE id = :id
                    """
                ),
                {"id": id},
            )
            row = result.fetchone()
        return self._map_to_schema(row) if row else None

    async def create(self, data: 'SessionInternalCreate') -> Optional[Session]:
        now = now_utc()
        user_id = data.user_id

        async_session = get_async_session_factory()
        async with async_session() as session:
            result = await session.execute(
                text(
                    f"""
                    INSERT INTO {self.TABLE} (
                        user_id, refresh_token_id, status, last_active_at,
                        revoked_at, revoked_reason, is_guest, comments, created_at, updated_at
                    ) VALUES (
                        :user_id, :refresh_token_id, :status, :last_active_at,
                        :revoked_at, :revoked_reason, :is_guest, :comments, :created_at, :updated_at
                    )
                    """
                ),
                {
                    "user_id": user_id,
                    "refresh_token_id": data.refresh_token_id,
                    "status": data.status,
                    "last_active_at": data.last_active_at,
                    "revoked_at": data.revoked_at,
                    "revoked_reason": data.revoked_reason,
                    "is_guest": 1 if data.is_guest else 0,
                    "comments": data.comment,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            await session.commit()
            new_id = result.lastrowid
        return await self.findById(new_id)

    async def update(self, id: int, update_data: SessionInternalUpdate) -> Optional[Session]:
        if not id:
            return None

        now = now_utc()
        updates = ["updated_at = :updated_at"]
        params = {"id": id, "updated_at": now}

        if "user_id" in update_data.model_fields_set:
            updates.append("user_id = :user_id")
            params["user_id"] = update_data.user_id

        if "refresh_token_id" in update_data.model_fields_set:
            updates.append("refresh_token_id = :refresh_token_id")
            params["refresh_token_id"] = str(update_data.refresh_token_id) if update_data.refresh_token_id is not None else None

        if "status" in update_data.model_fields_set:
            updates.append("status = :status")
            params["status"] = str(update_data.status) if update_data.status is not None else None

        if "last_active_at" in update_data.model_fields_set:
            updates.append("last_active_at = :last_active_at")
            params["last_active_at"] = update_data.last_active_at

        if "revoked_at" in update_data.model_fields_set:
            updates.append("revoked_at = :revoked_at")
            params["revoked_at"] = update_data.revoked_at

        if "revoked_reason" in update_data.model_fields_set:
            updates.append("revoked_reason = :revoked_reason")
            params["revoked_reason"] = update_data.revoked_reason

        if "is_guest" in update_data.model_fields_set:
            updates.append("is_guest = :is_guest")
            params["is_guest"] = 1 if update_data.is_guest else 0

        if "comment" in update_data.model_fields_set:
            updates.append("comments = :comments")
            params["comments"] = update_data.comment
        elif "comments" in update_data.model_fields_set:
            updates.append("comments = :comments")
            params["comments"] = update_data.comments

        set_sql = ", ".join(updates)
        async_session = get_async_session_factory()
        async with async_session() as session:
            result = await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
            if result.rowcount == 0:
                chk = await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE id = :id"), {"id": id})
                if not chk.fetchone():
                    return None

        return await self.findById(id)

    async def touch(self, session_id: int, device: Optional[DeviceSnippet] = None) -> None:
        """Lightweight session touch — single UPDATE with SQL-level 60s debounce. Fire-and-forget."""
        if not session_id:
            return
        now = now_utc()
        from datetime import timedelta
        throttle_time = now - timedelta(seconds=60)
        try:
            async_session = get_async_session_factory()
            async with async_session() as session:
                await session.execute(
                    text(
                        f"""
                        UPDATE {self.TABLE}
                        SET last_active_at = :now, updated_at = :now
                        WHERE id = :id AND status = 'active'
                          AND (last_active_at IS NULL OR last_active_at < :throttle)
                        """
                    ),
                    {"now": now, "id": session_id, "throttle": throttle_time},
                )
                await session.commit()
        except Exception as e:
            logging.warning("mysql_session_dao.touch: failed for session %s: %s", session_id, e, exc_info=e)

    async def revoke_active_for_user(
        self,
        user_id: int,
        reason: str,
        exclude_session_id: Optional[int] = None,
    ) -> int:
        """Revoke all active sessions for a user in a single UPDATE.

        Much more efficient than findAll() + Python loop + N individual UPDATEs.
        Returns the number of sessions revoked.
        """
        if user_id is None:
            return 0
        now = now_utc()
        params: dict = {
            "user_id": user_id,
            "reason": reason,
            "now": now,
        }
        exclude_clause = ""
        if exclude_session_id:
            exclude_clause = "AND id != :exclude_id"
            params["exclude_id"] = exclude_session_id
        try:
            async_session = get_async_session_factory()
            async with async_session() as session:
                result = await session.execute(
                    text(
                        f"""
                        UPDATE {self.TABLE}
                        SET status = 'revoked',
                            revoked_at = :now,
                            revoked_reason = :reason,
                            updated_at = :now
                        WHERE user_id = :user_id
                          AND status = 'active'
                          {exclude_clause}
                        """
                    ),
                    params,
                )
                await session.commit()
                return result.rowcount
        except Exception as e:
            logging.warning(
                "mysql_session_dao.revoke_active_for_user: failed for user %s: %s", user_id, e, exc_info=e
            )
            return 0

    async def delete(self, id: int) -> bool:
        if not id:
            return False
        async_session = get_async_session_factory()
        async with async_session() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": id},
            )
            await session.commit()
            return result.rowcount > 0

    async def deleteMany(self, user_id: Optional[int] = None) -> int:
        """Delete matching sessions in a single SQL statement instead of N+1 deletes."""
        if user_id is None:
            return 0
        async_session = get_async_session_factory()
        async with async_session() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE user_id = :uid"),
                {"uid": user_id},
            )
            await session.commit()
        return result.rowcount

    async def delete_by_user_id(self, user_id: int) -> int:
        """Delete all sessions for a user with a single targeted SQL DELETE.
        Used in test teardown to avoid FK constraint violations."""
        return await self.deleteMany(user_id=user_id)

    async def count(
        self,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> int:
        """Count sessions using SELECT COUNT(*) — never loads row data."""
        where_clauses = []
        params = {}
        if user_id is not None:
            where_clauses.append("user_id = :user_id")
            params["user_id"] = user_id
        if status is not None:
            where_clauses.append("status = :status")
            params["status"] = str(status)
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        async_session = get_async_session_factory()
        async with async_session() as session:
            result = await session.execute(text(f"SELECT COUNT(*) FROM {self.TABLE} {where_sql}"), params)
            return int(result.scalar() or 0)

    async def get_sessions_by_device_type_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[SessionsByDeviceResponse]:
        where_clauses = []
        params = {}
        if start_date:
            where_clauses.append("start_time >= :start_date")
            params["start_date"] = start_date
        if end_date:
            where_clauses.append("start_time <= :end_date")
            params["end_date"] = end_date

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        sql = text(
            f"""
            SELECT 
                COALESCE(LOWER(NULLIF(device_type, '')), 'desktop') AS device,
                COUNT(*) AS sessions
            FROM sj_analytics_sessions
            {where_sql}
            GROUP BY device
            ORDER BY sessions DESC
            """
        )
        async_session = get_async_session_factory()
        async with async_session() as session:
            rows = (await session.execute(sql, params)).fetchall()
            return [
                SessionsByDeviceResponse(
                    device=r.device,
                    sessions=r.sessions or 0,
                )
                for r in rows
            ]

    find_all = findAll
    find_by_id = findById
    find_one = findOne
    touch_session = touch

