import json
from datetime import datetime, timezone
from typing import List, Optional

from app.db.storage_factory import get_storage
from app.models.about_us import AboutUs
from app.models.privacy_policy import PrivacyPolicy
from app.models.daos_flat import (
    AboutUsInternalCreate, AboutUsInternalUpdate,
    PrivacyPolicyInternalCreate, PrivacyPolicyInternalUpdate
)
from app.models.daos import (
    FaqSectionInternalCreate, FaqSectionInternalUpdate
)

def _increment_version(version: str) -> str:
    parts = version.split(".")
    try:
        parts[-1] = str(int(parts[-1]) + 1)
    except ValueError:
        parts.append("1")
    return ".".join(parts)


class AboutUsRepository:
    def __init__(self):
        self.storage = get_storage("aboutUs")

    async def get(self) -> Optional[AboutUs]:
        docs = await self.storage.findAll()
        return docs[0] if docs else None

    async def upsert(self, data) -> AboutUs:
        existing = await self.get()
        
        # Serialize the UI-specific fields into the single 'content' column
        # since the MySQL DAO schema doesn't have brandName, tagline, etc.
        content_json = data.model_dump_json(exclude_unset=True)

        if existing:
            update_data = AboutUsInternalUpdate(
                content=content_json,
                isPublished=True
            )
            return await self.storage.update(existing.id, update_data)
        
        create_data = AboutUsInternalCreate(
            content=content_json,
            isPublished=True
        )
        return await self.storage.create(create_data)


class PrivacyPolicyRepository:
    def __init__(self):
        self.storage = get_storage("privacyPolicy")

    async def get(self) -> Optional[PrivacyPolicy]:
        docs = await self.storage.findAll()
        return docs[0] if docs else None

    async def upsert(self, data) -> PrivacyPolicy:
        existing = await self.get()
        
        if data.version:
            next_version = str(data.version).strip()
        elif existing and existing.version:
            next_version = _increment_version(str(existing.version))
        else:
            next_version = "1.0"

        # Serialize the sections into the single 'content' column
        content_json = json.dumps([s.model_dump() for s in data.sections]) if data.sections else ""

        if existing:
            update_data = PrivacyPolicyInternalUpdate(
                content=content_json,
                effectiveDate=data.lastUpdated,
                version=next_version,
                is_active=True
            )
            return await self.storage.update(existing.id, update_data)

        create_data = PrivacyPolicyInternalCreate(
            content=content_json,
            effectiveDate=data.lastUpdated,
            version=next_version,
            is_active=True
        )
        return await self.storage.create(create_data)


class FAQRepository:
    def __init__(self):
        self.storage = get_storage("faqSections")

    async def find_all(self) -> List[object]:
        sections = await self.storage.findAll()
        return sorted(sections, key=lambda s: (s.display_order if s.display_order is not None else 0))

    async def find_by_id(self, section_id: str) -> Optional[object]:
        return await self.storage.findById(section_id)

    async def create_section(self, data: FaqSectionInternalCreate) -> object:
        if data.icon is None:
            data.icon = "help-circle-outline"
        if data.display_order is None:
            data.display_order = 0
        if data.items is None:
            data.items = []
        return await self.storage.create(data)

    async def update_section(self, section_id: str, data: FaqSectionInternalUpdate) -> object:
        return await self.storage.update(section_id, data)

    async def delete_section(self, section_id: str) -> object:
        return await self.storage.delete(section_id)


faq_repository = FAQRepository()
about_repository = AboutUsRepository()
privacy_repository = PrivacyPolicyRepository()
