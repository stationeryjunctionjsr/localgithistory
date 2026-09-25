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


def json_dumps(value: dict) -> Optional[str]:
    if value is None:
        return None
    return json.dumps(value, default=str)


def json_loads(value: dict) -> dict:
    if value is None:
        return None
    try:
        value = value.read()
    except AttributeError:
        pass
    except Exception as e:
        logging.warning("json_loads: unexpected error reading LOB/stream value %r: %s", type(value).__name__, e, exc_info=e)
        return None
    if not isinstance(value, str):
        return value
    if value == "":
        return None
    try:
        return json.loads(value)
    except Exception as e:
        logging.warning("json_loads: could not parse JSON string (%.80r...): %s", value, e, exc_info=e)
        return None
