import logging
"""
Database utility helpers (MySQL).
These are pure-Python helpers shared across all MySQL DAOs.
"""

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
    try:
        value = value.read()
    except AttributeError:
        pass
    except Exception as e:
        logging.warning("Background task failed", exc_info=e)
        return None
    if not isinstance(value, str):
        return value
    if value == "":
        return None
    try:
        return json.loads(value)
    except Exception as e:
        logging.warning("Background task failed", exc_info=e)
        return None
