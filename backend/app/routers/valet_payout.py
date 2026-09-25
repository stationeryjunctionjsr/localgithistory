import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from app.models.user import User
from app.models.schemas import MessageResponse, ValetPayoutSettingsResponse, ValetEarningsResponse, ValetPayoutDetailResponse, ValetPayoutCreate, MarkPaidRequest
from app.models.daos import ValetPayoutInternalCreate, ValetPayoutInternalUpdate
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
        return self.deliveryChargePerOrder

    @property
    def return_pickup_charge_per_order(self) -> float:
        return self.returnPickupChargePerOrder

    @property
    def updated_at(self) -> Optional[datetime]:
        return self.updatedAt


async def _get_settings() -> ValetPayoutSettingsModel:
    storage = _storage()
    docs = await storage.findAll()
    if docs:
        doc = docs[0]
        return doc if isinstance(doc, ValetPayoutSettingsModel) else ValetPayoutSettingsModel.model_validate(doc, from_attributes=True)
    default = {
        "deliveryChargePerOrder": 0.0,
        "returnPickupChargePerOrder": 0.0,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
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
        "deliveryChargePerOrder": (settings.delivery_charge_per_order if settings.delivery_charge_per_order is not None else 0.0),
        "returnPickupChargePerOrder": (settings.return_pickup_charge_per_order if settings.return_pickup_charge_per_order is not None else 0.0),
        "updatedAt": settings.updated_at,
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
            "deliveryChargePerOrder": payload.deliveryChargePerOrder,
            "returnPickupChargePerOrder": payload.returnPickupChargePerOrder,
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        },
    )
    if not updated:
        return {
            "deliveryChargePerOrder": payload.deliveryChargePerOrder,
            "returnPickupChargePerOrder": payload.returnPickupChargePerOrder,
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        }
    updated_model = updated if isinstance(updated, ValetPayoutSettingsModel) else ValetPayoutSettingsModel.model_validate(updated, from_attributes=True)
    return {
        "deliveryChargePerOrder": (updated_model.deliveryChargePerOrder if updated_model.deliveryChargePerOrder is not None else 0.0),
        "returnPickupChargePerOrder": (updated_model.returnPickupChargePerOrder if updated_model.returnPickupChargePerOrder is not None else 0.0),
        "updatedAt": updated_model.updatedAt,
    }


from app.models.schemas import ValetEarningsResponse
async def _compute_valet_earnings(valet_id: str, settings: dict, orders: list, returns: list) -> ValetEarningsResponse:
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

async def _enrich_with_valet(doc: ValetPayoutDetailResponse) -> ValetPayoutDetailResponse:
    valet = await user_repository.findById(doc.valetId)
    if valet:
        doc.valetName = valet.name
        doc.valetPhone = valet.phone
        doc.valetUpiId = valet.upi_id
        doc.valetQrCodeUrl = valet.qr_code_url
        doc.valetBankAccountNumber = valet.bank_account_number
        doc.valetBankIfscCode = valet.bank_ifsc_code
        doc.valetBankAccountHolder = valet.bank_account_holder
        doc.valetBankName = valet.bank_name
    return doc


@router.post("/payouts", response_model=ValetPayoutDetailResponse, status_code=201)
async def create_valet_payout(
    data: ValetPayoutCreate,
    current_user: User = Depends(require_super_admin)
):
    valet = await user_repository.findById(data.valetId)
    if not valet or valet.role != "valet":
        raise HTTPException(status_code=404, detail="Valet not found")
        
    created = await valet_payout_dao.create(ValetPayoutInternalCreate(
        valetId=data.valetId,
        amount=data.amount,
        deliveryCount=data.deliveryCount,
        returnCount=data.returnCount,
        periodStart=data.periodStart,
        periodEnd=data.periodEnd,
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
            paymentMethod=data.paymentMethod,
            paymentReference=data.paymentReference,
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
        
    if existing.valetId != str(current_user.id):
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
