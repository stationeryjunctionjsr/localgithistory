from app.models.daos import SessionInternalCreate, SessionInternalUpdate, DeviceSnippet
from app.models.analytics_schemas import (
    SessionsByDeviceResponse,
    SessionsByLocationResponse,
    AllUserEngagementResponse,
    DurationBucket,
    UserMetric,
    UserEngagementResponse,
)
import logging
"""
MySQL DAO for sj_sessions. Implements FileStorage-like interface for 'sessions'.
"""

from datetime import datetime
from typing import List, Optional, Union
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

    async def get_sessions_by_location_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[SessionsByLocationResponse]:
        where_clauses = []
        params = {}
        if start_date:
            where_clauses.append("s.start_time >= :start_date")
            params["start_date"] = start_date
        if end_date:
            where_clauses.append("s.start_time <= :end_date")
            params["end_date"] = end_date

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        sql = text(
            f"""
            SELECT 
                COALESCE(NULLIF(TRIM(a.city), ''), NULLIF(TRIM(a.state), ''), 'Unknown') AS location,
                COUNT(DISTINCT s.session_id) AS sessions
            FROM sj_analytics_sessions s
            LEFT JOIN sj_users u ON (s.user_id = u.id OR s.user_id = u.external_id)
            LEFT JOIN (
                SELECT user_id, city, state,
                       ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY is_primary DESC, id ASC) as rn
                FROM sj_user_addresses
            ) a ON a.user_id = u.id AND a.rn = 1
            {where_sql}
            GROUP BY location
            ORDER BY sessions DESC
            """
        )
        async_session = get_async_session_factory()
        async with async_session() as session:
            rows = (await session.execute(sql, params)).fetchall()
            return [
                SessionsByLocationResponse(
                    location=r.location,
                    sessions=r.sessions or 0,
                )
                for r in rows
            ]

    async def get_all_user_engagement_aggregate_stats(self) -> AllUserEngagementResponse:
        sql = text(
            f"""
            WITH user_session_agg AS (
                SELECT 
                    u.id AS user_id,
                    COALESCE(u.name, 'Unknown') AS name,
                    COALESCE(u.email, 'Unknown') AS email,
                    COALESCE(
                        ROUND(AVG(
                            CASE 
                                WHEN TIMESTAMPDIFF(SECOND, s.created_at, COALESCE(s.revoked_at, s.last_active_at, NOW())) >= 0 
                                THEN TIMESTAMPDIFF(SECOND, s.created_at, COALESCE(s.revoked_at, s.last_active_at, NOW()))
                                ELSE 0 
                            END
                        ), 2),
                        0.0
                    ) AS average_session_time_seconds,
                    COUNT(s.id) AS total_sessions
                FROM sj_users u
                LEFT JOIN {self.TABLE} s ON s.user_id = u.id AND s.is_guest = 0
                GROUP BY u.id, u.name, u.email
            )
            SELECT 
                user_id,
                name,
                email,
                average_session_time_seconds,
                total_sessions
            FROM user_session_agg
            ORDER BY user_id ASC
            """
        )
        async_session = get_async_session_factory()
        async with async_session() as session:
            rows = (await session.execute(sql)).fetchall()
            buckets = {"0-60s": 0, "60-300s": 0, "300-600s": 0, "600s+": 0}
            user_metrics = []
            for r in rows:
                avg_time = float(r.average_session_time_seconds or 0.0)
                if avg_time <= 60:
                    buckets["0-60s"] += 1
                elif avg_time <= 300:
                    buckets["60-300s"] += 1
                elif avg_time <= 600:
                    buckets["300-600s"] += 1
                else:
                    buckets["600s+"] += 1

                user_metrics.append(
                    UserMetric(
                        userId=str(r.user_id),
                        name=r.name,
                        email=r.email,
                        averageSessionTimeSeconds=avg_time,
                        totalSessions=r.total_sessions or 0,
                    )
                )

            return AllUserEngagementResponse(
                duration_buckets=[DurationBucket(range=k, count=v) for k, v in buckets.items()],
                user_metrics=user_metrics,
            )

    async def get_user_engagement_metrics_stats(self, user_id: Union[int, str]) -> UserEngagementResponse:
        user_sql = text("SELECT id, created_at FROM sj_users WHERE id = :user_id OR external_id = :user_id LIMIT 1")
        async_session = get_async_session_factory()
        async with async_session() as session:
            user_row = (await session.execute(user_sql, {"user_id": str(user_id)})).fetchone()
            if not user_row:
                return UserEngagementResponse(
                    error="User not found",
                    totalSessions=0,
                    sessionsWithOrder=0,
                )

            uid = user_row.id
            reg_dt = user_row.created_at
            params = {"uid": uid, "reg_dt": reg_dt}

            # 1. Total sessions and average duration
            sess_sql = text(
                f"""
                SELECT 
                    COUNT(s.id) AS total_sessions,
                    ROUND(AVG(
                        CASE 
                            WHEN TIMESTAMPDIFF(SECOND, s.created_at, COALESCE(s.revoked_at, s.last_active_at, NOW())) >= 0 
                            THEN TIMESTAMPDIFF(SECOND, s.created_at, COALESCE(s.revoked_at, s.last_active_at, NOW()))
                            ELSE 0 
                        END
                    ), 2) AS average_session_time_seconds
                FROM {self.TABLE} s
                WHERE s.user_id = :uid AND s.is_guest = 0
                  AND (:reg_dt IS NULL OR s.created_at >= :reg_dt)
                """
            )
            row_sess = (await session.execute(sess_sql, params)).fetchone()
            total_sessions = row_sess.total_sessions or 0 if row_sess else 0
            avg_session_time = float(row_sess.average_session_time_seconds) if row_sess and row_sess.average_session_time_seconds is not None else None

            # 2. Average days between consecutive sessions using LAG()
            gaps_sql = text(
                f"""
                WITH user_sessions AS (
                    SELECT 
                        created_at,
                        LAG(created_at) OVER (ORDER BY created_at ASC) AS prev_created_at
                    FROM {self.TABLE}
                    WHERE user_id = :uid AND is_guest = 0
                      AND (:reg_dt IS NULL OR created_at >= :reg_dt)
                )
                SELECT 
                    ROUND(AVG(TIMESTAMPDIFF(SECOND, prev_created_at, created_at) / 86400.0), 2) AS avg_days_between_sessions
                FROM user_sessions
                WHERE prev_created_at IS NOT NULL
                """
            )
            row_gaps = (await session.execute(gaps_sql, params)).fetchone()
            avg_days = float(row_gaps.avg_days_between_sessions) if row_gaps and row_gaps.avg_days_between_sessions is not None else None

            # 3. Average pages per session
            pages_sql = text(
                f"""
                WITH user_sess AS (
                    SELECT id
                    FROM {self.TABLE}
                    WHERE user_id = :uid AND is_guest = 0
                      AND (:reg_dt IS NULL OR created_at >= :reg_dt)
                )
                SELECT 
                    ROUND(AVG(COALESCE(pv.cnt, 0)), 2) AS avg_pages_per_session
                FROM user_sess s
                LEFT JOIN (
                    SELECT session_id, COUNT(*) AS cnt
                    FROM sj_tracking
                    WHERE event_type = 'page_view'
                    GROUP BY session_id
                ) pv ON pv.session_id = CAST(s.id AS CHAR)
                """
            )
            row_pages = (await session.execute(pages_sql, params)).fetchone()
            avg_pages = float(row_pages.avg_pages_per_session) if row_pages and row_pages.avg_pages_per_session is not None else None

            # 4. Sessions with orders
            orders_sql = text(
                """
                SELECT 
                    COUNT(DISTINCT o.session_id) AS sessions_with_order
                FROM sj_orders o
                WHERE o.user_id = :uid
                  AND (:reg_dt IS NULL OR o.created_at >= :reg_dt)
                  AND o.session_id IS NOT NULL AND o.session_id != ''
                """
            )
            row_orders = (await session.execute(orders_sql, params)).fetchone()
            sessions_with_order = row_orders.sessions_with_order or 0 if row_orders else 0
            session_order_rate = round(sessions_with_order / total_sessions, 4) if total_sessions > 0 else None

            reg_str = reg_dt.isoformat() if isinstance(reg_dt, datetime) else (str(reg_dt) if reg_dt else None)

            return UserEngagementResponse(
                userId=str(user_id),
                registrationDate=reg_str,
                totalSessions=total_sessions,
                averageSessionTimeSeconds=avg_session_time,
                averageDaysBetweenSessions=avg_days,
                averagePagesPerSession=avg_pages,
                sessionsWithOrder=sessions_with_order,
                sessionOrderRate=session_order_rate,
            )

    find_all = findAll
    find_by_id = findById
    find_one = findOne
    touch_session = touch

