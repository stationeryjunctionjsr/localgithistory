from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.db.storage_factory import get_storage


class ContentRepository:
    """Generic repository for single-document content pages (About Us, Privacy Policy)."""

    def __init__(self, collection_name: str):
        self.storage = get_storage(collection_name)

    def _ts(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    async def get(self) -> Optional[Dict]:
        docs = await self.storage.findAll()
        return docs[0] if docs else None

    async def upsert(self, data: Dict) -> Dict:
        existing = await self.get()
        payload = {**data, "updatedAt": self._ts()}
        if existing:
            return await self.storage.update(existing["_id"], payload)
        payload["createdAt"] = self._ts()
        return await self.storage.create(payload)


def _increment_version(version: str) -> str:
    """Increment the last numeric segment of a dot-separated version string.

    Examples:
        "1.0"   -> "1.1"
        "1.0.1" -> "1.0.2"
        "2.9"   -> "2.10"
        "2"     -> "3"
    """
    parts = version.split(".")
    try:
        parts[-1] = str(int(parts[-1]) + 1)
    except ValueError:
        # Last segment is not an integer — append a new ".1" patch segment
        parts.append("1")
    return ".".join(parts)


class VersionedContentRepository(ContentRepository):
    """ContentRepository that tracks a string version (e.g. '1.0', '1.0.1', '2.0')
    and keeps a full version history on every upsert.

    Version resolution rules:
    - If the request payload contains a ``version`` field, that value is used as-is.
    - If ``version`` is omitted, the last segment of the existing version is auto-incremented
      (e.g. '1.0' -> '1.1', '1.0.1' -> '1.0.2').
    - On first creation with no version supplied, defaults to '1.0'.
    """

    async def upsert(self, data: Dict) -> Dict:
        existing = await self.get()
        now = self._ts()

        # Determine which version string to store
        if "version" in data and data["version"]:
            # Admin explicitly supplied a version — use it as-is
            next_version: str = str(data["version"]).strip()
        elif existing and existing.get("version"):
            # No version supplied — auto-increment the last segment
            next_version = _increment_version(str(existing["version"]))
        else:
            # First-time creation with no version supplied
            next_version = "1.0"

        # Build the history entry for this save
        history_entry = {
            "version": next_version,
            "savedAt": now,
            "lastUpdated": data.get("lastUpdated", ""),
        }

        # Append to existing history (or start fresh)
        history: List[Dict] = list((existing or {}).get("versionHistory", []))
        history.append(history_entry)

        payload = {
            **data,
            "version": next_version,
            "versionHistory": history,
            "updatedAt": now,
        }

        if existing:
            return await self.storage.update(existing["_id"], payload)

        payload["createdAt"] = now
        return await self.storage.create(payload)


class FAQRepository:
    def __init__(self):
        self.storage = get_storage("faqSections")

    def _ts(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    async def find_all(self) -> List[Dict]:
        sections = await self.storage.findAll()
        return sorted(sections, key=lambda s: s.get("displayOrder", 0))

    async def find_by_id(self, section_id: str) -> Optional[Dict]:
        return await self.storage.findById(section_id)

    async def create_section(self, data: Dict) -> Dict:
        section = {
            "title": data["title"],
            "icon": data.get("icon", "help-circle-outline"),
            "displayOrder": data.get("displayOrder", 0),
            "items": data.get("items", []),
            "createdAt": self._ts(),
            "updatedAt": self._ts(),
        }
        return await self.storage.create(section)

    async def update_section(self, section_id: str, data: Dict) -> Dict:
        updates = {k: v for k, v in data.items() if v is not None}
        updates["updatedAt"] = self._ts()
        return await self.storage.update(section_id, updates)

    async def delete_section(self, section_id: str) -> Dict:
        return await self.storage.delete(section_id)


faq_repository = FAQRepository()
about_repository = ContentRepository("aboutUs")
privacy_repository = VersionedContentRepository("privacyPolicy")
