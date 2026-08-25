"""
Delivery Zones router.

Super admin creates named zones that group pincodes together.
Each zone has a default capacity (inherited by delivery slot configs) and
an optional urgent-delivery flag.

Public endpoint: GET /for-pincode?pincode=<pin>
  — Resolves which zone a pincode belongs to (used at checkout + order creation).

All other endpoints: super_admin only.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.db.storage_factory import get_storage
from app.utils.auth import require_super_admin

router = APIRouter()


# ── Pydantic models ────────────────────────────────────────────────────────────


class ZoneCreate(BaseModel):
    name: str
    description: Optional[str] = None
    pincodes: List[str] = []
    defaultCapacity: int = 10
    urgentDeliveryAvailable: bool = False
    isActive: bool = True


class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    pincodes: Optional[List[str]] = None
    defaultCapacity: Optional[int] = None
    urgentDeliveryAvailable: Optional[bool] = None
    isActive: Optional[bool] = None


# ── Helpers ────────────────────────────────────────────────────────────────────


async def _get_storage():
    return get_storage("deliveryZones")


async def _check_pincode_conflicts(
    pincodes: List[str],
    exclude_zone_id: Optional[str] = None,
) -> List[str]:
    """Return list of pincodes that already belong to another zone."""
    storage = get_storage("deliveryZones")
    all_zones = await storage.findAll({})
    taken: Dict[str, str] = {}
    for z in all_zones:
        if exclude_zone_id and str(z["_id"]) == str(exclude_zone_id):
            continue
        for pc in z.get("pincodes") or []:
            taken[pc] = z.get("name", str(z["_id"]))
    return [pc for pc in pincodes if pc in taken]


# ── Routes — ORDER MATTERS: static paths before /{zone_id} ───────────────────


@router.get("/for-pincode")
async def get_zone_for_pincode(pincode: str = Query(..., description="6-digit pincode")):
    """
    Public endpoint — resolve which zone a pincode belongs to.
    Returns zone metadata including defaultCapacity and urgentDeliveryAvailable.
    Used by checkout slot-picker and order creation.
    """
    storage = get_storage("deliveryZones")
    all_zones = await storage.findAll({"isActive": True})
    for zone in all_zones:
        if pincode in (zone.get("pincodes") or []):
            return {
                "zoneId": str(zone["_id"]),
                "zoneName": zone.get("name"),
                "defaultCapacity": zone.get("defaultCapacity", 10),
                "urgentDeliveryAvailable": bool(zone.get("urgentDeliveryAvailable", False)),
            }
    # Pincode not mapped to any zone
    return {
        "zoneId": None,
        "zoneName": None,
        "defaultCapacity": None,
        "urgentDeliveryAvailable": False,
    }


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
async def get_zones(current_user: dict = Depends(require_super_admin)):
    """List all delivery zones."""
    storage = get_storage("deliveryZones")
    return await storage.findAll({})


@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_zone(
    zone: ZoneCreate,
    current_user: dict = Depends(require_super_admin),
):
    """Create a new delivery zone. Rejects pincodes already assigned to another zone."""
    if zone.pincodes:
        conflicts = await _check_pincode_conflicts(zone.pincodes)
        if conflicts:
            raise HTTPException(
                status_code=400,
                detail=f"These pincodes are already assigned to another zone: {', '.join(conflicts)}",
            )
    storage = get_storage("deliveryZones")
    result = await storage.create(zone.dict())
    return result


@router.get("/{zone_id}", response_model=Dict[str, Any])
async def get_zone(zone_id: str, current_user: dict = Depends(require_super_admin)):
    """Get a single delivery zone by ID."""
    storage = get_storage("deliveryZones")
    zone = await storage.findById(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone


@router.put("/{zone_id}", response_model=Dict[str, Any])
async def update_zone(
    zone_id: str,
    zone: ZoneUpdate,
    current_user: dict = Depends(require_super_admin),
):
    """Update a delivery zone."""
    storage = get_storage("deliveryZones")
    existing = await storage.findById(zone_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Zone not found")

    # Validate pincode conflicts only when pincodes field is being changed
    if zone.pincodes is not None:
        conflicts = await _check_pincode_conflicts(zone.pincodes, exclude_zone_id=zone_id)
        if conflicts:
            raise HTTPException(
                status_code=400,
                detail=f"These pincodes are already assigned to another zone: {', '.join(conflicts)}",
            )

    update_data = {k: v for k, v in zone.dict().items() if v is not None}
    updated = await storage.update(zone_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Zone not found")
    return updated


@router.delete("/{zone_id}")
async def delete_zone(
    zone_id: str,
    current_user: dict = Depends(require_super_admin),
):
    """Delete a delivery zone."""
    storage = get_storage("deliveryZones")
    existing = await storage.findById(zone_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Zone not found")

    result = await storage.delete(zone_id)
    if not result:
        raise HTTPException(status_code=404, detail="Zone not found")
    return {"message": "Zone deleted successfully"}
