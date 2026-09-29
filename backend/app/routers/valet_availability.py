from app.models.user import User
from app.models.schemas import MessageResponse
"""
Valet Availability Router

Valets mark their availability ahead of time per day.
Super Admin can view all valets' availability.

Endpoints:
  POST   /valet-availability          – Mark / upsert availability for a date (valet)
  GET    /valet-availability/my       – View own upcoming availability (valet)
  GET    /valet-availability          – View all valets' availability (super admin)
  DELETE /valet-availability/{id}     – Remove own availability entry (valet)
"""

from datetime import date as dt_date
from datetime import timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ValidationInfo, field_validator, model_validator, Field

from app.db.storage_factory import get_storage
from app.utils.auth import get_current_user, require_super_admin_or_seller


from app.models.valet_availability import ValetAvailability
class EnrichedValetAvailabilityResponse(ValetAvailability):
    valetName: Optional[str] = None
    valetPhone: Optional[str] = None
    serviceAreaZones: Optional[List[str]] = []

router = APIRouter()
storage = get_storage("valetAvailability")


# ─── Schemas ─────────────────────────────────────────────────────────────────


class ValetAvailabilityCreate(BaseModel):
    date: str  # ISO date string, e.g. "2026-08-10"
    availabilityType: str  # "full_day" | "custom"
    slots: Optional[List[str]] = []  # slot IDs — only used when type = "custom"
    zones: List[str] = []  # zones selected for this date

    @field_validator("availabilityType")
    @classmethod
    def validate_type(cls, v):
        if v not in ("full_day", "custom"):
            raise ValueError("availabilityType must be 'full_day' or 'custom'")
        return v

    @model_validator(mode="after")
    def validate_slots(self):
        if self.availabilityType == "full_day" and self.slots:
            raise ValueError("slots must be empty when availabilityType is 'full_day'")
        if self.availabilityType == "custom" and not self.slots:
            raise ValueError("slots must not be empty when availabilityType is 'custom'")
        return self


# ─── Helper ───────────────────────────────────────────────────────────────────


def _require_valet(current_user: User):
    if current_user.role != "valet":
        raise HTTPException(status_code=403, detail="Only valets can access this endpoint")


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.post("", response_model=ValetAvailability, status_code=201)
@router.post("/", response_model=ValetAvailability, status_code=201)
async def mark_availability(
    data: ValetAvailabilityCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Mark (or update) availability for a date.
    One document per valetId + date — upserts on conflict.
    """
    _require_valet(current_user)

    # Validate date is today or in the future (up to 7 days)
    try:
        target_date = dt_date.fromisoformat(data.date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    today = dt_date.today()
    if target_date < today:
        raise HTTPException(status_code=400, detail="Cannot mark availability for a past date.")
    if target_date > today + timedelta(days=7):
        raise HTTPException(status_code=400, detail="Cannot mark availability more than 7 days in advance.")

    # Validate slot IDs exist in delivery slot config for the given date
    if data.availabilityType == "custom" and data.slots:
        slot_cfg_storage = get_storage("deliverySlots")
        slot_configs = await slot_cfg_storage.findAll({"date": data.date, "isActive": True})
        all_valid_slot_ids = {
            slot.id
            for config in slot_configs
            for slot in (config.slots or [])
            if slot.id
        }
        invalid_slots = [s for s in data.slots if s not in all_valid_slot_ids]
        if invalid_slots:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid or inactive slot IDs for date {data.date}: {invalid_slots}. "
                f"Available slots: {list(all_valid_slot_ids) or 'none configured'}",
            )

    valet_id = str(current_user.id)

    # Validate zones are within valet's permitted zones
    permitted_zones = set(current_user.service_area_zones or [])
    invalid_zones = [z for z in data.zones if z not in permitted_zones]
    if invalid_zones:
        raise HTTPException(
            status_code=400,
            detail=f"You are not assigned to these zones: {invalid_zones}. Your assigned zones: {list(permitted_zones)}",
        )

    # Check for existing entry to upsert
    existing = await storage.findAll({"valetId": valet_id, "date": data.date})

    from datetime import datetime, timezone

    from app.models.daos import ValetAvailabilityInternalCreate, ValetAvailabilityInternalUpdate

    if existing:
        doc_id = str(existing[0]["_id"])
        updated = await storage.update(doc_id, ValetAvailabilityInternalUpdate(
            valetId=valet_id,
            date=data.date,
            availabilityType=data.availabilityType,
            slots=data.slots,
            zones=data.zones
        ))
        return updated
    else:
        created = await storage.create(ValetAvailabilityInternalCreate(
            valetId=valet_id,
            date=data.date,
            availabilityType=data.availabilityType,
            slots=data.slots,
            zones=data.zones
        ))
        return created


@router.get("/my", response_model=List[ValetAvailability])
async def get_my_availability(
    current_user: User = Depends(get_current_user),
):
    """Return own upcoming availability (today + next 7 days)."""
    _require_valet(current_user)

    today = dt_date.today()
    upcoming_dates = [(today + timedelta(days=i)).isoformat() for i in range(8)]

    valet_id = str(current_user.id)
    all_docs = await storage.findAll({"valetId": valet_id})

    return [record for record in all_docs if (record.date.strftime("%Y-%m-%d")) in upcoming_dates]


@router.get("", response_model=List[EnrichedValetAvailabilityResponse])
@router.get("/", response_model=List[EnrichedValetAvailabilityResponse])
async def get_all_availability(
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    valetId: Optional[str] = Query(None, description="Filter by valet ID"),
    current_user: User = Depends(require_super_admin_or_seller),
):
    """Return valets' availability. Super Admin sees all. Sellers see valets in their service area."""
    query: dict = {}
    if date:
        query["date"] = date
    if valetId:
        query["valetId"] = valetId

    records = await storage.findAll(query)

    # Enrich with valet name for admin display
    from app.repositories.user_repository import user_repository

    valet_ids = list({record.valet_id for record in records if record.valet_id})
    valets_map: Dict[str, User] = {}
    for vid in valet_ids:
        valet = await user_repository.findById(vid)
        if valet:
            valets_map[vid] = valet

    # Determine seller's service area if applicable
    is_seller = current_user.is_seller_admin or current_user.role == "seller"
    seller_zones = set()
    if is_seller and current_user.role != "super_admin":
        # Use serviceableZoneIds directly — sellers now declare zones, not pincodes
        zone_ids = current_user.service_area_zones or []
        seller_zones = set(zone_ids)

    enriched = []
    for record in records:
        vid = (record.valet_id or "")
        valet = valets_map.get(vid)

        # Filter for sellers
        if is_seller and current_user.role != "super_admin":
            # Compare valet's daily selected zones with seller's zones
            valet_daily_zones = set(record.zones or [])
            if not seller_zones.intersection(valet_daily_zones):
                continue

        enriched.append(
            EnrichedValetAvailabilityResponse(
                **record.model_dump(),
                valetName=valet.name if valet else "",
                valetPhone=valet.phone if valet else "",
                serviceAreaZones=valet.service_area_zones if valet else [],
            )
        )

    # Sort by date ascending
    enriched.sort(key=lambda r: r.date or "")
    return enriched


@router.delete("/{record_id}", response_model=MessageResponse)
async def delete_availability(
    record_id: str,
    current_user: User = Depends(get_current_user),
):
    """Remove an availability entry. Valets can only delete their own entries."""
    _require_valet(current_user)

    record = await storage.findById(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Availability entry not found")

    if str(record.valet_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="You can only delete your own availability entries")

    # Prevent deleting past entries
    try:
        entry_date = dt_date.fromisoformat(record.date)
        if entry_date < dt_date.today():
            raise HTTPException(status_code=400, detail="Cannot delete past availability entries")
    except (ValueError, KeyError):
        pass

    await storage.delete(record_id)
    return {"message": "Availability entry deleted successfully"}
