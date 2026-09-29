
from typing import Optional
from pydantic import BaseModel
from app.utils.device import DeviceContext

from app.db.storage_factory import get_storage


class ActivityRepository:
    def __init__(self):
        self.storage = get_storage("activities")

    async def log_activity(
        self,
        user_id: Optional[str],
        session_id: str,
        action: str,
        meta: BaseModel,
        device: DeviceContext,
        comment: Optional[str] = None,
        is_guest: bool = False,
    ):
        from app.models.daos_flat import ActivityInternalCreate, ActivityMetaInternal
        meta_dict = meta.model_dump(exclude_unset=True, exclude_none=True) if meta else {}
        meta_list = [ActivityMetaInternal(key=k, value=str(v)) for k, v in meta_dict.items()]
        payload = ActivityInternalCreate(
            user_id=user_id,
            session_id=session_id,
            action=action,
            meta=meta_list,
            comment=comment,
            is_guest=is_guest,
        )
        if device:
            payload.user_agent = device.userAgent
            payload.os = device.os
            payload.os_version = device.osVersion
            payload.device_type = device.deviceType
            
        return await self.storage.create(payload)

    async def promote_guest_activities(self, session_id: str, user_id: str) -> object:
        from app.models.daos_flat import ActivityInternalUpdate
        activities = await self.storage.findAll({"sessionId": session_id})
        updated = 0
        for act in activities:
            if act.userId is None:
                await self.storage.update(
                    act.id, ActivityInternalUpdate(user_id=user_id, is_guest=False, comment="login performed in the same session")
                )
                updated += 1
        return {"updated": updated}


activity_repository = ActivityRepository()
