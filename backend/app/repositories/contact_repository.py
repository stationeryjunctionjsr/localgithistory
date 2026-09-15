from typing import Dict, Optional

from app.db.storage_factory import get_storage


class ContactRepository:
    def __init__(self):
        self.storage = get_storage("contacts")

    async def findAll(self, query: Optional[Dict] = None):
        return await self.storage.findAll(query or {})

    async def findById(self, id: str):
        return await self.storage.findById(id)

    async def create(self, contact_data: Any):
        # Ensure addresses array has max 2 items
        addresses = contact_data["addresses"] if "addresses" in contact_data else []
        if len(addresses) > 2:
            addresses = addresses[:2]

        # Ensure phoneNumbers array has max 3 items
        phone_numbers = contact_data["phoneNumbers"] if "phoneNumbers" in contact_data else []
        if len(phone_numbers) > 3:
            phone_numbers = phone_numbers[:3]

        contact = {
            "addresses": addresses,
            "phoneNumbers": phone_numbers,
            "email": contact_data["email"] if "email" in contact_data and contact_data["email"] is not None else "",
            "description": contact_data["description"] if "description" in contact_data else "",
            "isActive": contact_data["isActive"] if "isActive" in contact_data else True,
            "displayOrder": contact_data["displayOrder"] if "displayOrder" in contact_data else 0,
        }

        return await self.storage.create(contact)

    async def update(self, id: str, update_data: Any):
        # If email is explicitly None, remove it from the contact
        if "email" in update_data and update_data.email is None:
            # Get the current contact
            contact = await self.storage.findById(id)
            if contact:
                # Remove email field
                contact.pop("email", None)
                update_data = {k: v for k, v in update_data.items() if k != "email"}
                # Merge with existing contact data
                updated_contact = {**contact, **update_data}
                return await self.storage.update(id, updated_contact)
        return await self.storage.update(id, update_data)

    async def delete(self, id: str):
        return await self.storage.delete(id)


contact_repository = ContactRepository()
