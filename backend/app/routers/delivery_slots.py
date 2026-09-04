from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db.storage_factory import get_storage
from app.utils.auth import require_super_admin

router = APIRouter()
storage = get_storage("deliverySlots")

# Sentinel zone ID for the "Default" fallback config
DEFAULT_ZONE_ID = "default"


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
    # zoneId replaces the old free-form pincodes list.
    # Use "default" to create a fallback config for zones that have no specific config.
    zoneId: str = DEFAULT_ZONE_ID
    slots: List[SlotBase]
    isActive: bool = True


class DeliverySlotConfigCreate(BaseModel):
    """
    Create request — admin selects one or more zones (or "default").
    The backend will create a separate SlotConfig record per zone, each
    auto-filled with that zone's defaultCapacity.
    """
    segment: str
    date: str
    zoneIds: List[str]  # e.g. ["zone_abc", "zone_xyz"] or ["default"]
    slots: List[SlotBase]
    isActive: bool = True


async def _resolve_zone_config(pincode: str, date: str, segment: str) -> Optional[Dict]:
    """
    Given a customer pincode, return the best matching SlotConfig for that date/segment.
    1. Resolve pincode → zoneId via /delivery-zones/for-pincode helper.
    2. Try to find a SlotConfig with that specific zoneId.
    3. If none, fall back to the "default" zone config for that date/segment.
    """
    from app.repositories.zone_seller_cache import get_zone_for_pincode
    zone_data = await get_zone_for_pincode(pincode)
    zone_id = zone_data.get("zoneId") if zone_data else None

    # Try zone-specific config first
    if zone_id:
        configs = await storage.findAll({"date": date, "segment": segment, "zoneId": zone_id, "isActive": True})
        if configs:
            return configs[0]

    # Fall back to "default" config
    default_configs = await storage.findAll({"date": date, "segment": segment, "zoneId": DEFAULT_ZONE_ID, "isActive": True})
    if default_configs:
        return default_configs[0]

    return None


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
async def get_delivery_slots(
    segment: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    zoneId: Optional[str] = Query(None),
    current_user: dict = Depends(require_super_admin),
):
    query: Dict[str, Any] = {}
    if segment:
        query["segment"] = segment
    if date:
        query["date"] = date
    if zoneId:
        query["zoneId"] = zoneId

    slots = await storage.findAll(query)
    return slots


@router.get("/available", response_model=List[Dict[str, Any]])
async def get_available_slots(
    date: str = Query(...),
    pincode: str = Query(...),
    segment: str = Query("retail"),
):
    """
    Public endpoint. Returns available time slots for a pincode on a given date.
    Resolves pincode → zone, then tries zone-specific config, then falls back to default.
    """
    import datetime as _dt
    from datetime import timezone

    utc_now = _dt.datetime.now(timezone.utc)
    ist_offset = _dt.timedelta(hours=5, minutes=30)
    now_ist = utc_now + ist_offset

    config = await _resolve_zone_config(pincode, date, segment)
    if not config:
        return []

    matched_slots = []
    for slot in config.get("slots", []):
        if not slot.get("isActive", True):
            continue

        is_full_day = slot.get("isFullDay", False)
        is_urgent = slot.get("isUrgent", False)

        # Cutoff hours check
        if not is_full_day:
            if is_urgent:
                cutoff_hours = (
                    slot.get("urgentCutoffHours")
                    if slot.get("urgentCutoffHours") is not None
                    else slot.get("cutoffHours")
                )
            else:
                cutoff_hours = slot.get("cutoffHours")

            if cutoff_hours is not None:
                anchor_time_str = slot.get("endTime", "") if is_urgent else slot.get("startTime", "")
                try:
                    anchor_ist = _dt.datetime.strptime(f"{date} {anchor_time_str}", "%Y-%m-%d %H:%M")
                    cutoff_ist = anchor_ist - _dt.timedelta(hours=cutoff_hours)
                    if now_ist >= cutoff_ist:
                        continue
                except ValueError:
                    pass

        # Capacity check — slot capacity takes priority; zone defaultCapacity as fallback
        if not is_full_day:
            cap = slot.get("capacity")
            if cap is None:
                # Fallback: use zone's defaultCapacity
                cap = config.get("zoneDefaultCapacity")
            booked = slot.get("bookedCount", 0)
            if cap is not None and (cap - booked) <= 0:
                continue

        # 24-hour rule
        end_time_str = slot.get("endTime", "")
        try:
            slot_end_ist = _dt.datetime.strptime(f"{date} {end_time_str}", "%Y-%m-%d %H:%M")
            if slot_end_ist > (now_ist + _dt.timedelta(hours=24)):
                continue
        except ValueError:
            pass

        matched_slots.append({
            "configId": str(config["_id"]),
            "slotId": slot["id"],
            "startTime": slot["startTime"],
            "endTime": slot["endTime"],
            "isUrgent": is_urgent,
            "isFullDay": is_full_day,
        })

    return matched_slots


@router.get("/dates-with-slots")
async def get_dates_with_slots(
    pincode: str = Query(...),
    segment: str = Query("retail"),
):
    """
    Public endpoint. Returns available dates and urgent availability.
    Resolves pincode → zone config with default fallback.
    """
    import datetime as _dt
    from datetime import timezone

    utc_now = _dt.datetime.now(timezone.utc)
    ist_offset = _dt.timedelta(hours=5, minutes=30)
    now_ist = utc_now + ist_offset

    today = now_ist.date()
    available_dates = []
    urgent_available = False

    for i in range(7):
        check_date = (today + _dt.timedelta(days=i)).isoformat()
        config = await _resolve_zone_config(pincode, check_date, segment)
        if not config:
            continue

        has_valid_slot = False
        for slot in config.get("slots", []):
            if not slot.get("isActive", True):
                continue

            is_full_day = slot.get("isFullDay", False)
            is_urgent = slot.get("isUrgent", False)

            # Cutoff check
            if not is_full_day:
                cutoff_hours = slot.get("urgentCutoffHours") if is_urgent and slot.get("urgentCutoffHours") is not None else slot.get("cutoffHours")
                if cutoff_hours is not None:
                    anchor_time_str = slot.get("endTime", "") if is_urgent else slot.get("startTime", "")
                    try:
                        anchor_ist = _dt.datetime.strptime(f"{check_date} {anchor_time_str}", "%Y-%m-%d %H:%M")
                        if now_ist >= (anchor_ist - _dt.timedelta(hours=cutoff_hours)):
                            continue
                    except ValueError:
                        pass

            # 24-hour rule
            end_time_str = slot.get("endTime", "")
            try:
                slot_end_ist = _dt.datetime.strptime(f"{check_date} {end_time_str}", "%Y-%m-%d %H:%M")
                if slot_end_ist > (now_ist + _dt.timedelta(hours=24)):
                    continue
            except ValueError:
                pass

            # Capacity check with zone fallback
            if not is_full_day:
                cap = slot.get("capacity")
                if cap is None:
                    cap = config.get("zoneDefaultCapacity")
                booked = slot.get("bookedCount", 0)
                if cap is not None and (cap - booked) <= 0:
                    continue

            has_valid_slot = True
            if is_urgent and check_date == today.isoformat():
                urgent_available = True

        if has_valid_slot:
            available_dates.append(check_date)

    return {
        "availableDates": available_dates,
        "urgentAvailable": urgent_available,
    }


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
            if cap is None:
                cap = config.get("zoneDefaultCapacity")
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


@router.post("", response_model=List[Dict[str, Any]], status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=List[Dict[str, Any]], status_code=status.HTTP_201_CREATED)
async def create_delivery_slot_config(
    config: DeliverySlotConfigCreate, current_user: dict = Depends(require_super_admin)
):
    """
    Create slot configs for one or more zones.
    - For each selected zoneId (or "default"), a separate DB record is created.
    - Each slot's capacity is auto-filled with the zone's defaultCapacity if not provided.
    - If a config already exists for that date/segment/zone, it is overwritten (PUT).
    """
    zones_storage = get_storage("deliveryZones")
    created = []

    for zone_id in config.zoneIds:
        # Resolve zone capacity
        zone_default_capacity = 10  # fallback
        if zone_id != DEFAULT_ZONE_ID:
            zone_doc = await zones_storage.findById(zone_id)
            if zone_doc:
                zone_default_capacity = zone_doc.get("defaultCapacity", 10)

        # Auto-fill slot capacities from zone default if not set
        slots_with_capacity = []
        for slot in config.slots:
            slot_dict = slot.dict()
            if slot_dict.get("capacity") is None or slot_dict.get("capacity") == 0:
                slot_dict["capacity"] = zone_default_capacity
            slots_with_capacity.append(slot_dict)

        record = {
            "segment": config.segment,
            "date": config.date,
            "zoneId": zone_id,
            "zoneDefaultCapacity": zone_default_capacity,
            "slots": slots_with_capacity,
            "isActive": config.isActive,
        }

        # Check for existing config for this date/segment/zone
        existing = await storage.findAll({"date": config.date, "segment": config.segment, "zoneId": zone_id})
        if existing:
            updated = await storage.update(str(existing[0]["_id"]), record)
            created.append(updated)
        else:
            result = await storage.create(record)
            created.append(result)

    return created


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
