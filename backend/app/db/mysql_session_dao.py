from app.models.daos import SessionInternalCreate, SessionInternalUpdate
import logging
"""
MySQL DAO for sj_sessions. Implements FileStorage-like interface for 'sessions'.
"""

import secrets
from datetime import datetime
from typing import Dict
from app.models.session import Session, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc


def _to_ts(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception as e:
        logging.warning("mysql_session_dao._to_ts: could not parse timestamp %r: %s", value, e, exc_info=e)
        return None


class MySQLSessionDAO:
    @property
    def TABLE(self):
        return "sj_sessions"

    def _factory(self):
        return get_async_session_factory()

    def _map_to_schema(self, r) -> 'Session':
        return Session.model_validate(r)

    async def findAll(self, query: Optional[Dict] = None) -> List['Session']:
        factory = self._factory()
        if not factory:
            return []
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id, external_id, user_id, refresh_token_id, status, last_active_at,
                           revoked_at, revoked_reason, is_guest, comments, created_at, updated_at
                    FROM {self.TABLE}
                    """
                )
            )
            rows = result.fetchall()
        docs = [self._map_to_schema(r) for r in rows]
        if not query:
            return docs
        filtered: list = []
        for d in docs:
            match = True
            for k, v in query.items():
                if k in ("_id", "id"):
                    if str(d.id) != str(v):
                        match = False
                        break
                elif (getattr(d, k, None) if hasattr(d, k) else None) != v:
                    match = False
                    break
            if match:
                filtered.append(d)
        return filtered

    async def findOne(self, query: Dict) -> Optional['Session']:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional['Session']:
        factory = self._factory()
        if not factory:
            return None
        sid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id, external_id, user_id, refresh_token_id, status, last_active_at,
                           revoked_at, revoked_reason, is_guest, comments, created_at, updated_at
                    FROM {self.TABLE} WHERE id = :id
                    """
                ),
                {"id": sid},
            )
            row = result.fetchone()
        return self._map_to_schema(row) if row else None

    async def create(self, data: 'SessionInternalCreate') -> Dict:
        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        now = now_utc()
        external_id = secrets.token_hex(16)
        user_id_raw = data.user_id
        user_id = int(user_id_raw) if str(user_id_raw or "").isdigit() else None
        if user_id is None and data.user_id is not None:
            raise ValueError("Session user must be numeric id when using MySQL")

        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    INSERT INTO {self.TABLE} (
                        external_id, user_id, refresh_token_id, status, last_active_at,
                        revoked_at, revoked_reason, is_guest, comments, created_at, updated_at
                    ) VALUES (
                        :external_id, :user_id, :refresh_token_id, :status, :last_active_at,
                        :revoked_at, :revoked_reason, :is_guest, :comments, :created_at, :updated_at
                    )
                    """
                ),
                {
                    "external_id": external_id,
                    "user_id": user_id,
                    "refresh_token_id": data.refresh_token_id,
                    "status": data.status,
                    "last_active_at": _to_ts(data.last_active_at),
                    "revoked_at": _to_ts(data.revoked_at),
                    "revoked_reason": data.revoked_reason,
                    "is_guest": 1 if data.is_guest else 0,
                    "comments": data.comment,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            await session.commit()
            r = await session.execute(
                text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"),
                {"eid": external_id},
            )
            new_id = r.scalar()
        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: 'SessionInternalUpdate') -> Optional['Session']:
        existing = await self.findById(id)
        if not existing:
            return None
        
        # update_data is SessionInternalUpdate. It uses userId, not user_id.
        # existing is Session. We can just use explicit properties.
        factory = self._factory()
        if not factory:
            return None
        
        now = now_utc()
        sid = int(id) if str(id).isdigit() else None
        
        # Extract fields from existing
        # existing is a Session object, which has user_id
        final_user_id = update_data.user_id if update_data.user_id is not None else existing.user_id
        final_refresh_token_id = update_data.refresh_token_id if update_data.refresh_token_id is not None else existing.refresh_token_id
        final_status = update_data.status if update_data.status is not None else existing.status
        final_last_active_at = update_data.last_active_at if update_data.last_active_at is not None else (existing.last_active_at.isoformat() if existing.last_active_at else None)
        final_revoked_at = update_data.revoked_at if update_data.revoked_at is not None else (existing.revoked_at.isoformat() if existing.revoked_at else None)
        final_revoked_reason = update_data.revoked_reason if update_data.revoked_reason is not None else existing.revoked_reason
        final_is_guest = update_data.is_guest if update_data.is_guest is not None else existing.is_guest
        final_comments = update_data.comment if update_data.comment is not None else existing.comments

        user_id = int(final_user_id) if str(final_user_id or "").isdigit() else None
        if user_id is None and final_user_id is not None:
            return None

        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    UPDATE {self.TABLE} SET
                        user_id = :user_id,
                        refresh_token_id = :refresh_token_id,
                        status = :status,
                        last_active_at = :last_active_at,
                        revoked_at = :revoked_at,
                        revoked_reason = :revoked_reason,
                        is_guest = :is_guest,
                        comments = :comments,
                        updated_at = :updated_at
                    WHERE id = :id
                    """
                ),
                {
                    "id": sid,
                    "user_id": user_id,
                    "refresh_token_id": final_refresh_token_id,
                    "status": final_status,
                    "last_active_at": _to_ts(final_last_active_at),
                    "revoked_at": _to_ts(final_revoked_at),
                    "revoked_reason": final_revoked_reason,
                    "is_guest": 1 if final_is_guest else 0,
                    "comments": final_comments,
                    "updated_at": now,
                },
            )
            await session.commit()
        return await self.findById(id)

    async def touch(self, session_id: str, device: dict = None) -> None:
        """Lightweight session touch — single UPDATE with SQL-level 60s debounce. Fire-and-forget."""
        factory = self._factory()
        if not factory:
            return
        sid = int(session_id) if str(session_id).isdigit() else None
        if not sid:
            return
        now = now_utc()
        from datetime import timedelta
        throttle_time = now - timedelta(seconds=60)
        try:
            async with factory() as session:
                await session.execute(
                    text(
                        f"""
                        UPDATE {self.TABLE}
                        SET last_active_at = :now, updated_at = :now
                        WHERE id = :id AND status = 'active'
                          AND (last_active_at IS NULL OR last_active_at < :throttle)
                        """
                    ),
                    {"now": now, "id": sid, "throttle": throttle_time},
                )
                await session.commit()
        except Exception as e:
            logging.warning("mysql_session_dao.touch: failed for session %s: %s", sid, e, exc_info=e)

    async def revoke_active_for_user(
        self,
        user_id: str,
        reason: str,
        exclude_session_id: Optional[str] = None,
    ) -> int:
        """Revoke all active sessions for a user in a single UPDATE.

        Much more efficient than findAll() + Python loop + N individual UPDATEs.
        Returns the number of sessions revoked.
        """
        factory = self._factory()
        if not factory:
            return 0
        uid = int(user_id) if str(user_id).isdigit() else None
        if uid is None:
            return 0
        now = now_utc()
        params: dict = {
            "user_id": uid,
            "reason": reason,
            "now": now,
        }
        exclude_clause = ""
        if exclude_session_id:
            exc_sid = int(exclude_session_id) if str(exclude_session_id).isdigit() else None
            if exc_sid:
                exclude_clause = "AND id != :exclude_id"
                params["exclude_id"] = exc_sid
        try:
            async with factory() as session:
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

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        sid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": sid},
            )
            await session.commit()
            return result.rowcount > 0

    async def deleteMany(self, query: Dict) -> Dict:
        """Delete matching sessions in a single SQL statement instead of N+1 deletes."""
        factory = self._factory()
        if not factory:
            return {"deletedCount": 0}
        # Only user_id-keyed deletes are issued by the codebase; build targeted DELETE.
        if "user_id" in query:
            uid = int(query["user_id"]) if str(query["user_id"]).isdigit() else None
            if uid is None:
                return {"deletedCount": 0}
            async with factory() as session:
                result = await session.execute(
                    text(f"DELETE FROM {self.TABLE} WHERE user_id = :uid"),
                    {"uid": uid},
                )
                await session.commit()
            return {"deletedCount": result.rowcount}
        # Fallback for any other query shape: load IDs then delete in one IN clause
        docs = await self.findAll(query)
        if not docs:
            return {"deletedCount": 0}
        ids = [int(d.id) for d in docs if str(d.id).isdigit()]
        if not ids:
            return {"deletedCount": 0}
        id_params = {f"id_{i}": v for i, v in enumerate(ids)}
        placeholders = ", ".join(f":{k}" for k in id_params)
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id IN ({placeholders})"),
                id_params,
            )
            await session.commit()
        return {"deletedCount": result.rowcount}

    async def delete_by_user_id(self, user_id: str) -> int:
        """Delete all sessions for a user with a single targeted SQL DELETE.
        Used in test teardown to avoid FK constraint violations."""
        result = await self.deleteMany({"user_id": user_id})
        return result.get("deletedCount", 0)

    async def count(self, query: Optional[Dict] = None) -> int:
        """Count sessions using SELECT COUNT(*) — never loads row data."""
        factory = self._factory()
        if not factory:
            return 0
        # Simple full count (no complex filter needed for sessions)
        async with factory() as session:
            result = await session.execute(text(f"SELECT COUNT(*) FROM {self.TABLE}"))
            return int(result.scalar() or 0)

    find_all = findAll
    find_by_id = findById
    find_one = findOne
    touch_session = touch

