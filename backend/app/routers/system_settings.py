from app.models.user import User
from fastapi import APIRouter, Depends

from app.db.storage_factory import get_storage
from app.utils.auth import require_super_admin

router = APIRouter()
storage = get_storage("systemSettings")


from app.models.system_settings import SystemSettingsUpdate, SystemSettingsResponse



@router.get("", response_model=SystemSettingsResponse)
@router.get("/", response_model=SystemSettingsResponse)
async def get_settings(current_user: User = Depends(require_super_admin)):
    """Get global system settings"""
    settings = await storage.findById(1)
    if not settings:
        return await storage.create(SystemSettingsUpdate())
    return settings


@router.put("", response_model=SystemSettingsResponse)
@router.put("/", response_model=SystemSettingsResponse)
async def update_settings(data: SystemSettingsUpdate, current_user: User = Depends(require_super_admin)):
    """Update global system settings"""
    settings = await storage.findById(1)
    if not settings:
        return await storage.create(data)

    updated = await storage.update(1, data)
    return updated


