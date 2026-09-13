from typing import Dict, Optional

from app.db.storage_factory import get_storage


class ActivityRepository:
    def __init__(self):
        self.storage = get_storage("activities")

    async def log_activity(
        self,
        user_id: Optional[str],
        session_id: str,
        action: str,
        meta: Dict,
        device: Any,
        comment: Optional[str] = None,
        is_guest: bool = False,
    ) -> Dict:
        payload = {
            "userId": user_id,
            "sessionId": session_id,
            "action": action,
            "meta": meta or {},
            "device": device,
            "comment": comment,
            "isGuest": is_guest,
        }
        if device:
            payload.update(device)
        return await self.storage.create(payload)

    async def promote_guest_activities(self, session_id: str, user_id: str) -> Dict:
        activities = await self.storage.findAll({"sessionId": session_id})
        updated = 0
        for act in activities:
            if getattr(act, "userId", None) is None:
                await self.storage.update(
                    act.id, {"userId": user_id, "isGuest": False, "comment": "login performed in the same session"}
                )
                updated += 1
        return {"updated": updated}


activity_repository = ActivityRepository()
