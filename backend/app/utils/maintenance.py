from fastapi import Request

from app.config.maintenance import MAINTENANCE_ALLOWLIST_PREFIXES, MAINTENANCE_MESSAGE_PARAGRAPHS
from app.config.settings import settings


def is_maintenance_allowlisted(path: str) -> bool:
    if path in ("/", ""):
        return True
    return any(path.startswith(prefix) for prefix in MAINTENANCE_ALLOWLIST_PREFIXES)


def maintenance_blocked_payload() -> dict:
    return {
        "code": "MAINTENANCE_MODE",
        "maintenance": True,
        "detail": "The application is currently undergoing a scheduled update.",
        "message": MAINTENANCE_MESSAGE_PARAGRAPHS,
    }


def is_maintenance_active() -> bool:
    return settings.maintenance_mode
