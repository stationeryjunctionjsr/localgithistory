import csv
import io
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.models.schemas import (
    DefaultDeliveryChargeCreate,
    DefaultDeliveryChargeResponse,
    DeliveryChargeCreate,
    DeliveryChargeResponse,
    DeliveryChargeUpdate,
)
from app.repositories.delivery_charge_repository import delivery_charge_repository
from app.utils.auth import require_super_admin
from app.utils.cache import cache

router = APIRouter()


@router.get("", response_model=List[DeliveryChargeResponse])
@router.get("/", response_model=List[DeliveryChargeResponse])
async def get_delivery_charges(current_user: dict = Depends(require_super_admin)):
    charges = await delivery_charge_repository.findAll()
    return charges


@router.get("/default", response_model=DefaultDeliveryChargeResponse)
async def get_default_delivery_charge(current_user: dict = Depends(require_super_admin)):
    default_charge = await delivery_charge_repository.getDefaultCharge()
    if not default_charge:
        raise HTTPException(status_code=404, detail="Default delivery charge not found")
    return default_charge


@router.get("/location")
@cache.ttl_cache(ttl=3600.0)
async def get_delivery_charge_by_location(
    state: str = Query(...),
    city: str = Query(...),
    district: str = Query(...),
    pincode: Optional[str] = Query(None),
    userRole: Optional[str] = Query("customer"),
    orderAmount: Optional[float] = Query(0),
):
    result = await delivery_charge_repository.getChargeForLocation(
        state, city, district, pincode, userRole, orderAmount
    )

    # Calculate delivery GST and total charge
    charge = result.get("charge", 0.0) or 0.0
    gst_percentage = 18.0
    gst_amount = 0.0
    total_charge = charge

    default_charge = await delivery_charge_repository.getDefaultCharge()
    if default_charge and default_charge.get("deliveryChargeGst"):
        gst_percentage = default_charge.get("deliveryChargeGstPercentage", 18.0)
        if charge > 0:
            gst_amount = round(charge * (gst_percentage / 100), 2)
            total_charge = round(charge + gst_amount, 2)

    result["gstPercentage"] = gst_percentage
    result["gstAmount"] = gst_amount
    result["totalCharge"] = total_charge

    return result


@router.get("/serviceable-pincodes", response_model=List[str])
async def get_serviceable_pincodes(current_user: dict = Depends(require_super_admin)):
    """Return all pincodes where serviceableForCustomer OR serviceableForWholesaler is True.
    Used by the Delivery Slots admin page to populate the pincode picker."""
    charges = await delivery_charge_repository.findAll()
    pincodes = [
        c["pincode"]
        for c in charges
        if c.get("pincode") and (c.get("serviceableForCustomer") or c.get("serviceableForWholesaler"))
    ]
    return sorted(set(pincodes))


@router.get("/check-serviceability")
@cache.ttl_cache(ttl=3600.0)
async def check_serviceability(pincode: str = Query(...), userRole: Optional[str] = Query("customer")):
    """Check if a pincode is serviceable for a user role. Also returns slot booking availability."""
    if not pincode or len(pincode) != 6 or not pincode.isdigit():
        return {
            "isServiceable": False,
            "pincode": pincode,
            "userRole": userRole,
            "sellerCount": 0,
            "slotBookingAvailable": False,
            "availableDates": [],
            "urgentDeliveryAvailable": False,
        }

    from app.db.storage_factory import get_storage

    is_serviceable = await delivery_charge_repository.isPincodeServiceable(pincode, userRole)

    platform_urgent = False
    zones_storage = get_storage("deliveryZones")
    zones = await zones_storage.findAll({"isActive": True})
    for z in zones:
        if pincode in z.get("pincodes", []):
            platform_urgent = bool(z.get("urgentDeliveryAvailable", False))
            break

    # Check if delivery slots are available for this pincode + segment
    slot_storage = get_storage("deliverySlots")
    segment = "wholesale" if userRole == "wholesaler" else "retail"
    import asyncio
    from datetime import date as dt_date, timedelta

    today = dt_date.today()
    dates_to_check = [(today + timedelta(days=i)).isoformat() for i in range(7)]

    # Execute all 7 date checks concurrently to avoid sequential latency
    tasks = [
        slot_storage.findAll({"date": check_date, "segment": segment, "isActive": True})
        for check_date in dates_to_check
    ]
    results = await asyncio.gather(*tasks)

    available_dates = []
    for check_date, configs in zip(dates_to_check, results):
        for config in configs:
            config_pincodes = config.get("pincodes", [])
            if config_pincodes and pincode not in config_pincodes:
                continue
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

    return {
        "isServiceable": is_serviceable,
        "pincode": pincode,
        "userRole": userRole,
        "sellerCount": 0,
        "slotBookingAvailable": len(available_dates) > 0,
        "availableDates": available_dates,
        "urgentDeliveryAvailable": platform_urgent,
    }


@router.get("/{charge_id}", response_model=DeliveryChargeResponse)
async def get_delivery_charge(charge_id: str, current_user: dict = Depends(require_super_admin)):
    charge = await delivery_charge_repository.findById(charge_id)
    if not charge:
        raise HTTPException(status_code=404, detail="Delivery charge not found")
    return charge


@router.post("", response_model=DeliveryChargeResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=DeliveryChargeResponse, status_code=status.HTTP_201_CREATED)
async def create_delivery_charge(charge_data: DeliveryChargeCreate, current_user: dict = Depends(require_super_admin)):
    if not charge_data.pincode or not charge_data.state or not charge_data.district:
        raise HTTPException(status_code=400, detail="Pincode, state, and district are required")

    if len(charge_data.pincode) != 6 or not charge_data.pincode.isdigit():
        raise HTTPException(status_code=400, detail="Pincode must be 6 digits")

    # Check for duplicate pincode
    existing = await delivery_charge_repository.findByPincode(charge_data.pincode)
    if existing:
        raise HTTPException(
            status_code=409, detail=f"Pincode {charge_data.pincode} already has a delivery charge configured"
        )

    charge = await delivery_charge_repository.create(charge_data.dict())
    return charge


@router.post("/default", response_model=DefaultDeliveryChargeResponse, status_code=status.HTTP_201_CREATED)
async def set_default_delivery_charge(
    default_data: DefaultDeliveryChargeCreate, current_user: dict = Depends(require_super_admin)
):
    default_charge = await delivery_charge_repository.setDefaultCharge(default_data.dict())
    return default_charge


@router.post("/upload-csv", status_code=status.HTTP_200_OK)
async def upload_delivery_charges_csv(file: UploadFile = File(...), current_user: dict = Depends(require_super_admin)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV file")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:  # 5 MB cap
        raise HTTPException(status_code=413, detail="CSV file exceeds the 5 MB size limit")
    csv_content = contents.decode("utf-8")
    csv_reader = csv.DictReader(io.StringIO(csv_content))

    success_count = 0
    errors = []

    for row in csv_reader:
        try:
            serviceable_for_customer = row.get("serviceableForCustomer", "true").lower() == "true"
            urgent_delivery_available = row.get("urgentDeliveryAvailable", "false").lower() == "true"

            # Based on the retail serviceable yes or no, the urgent delivery values will be set.
            if not serviceable_for_customer:
                urgent_delivery_available = False

            charge_data = {
                "pincode": row.get("pincode", "").strip() or None,
                "state": row.get("state", "").strip(),
                "city": row.get("city", "").strip(),
                "district": row.get("district", "").strip(),
                "charge": float(row.get("charge", 0)),
                "minCartValue": float(row.get("minCartValue", 0)),
                "isActive": row.get("isActive", "true").lower() == "true",
                "serviceableForCustomer": serviceable_for_customer,
                "urgentDeliveryAvailable": urgent_delivery_available,
                "urgentDeliveryCharge": float(row.get("urgentDeliveryCharge"))
                if row.get("urgentDeliveryCharge", "").strip()
                else None,
            }

            if not charge_data["state"] or not charge_data["city"] or not charge_data["district"]:
                errors.append({"row": row, "error": "Missing required fields: state, city, or district"})
                continue

            await delivery_charge_repository.create(charge_data)
            success_count += 1
        except Exception as e:
            errors.append({"row": row, "error": str(e)})

    return {
        "message": "CSV upload completed",
        "success": success_count,
        "errors": len(errors),
        "errorDetails": errors[:10],  # Return first 10 errors
    }


@router.put("/{charge_id}", response_model=DeliveryChargeResponse)
async def update_delivery_charge(
    charge_id: str, charge_data: DeliveryChargeUpdate, current_user: dict = Depends(require_super_admin)
):
    charge = await delivery_charge_repository.update(charge_id, charge_data.dict(exclude_unset=True))
    if not charge:
        raise HTTPException(status_code=404, detail="Delivery charge not found")
    return charge


@router.delete("/default")
async def delete_default_charge(current_user: dict = Depends(require_super_admin)):
    """Delete default delivery charge"""
    result = await delivery_charge_repository.deleteDefaultCharge()
    if not result:
        raise HTTPException(status_code=404, detail="Default delivery charge not found")
    return {"message": "Default delivery charge deleted successfully"}


@router.delete("/{charge_id}")
async def delete_delivery_charge(charge_id: str, current_user: dict = Depends(require_super_admin)):
    result = await delivery_charge_repository.delete(charge_id)
    if not result:
        raise HTTPException(status_code=404, detail="Delivery charge not found")
    return {"message": "Delivery charge deleted successfully"}
