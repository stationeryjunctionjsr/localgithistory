from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import ContactCreate, ContactResponse, ContactUpdate
from app.repositories.contact_repository import contact_repository
from app.utils.auth import get_current_user, require_super_admin
from app.utils.cache import cache

router = APIRouter()


@router.get("", response_model=List[ContactResponse])
@router.get("/", response_model=List[ContactResponse])
async def get_contacts(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") == "super_admin":
        contacts = await contact_repository.findAll()
    else:
        contacts = await contact_repository.findAll({"isActive": True})

    contacts.sort(key=lambda x: x.get("displayOrder", 0))
    return contacts


@router.get("/public", response_model=List[ContactResponse])
@cache.ttl_cache(ttl=3600.0)
async def get_public_contacts():
    contacts = await contact_repository.findAll({"isActive": True})
    contacts.sort(key=lambda x: x.get("displayOrder", 0))
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: str):
    contact = await contact_repository.findById(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.post("", response_model=ContactResponse, status_code=201)
@router.post("/", response_model=ContactResponse, status_code=201)
async def create_contact(contact_data: ContactCreate, current_user: dict = Depends(require_super_admin)):
    contact = await contact_repository.create(contact_data.dict())
    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: str, contact_data: ContactUpdate, current_user: dict = Depends(require_super_admin)
):
    contact = await contact_repository.update(contact_id, contact_data.dict(exclude_unset=True))
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.delete("/{contact_id}")
async def delete_contact(contact_id: str, current_user: dict = Depends(require_super_admin)):
    result = await contact_repository.delete(contact_id)
    if not result:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"message": "Contact deleted successfully"}
