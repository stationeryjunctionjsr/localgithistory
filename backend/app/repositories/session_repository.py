from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.db.storage_factory import get_storage
from app.utils.logger import logger


class SessionRepository:
    def __init__(self):
        self.storage = get_storage("sessions")

    async def create_session(self, user_id: Optional[str], device: Dict, refresh_token_id: str) -> Dict:
        return await self.storage.create(
            {
                "userId": user_id,
                "refreshTokenId": refresh_token_id,
                "status": "active",
                "lastActiveAt": datetime.utcnow().isoformat(),
                "revokedAt": None,
                "revokedReason": None,
                "device": device,
                "isGuest": user_id is None,
                "comment": None,
            }
        )

    async def find_by_refresh_id(self, refresh_id: str) -> Optional[Dict]:
        return await self.storage.findOne({"refreshTokenId": refresh_id})

    async def find_by_id(self, session_id: str) -> Optional[Dict]:
        return await self.storage.findById(session_id)

    async def update_session(self, session_id: str, updates: Dict) -> Optional[Dict]:
        existing = await self.storage.findById(session_id)
        if not existing:
            return None
        existing.update(updates)
        return await self.storage.update(session_id, existing)

    async def revoke_session(self, session_id: str, reason: str) -> Optional[Dict]:
        return await self.update_session(
            session_id, {"status": "revoked", "revokedReason": reason, "revokedAt": datetime.utcnow().isoformat()}
        )

    async def revoke_other_sessions(self, user_id: str, exclude_session_id: Optional[str] = None) -> List[Dict]:
        sessions = await self.storage.findAll()
        updated = []
        for s in sessions:
            if s.get("userId") == user_id and s.get("_id") != exclude_session_id and s.get("status") == "active":
                updated.append(await self.revoke_session(s["_id"], "single_session"))
        return updated

    async def touch_last_active(self, session_id: str):
        await self.update_session(session_id, {"lastActiveAt": datetime.utcnow().isoformat()})

    async def touch(self, session_id: str, device: dict = None) -> None:
        """Lightweight session touch — delegates to DAO's single-UPDATE touch."""
        if hasattr(self.storage, "touch"):
            await self.storage.touch(session_id, device)
        else:
            # Fallback for non-Oracle storage backends
            updates = {"lastActiveAt": datetime.utcnow().isoformat()}
            if device:
                updates["device"] = device
            await self.update_session(session_id, updates)

    async def check_inactivity_and_revoke(self, session: Dict, max_inactive_days: int) -> Dict:
        last_active = session.get("lastActiveAt")
        if last_active:
            try:
                dt = datetime.fromisoformat(last_active.replace("Z", "+00:00"))
                if datetime.utcnow() - dt > timedelta(days=max_inactive_days):
                    return await self.revoke_session(session["_id"], "inactive")
            except Exception as e:
                logger.warning("Invalid lastActiveAt for session %s: %s", session.get("_id"), str(e))
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
                    await self.storage.delete(s["_id"])
                except Exception:
                    pass


session_repository = SessionRepository()
