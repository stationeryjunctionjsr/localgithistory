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
    Public endpoint. Returns available time slots.
    """
    import datetime as _dt
    from datetime import timezone

    utc_now = _dt.datetime.now(timezone.utc)
    ist_offset = _dt.timedelta(hours=5, minutes=30)
    now_ist = utc_now + ist_offset

    all_configs = await storage.findAll({"date": date, "segment": segment, "isActive": True})

    matched_slots = []
    for config in all_configs:
        config_pincodes = config.get("pincodes", [])
        if config_pincodes and pincode not in config_pincodes:
            continue

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

            # Capacity check
            if not is_full_day:
                cap = slot.get("capacity")
                booked = slot.get("bookedCount", 0)
                if cap is not None and (cap - booked) <= 0:
                    continue

            # 24 Hour Rule
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
                "isFullDay": is_full_day
            })

    return matched_slots


@router.get("/dates-with-slots")
async def get_dates_with_slots(
    pincode: str = Query(...),
    segment: str = Query("retail"),
):
    """
    Public endpoint. Returns available dates and urgent availability.
    """
    import datetime as _dt
    from datetime import timezone
    from app.db.storage_factory import get_storage as _get_storage

    slot_storage = _get_storage("deliverySlots")
    available_dates = []
    urgent_available = False
    
    # Current time in IST (UTC+5:30)
    utc_now = _dt.datetime.now(timezone.utc)
    ist_offset = _dt.timedelta(hours=5, minutes=30)
    now_ist = utc_now + ist_offset
    
    today = now_ist.date()
    for i in range(7):
        check_date = (today + _dt.timedelta(days=i)).isoformat()
        configs = await slot_storage.findAll({"date": check_date, "segment": segment, "isActive": True})
        
        has_valid_slot = False
        for config in configs:
            config_pincodes = config.get("pincodes", [])
            if config_pincodes and pincode not in config_pincodes:
                continue
                
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
                
                # 24 Hour Rule
                end_time_str = slot.get("endTime", "")
                try:
                    slot_end_ist = _dt.datetime.strptime(f"{check_date} {end_time_str}", "%Y-%m-%d %H:%M")
                    if slot_end_ist > (now_ist + _dt.timedelta(hours=24)):
                        continue
                except ValueError:
                    pass

                # Capacity check
                if not is_full_day:
                    cap = slot.get("capacity")
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
        "urgentAvailable": urgent_available
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
