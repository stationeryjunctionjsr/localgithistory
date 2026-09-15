from typing import Dict, Any, List
from app.models.schemas import MessageResponse
from typing import Optional

from fastapi import APIRouter, Query

from app.config import version as config
from app.config.maintenance import MAINTENANCE_MESSAGE_PARAGRAPHS
from app.config.settings import settings
from app.utils.cache import cache


from pydantic import BaseModel
class VersionResponse(BaseModel):
    current: str
    currentVersion: str
    min: Dict[str, str]
    minVersion: str

class MaintenanceResponse(BaseModel):
    active: bool
    message: List[str]

router = APIRouter()


@router.get("/version", response_model=VersionResponse)
@cache.ttl_cache(ttl=3600.0)
async def get_version(platform: Optional[str] = Query(None)):
    """App version info for force-update checks (web / mobile)."""
    min_versions = {
        "ios": config.MIN_APP_VERSION_IOS,
        "android": config.MIN_APP_VERSION_ANDROID,
        "web": config.MIN_APP_VERSION_WEB,
    }
    platform_key = (platform or "web").lower()
    min_for_platform = (min_versions[platform_key] if platform_key in min_versions else config.MIN_APP_VERSION_WEB)
    return {
        "current": config.CURRENT_APP_VERSION,
        "currentVersion": config.CURRENT_APP_VERSION,
        "min": min_versions,
        "minVersion": min_for_platform,
    }


@router.get("/maintenance", response_model=MaintenanceResponse)
async def get_maintenance_status():
    """Public status for scheduled upgrade / maintenance screens."""
    return {
        "active": settings.maintenance_mode,
        "message": MAINTENANCE_MESSAGE_PARAGRAPHS,
    }
