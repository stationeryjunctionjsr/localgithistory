from app.models.daos_flat import DeliveryChargeInternalCreate, DeliveryChargeDefaultInternalCreate, DeliveryChargeInternalUpdate
from app.models.user import User
from app.models.schemas import MessageResponse
import csv
import io
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.models.schemas import (
    DefaultDeliveryChargeCreate,
    DefaultDeliveryChargeResponse,
    DeliveryChargeCreate,
    DeliveryChargeResponse,
    DeliveryChargeUpdate,
    DeliveryChargeTier,
)
from app.repositories.delivery_charge_repository import delivery_charge_repository
from app.utils.auth import require_super_admin
from app.utils.cache import cache
from pydantic import BaseModel, ConfigDict, Field
from app.models.base import CamelBaseModel

class LocationChargeResponse(CamelBaseModel):
    charge: float = 0.0
    min_cart_value: float = 0.0
    source: str = ""
    delivery_charge: Optional[float] = None
    is_applicable_to_role: bool = True
    applied_tier: Optional[DeliveryChargeTier] = None
    urgent_delivery_available: bool = False
    urgentdelivery_charge: Optional[float] = None
    gstPercentage: float = 0.0
    gstAmount: float = 0.0
    totalCharge: float = 0.0

class ServiceableSeller(CamelBaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: str
    name: str
    company_name: str
    city: Optional[str] = None

class ServiceabilityResponse(CamelBaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    is_serviceable: bool
    pincode: str
    user_role: Optional[str] = None
    seller_count: int = 0
    serviceable_sellers: List[ServiceableSeller] = Field(default_factory=list)
    show_seller_count: bool = True
    slot_booking_available: bool = False
    available_dates: List[str] = Field(default_factory=list)
    urgent_delivery_available: bool = False
    zone_customer_type: str = "retail"
    zone_id: Optional[str] = None
    zone_name: Optional[str] = None
    has_zone: bool = False
    has_pan_india: bool = False
    allowed_modes: List[str] = Field(default_factory=list)
    default_mode: str = "pan_india"

class UploadCsvResponse(BaseModel):
    message: str
    errors: List[str] = []


class CsvDeliveryChargeRow(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    pincode: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    charge: Optional[float] = 0.0
    min_cart_value: Optional[float] = Field(0.0, alias="min_cart_value")
    isActive: Optional[str] = Field("true", alias="is_active")
    serviceableForCustomer: Optional[str] = Field("true", alias="serviceable_for_customer")
    serviceableForWholesaler: Optional[str] = Field("false", alias="serviceable_for_wholesaler")
    urgent_delivery_available: Optional[str] = Field("false", alias="urgent_delivery_available")
    urgentdelivery_charge: Optional[str] = Field(None, alias="urgent_delivery_charge")


router = APIRouter()


@router.get("", response_model=List[DeliveryChargeResponse])
@router.get("/", response_model=List[DeliveryChargeResponse])
async def get_delivery_charges(current_user: User = Depends(require_super_admin)):
    charges = await delivery_charge_repository.findAll()
    return charges


@router.get("/default", response_model=DefaultDeliveryChargeResponse)
async def get_default_delivery_charge(current_user: User = Depends(require_super_admin)):
    default_charge = await delivery_charge_repository.getDefaultCharge()
    if not default_charge:
        raise HTTPException(status_code=404, detail="Default delivery charge not found")
    return default_charge


@router.get("/location", response_model=LocationChargeResponse)
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
    charge = result.charge or 0.0
    gst_percentage = 18.0
    gst_amount = 0.0
    total_charge = charge

    default_charge = await delivery_charge_repository.getDefaultCharge()
    if default_charge and default_charge.delivery_charge_gst:
        gst_percentage = (default_charge.delivery_charge_gst_percentage if default_charge.delivery_charge_gst_percentage is not None else 18.0)
        if charge > 0:
            gst_amount = round(charge * (gst_percentage / 100), 2)
            total_charge = round(charge + gst_amount, 2)

    # Mutate the typed Pydantic model directly
    result.gstPercentage = gst_percentage
    result.gstAmount = gst_amount
    result.totalCharge = total_charge
    # deliveryCharge was previously passed the whole object; we now return the flat float
    
    return result


@router.get("/serviceable-pincodes", response_model=List[str])
async def get_serviceable_pincodes(current_user: User = Depends(require_super_admin)):
    """Return all pincodes where serviceableForCustomer OR serviceableForWholesaler is True.
    Used by the Delivery Slots admin page to populate the pincode picker."""
    charges = await delivery_charge_repository.findAll()
    pincodes = [
        c.pincode
        for c in charges
        if c.pincode and (c.serviceable_for_customer or c.serviceable_for_wholesaler)
    ]
    return sorted(set(pincodes))


@router.get("/check-serviceability", response_model=ServiceabilityResponse)
@cache.ttl_cache(ttl=3600.0)
async def check_serviceability(pincode: str = Query(...), userRole: Optional[str] = Query("customer")):
    """Check if a pincode is serviceable for a user role. Also returns slot booking availability
    and the list of sellers that service this pincode (resolved via delivery zone)."""
    if not pincode or len(pincode) != 6 or not pincode.isdigit():
        return ServiceabilityResponse(
            is_serviceable=False,
            pincode=pincode or "",
            user_role=userRole,
            seller_count=0,
            serviceable_sellers=[],
            show_seller_count=True,
            slot_booking_available=False,
            available_dates=[],
            urgent_delivery_available=False,
            zone_customer_type="retail",
            zone_id=None,
            zone_name=None,
            has_zone=False,
            has_pan_india=False,
            allowed_modes=[],
            default_mode="pan_india",
        )

    from app.db.storage_factory import get_storage
    from app.repositories.zone_seller_cache import get_seller_ids_for_pincode, get_zone_for_pincode
    from app.repositories.user_repository import user_repository

    is_serviceable = await delivery_charge_repository.isPincodeServiceable(pincode, userRole)

    # ── Zone metadata (urgent delivery flag + customerType + seller IDs) ───────
    zone = await get_zone_for_pincode(pincode)
    platform_urgent = bool((zone.urgent_delivery_available if zone.urgent_delivery_available is not None else False)) if zone else False
    zone_customer_type = (zone.customer_type if zone.customer_type is not None else "retail") if zone else "retail"

    is_wholesaler = (userRole == "wholesaler")

    # ── Seller resolution ──────────────────────────────────────────────────────
    # For wholesale customers the only seller is always the Super Admin — the
    # marketplace model does not apply.  We skip the per-zone seller lookup and
    # return the super admin as the only serviceable seller.
    serviceable_sellers: List[ServiceableSeller] = []
    if is_wholesaler:
        from app.repositories.zone_seller_cache import get_super_admin_seller_id
        sa_id = await get_super_admin_seller_id()
        if sa_id:
            try:
                seller_doc = await user_repository.findById(sa_id)
                if seller_doc:
                    serviceable_sellers.append(
                        ServiceableSeller(
                            id=str(seller_doc.id or sa_id),
                            name=seller_doc.name or "",
                            company_name=seller_doc.company_name or seller_doc.name or "",
                            city=seller_doc.city or (seller_doc.address.city if seller_doc.address else None),
                        )
                    )
            except Exception as exc:
                from app.utils.logger import logger
                logger.warning("check_serviceability: could not fetch super admin %s: %s", sa_id, exc)
    else:
        seller_id_set = await get_seller_ids_for_pincode(pincode)  # None | set()| set(ids)
        if seller_id_set:  # non-None and non-empty
            for sid in seller_id_set:
                try:
                    seller_doc = await user_repository.findById(sid)
                    if not seller_doc:
                        continue
                    serviceable_sellers.append(
                        ServiceableSeller(
                            id=str(seller_doc.id or sid),
                            name=seller_doc.name or "",
                            company_name=seller_doc.company_name or seller_doc.name or "",
                            city=seller_doc.city or (seller_doc.address.city if seller_doc.address else None),
                        )
                    )
                except Exception as exc:
                    from app.utils.logger import logger
                    logger.warning("check_serviceability: could not fetch seller %s: %s", sid, exc)

    # ── Delivery slot availability ─────────────────────────────────────────────
    slot_storage = get_storage("deliverySlots")
    segment = "wholesale" if is_wholesaler else "retail"

    # For business customers: slots are only available when the zone is tagged
    # "business" or "both".  A "retail"-only zone has no wholesale slots.
    wholesale_zone_eligible = zone_customer_type in ("business", "both")

    from datetime import date as dt_date, timedelta

    today = dt_date.today()
    dates_to_check = [(today + timedelta(days=i)).isoformat() for i in range(7)]

    available_dates = []

    # Resolve zone_id for this pincode (already done above — reuse `zone`)
    zone_id = str((zone.id or "")) if zone else None

    if not is_wholesaler or wholesale_zone_eligible:
        for check_date in dates_to_check:
            # Zone-specific config first, then "default" fallback — same logic as
            # delivery-slots/available and order creation.
            slot_config = None
            if zone_id:
                zone_configs = await slot_storage.findAll(
                    {"date": check_date, "segment": segment, "zoneId": zone_id, "isActive": True}
                )
                if zone_configs:
                    slot_config = zone_configs[0]
            if not slot_config:
                default_configs = await slot_storage.findAll(
                    {"date": check_date, "segment": segment, "zoneId": "default", "isActive": True}
                )
                if default_configs:
                    slot_config = default_configs[0]

            if slot_config:
                slots = slot_config.slots if slot_config.slots else []
                for slot in slots:
                    if not slot.is_active:
                        continue
                    cap = slot.capacity if slot.capacity else None
                    booked = slot.booked_count if slot.booked_count else 0
                    if cap is None or (cap - booked) > 0:
                        available_dates.append(check_date)
                        break

    has_zone = zone is not None and bool(zone.is_active)
    # Pan-India 1P courier delivery is supported for valid Indian 6-digit pincodes
    has_pan_india = True

    allowed_modes = []
    if has_zone:
        allowed_modes.append("hyperlocal")
    if has_pan_india:
        allowed_modes.append("pan_india")

    default_mode = "hyperlocal" if has_zone else "pan_india"

    return ServiceabilityResponse(
        is_serviceable=is_serviceable,
        pincode=pincode,
        user_role=userRole,
        seller_count=len(serviceable_sellers),
        serviceable_sellers=serviceable_sellers,
        show_seller_count=not is_wholesaler,
        slot_booking_available=len(available_dates) > 0,
        available_dates=available_dates,
        urgent_delivery_available=platform_urgent,
        zone_customer_type=zone_customer_type,
        zone_id=zone_id,
        zone_name=zone.name if zone else None,
        has_zone=has_zone,
        has_pan_india=has_pan_india,
        allowed_modes=allowed_modes,
        default_mode=default_mode,
    )



@router.get("/{charge_id}", response_model=DeliveryChargeResponse)
async def get_delivery_charge(charge_id: str, current_user: User = Depends(require_super_admin)):
    charge = await delivery_charge_repository.findById(charge_id)
    if not charge:
        raise HTTPException(status_code=404, detail="Delivery charge not found")
    return charge


@router.post("", response_model=DeliveryChargeResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=DeliveryChargeResponse, status_code=status.HTTP_201_CREATED)
async def create_delivery_charge(charge_data: DeliveryChargeCreate, current_user: User = Depends(require_super_admin)):
    if not charge_data.pincode or not charge_data.state or not charge_data.district:
        raise HTTPException(status_code=400, detail="Pincode, state, and district are required")

    if len(charge_data.pincode) != 6 or not charge_data.pincode.isdigit():
        raise HTTPException(status_code=400, detail="Pincode must be 6 digits")
        
    if not charge_data.serviceable_for_customer:
        charge_data.urgent_delivery_available = False

    # Check for duplicate pincode
    existing = await delivery_charge_repository.findByPincode(charge_data.pincode)
    if existing:
        raise HTTPException(
            status_code=409, detail=f"Pincode {charge_data.pincode} already has a delivery charge configured"
        )

    internal_create = DeliveryChargeInternalCreate.model_validate(charge_data, from_attributes=True)
    charge = await delivery_charge_repository.create(internal_create)
    return charge


@router.post("/default", response_model=DefaultDeliveryChargeResponse, status_code=status.HTTP_201_CREATED)
async def set_default_delivery_charge(
    default_data: DefaultDeliveryChargeCreate, current_user: User = Depends(require_super_admin)
):
    internal_default = DeliveryChargeDefaultInternalCreate.model_validate(default_data, from_attributes=True)
    default_charge = await delivery_charge_repository.setDefaultCharge(internal_default)
    return default_charge


@router.post("/upload-csv", status_code=status.HTTP_200_OK, response_model=UploadCsvResponse)
async def upload_delivery_charges_csv(file: UploadFile = File(...), current_user: User = Depends(require_super_admin)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV file")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:  # 5 MB cap
        raise HTTPException(status_code=413, detail="CSV file exceeds the 5 MB size limit")
    csv_content = contents.decode("utf-8")
    csv_reader = csv.DictReader(io.StringIO(csv_content))

    success_count = 0
    errors = []

    for raw_row in csv_reader:
        try:
            row = CsvDeliveryChargeRow.model_validate(raw_row)
            serviceable_for_customer = (row.serviceable_for_customer if row.serviceable_for_customer is not None else "true").lower() == "true"
            serviceable_for_wholesaler = (row.serviceable_for_wholesaler if row.serviceable_for_wholesaler is not None else "false").lower() == "true"
            urgent_delivery_available = (row.urgent_delivery_available if row.urgent_delivery_available is not None else "false").lower() == "true"

            # Based on the retail serviceable yes or no, the urgent delivery values will be set.
            if not serviceable_for_customer:
                urgent_delivery_available = False
                
            state_val = (row.state or "").strip()
            city_val = (row.city or "").strip()
            district_val = (row.district or "").strip()
            
            if not state_val or not city_val or not district_val:
                errors.append({"row": raw_row, "error": "Missing required fields: state, city, or district"})
                continue

            from app.models.daos_flat import DeliveryChargeInternalCreate
            internal_model = DeliveryChargeInternalCreate(
                pincode=(row.pincode or "").strip() or None,
                state=state_val,
                city=city_val,
                district=district_val,
                charge=float(row.charge if row.charge is not None else 0),
                min_cart_value=float(row.min_cart_value if row.min_cart_value is not None else 0),
                is_active=(row.is_active if row.is_active is not None else "true").lower() == "true",
                serviceable_for_customer=serviceable_for_customer,
                serviceable_for_wholesaler=serviceable_for_wholesaler,
                urgent_delivery_available=urgent_delivery_available,
                urgent_delivery_charge=float(row.urgentDeliveryCharge) if (row.urgentDeliveryCharge or "").strip() else None
            )

            await delivery_charge_repository.create(internal_model)
            success_count += 1
        except Exception as e:
            errors.append({"row": raw_row, "error": str(e)})

    return {
        "message": "CSV upload completed",
        "success": success_count,
        "errors": len(errors),
        "errorDetails": errors[:10],  # Return first 10 errors
    }


@router.put("/{charge_id}", response_model=DeliveryChargeResponse)
async def update_delivery_charge(
    charge_id: str, charge_data: DeliveryChargeUpdate, current_user: User = Depends(require_super_admin)
):
    # charge_data is a Pydantic model. The previous code assigned it to update_dict
    # and then checked isinstance(update_dict, dict) which was always False, so
    # urgentDeliveryAvailable was never cleared when serviceableForCustomer was False.
    # Fix: check the attribute directly on the Pydantic model.
    if charge_data.serviceable_for_customer is False:
        charge_data.urgent_delivery_available = False

    internal_update = DeliveryChargeInternalUpdate.model_validate(charge_data, from_attributes=True)
    charge = await delivery_charge_repository.update(charge_id, internal_update)
    if not charge:
        raise HTTPException(status_code=404, detail="Delivery charge not found")
    return charge


@router.delete("/default", response_model=MessageResponse)
async def delete_default_charge(current_user: User = Depends(require_super_admin)):
    """Delete default delivery charge"""
    result = await delivery_charge_repository.deleteDefaultCharge()
    if not result:
        raise HTTPException(status_code=404, detail="Default delivery charge not found")
    return {"message": "Default delivery charge deleted successfully"}


@router.delete("/{charge_id}", response_model=MessageResponse)
async def delete_delivery_charge(charge_id: str, current_user: User = Depends(require_super_admin)):
    result = await delivery_charge_repository.delete(charge_id)
    if not result:
        raise HTTPException(status_code=404, detail="Delivery charge not found")
    return {"message": "Delivery charge deleted successfully"}

