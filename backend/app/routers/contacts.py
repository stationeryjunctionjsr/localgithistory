from app.models.user import User
from app.models.schemas import MessageResponse
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.models.daos_flat import ContactInternalCreate, ContactInternalUpdate
from app.models.schemas import ContactCreate, ContactResponse, ContactUpdate
from app.repositories.contact_repository import contact_repository
from app.utils.auth import get_current_user, require_super_admin
from app.utils.cache import cache

router = APIRouter()


@router.get("", response_model=List[ContactResponse])
@router.get("/", response_model=List[ContactResponse])
async def get_contacts(current_user: User = Depends(get_current_user)):
    if current_user.role == "super_admin":
        contacts = await contact_repository.findAll()
    else:
        contacts = await contact_repository.findAll({"isActive": True})

    contacts.sort(key=lambda x: (x.display_order if x.display_order is not None else 0))
    return contacts


@router.get("/public", response_model=List[ContactResponse])
@cache.ttl_cache(ttl=3600.0)
async def get_public_contacts():
    contacts = await contact_repository.findAll({"isActive": True})
    contacts.sort(key=lambda x: (x.display_order if x.display_order is not None else 0))
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: str):
    contact = await contact_repository.findById(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.post("", response_model=ContactResponse, status_code=201)
@router.post("/", response_model=ContactResponse, status_code=201)
async def create_contact(contact_data: ContactCreate, current_user: User = Depends(require_super_admin)):
    internal_data = ContactInternalCreate.model_validate(contact_data, from_attributes=True)
    contact = await contact_repository.create(internal_data)
    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: str, contact_data: ContactUpdate, current_user: User = Depends(require_super_admin)
):
    internal_data = ContactInternalUpdate.model_validate(contact_data, from_attributes=True)
    contact = await contact_repository.update(contact_id, internal_data)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.delete("/{contact_id}", response_model=MessageResponse)
async def delete_contact(contact_id: str, current_user: User = Depends(require_super_admin)):
    result = await contact_repository.delete(contact_id)
    if not result:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"message": "Contact deleted successfully"}
