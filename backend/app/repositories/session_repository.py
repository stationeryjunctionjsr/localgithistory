import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

from app.db.storage_factory import get_storage
from app.utils.logger import logger
from app.models.daos import SessionInternalCreate, SessionInternalUpdate


class SessionRepository:
    def __init__(self):
        self.storage = get_storage("sessions")

    async def create_session(self, user_id: Optional[str], device: dict, refresh_token_id: str) -> Dict:
        data = SessionInternalCreate(
            userId=user_id,
            refreshTokenId=refresh_token_id,
            status="active",
            lastActiveAt=datetime.now(timezone.utc).isoformat(),
            revokedAt=None,
            revokedReason=None,
            device=device,
            isGuest=user_id is None,
            comment=None,
        )
        return await self.storage.create(data)

    async def find_by_refresh_id(self, refresh_token_id: str) -> Optional[Dict]:
        return await self.storage.findOne({"refreshTokenId": refresh_token_id})

    async def find_by_id(self, session_id: str) -> Optional[Dict]:
        return await self.storage.findById(session_id)

    async def update_session(self, session_id: str, updates: SessionInternalUpdate) -> Optional['Session']:
        existing = await self.storage.findById(session_id)
        if not existing:
            return None
        
        # update existing with set fields from updates
        # since we can't use getattr, we use model_fields_set and explicitly assign
        for field in updates.model_fields_set:
            match field:
                case "userId": existing.user_id = updates.userId
                case "refreshTokenId": existing.refresh_token_id = updates.refresh_tokenId
                case "status": existing.status = updates.status
                case "lastActiveAt": existing.last_active_at = updates.lastActiveAt
                case "revokedAt": existing.revoked_at = updates.revokedAt
                case "revokedReason": existing.revoked_reason = updates.revokedReason
                case "device": existing.device = updates.device
                case "isGuest": existing.is_guest = updates.is_guest

        return await self.storage.update(session_id, SessionInternalUpdate.model_validate(existing))

    async def revoke_session(self, session_id: str, reason: str) -> Optional['Session']:
        return await self.update_session(
            session_id, SessionInternalUpdate(status="revoked", revokedReason=reason, revokedAt=datetime.now(timezone.utc).isoformat())
        )

    async def revoke_other_sessions(self, user_id: str, exclude_session_id: Optional[str] = None) -> List['Session']:
        sessions = await self.storage.findAll()
        updated = []
        for s in sessions:
            if s.userId == user_id and s.id != exclude_session_id and s.status == "active":
                updated.append(await self.revoke_session(s.id, "single_session"))
        return updated

    async def touch_last_active(self, session_id: str):
        await self.update_session(session_id, SessionInternalUpdate(lastActiveAt=datetime.now(timezone.utc).isoformat()))

    async def touch(self, session_id: str, device: dict = None) -> None:
        """Lightweight session touch — delegates to DAO's single-UPDATE touch."""
        try:
            await self.storage.touch(session_id, device)
        except AttributeError:
            # Fallback for non-Oracle storage backends
            updates = SessionInternalUpdate(lastActiveAt=datetime.now(timezone.utc).isoformat())
            if device:
                updates.device = device
            await self.update_session(session_id, updates)

    async def check_inactivity_and_revoke(self, session: 'Session', max_inactive_days: int) -> Dict:
        last_active = session.last_active_at
        if last_active:
            try:
                dt = last_active if isinstance(last_active, datetime) else datetime.fromisoformat(last_active.replace("Z", "+00:00"))
                if datetime.now(timezone.utc) - dt > timedelta(days=max_inactive_days):
                    return await self.revoke_session(session.id, "inactive")
            except Exception as e:
                logger.warning("Invalid lastActiveAt for session %s: %s", session.id, str(e))
        return session

    async def delete_all_for_user(self, user_id: str) -> None:
        """Delete all sessions belonging to a user. Used in test teardown to avoid FK constraint violations."""
        try:
            await self.storage.delete_by_user_id(str(user_id))
        except AttributeError:
            # Fallback for non-Oracle backends
            all_sessions = await self.storage.findAll({"userId": str(user_id)})
            for s in all_sessions:
                try:
                    await self.storage.delete(s.id)
                except Exception as e:
                    logging.warning("session_repository.delete_by_user: failed to delete session %r for user %r: %s", s.id, user_id, e, exc_info=e)


session_repository = SessionRepository()
