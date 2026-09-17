from fastapi import APIRouter, Depends

from app.models.schemas import ReturnSettingsResponse, ReturnSettingsUpdate
from app.repositories.return_settings_repository import return_settings_repository
from app.utils.auth import require_super_admin
from app.utils.cache import cache

router = APIRouter()


@router.get("", response_model=ReturnSettingsResponse)
@router.get("/", response_model=ReturnSettingsResponse)
@cache.ttl_cache(ttl=3600.0)
async def get_return_settings():
    """Get global return settings (Public)"""
    settings = await return_settings_repository.get_settings()
    return settings


@router.put("", response_model=ReturnSettingsResponse)
@router.put("/", response_model=ReturnSettingsResponse)
async def update_return_settings(settings_update: ReturnSettingsUpdate, admin=Depends(require_super_admin)):
    """Update global return settings (Super Admin only)"""
    from app.models.daos_flat import ReturnSettingsInternalUpdate
    update_data = ReturnSettingsInternalUpdate()
    if settings_update.returnDays is not None:
        update_data.returnDays = settings_update.returnDays

    updated = await return_settings_repository.update_settings(update_data)
    return updated
