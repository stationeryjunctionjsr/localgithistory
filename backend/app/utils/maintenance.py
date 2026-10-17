from typing import List
from fastapi import Request
from pydantic import Field

from app.config.maintenance import MAINTENANCE_ALLOWLIST_PREFIXES, MAINTENANCE_MESSAGE_PARAGRAPHS
from app.config.settings import settings
from app.models.base import CamelBaseModel


class MaintenanceBlockedResponse(CamelBaseModel):
    code: str = "MAINTENANCE_MODE"
    maintenance: bool = True
    detail: str = "The application is currently undergoing a scheduled update."
    message: List[str] = Field(default_factory=lambda: list(MAINTENANCE_MESSAGE_PARAGRAPHS))


def is_maintenance_allowlisted(path: str) -> bool:
    if path in ("/", ""):
        return True
    return any(path.startswith(prefix) for prefix in MAINTENANCE_ALLOWLIST_PREFIXES)


def maintenance_blocked_payload() -> MaintenanceBlockedResponse:
    return MaintenanceBlockedResponse()


def is_maintenance_active() -> bool:
    return settings.maintenance_mode
