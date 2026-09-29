from app.models.user import User
from typing import List
from app.models.daos_flat import PromoStripsInternalCreate, PromoStripsInternalUpdate
from app.models.schemas import MessageResponse, PromoStripResponse
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.repositories.promo_strip_repository import promo_strip_repository
from app.utils.auth import require_super_admin
from app.utils.cache import cache

router = APIRouter()


class PromoStripCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")
    text: str = Field(..., min_length=1)
    isActive: Optional[bool] = True
    zoneIds: Optional[List[str]] = None


class PromoStripUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")
    text: Optional[str] = None
    isActive: Optional[bool] = None
    zoneIds: Optional[List[str]] = None


@router.get("", response_model=List[PromoStripResponse])
@router.get("/", response_model=List[PromoStripResponse])
async def get_promo_strips():
    """Public endpoint to get all promo strips"""
    return await promo_strip_repository.findAll()


@cache.ttl_cache(ttl=300.0)
async def _get_active_promo_strips_cached(zone_id: Optional[str]) -> List[PromoStripResponse]:
    """Internal cached function. zone_id = None means wholesaler/no-pincode (show only global strips)."""
    return await promo_strip_repository.findActive(zone_id=zone_id)


@router.get("/active", response_model=List[PromoStripResponse])
async def get_active_promo_strips(
    pincode: Optional[str] = None,
    userRole: Optional[str] = "guest",
):
    """
    Return active promo strips for the caller's zone.
    - Wholesaler / no pincode: global strips only (zoneIds is None/empty).
    - Retail with pincode: global strips + strips targeting this zone.
    """
    zone_id: Optional[str] = None
    if userRole != "wholesaler" and pincode:
        from app.repositories.zone_seller_cache import get_zone_id_and_seller_ids_for_pincode
        zone_id_result, _ = await get_zone_id_and_seller_ids_for_pincode(pincode)
        zone_id = zone_id_result
    return await _get_active_promo_strips_cached(zone_id)


@router.post("", response_model=PromoStripResponse)
@router.post("/", response_model=PromoStripResponse)
async def create_promo_strip(data: PromoStripCreate, user: User = Depends(require_super_admin)):
    """Admin endpoint to create a promo strip"""
    internal_data = PromoStripsInternalCreate(
        text=data.text,
        is_active=data.is_active if data.is_active is not None else True,
        zone_ids=data.zone_ids,
    )
    res = await promo_strip_repository.create(internal_data)
    cache.invalidate(_get_active_promo_strips_cached)
    return res


@router.patch("/{id}/toggle", response_model=PromoStripResponse)
async def toggle_promo_strip(id: str, user: User = Depends(require_super_admin)):
    """Admin endpoint to toggle active status"""
    strip = await promo_strip_repository.findById(id)
    if not strip:
        raise HTTPException(status_code=404, detail="Promo strip not found")

    update_data = PromoStripsInternalUpdate(is_active=not (strip.is_active if strip.is_active is not None else True))
    res = await promo_strip_repository.update(id, update_data)
    cache.invalidate(_get_active_promo_strips_cached)
    return res


@router.put("/{id}", response_model=PromoStripResponse)
async def update_promo_strip(id: str, data: PromoStripUpdate, user: User = Depends(require_super_admin)):
    """Admin endpoint to update promo strip"""
    strip = await promo_strip_repository.findById(id)
    if not strip:
        raise HTTPException(status_code=404, detail="Promo strip not found")

    update_data = PromoStripsInternalUpdate(
        text=data.text,
        is_active=data.is_active,
        zone_ids=data.zone_ids,
    )
    res = await promo_strip_repository.update(id, update_data)
    cache.invalidate(_get_active_promo_strips_cached)
    return res


@router.delete("/{id}", response_model=MessageResponse)
async def delete_promo_strip(id: str, user: User = Depends(require_super_admin)):
    """Admin endpoint to permanently delete a promo strip"""
    strip = await promo_strip_repository.findById(id)
    if not strip:
        raise HTTPException(status_code=404, detail="Promo strip not found")

    await promo_strip_repository.delete(id)
    cache.invalidate(_get_active_promo_strips_cached)
    return {"message": "Promo strip deleted successfully"}
