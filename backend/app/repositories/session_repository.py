import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Union

from app.db.storage_factory import get_storage
from app.utils.device import DeviceContext
from app.utils.logger import logger
from app.models.daos import SessionInternalCreate, SessionInternalUpdate, DeviceSnippet
from app.models.session import Session

class SessionRepository:
    def __init__(self):
        self.storage = get_storage("sessions")

    async def create_session(
        self,
        user_id: Optional[int],
        device: Optional[Union[DeviceSnippet, DeviceContext]],
        refresh_token_id: str,
    ) -> Session:
        dev_snippet: Optional[DeviceSnippet] = None
        if device is not None:
            if isinstance(device, DeviceSnippet):
                dev_snippet = device
            elif isinstance(device, DeviceContext):
                dev_snippet = DeviceSnippet.model_validate(device)
        data = SessionInternalCreate(
            user_id=user_id,
            refresh_token_id=refresh_token_id,
            status="active",
            last_active_at=datetime.now(timezone.utc).isoformat(),
            revoked_at=None,
            revoked_reason=None,
            device=dev_snippet,
            is_guest=user_id is None,
            comment=None,
        )
        return await self.storage.create(data)

    async def find_by_refresh_id(self, refresh_token_id: str) -> Optional[Session]:
        return await self.storage.findOne(refresh_token_id=refresh_token_id)

    async def find_by_id(self, session_id: int) -> Optional[Session]:
        return await self.storage.findById(session_id)

    async def update_session(self, session_id: int, updates: SessionInternalUpdate) -> Optional[Session]:
        return await self.storage.update(session_id, updates)

    async def revoke_session(self, session_id: int, reason: str) -> Optional[Session]:
        return await self.update_session(
            session_id, SessionInternalUpdate(status="revoked", revoked_reason=reason, revoked_at=datetime.now(timezone.utc).isoformat())
        )

    async def revoke_other_sessions(self, user_id: int, exclude_session_id: Optional[int] = None) -> List[Session]:
        """Revoke all active sessions for a user except the given one.

        Delegates to the DAO's bulk UPDATE when available (MySQL), which runs a
        single SQL statement instead of findAll() + N individual UPDATEs.
        """
        try:
            # Fast path: single SQL UPDATE (MySQL DAO)
            await self.storage.revoke_active_for_user(user_id, "single_session", exclude_session_id)
            return []  # callers only check for exceptions; return value is unused
        except AttributeError:
            # Fallback for non-MySQL backends
            sessions = await self.storage.findAll()
            updated = []
            for s in sessions:
                if s.user_id == user_id and s.id != exclude_session_id and s.status == "active":
                    updated.append(await self.revoke_session(s.id, "single_session"))
            return updated

    async def touch_last_active(self, session_id: int):
        await self.update_session(session_id, SessionInternalUpdate(last_active_at=datetime.now(timezone.utc).isoformat()))

    async def touch(self, session_id: int, device: Optional[DeviceSnippet] = None) -> None:
        """Lightweight session touch — delegates to DAO's single-UPDATE touch."""
        try:
            await self.storage.touch(session_id, device)
        except AttributeError:
            # Fallback for non-Oracle storage backends
            updates = SessionInternalUpdate(last_active_at=datetime.now(timezone.utc).isoformat())
            if device:
                updates.device = device
            await self.update_session(session_id, updates)

    async def check_inactivity_and_revoke(self, session: Session, max_inactive_days: int) -> Session:
        last_active = session.last_active_at
        if last_active:
            try:
                dt = last_active if isinstance(last_active, datetime) else datetime.fromisoformat(last_active.replace("Z", "+00:00"))
                if datetime.now(timezone.utc) - dt > timedelta(days=max_inactive_days):
                    return await self.revoke_session(session.id, "inactive")
            except Exception as e:
                logger.warning("Invalid lastActiveAt for session %s: %s", session.id, str(e))
        return session

    async def delete_all_for_user(self, user_id: int) -> None:
        """Delete all sessions belonging to a user. Used in test teardown to avoid FK constraint violations."""
        try:
            await self.storage.delete_by_user_id(user_id)
        except AttributeError:
            # Fallback for non-Oracle backends
            all_sessions = await self.storage.findAll(user_id=user_id)
            for s in all_sessions:
                try:
                    await self.storage.delete(s.id)
                except Exception as e:
                    logging.warning("session_repository.delete_by_user: failed to delete session %r for user %r: %s", s.id, user_id, e, exc_info=e)


session_repository = SessionRepository()
