import asyncio
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from app.models.user import User
from app.models.schemas import MessageResponse, ValetPayoutSettingsResponse, ValetEarningsResponse, ValetPayoutDetailResponse, ValetPayoutCreate, MarkPaidRequest
from app.models.daos import ValetPayoutInternalCreate, ValetPayoutInternalUpdate
from app.models.valet_payout_settings import ValetPayoutSettings
from app.db.storage_factory import get_storage
from app.db.mysql_valet_payout_dao import MySQLValetPayoutDAO
from app.utils.auth import get_current_user, require_super_admin
from app.repositories.order_repository import order_repository
from app.repositories.return_request_repository import return_request_repository
from app.repositories.user_repository import user_repository

router = APIRouter()
COLLECTION = "valetPayoutSettings"

def _storage():
    return get_storage(COLLECTION)

valet_payout_dao = MySQLValetPayoutDAO()

class ValetPayoutSettingsModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: Optional[str] = Field(None, alias="_id")
    deliveryChargePerOrder: float = Field(0.0, alias="delivery_charge_per_order")
    returnPickupChargePerOrder: float = Field(0.0, alias="return_pickup_charge_per_order")
    createdAt: Optional[datetime] = Field(None, alias="created_at")
    updatedAt: Optional[datetime] = Field(None, alias="updated_at")

    @property
    def delivery_charge_per_order(self) -> float:
        return self.delivery_charge_per_order

    @property
    def return_pickup_charge_per_order(self) -> float:
        return self.return_pickup_charge_per_order

    @property
    def updated_at(self) -> Optional[datetime]:
        return self.updated_at


async def _get_settings() -> ValetPayoutSettingsModel:
    storage = _storage()
    rows = await storage.findAll()
    if rows:
        row = rows[0]
        return row if isinstance(row, ValetPayoutSettingsModel) else ValetPayoutSettingsModel.model_validate(row, from_attributes=True)
    default = {
        "delivery_charge_per_order": 0.0,
        "return_pickup_charge_per_order": 0.0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    created = await storage.create(default)
    return created if isinstance(created, ValetPayoutSettingsModel) else ValetPayoutSettingsModel.model_validate(created, from_attributes=True)


class ValetPayoutSettingsPayload(BaseModel):
    deliveryChargePerOrder: float = Field(..., ge=0, description="Fixed amount paid to valet per delivered order")
    returnPickupChargePerOrder: float = Field(..., ge=0, description="Fixed amount paid to valet per return pickup")


@router.get("/settings", response_model=ValetPayoutSettingsResponse)
async def get_valet_payout_settings(current_user: User = Depends(require_super_admin)):
    settings = await _get_settings()
    return {
        "delivery_charge_per_order": (settings.delivery_charge_per_order if settings.delivery_charge_per_order is not None else 0.0),
        "return_pickup_charge_per_order": (settings.return_pickup_charge_per_order if settings.return_pickup_charge_per_order is not None else 0.0),
        "updated_at": settings.updated_at,
    }

@router.put("/settings", response_model=ValetPayoutSettingsResponse)
async def update_valet_payout_settings(
    payload: ValetPayoutSettingsPayload,
    current_user: User = Depends(require_super_admin),
):
    storage = _storage()
    settings = await _get_settings()
    updated = await storage.update(
        settings.id,
        {
            "delivery_charge_per_order": payload.delivery_charge_per_order,
            "return_pickup_charge_per_order": payload.return_pickup_charge_per_order,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    if not updated:
        return {
            "delivery_charge_per_order": payload.delivery_charge_per_order,
            "return_pickup_charge_per_order": payload.return_pickup_charge_per_order,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    updated_model = updated if isinstance(updated, ValetPayoutSettingsModel) else ValetPayoutSettingsModel.model_validate(updated, from_attributes=True)
    return {
        "delivery_charge_per_order": (updated_model.delivery_charge_per_order if updated_model.delivery_charge_per_order is not None else 0.0),
        "return_pickup_charge_per_order": (updated_model.return_pickup_charge_per_order if updated_model.return_pickup_charge_per_order is not None else 0.0),
        "updated_at": updated_model.updated_at,
    }


from app.models.schemas import ValetEarningsResponse
async def _compute_valet_earnings(valet_id: str, settings: ValetPayoutSettings, orders: list, returns: list) -> ValetEarningsResponse:
    delivery_rate = float((settings.delivery_charge_per_order if settings.delivery_charge_per_order is not None else 0.0))
    return_rate = float((settings.return_pickup_charge_per_order if settings.return_pickup_charge_per_order is not None else 0.0))

    delivery_records = [
        {
            "type": "delivery",
            "orderId": str(o.id),
            "orderNumber": o.order_number,
            "deliveredAt": o.delivered_at,
            "amount": delivery_rate,
            "status": o.status,
        }
        for o in orders if o.status == "delivered"
    ]

    return_records = [
        {
            "type": "return_pickup",
            "returnId": str(r.id),
            "orderId": r.order_id,
            "collectedAt": r.collected_at,
            "amount": return_rate,
            "status": r.status,
        }
        for r in returns if r.valet_status in ("collected", "returned") or r.status in ("collected", "returned")
    ]

    total_deliveries = len(delivery_records)
    total_returns = len(return_records)
    total_earned = round(total_deliveries * delivery_rate + total_returns * return_rate, 2)

    from app.models.schemas import ValetEarningsResponse
    return ValetEarningsResponse(
        valetId=valet_id,
        totalDeliveries=total_deliveries,
        totalReturnPickups=total_returns,
        deliveryRatePerOrder=delivery_rate,
        returnRatePerOrder=return_rate,
        totalEarned=total_earned,
        records=delivery_records + return_records,
    )


@router.get("/earnings/me", response_model=ValetEarningsResponse)
async def get_my_valet_earnings(
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "valet":
        raise HTTPException(status_code=403, detail="Only valets can access this endpoint")

    valet_id = str(current_user.id)
    settings = await _get_settings()
    orders = await order_repository.findAll({"assignedValet": valet_id})
    returns = await return_request_repository.findAll({"valetId": valet_id})

    return await _compute_valet_earnings(valet_id, settings, orders, returns)


@router.get("/earnings/{valet_id}", response_model=ValetEarningsResponse)
async def get_valet_earnings_by_id(
    valet_id: str,
    current_user: User = Depends(require_super_admin),
):
    valet = await user_repository.findById(valet_id)
    if not valet or valet.role != "valet":
        raise HTTPException(status_code=404, detail="Valet not found")

    settings = await _get_settings()
    orders = await order_repository.findAll({"assignedValet": valet_id})
    returns = await return_request_repository.findAll({"valetId": valet_id})

    result = await _compute_valet_earnings(valet_id, settings, orders, returns)
    return result

async def _enrich_with_valet(record: ValetPayoutDetailResponse) -> ValetPayoutDetailResponse:
    valet = await user_repository.findById(record.valet_id)
    if valet:
        record.valet_name = valet.name
        record.valet_phone = valet.phone
        record.valet_upi_id = valet.upi_id
        record.valet_qr_code_url = valet.qr_code_url
        record.valet_bank_account_number = valet.bank_account_number
        record.valet_bank_ifsc_code = valet.bank_ifsc_code
        record.valet_bank_account_holder = valet.bank_account_holder
        record.valet_bank_name = valet.bank_name
    return record


@router.post("/payouts", response_model=ValetPayoutDetailResponse, status_code=201)
async def create_valet_payout(
    data: ValetPayoutCreate,
    current_user: User = Depends(require_super_admin)
):
    valet = await user_repository.findById(data.valet_id)
    if not valet or valet.role != "valet":
        raise HTTPException(status_code=404, detail="Valet not found")
        
    created = await valet_payout_dao.create(ValetPayoutInternalCreate(
        valetId=data.valet_id,
        amount=data.amount,
        deliveryCount=data.delivery_count,
        returnCount=data.return_count,
        periodStart=data.period_start,
        periodEnd=data.period_end,
        status='pending_payment',
        notes=data.notes
    ))
    
    await _enrich_with_valet(created)
    return created

@router.get("/payouts", response_model=List[ValetPayoutDetailResponse])
async def list_valet_payouts(
    valet_id: Optional[str] = Query(None),
    current_user: User = Depends(require_super_admin)
):
    query = {}
    if valet_id:
        query["valetId"] = valet_id
    records = await valet_payout_dao.findAll(query)
    for r in records:
        await _enrich_with_valet(r)
    return records

@router.get("/payouts/my", response_model=List[ValetPayoutDetailResponse])
async def list_my_valet_payouts(
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "valet":
        raise HTTPException(status_code=403, detail="Only valets can access this endpoint")
        
    records = await valet_payout_dao.findAll({"valetId": str(current_user.id)})
    for r in records:
        await _enrich_with_valet(r)
    return records

@router.post("/payouts/{payout_id}/mark-paid", response_model=ValetPayoutDetailResponse)
async def mark_valet_payout_paid(
    payout_id: str,
    data: MarkPaidRequest,
    current_user: User = Depends(require_super_admin)
):
    existing = await valet_payout_dao.findById(payout_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Payout not found")
        
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    updated = await valet_payout_dao.update(
        payout_id,
        ValetPayoutInternalUpdate(
            status="admin_paid",
            adminPaidAt=now,
            adminPaidBy=str(current_user.id),
            paymentMethod=data.payment_method,
            paymentReference=data.payment_reference,
            notes=data.notes if data.notes else existing.notes
        )
    )
    await _enrich_with_valet(updated)
    return updated

@router.post("/payouts/{payout_id}/mark-received", response_model=ValetPayoutDetailResponse)
async def mark_valet_payout_received(
    payout_id: str,
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "valet":
        raise HTTPException(status_code=403, detail="Only valets can access this endpoint")
        
    existing = await valet_payout_dao.findById(payout_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Payout not found")
        
    if existing.valet_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to update this payout")
        
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    updated = await valet_payout_dao.update(
        payout_id,
        ValetPayoutInternalUpdate(
            status="valet_received",
            valetReceivedAt=now
        )
    )
    await _enrich_with_valet(updated)
    return updated
