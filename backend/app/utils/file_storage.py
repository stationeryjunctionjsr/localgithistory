import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data"


def ensure_data_dir():
    """Ensure data directory exists"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def generate_id() -> str:
    """Generate unique ID"""
    return secrets.token_hex(16)


# ===========================================================================
# ARCHIVED / DEPRECATED: FileStorage (Legacy MongoDB JSON Mock)
# ===========================================================================
# The FileStorage class below was the mock storage engine used before migrating
# to MySQL relational storage. All application entities now use MySQL DAOs
# via app.db.storage_factory.
#
# Preserved here in comments for historical reference. Can be restored from
# git commit history at any time.
# ===========================================================================


class FileStorage:
    """Deprecated legacy mock storage engine. Use MySQL DAOs via app.db.storage_factory."""

    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.file_path = DATA_DIR / f"{collection_name}.json"

    def __getattr__(self, name: str):
        raise NotImplementedError(
            f"FileStorage.{name} is deprecated and decommissioned. "
            f"All collections are managed via MySQL DAOs in app.db.storage_factory."
        )


# --- Legacy implementation preserved for reference (can be restored from git) ---
# import time as _time
# _FILE_CACHE: dict = {}
# _FILE_CACHE_TTL: float = 10.0
#
#     def _initialize(self):
#         ensure_data_dir()
#         if not self.file_path.exists():
#             self.file_path.write_text(json.dumps([], indent=2), encoding="utf-8")
#
#     def _invalidate_cache(self):
#         _FILE_CACHE.pop(self.collection_name, None)
#
#     def _read_file(self):
#         now = _time.monotonic()
#         mtime = 0
#         if self.file_path.exists():
#             try:
#                 mtime = self.file_path.stat().st_mtime
#             except Exception:
#                 mtime = 0
#         entry = _FILE_CACHE[self.collection_name] if self.collection_name in _FILE_CACHE else None
#         if entry and now < entry[1] and entry[2] == mtime:
#             return entry[0]
#         self._initialize()
#         data = self.file_path.read_text(encoding="utf-8")
#         records = json.loads(data or "[]")
#         _FILE_CACHE[self.collection_name] = (records, now + _FILE_CACHE_TTL, mtime)
#         return records
#
#     async def findAll(self, query=None): ...
#     async def findOne(self, query): ...
#     async def findById(self, id): ...
#     async def create(self, data): ...
#     async def update(self, id, update_data): ...
#     async def delete(self, id): ...

