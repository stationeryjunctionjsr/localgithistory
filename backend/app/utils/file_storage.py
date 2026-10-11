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


# ---------------------------------------------------------------------------
# Process-level shared cache: keyed by collection name.
# All FileStorage instances for the same collection share one cached copy,
# so repeated findAll() calls within the TTL window hit RAM, not disk.
# ---------------------------------------------------------------------------
import time as _time

_FILE_CACHE: dict = {}  # collection_name -> (data, expires_at)
_FILE_CACHE_TTL: float = 10.0  # seconds (hot read collections)


class FileStorage:
    """File-based storage operations with process-level shared caching"""

    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.file_path = DATA_DIR / f"{collection_name}.json"

    def _initialize(self):
        """Initialize file if it doesn't exist"""
        ensure_data_dir()
        if not self.file_path.exists():
            self.file_path.write_text(json.dumps([], indent=2), encoding="utf-8")

    def _invalidate_cache(self):
        """Invalidate process-level cache for this collection"""
        _FILE_CACHE.pop(self.collection_name, None)

    def _read_file(self):
        """Read file with process-level shared caching and mtime verification"""
        now = _time.monotonic()
        mtime = 0
        if self.file_path.exists():
            try:
                mtime = self.file_path.stat().st_mtime
            except Exception as exc:
                from app.utils.logger import logger

                logger.warning("Failed to stat file %s: %s", self.file_path, exc)
                mtime = 0

        entry = _FILE_CACHE[self.collection_name] if self.collection_name in _FILE_CACHE else None

        # entry structure: (data, expires_at, stored_mtime)
        if entry and now < entry[1] and entry[2] == mtime:
            return entry[0]

        self._initialize()
        # Refresh mtime after initialization
        try:
            mtime = self.file_path.stat().st_mtime
        except Exception as exc:
            from app.utils.logger import logger

            logger.warning("Failed to stat file %s after initialization: %s", self.file_path, exc)
            mtime = 0

        data = self.file_path.read_text(encoding="utf-8")
        records = json.loads(data or "[]")

        _FILE_CACHE[self.collection_name] = (records, now + _FILE_CACHE_TTL, mtime)
        return records

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        """Read all records with optional query filters"""
        records = self._read_file()

        if query:
            filtered = []
            for record in records:
                match = True
                for key, value in query.items():
                    if key in ["_id", "id"]:
                        if (record["_id"] if "_id" in record else None) != value and (record["id"] if "id" in record else None) != value:
                            match = False
                            break
                    elif key == "name":
                        if ((record["name"] if "name" in record else None) or "").lower() != str(value).lower():
                            match = False
                            break
                    elif key == "allowed_ids":
                        allowed_ids_strs = [str(aid) for aid in value]
                        if str((record["_id"] if "_id" in record else None)) not in allowed_ids_strs and str((record["id"] if "id" in record else None)) not in allowed_ids_strs:
                            match = False
                            break
                    elif (record[key] if key in record else None) != value:
                        match = False
                        break
                if match:
                    filtered.append(record)
            return filtered

        return records

    async def findOne(self, query: Dict) -> Optional[Dict]:
        """Find one record matching query"""
        records = await self.findAll(query)
        return records[0] if records else None

    async def findById(self, id: str) -> Optional[Dict]:
        """Find record by ID"""
        return await self.findOne({"id": id}) or await self.findOne({"_id": id})

    # Aliases for repositories that use find_all / find_by_id / find_one
    find_all = findAll
    find_by_id = findById
    find_one = findOne

    def _get_next_id(self, records: List[Dict]) -> str:
        """Find max numeric ID and increment by 1. Returns '1' if empty."""
        max_id = 0
        for record in records:
            id_val = record.get("id") or record.get("_id")
            if id_val:
                try:
                    # Try to parse as int (handles "123" and 123)
                    numeric_id = int(id_val)
                    if numeric_id > max_id:
                        max_id = numeric_id
                except (ValueError, TypeError):
                    continue
        return str(max_id + 1)

    async def create(self, data: Dict) -> Dict:
        """Create new record. Preserves any 'id' or '_id' already in data; falls back to auto-increment."""
        self._initialize()
        records = await self.findAll()

        # Preserve caller-supplied id (e.g. seeded system segments), otherwise auto-increment
        supplied_id = data.get("id") or data.get("_id")
        if not supplied_id:
            supplied_id = self._get_next_id(records)

        # Strip id and _id from data so the explicit assignment below is authoritative
        data_without_id = {k: v for k, v in data.items() if k not in ("_id", "id")}

        new_record = dict(data_without_id)
        new_record["id"] = supplied_id
        new_record["_id"] = supplied_id
        new_record["createdAt"] = (data["createdAt"] if "createdAt" in data else datetime.now(timezone.utc).isoformat())
        new_record["updatedAt"] = (data["updatedAt"] if "updatedAt" in data else datetime.now(timezone.utc).isoformat())

        records.append(new_record)
        self.file_path.write_text(json.dumps(records, indent=2, default=str), encoding="utf-8")
        self._invalidate_cache()
        return new_record

    async def update(self, id: str, update_data: Dict) -> Optional[Dict]:
        """Update record"""
        self._initialize()
        records = await self.findAll()

        index = next((i for i, r in enumerate(records) if (r.get("id") == id or r.get("_id") == id)), None)
        if index is None:
            return None

        updated_record = dict(records[index])
        updated_record.update(update_data)
        updated_record["updatedAt"] = datetime.now(timezone.utc).isoformat()
        records[index] = updated_record

        self.file_path.write_text(json.dumps(records, indent=2, default=str), encoding="utf-8")
        self._invalidate_cache()
        return records[index]

    async def delete(self, id: str) -> bool:
        """Delete record"""
        self._initialize()
        records = await self.findAll()
        original_count = len(records)

        records = [r for r in records if r.get("id") != id and r.get("_id") != id]

        if len(records) == original_count:
            return False

        self.file_path.write_text(json.dumps(records, indent=2, default=str), encoding="utf-8")
        self._invalidate_cache()
        return True

    async def deleteMany(self, query: Dict) -> Dict:
        """Delete many records matching query"""
        self._initialize()
        records = await self.findAll()
        original_count = len(records)

        filtered = [
            r for r in records
            if not all(r.get(key) == value for key, value in query.items())
        ]

        deleted_count = original_count - len(filtered)
        self.file_path.write_text(json.dumps(filtered, indent=2, default=str), encoding="utf-8")
        self._invalidate_cache()
        return {"deletedCount": deleted_count}

    async def updateMany(self, query: Dict, update_data: Dict) -> int:
        """Update many records matching query. Returns count of updated records."""
        self._initialize()
        records = await self.findAll()

        count = 0
        now_str = datetime.now(timezone.utc).isoformat()

        for record in records:
            match = True
            if query:
                for key, value in query.items():
                    if key in ["_id", "id"]:
                        if record.get("_id") != value and record.get("id") != value:
                            match = False
                            break
                    elif record.get(key) != value:
                        match = False
                        break
            if match:
                record.update(update_data)
                record["updatedAt"] = now_str
                count += 1

        if count > 0:
            self.file_path.write_text(json.dumps(records, indent=2, default=str), encoding="utf-8")
            self._invalidate_cache()

        return count

    async def count(self, query: Optional[Dict] = None) -> int:
        """Count records matching query"""
        records = await self.findAll(query)
        return len(records)
