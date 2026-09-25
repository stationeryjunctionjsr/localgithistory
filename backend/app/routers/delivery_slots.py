from app.models.daos_flat import DeliverySlotConfigInternalUpdate
from app.models.user import User
from app.models.schemas import MessageResponse
from app.models.daos_flat import DeliverySlotConfigInternalCreate, DeliverySlotInternal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from fastapi import APIRouter, Depends, HTTPException, Query, status



from app.db.storage_factory import get_storage
from app.utils.auth import require_super_admin

router = APIRouter()
storage = get_storage("deliverySlots")

# Sentinel zone ID for the "Default" fallback config
DEFAULT_ZONE_ID = "default"


class SlotBase(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: Optional[str] = None
    startTime: str = ""
    endTime: str = ""
    capacity: Optional[int] = None  # max bookings allowed; None = unlimited
    bookedCount: Optional[int] = 0  # current bookings for this slot
    isFullDay: Optional[bool] = False
    isActive: Optional[bool] = True
    isUrgent: Optional[bool] = False  # marks this as an urgent delivery slot
    cutoffHours: Optional[int] = None  # slot closes N hours before startTime; None = no cutoff
    urgentCutoffHours: Optional[int] = (
        None  # cutoff specifically for urgent slots; overrides cutoffHours when isUrgent=True
    )


class DeliverySlotConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: Optional[str] = Field(None, alias="_id")
    segment: Optional[str] = None
    date: Optional[str] = None
    zoneId: Optional[str] = None
    zoneDefaultCapacity: Optional[int] = 10
    slots: List[SlotBase] = Field(default_factory=list)
    isActive: Optional[bool] = True


class DeliverySlotConfigResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: Optional[str] = Field(None, alias="_id")
    segment: str
    date: str
    zoneId: str
    slots: List[SlotBase]
    isActive: bool
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class AvailableSlotItem(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    configId: str
    slotId: str
    startTime: str
    endTime: str
    isUrgent: bool = False
    isFullDay: bool = False


class AvailableSlotsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    date: Optional[str] = None
    slots: List[SlotBase] = Field(default_factory=list)


class DatesWithSlotsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    availableDates: List[str] = Field(default_factory=list)
    urgentAvailable: bool = False


class BookSlotResponse(BaseModel):
    success: bool
    slot: Optional[SlotBase] = None


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


async def _resolve_zone_config(pincode: str, date: str, segment: str) -> Optional[DeliverySlotConfigModel]:
    from app.repositories.zone_seller_cache import get_zone_for_pincode
    import logging
    logger = logging.getLogger(__name__)
    
    zone_data = await get_zone_for_pincode(pincode)
    zone_id = zone_data.id or (zone_data["_id"] if isinstance(zone_data, dict) and "_id" in zone_data else zone_data["id"] if isinstance(zone_data, dict) and "id" in zone_data else None) if zone_data else None
    logger.debug(f"_resolve_zone_config: pincode={pincode} date={date} segment={segment} zone_id={zone_id}")

    if zone_id:
        configs = await storage.findAll({"date": date, "segment": segment, "zoneId": str(zone_id), "isActive": True})
        logger.debug(f"_resolve_zone_config: found {len(configs)} configs for zone_id={zone_id}")
        if configs:
            doc = configs[0]
            return doc if isinstance(doc, DeliverySlotConfigModel) else DeliverySlotConfigModel.model_validate(doc, from_attributes=True)

    default_configs = await storage.findAll({"date": date, "segment": segment, "zoneId": DEFAULT_ZONE_ID, "isActive": True})
    logger.debug(f"_resolve_zone_config: found {len(default_configs)} default configs")
    if default_configs:
        doc = default_configs[0]
        return doc if isinstance(doc, DeliverySlotConfigModel) else DeliverySlotConfigModel.model_validate(doc, from_attributes=True)

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


@router.get("/available", response_model=List[AvailableSlotItem])
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
    logger.debug(f"get_available_slots: config found={config is not None}")
    if not config:
        return []

    matched_slots = []
    slots = config.slots
    for slot in slots:
        logger.debug(f"get_available_slots: evaluating slot id={slot.id}")
        if not (slot.isActive if slot.isActive is not None else True):
            continue

        is_full_day = bool(slot.isFullDay)
        is_urgent = bool(slot.isUrgent)

        if not is_full_day:
            if is_urgent:
                cutoff_hours = (
                    slot.urgentCutoffHours
                    if slot.urgentCutoffHours is not None
                    else slot.cutoffHours
                )
            else:
                cutoff_hours = slot.cutoffHours

            if cutoff_hours is not None:
                anchor_time_str = (slot.endTime or "") if is_urgent else (slot.startTime or "")
                try:
                    anchor_ist = _dt.datetime.strptime(f"{date} {anchor_time_str}", "%Y-%m-%d %H:%M")
                    cutoff_ist = anchor_ist - _dt.timedelta(hours=cutoff_hours)
                    if now_ist >= cutoff_ist:
                        logger.debug(f"get_available_slots: slot skipped — cutoff passed")
                        continue
                except ValueError:
                    pass

        if not is_full_day:
            cap = int(slot.capacity) if slot.capacity is not None else config.zoneDefaultCapacity
            booked = int(slot.bookedCount or 0)
            if cap is not None and booked >= cap:
                logger.debug(f"get_available_slots: slot skipped — at capacity")
                continue

        end_time_str = slot.endTime or ""
        if end_time_str:
            try:
                end_ist = _dt.datetime.strptime(f"{date} {end_time_str}", "%Y-%m-%d %H:%M")
                if now_ist >= end_ist:
                    logger.debug(f"get_available_slots: slot skipped — end time passed")
                    continue
            except ValueError:
                pass

        logger.debug(f"get_available_slots: slot matched")
        slot_id = slot.id or f"{slot.startTime}-{slot.endTime}"
        config_id_val = config.id or ""
        matched_slots.append({
            "configId": str(config_id_val),
            "slotId": slot_id,
            "startTime": slot.startTime,
            "endTime": slot.endTime,
            "isUrgent": is_urgent,
            "isFullDay": is_full_day,
        })

    logger.debug(f"get_available_slots: returning {len(matched_slots)} slots")
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
        slots = config.slots
        for slot in slots:
            if not (slot.isActive if slot.isActive is not None else True):
                continue

            is_full_day = bool(slot.isFullDay)
            is_urgent = bool(slot.isUrgent)

            # Cutoff check
            if not is_full_day:
                cutoff_hours = slot.urgentCutoffHours if is_urgent and slot.urgentCutoffHours is not None else slot.cutoffHours
                if cutoff_hours is not None:
                    anchor_time_str = (slot.endTime or "") if is_urgent else (slot.startTime or "")
                    try:
                        anchor_ist = _dt.datetime.strptime(f"{check_date} {anchor_time_str}", "%Y-%m-%d %H:%M")
                        if now_ist >= (anchor_ist - _dt.timedelta(hours=cutoff_hours)):
                            continue
                    except ValueError:
                        pass

            # 24-hour rule
            end_time_str = slot.endTime or ""
            try:
                slot_end_ist = _dt.datetime.strptime(f"{check_date} {end_time_str}", "%Y-%m-%d %H:%M")
                if slot_end_ist > (now_ist + _dt.timedelta(hours=24)):
                    continue
            except ValueError:
                pass

            # Capacity check with zone fallback
            if not is_full_day:
                cap = int(slot.capacity) if slot.capacity is not None else config.zoneDefaultCapacity
                booked = int(slot.bookedCount or 0)
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
async def book_slot(
    config_id: str,
    slot_id: str = Query(...),
    current_user: User = Depends(require_super_admin),
):
    """
    Super-admin-only endpoint for manual slot booking adjustments.

    NOTE: Order creation does NOT call this endpoint — it uses a direct atomic
    SQL UPDATE (WHERE booked_count < capacity) inside orders.py for race-safety.
    This HTTP route is only for administrative corrections and is now protected
    to prevent unauthenticated actors from inflating bookedCount.
    """
    config = await storage.findById(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Slot configuration not found")

    cfg = config if isinstance(config, DeliverySlotConfigModel) else DeliverySlotConfigModel.model_validate(config, from_attributes=True)
    updated = False
    booked_slot: Optional[SlotBase] = None
    for slot in cfg.slots:
        current_slot_id = slot.id or f"{slot.startTime}-{slot.endTime}"
        if current_slot_id == slot_id:
            cap = int(slot.capacity) if slot.capacity is not None else cfg.zoneDefaultCapacity
            booked = int(slot.bookedCount or 0)
            if cap is not None and booked >= cap:
                raise HTTPException(status_code=409, detail="Slot is fully booked")
            slot.bookedCount = booked + 1
            updated = True
            booked_slot = slot
            break

    if not updated:
        raise HTTPException(status_code=404, detail="Slot not found in configuration")

    await storage.update(config_id, cfg)
    return {"success": True, "slot": booked_slot}


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

    for zone_id in config.zone_ids:
        # Resolve zone capacity
        zone_default_capacity = 10  # fallback
        if zone_id != DEFAULT_ZONE_ID:
            zone_doc = await zones_storage.findById(zone_id)
            if zone_doc:
                cap_val = (zone_doc.default_capacity if zone_doc.default_capacity is not None else 10)
                zone_default_capacity = int(cap_val) if cap_val is not None else 10

        # Auto-fill slot capacities from zone default if not set
        slots_with_capacity = []
        slots = config.slots
        for slot in slots:
            cap_val = slot.capacity
            if cap_val is None or cap_val == 0:
                slot.capacity = zone_default_capacity
            slots_with_capacity.append(slot)

        config_obj = DeliverySlotConfigInternalCreate(
            segment=config.segment,
            date=config.date,
            zoneId=zone_id,
            slots=[DeliverySlotInternal.model_validate(s, from_attributes=True) for s in slots_with_capacity],
            isActive=config.isActive
        )

        # Check for existing config for this date/segment/zone
        existing = await storage.findAll({"date": config.date, "segment": config.segment, "zoneId": zone_id})
        if existing:
            doc_id = str(existing[0].id)
            updated = await storage.update(doc_id, config_obj)
            created.append(updated)
        else:
            result = await storage.create(config_obj)
            created.append(result)

    return created


@router.put("/{config_id}", response_model=DeliverySlotConfigResponse)
async def update_delivery_slot_config(
    config_id: str, config: DeliverySlotConfigBase, current_user: User = Depends(require_super_admin)
):
    internal_update = DeliverySlotConfigInternalUpdate.model_validate(config, from_attributes=True)
    updated = await storage.update(config_id, internal_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return updated


@router.delete("/{config_id}", response_model=MessageResponse)
async def delete_delivery_slot_config(config_id: str, current_user: User = Depends(require_super_admin)):
    result = await storage.delete(config_id)
    if not result:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return {"message": "Deleted successfully"}
