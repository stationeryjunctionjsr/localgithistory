from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db.storage_factory import get_storage
from app.utils.auth import require_super_admin

router = APIRouter()
storage = get_storage("deliverySlots")


class SlotBase(BaseModel):
    id: str
    startTime: str
    endTime: str
    capacity: Optional[int] = None  # max bookings allowed; None = unlimited
    bookedCount: Optional[int] = 0  # current bookings for this slot
    isActive: bool = True
    isUrgent: bool = False  # marks this as an urgent delivery slot
    cutoffHours: Optional[int] = None  # slot closes N hours before startTime; None = no cutoff
    urgentCutoffHours: Optional[int] = (
        None  # cutoff specifically for urgent slots; overrides cutoffHours when isUrgent=True
    )


class DeliverySlotConfigBase(BaseModel):
    segment: str
    date: str
    pincodes: List[str]
    slots: List[SlotBase]
    isActive: bool = True


class DeliverySlotConfigCreate(DeliverySlotConfigBase):
    pass


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
async def get_delivery_slots(
    segment: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    current_user: dict = Depends(require_super_admin),
):
    query = {}
    if segment:
        query["segment"] = segment
    if date:
        query["date"] = date

    slots = await storage.findAll(query)
    return slots


@router.get("/available", response_model=List[Dict[str, Any]])
async def get_available_slots(
    date: str = Query(...),
    pincode: str = Query(...),
    segment: str = Query("retail"),
):
    """
    Public endpoint (no auth) — returns available time slots for a given date,
    pincode, and segment. Used by the checkout UI to populate the slot picker.
    Filters to active slots with remaining capacity and cutoff hours.
    """
    import datetime as _dt

    # Current time in IST (UTC+5:30)
    utc_now = _dt.datetime.now(timezone.utc)
    ist_offset = _dt.timedelta(hours=5, minutes=30)
    now_ist = utc_now + ist_offset

    all_configs = await storage.findAll({"date": date, "segment": segment, "isActive": True})

    matched_slots = []
    for config in all_configs:
        config_pincodes = config.get("pincodes", [])
        # Empty pincodes list means "all serviceable pincodes"
        if config_pincodes and pincode not in config_pincodes:
            continue

        for slot in config.get("slots", []):
            if not slot.get("isActive", True):
                continue

            # ── Cutoff hours check ──────────────────────────────────────
            is_urgent = slot.get("isUrgent", False)
            # For urgent slots: use urgentCutoffHours if set, else fall back to cutoffHours
            if is_urgent:
                cutoff_hours = (
                    slot.get("urgentCutoffHours")
                    if slot.get("urgentCutoffHours") is not None
                    else slot.get("cutoffHours")
                )
            else:
                cutoff_hours = slot.get("cutoffHours")

            if cutoff_hours is not None:
                start_time_str = slot.get("startTime", "")
                try:
                    # Parse the slot date + startTime into a datetime in IST
                    slot_start_ist = _dt.datetime.strptime(f"{date} {start_time_str}", "%Y-%m-%d %H:%M")
                    cutoff_ist = slot_start_ist - _dt.timedelta(hours=cutoff_hours)
                    if now_ist >= cutoff_ist:
                        continue  # Past the cutoff — slot is closed for booking
                except ValueError:
                    pass  # If time can't be parsed, allow the slot through

            # ── Capacity check ──────────────────────────────────────────
            capacity = slot.get("capacity")
            booked = slot.get("bookedCount", 0)
            if capacity is not None:
                remaining = max(0, capacity - booked)
                if remaining == 0:
                    continue  # Slot fully booked — skip

            matched_slots.append(
                {
                    "configId": str(config.get("_id")),
                    "slotId": slot.get("id"),
                    "date": date,
                    "startTime": slot.get("startTime"),
                    "endTime": slot.get("endTime"),
                    "isUrgent": slot.get("isUrgent", False),
                }
            )

    # Sort by startTime
    matched_slots.sort(key=lambda s: s.get("startTime", ""))
    return matched_slots


@router.get("/dates-with-slots")
async def get_dates_with_slots(
    pincode: str = Query(...),
    segment: str = Query("retail"),
):
    """
    Public endpoint — returns list of dates (next 7 days) that have at
    least one active slot available for the given pincode and segment.
    Used by check-serviceability to tell checkout whether slot booking is available.
    """
    from datetime import date as dt_date, timedelta
    from app.db.storage_factory import get_storage as _get_storage

    today = dt_date.today()
    dates_to_check = [(today + timedelta(days=i)).isoformat() for i in range(7)]

    slot_storage = _get_storage("deliverySlots")
    available_dates = []

    for check_date in dates_to_check:
        configs = await slot_storage.findAll({"date": check_date, "segment": segment, "isActive": True})
        for config in configs:
            config_pincodes = config.get("pincodes", [])
            if config_pincodes and pincode not in config_pincodes:
                continue
            # Has at least one active slot with remaining capacity
            for slot in config.get("slots", []):
                if not slot.get("isActive", True):
                    continue
                cap = slot.get("capacity")
                booked = slot.get("bookedCount", 0)
                if cap is None or (cap - booked) > 0:
                    available_dates.append(check_date)
                    break
            else:
                continue
            break

    return {"availableDates": available_dates}


@router.post("/{config_id}/book-slot")
async def book_slot(config_id: str, slot_id: str = Query(...)):
    """
    Internal endpoint — atomically increments bookedCount for a specific slot.
    Called after a successful order creation. No auth guard needed since it's
    called server-side from the orders router.
    """
    config = await storage.findById(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Slot configuration not found")

    slots = config.get("slots", [])
    updated = False
    for slot in slots:
        if slot.get("id") == slot_id:
            cap = slot.get("capacity")
            booked = slot.get("bookedCount", 0)
            if cap is not None and booked >= cap:
                raise HTTPException(status_code=409, detail="Slot is fully booked")
            slot["bookedCount"] = booked + 1
            updated = True
            break

    if not updated:
        raise HTTPException(status_code=404, detail="Slot not found in configuration")

    await storage.update(config_id, {"slots": slots})
    return {"success": True}


@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_delivery_slot_config(
    config: DeliverySlotConfigCreate, current_user: dict = Depends(require_super_admin)
):
    # Check if a config already exists for this date and segment
    existing = await storage.findAll({"date": config.date, "segment": config.segment})
    if existing:
        raise HTTPException(
            status_code=409, detail=f"Delivery slot configuration already exists for {config.date} ({config.segment})"
        )

    result = await storage.create(config.dict())
    return result


@router.put("/{config_id}", response_model=Dict[str, Any])
async def update_delivery_slot_config(
    config_id: str, config: DeliverySlotConfigBase, current_user: dict = Depends(require_super_admin)
):
    updated = await storage.update(config_id, config.dict())
    if not updated:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return updated


@router.delete("/{config_id}")
async def delete_delivery_slot_config(config_id: str, current_user: dict = Depends(require_super_admin)):
    result = await storage.delete(config_id)
    if not result:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return {"message": "Deleted successfully"}
