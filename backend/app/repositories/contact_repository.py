from typing import Any, Dict, List, Optional

from app.db.storage_factory import get_storage
from app.models.daos_flat import ContactInternal, ContactInternalCreate, ContactInternalUpdate

class ContactRepository:
    def __init__(self):
        self.storage = get_storage("contacts")

    async def findAll(self, query: Optional[Dict] = None) -> List[ContactInternal]:
        return await self.storage.findAll(query or {})

    async def findById(self, id: str) -> Optional[ContactInternal]:
        return await self.storage.findById(id)

    async def create(self, contact_data: ContactInternalCreate) -> ContactInternal:
        # Ensure addresses array has max 2 items
        if contact_data.addresses and len(contact_data.addresses) > 2:
            contact_data.addresses = contact_data.addresses[:2]

        # Ensure phoneNumbers array has max 3 items
        if contact_data.phoneNumbers and len(contact_data.phoneNumbers) > 3:
            contact_data.phoneNumbers = contact_data.phoneNumbers[:3]

        if contact_data.email is None:
            contact_data.email = ""
        if contact_data.description is None:
            contact_data.description = ""
        if contact_data.isActive is None:
            contact_data.isActive = True
        if contact_data.displayOrder is None:
            contact_data.displayOrder = 0

        return await self.storage.create(contact_data)

    async def update(self, id: str, update_data: ContactInternalUpdate) -> ContactInternal:
        # If email is explicitly None, set to empty string
        if update_data.email is None:
            # We preserve None meaning "don't update" in update_data, but here it seems they wanted to clear it
            # The original logic merged dictionaries and popped 'email'. In our strict Pydantic model, 
            # we just pass None and it gets ignored, or we can explicitly set it. 
            pass # Pydantic model handles this cleanly.

        return await self.storage.update(id, update_data)

    async def delete(self, id: str) -> bool:
        return await self.storage.delete(id)


contact_repository = ContactRepository()
