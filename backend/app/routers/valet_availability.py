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

import logging
from datetime import date as dt_date
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator, model_validator

from app.db.storage_factory import get_storage
from app.models.base import CamelBaseModel
from app.models.daos import (
    ValetAvailabilityFilter,
    ValetAvailabilityInternalCreate,
    ValetAvailabilityInternalUpdate,
)
from app.models.schemas import MessageResponse
from app.models.user import User
from app.models.valet_availability import ValetAvailability
from app.repositories.user_repository import user_repository
from app.utils.auth import get_current_user, require_super_admin_or_seller

logger = logging.getLogger(__name__)

router = APIRouter()
storage = get_storage("valetAvailability")


# ─── Schemas ─────────────────────────────────────────────────────────────────


class EnrichedValetAvailabilityResponse(ValetAvailability):
    valet_name: Optional[str] = None
    valet_phone: Optional[str] = None
    service_area_zones: list[str] = Field(default_factory=list)


class ValetAvailabilityCreate(BaseModel):
    date: str  # ISO date string, e.g. "2026-08-10"
    availabilityType: str  # "full_day" | "custom"
    slots: list[str] = Field(default_factory=list)  # slot IDs — only used when type = "custom"
    zones: list[str] = Field(default_factory=list)  # zones selected for this date

    @field_validator("availabilityType")
    @classmethod
    def validate_type(cls, v: str) -> str:
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
    One document per valetId + date — upserts on conflict via DAO.
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
        slot_configs = await slot_cfg_storage.findAll(date=data.date, is_active=True)
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

    return await storage.upsert_availability(
        ValetAvailabilityInternalCreate(
            valet_id=valet_id,
            date=data.date,
            availability_type=data.availabilityType,
            slots=data.slots,
            zones=data.zones,
        )
    )


@router.get("/my", response_model=list[ValetAvailability])
async def get_my_availability(
    current_user: User = Depends(get_current_user),
):
    """Return own upcoming availability (today + next 7 days) via pushdown SQL, ordered by date ASC."""
    _require_valet(current_user)

    today = dt_date.today()
    max_date = today + timedelta(days=7)
    valet_id = str(current_user.id)

    return await storage.get_my_upcoming_availability(
        valet_id=valet_id,
        start_date=today.isoformat(),
        end_date=max_date.isoformat(),
    )


@router.get("", response_model=list[EnrichedValetAvailabilityResponse])
@router.get("/", response_model=list[EnrichedValetAvailabilityResponse])
async def get_all_availability(
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    valetId: Optional[str] = Query(None, description="Filter by valet ID"),
    current_user: User = Depends(require_super_admin_or_seller),
):
    """Return valets' availability. Super Admin sees all. Sellers see valets in their service area."""
    is_seller = current_user.role == "seller" or current_user.is_seller_admin
    seller_zones: Optional[list[str]] = None
    if is_seller and current_user.role != "super_admin":
        seller_zones = current_user.service_area_zones or []

    filters = ValetAvailabilityFilter(
        date=date,
        valet_id=valetId,
        seller_zones=seller_zones if seller_zones else None,
    )

    records = await storage.findAll(filters)

    valet_ids = list({record.valet_id for record in records if record.valet_id})
    valet_users = await user_repository.findByIds(valet_ids)
    valets_map: dict[str, User] = {str(u.id): u for u in valet_users}

    enriched: list[EnrichedValetAvailabilityResponse] = []
    for record in records:
        vid = record.valet_id or ""
        valet = valets_map.get(vid)
        enriched.append(
            EnrichedValetAvailabilityResponse(
                id=record.id,
                valet_id=record.valet_id,
                date=record.date,
                availability_type=record.availability_type,
                slots=record.slots,
                zones=record.zones,
                created_at=record.created_at,
                updated_at=record.updated_at,
                valet_name=valet.name if valet else "",
                valet_phone=valet.phone if valet else "",
                service_area_zones=valet.service_area_zones if valet else [],
            )
        )

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

    if record.date:
        try:
            entry_date = dt_date.fromisoformat(str(record.date))
            if entry_date < dt_date.today():
                raise HTTPException(status_code=400, detail="Cannot delete past availability entries")
        except (ValueError, TypeError):
            pass

    await storage.delete(record_id)
    return {"message": "Availability entry deleted successfully"}
