from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.repositories.promo_strip_repository import promo_strip_repository
from app.utils.auth import require_super_admin
from app.utils.cache import cache

router = APIRouter()


class PromoStripCreate(BaseModel):
    text: str = Field(..., min_length=1)
    isActive: Optional[bool] = True


class PromoStripUpdate(BaseModel):
    text: Optional[str] = None
    isActive: Optional[bool] = None


@router.get("")
@router.get("/")
async def get_promo_strips():
    """Public endpoint to get all promo strips"""
    return await promo_strip_repository.findAll()


@router.get("/active")
@cache.ttl_cache(ttl=300.0)
async def get_active_promo_strips():
    """Public endpoint to get only active promo strips"""
    strips = await promo_strip_repository.findAll()
    return [s for s in strips if s.get("isActive", True)]


@router.post("")
@router.post("/")
async def create_promo_strip(data: PromoStripCreate, user: dict = Depends(require_super_admin)):
    """Admin endpoint to create a promo strip"""
    res = await promo_strip_repository.create(data.dict())
    cache.invalidate(get_active_promo_strips)
    return res


@router.patch("/{id}/toggle")
async def toggle_promo_strip(id: str, user: dict = Depends(require_super_admin)):
    """Admin endpoint to toggle active status"""
    strip = await promo_strip_repository.findById(id)
    if not strip:
        raise HTTPException(status_code=404, detail="Promo strip not found")

    res = await promo_strip_repository.update(id, {"isActive": not (strip.is_active if strip.is_active is not None else True)})
    cache.invalidate(get_active_promo_strips)
    return res


@router.put("/{id}")
async def update_promo_strip(id: str, data: PromoStripUpdate, user: dict = Depends(require_super_admin)):
    """Admin endpoint to update promo strip"""
    strip = await promo_strip_repository.findById(id)
    if not strip:
        raise HTTPException(status_code=404, detail="Promo strip not found")

    update_data = {k: v for k, v in data.dict().items() if v is not None}
    res = await promo_strip_repository.update(id, update_data)
    cache.invalidate(get_active_promo_strips)
    return res


@router.delete("/{id}")
async def delete_promo_strip(id: str, user: dict = Depends(require_super_admin)):
    """Admin endpoint to permanently delete a promo strip"""
    strip = await promo_strip_repository.findById(id)
    if not strip:
        raise HTTPException(status_code=404, detail="Promo strip not found")

    await promo_strip_repository.delete(id)
    cache.invalidate(get_active_promo_strips)
    return {"message": "Promo strip deleted successfully"}
