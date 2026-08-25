from typing import Any, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db.storage_factory import get_storage
from app.utils.auth import require_super_admin

router = APIRouter()
storage = get_storage("systemSettings")


class SystemSettingsUpdate(BaseModel):
    maxConcurrentOrders: int


@router.get("", response_model=Dict[str, Any])
@router.get("/", response_model=Dict[str, Any])
async def get_settings(current_user: dict = Depends(require_super_admin)):
    """Get global system settings"""
    doc = await storage.findById("global_settings")
    if not doc:
        return {"maxConcurrentOrders": 1}
    return doc


@router.put("", response_model=Dict[str, Any])
@router.put("/", response_model=Dict[str, Any])
async def update_settings(data: SystemSettingsUpdate, current_user: dict = Depends(require_super_admin)):
    """Update global system settings"""
    doc = await storage.findById("global_settings")
    if not doc:
        new_doc = {"_id": "global_settings", "maxConcurrentOrders": data.maxConcurrentOrders}
        await storage.create(new_doc)
        return new_doc

    updated = await storage.update("global_settings", {"maxConcurrentOrders": data.maxConcurrentOrders})
    return updated
