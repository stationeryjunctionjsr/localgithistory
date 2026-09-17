from app.models.user import User
from typing import Dict, Any, List
from app.models.schemas import MessageResponse, DeliveryZoneResponse
"""
Delivery Zones router.

Super admin creates named zones that group pincodes together.
Each zone has a default capacity (inherited by delivery slot configs) and
an optional urgent-delivery flag.

Each zone is tagged with a customerType:
  - "retail"   — only Retail Customers are served by this zone
  - "business" — only Business (Wholesale) Customers are served by this zone
  - "both"     — both Retail and Business Customers are served by this zone

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
    customerType: str = "retail"  # "retail" | "business" | "both"


class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    pincodes: Optional[List[str]] = None
    defaultCapacity: Optional[int] = None
    urgentDeliveryAvailable: Optional[bool] = None
    isActive: Optional[bool] = None
    customerType: Optional[str] = None  # "retail" | "business" | "both"


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
        if exclude_zone_id and str(z.id) == str(exclude_zone_id):
            continue
        for pc in (z.pincodes or []):
            taken[pc] = z.name if z.name is not None else str(z.id)
    return [pc for pc in pincodes if pc in taken]


# ── Routes — ORDER MATTERS: static paths before /{zone_id} ───────────────────


from app.config.database import get_async_session_factory
from sqlalchemy import text

@router.get("/for-pincode", response_model=DeliveryZoneResponse)
async def get_zone_for_pincode(pincode: str = Query(..., description="6-digit pincode")):
    """
    Public endpoint - resolve which zone a pincode belongs to.
    Returns zone metadata including defaultCapacity, urgentDeliveryAvailable, and customerType.
    Used by checkout slot-picker and order creation.
    """
    factory = get_async_session_factory()
    async with factory() as session:
        result = await session.execute(
            text("""
                SELECT z.id, z.name, z.default_capacity, z.urgent_delivery_available, z.customer_type
                FROM sj_delivery_zones z
                JOIN sj_delivery_zone_pincodes p ON z.id = p.sj_delivery_zones_id
                WHERE p.pincode = :pincode AND z.is_active = 1
                LIMIT 1
            """),
            {"pincode": pincode}
        )
        row = result.fetchone()
        
    if row:
        return {
            "zoneId": str(row.id),
            "zoneName": row.name,
            "defaultCapacity": row.default_capacity if row.default_capacity is not None else 10,
            "urgentDeliveryAvailable": bool(row.urgent_delivery_available),
            "customerType": row.customer_type or "retail",
        }

    # Pincode not mapped to any zone
    return {
        "zoneId": None,
        "zoneName": None,
        "defaultCapacity": None,
        "urgentDeliveryAvailable": False,
        "customerType": "retail",
    }


@router.get("", response_model=List[DeliveryZoneResponse])
@router.get("/", response_model=List[DeliveryZoneResponse])
async def get_zones(current_user: User = Depends(require_super_admin)):
    """List all delivery zones."""
    storage = get_storage("deliveryZones")
    return await storage.findAll({})


@router.post("", response_model=DeliveryZoneResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=DeliveryZoneResponse, status_code=status.HTTP_201_CREATED)
async def create_zone(
    zone: ZoneCreate,
    current_user: User = Depends(require_super_admin),
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
    internal_create = DeliveryZoneInternalCreate.model_validate(zone, from_attributes=True)
    result = await storage.create(internal_create)
    # New zone means a new zone_id — full cache clear is cheapest
    from app.repositories.zone_seller_cache import invalidate_zone_cache
    invalidate_zone_cache()
    return result


@router.get("/{zone_id}", response_model=DeliveryZoneResponse)
async def get_zone(zone_id: str, current_user: User = Depends(require_super_admin)):
    """Get a single delivery zone by ID."""
    storage = get_storage("deliveryZones")
    zone = await storage.findById(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone


@router.put("/{zone_id}", response_model=DeliveryZoneResponse)
async def update_zone(
    zone_id: str,
    zone: ZoneUpdate,
    current_user: User = Depends(require_super_admin),
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

    internal_update = DeliveryZoneInternalUpdate.model_validate(zone, from_attributes=True)
    updated_zone = await storage.update(zone_id, internal_update)
    if not updated_zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    # Evict this specific zone so fresh sellers are picked up immediately
    from app.repositories.zone_seller_cache import invalidate_zone_cache
    invalidate_zone_cache(zone_id)
    return updated_zone


@router.delete("/{zone_id}", response_model=MessageResponse)
async def delete_zone(
    zone_id: str,
    current_user: User = Depends(require_super_admin),
):
    """Delete a delivery zone."""
    storage = get_storage("deliveryZones")
    existing = await storage.findById(zone_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Zone not found")

    result = await storage.delete(zone_id)
    if not result:
        raise HTTPException(status_code=404, detail="Zone not found")
    from app.repositories.zone_seller_cache import invalidate_zone_cache
    invalidate_zone_cache(zone_id)
    return {"message": "Zone deleted successfully"}
