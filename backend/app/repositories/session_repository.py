from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

from app.db.storage_factory import get_storage
from app.utils.logger import logger
from app.models.daos import SessionInternalCreate, SessionInternalUpdate


class SessionRepository:
    def __init__(self):
        self.storage = get_storage("sessions")

    async def create_session(self, user_id: Optional[str], device: Any, refresh_token_id: str) -> Dict:
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

    async def update_session(self, session_id: str, updates: Any) -> Optional[Dict]:
        existing = await self.storage.findById(session_id)
        if not existing:
            return None
        existing_dict = {}
        for field in existing.model_fields_set if hasattr(existing, 'model_fields_set') else existing:
            existing_dict[field] = getattr(existing, field) if not isinstance(existing, dict) else existing[field]
        updates_dict = {}
        for field in updates.model_fields_set if hasattr(updates, 'model_fields_set') else updates:
            updates_dict[field] = getattr(updates, field) if not isinstance(updates, dict) else updates[field]
        existing_dict.update(updates_dict)
        return await self.storage.update(session_id, SessionInternalUpdate.model_validate(existing_dict))

    async def revoke_session(self, session_id: str, reason: str) -> Optional[Dict]:
        return await self.update_session(
            session_id, {"status": "revoked", "revokedReason": reason, "revokedAt": datetime.now(timezone.utc).isoformat()}
        )

    async def revoke_other_sessions(self, user_id: str, exclude_session_id: Optional[str] = None) -> List[Dict]:
        sessions = await self.storage.findAll()
        updated = []
        for s in sessions:
            if s.userId == user_id and s.id != exclude_session_id and s.status == "active":
                updated.append(await self.revoke_session(s.id, "single_session"))
        return updated

    async def touch_last_active(self, session_id: str):
        await self.update_session(session_id, {"lastActiveAt": datetime.now(timezone.utc).isoformat()})

    async def touch(self, session_id: str, device: dict = None) -> None:
        """Lightweight session touch — delegates to DAO's single-UPDATE touch."""
        if hasattr(self.storage, "touch"):
            await self.storage.touch(session_id, device)
        else:
            # Fallback for non-Oracle storage backends
            updates = {"lastActiveAt": datetime.now(timezone.utc).isoformat()}
            if device:
                updates["device"] = device
            await self.update_session(session_id, updates)

    async def check_inactivity_and_revoke(self, session: Any, max_inactive_days: int) -> Dict:
        last_active = session.last_active_at
        if last_active:
            try:
                dt = datetime.fromisoformat(last_active.replace("Z", "+00:00"))
                if datetime.now(timezone.utc) - dt > timedelta(days=max_inactive_days):
                    return await self.revoke_session(session.id, "inactive")
            except Exception as e:
                logger.warning("Invalid lastActiveAt for session %s: %s", session.id, str(e))
        return session

    async def delete_all_for_user(self, user_id: str) -> None:
        """Delete all sessions belonging to a user. Used in test teardown to avoid FK constraint violations."""
        if hasattr(self.storage, "delete_by_user_id"):
            await self.storage.delete_by_user_id(str(user_id))
        else:
            # Fallback for non-Oracle backends
            all_sessions = await self.storage.findAll({"userId": str(user_id)})
            for s in all_sessions:
                try:
                    await self.storage.delete(s.id)
                except Exception:
                    pass


session_repository = SessionRepository()
