import json
from datetime import datetime, timezone
from typing import Any, Optional


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def json_dumps(value: Any) -> Optional[str]:
    if value is None:
        return None
    return json.dumps(value, default=str)


def json_loads(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "read"):
        try:
            value = value.read()
        except Exception:
            return None
    if not isinstance(value, str):
        return value
    if value == "":
        return None
    try:
        return json.loads(value)
    except Exception:
        return None
