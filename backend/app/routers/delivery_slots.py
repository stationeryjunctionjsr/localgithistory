from app.models.user import User
from app.models.schemas import MessageResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db.storage_factory import get_storage
from app.utils.auth import require_super_admin

router = APIRouter()
storage = get_storage("deliverySlots")

# Sentinel zone ID for the "Default" fallback config
DEFAULT_ZONE_ID = "default"



class DeliverySlotConfigResponse(BaseModel):
    id: str = Field(alias="_id")
    segment: str
    date: str
    zoneId: str
    slots: List[SlotBase]
    isActive: bool
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class AvailableSlotsResponse(BaseModel):
    date: str
    slots: List[SlotBase]

class DatesWithSlotsResponse(BaseModel):
    dates: List[str]

class BookSlotResponse(BaseModel):
    success: bool
    slot: SlotBase

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
    from app.repositories.zone_seller_cache import get_zone_for_pincode
    import logging
    logger = logging.getLogger(__name__)
    
    zone_data = await get_zone_for_pincode(pincode)
    zone_id = zone_data.get("_id") or zone_data.get("id") if zone_data else None
    logger.error(f"_resolve_zone_config: pincode={pincode} date={date} segment={segment} zone_data={zone_data} zone_id={zone_id}")

    if zone_id:
        configs = await storage.findAll({"date": date, "segment": segment, "zoneId": str(zone_id), "isActive": True})
        logger.error(f"_resolve_zone_config: found configs for zone_id: {configs}")
        if configs:
            return configs[0]

    default_configs = await storage.findAll({"date": date, "segment": segment, "zoneId": DEFAULT_ZONE_ID, "isActive": True})
    logger.error(f"_resolve_zone_config: found default configs: {default_configs}")
    if default_configs:
        return default_configs[0]

    return None


@router.get("", response_model=List[DeliverySlotConfigResponse])
@router.get("/", response_model=List[DeliverySlotConfigResponse])
async def get_delivery_slots(
    segment: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    zoneId: Optional[str] = Query(None),
    current_user: User = Depends(require_super_admin),
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


@router.get("/available", response_model=AvailableSlotsResponse)
async def get_available_slots(
    date: str = Query(...),
    pincode: str = Query(...),
    segment: str = Query("retail"),
):
    import logging
    logger = logging.getLogger(__name__)
    
    import datetime as _dt
    from datetime import timezone

    utc_now = _dt.datetime.now(timezone.utc)
    ist_offset = _dt.timedelta(hours=5, minutes=30)
    now_ist = (utc_now + ist_offset).replace(tzinfo=None)  # naive IST for comparison with strptime results

    config = await _resolve_zone_config(pincode, date, segment)
    logger.error(f"get_available_slots: config={config}")
    if not config:
        return []

    matched_slots = []
    for slot in config.get("slots", []):
        logger.error(f"get_available_slots: slot={slot}")
        if not (slot.get("isActive") if slot.get("isActive") is not None else True):
            continue

        is_full_day = (slot.get("isFullDay") if slot.get("isFullDay") is not None else False)
        is_urgent = (slot.get("isUrgent") if slot.get("isUrgent") is not None else False)

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
                anchor_time_str = (slot.get("endTime") or "") if is_urgent else (slot.get("startTime") or "")
                try:
                    anchor_ist = _dt.datetime.strptime(f"{date} {anchor_time_str}", "%Y-%m-%d %H:%M")
                    cutoff_ist = anchor_ist - _dt.timedelta(hours=cutoff_hours)
                    if now_ist >= cutoff_ist:
                        logger.error(f"get_available_slots: cutoff failed")
                        continue
                except ValueError:
                    pass

        if not is_full_day:
            cap = int(slot.get("capacity")) if slot.get("capacity") not in (None, "") else None
            if cap is None:
                cap = config.get("zoneDefaultCapacity")
            booked = int(slot.get("bookedCount") or 0)
            if cap is not None and booked >= cap:
                logger.error(f"get_available_slots: capacity failed")
                continue

        end_time_str = slot.get("endTime", "")
        if end_time_str:
            try:
                end_ist = _dt.datetime.strptime(f"{date} {end_time_str}", "%Y-%m-%d %H:%M")
                if now_ist >= end_ist:
                    logger.error(f"get_available_slots: 24h failed")
                    continue
            except ValueError:
                pass

        logger.error(f"get_available_slots: matched slot={slot}")
        matched_slots.append({
            "configId": str(config["_id"]),
            "slotId": slot.get("id", f"{slot.get('startTime')}-{slot.get('endTime')}"),
            "startTime": slot.get("startTime", ""),
            "endTime": slot.get("endTime", ""),
            "isUrgent": is_urgent,
            "isFullDay": is_full_day,
        })

    logger.error(f"get_available_slots: returning {matched_slots}")
    return matched_slots


@router.get("/dates-with-slots", response_model=DatesWithSlotsResponse)
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
    now_ist = (utc_now + ist_offset).replace(tzinfo=None)  # naive IST for comparison with strptime results

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
            if not (slot.get("isActive") if slot.get("isActive") is not None else True):
                continue

            is_full_day = (slot.get("isFullDay") if slot.get("isFullDay") is not None else False)
            is_urgent = (slot.get("isUrgent") if slot.get("isUrgent") is not None else False)

            # Cutoff check
            if not is_full_day:
                cutoff_hours = slot.get("urgentCutoffHours") if is_urgent and slot.get("urgentCutoffHours") is not None else slot.get("cutoffHours")
                if cutoff_hours is not None:
                    anchor_time_str = (slot.get("endTime") or "") if is_urgent else (slot.get("startTime") or "")
                    try:
                        anchor_ist = _dt.datetime.strptime(f"{check_date} {anchor_time_str}", "%Y-%m-%d %H:%M")
                        if now_ist >= (anchor_ist - _dt.timedelta(hours=cutoff_hours)):
                            continue
                    except ValueError:
                        pass

            # 24-hour rule
            end_time_str = (slot.get("endTime") or "")
            try:
                slot_end_ist = _dt.datetime.strptime(f"{check_date} {end_time_str}", "%Y-%m-%d %H:%M")
                if slot_end_ist > (now_ist + _dt.timedelta(hours=24)):
                    continue
            except ValueError:
                pass

            # Capacity check with zone fallback
            if not is_full_day:
                cap = int(slot.get("capacity")) if slot.get("capacity") not in (None, "") else None
                if cap is None:
                    cap = config.get("zoneDefaultCapacity")
                booked = (int(slot.get("bookedCount")) if slot.get("bookedCount") not in (None, "") else 0)
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


@router.post("/{config_id}/book-slot", response_model=BookSlotResponse)
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
        if slot.get("id") == slot_id or f"{slot.get('startTime')}-{slot.get('endTime')}" == slot_id:
            cap = int(slot.get("capacity")) if slot.get("capacity") not in (None, "") else None
            if cap is None:
                cap = config.get("zoneDefaultCapacity")
            booked = (int(slot.get("bookedCount")) if slot.get("bookedCount") not in (None, "") else 0)
            if cap is not None and booked >= cap:
                raise HTTPException(status_code=409, detail="Slot is fully booked")
            slot["bookedCount"] = booked + 1
            updated = True
            break

    if not updated:
        raise HTTPException(status_code=404, detail="Slot not found in configuration")

    await storage.update(config_id, {"slots": slots})
    return {"success": True}


@router.post("", response_model=List[DeliverySlotConfigResponse], status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=List[DeliverySlotConfigResponse], status_code=status.HTTP_201_CREATED)
async def create_delivery_slot_config(
    config: DeliverySlotConfigCreate, current_user: User = Depends(require_super_admin)
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
            slot_dict = slot if hasattr(slot, "model_dump") else slot if hasattr(slot, "dict") else slot
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


@router.put("/{config_id}", response_model=DeliverySlotConfigResponse)
async def update_delivery_slot_config(
    config_id: str, config: DeliverySlotConfigBase, current_user: User = Depends(require_super_admin)
):
    updated = await storage.update(config_id, config)
    if not updated:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return updated


@router.delete("/{config_id}", response_model=MessageResponse)
async def delete_delivery_slot_config(config_id: str, current_user: User = Depends(require_super_admin)):
    result = await storage.delete(config_id)
    if not result:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return {"message": "Deleted successfully"}
