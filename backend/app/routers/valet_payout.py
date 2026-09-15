from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict

from app.models.user import User
from app.models.schemas import MessageResponse, ValetPayoutSettingsResponse, ValetEarningsResponse
from app.db.storage_factory import get_storage
from app.utils.auth import get_current_user, require_super_admin
from app.repositories.order_repository import order_repository
from app.repositories.return_request_repository import return_request_repository
from app.repositories.user_repository import user_repository

"""
Valet payout settings router.

Endpoints:
  GET  /api/valet-payout/settings  – Fetch global per-delivery and per-return charges
  PUT  /api/valet-payout/settings  – Update charges (super admin only)
"""

router = APIRouter()

COLLECTION = "valetPayoutSettings"


def _storage():
    return get_storage(COLLECTION)


class ValetPayoutSettingsModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: Optional[Any] = Field(None, alias="_id")
    deliveryChargePerOrder: float = Field(0.0, alias="delivery_charge_per_order")
    returnPickupChargePerOrder: float = Field(0.0, alias="return_pickup_charge_per_order")
    createdAt: Optional[Any] = Field(None, alias="created_at")
    updatedAt: Optional[Any] = Field(None, alias="updated_at")

    @property
    def delivery_charge_per_order(self) -> float:
        return self.deliveryChargePerOrder

    @property
    def return_pickup_charge_per_order(self) -> float:
        return self.returnPickupChargePerOrder

    @property
    def updated_at(self) -> Optional[Any]:
        return self.updatedAt


async def _get_settings() -> ValetPayoutSettingsModel:
    storage = _storage()
    docs = await storage.findAll()
    if docs:
        doc = docs[0]
        return doc if isinstance(doc, ValetPayoutSettingsModel) else ValetPayoutSettingsModel.model_validate(doc)
    default = {
        "deliveryChargePerOrder": 0.0,
        "returnPickupChargePerOrder": 0.0,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }
    created = await storage.create(default)
    return created if isinstance(created, ValetPayoutSettingsModel) else ValetPayoutSettingsModel.model_validate(created)


class ValetPayoutSettingsPayload(BaseModel):
    deliveryChargePerOrder: float = Field(..., ge=0, description="Fixed amount paid to valet per delivered order")
    returnPickupChargePerOrder: float = Field(..., ge=0, description="Fixed amount paid to valet per return pickup")


@router.get("/settings", response_model=ValetPayoutSettingsResponse)
async def get_valet_payout_settings(current_user: User = Depends(require_super_admin)):
    """Fetch global valet payout charge settings."""
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
    """Update global valet payout charge settings."""
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
    updated_model = updated if isinstance(updated, ValetPayoutSettingsModel) else ValetPayoutSettingsModel.model_validate(updated)
    return {
        "deliveryChargePerOrder": (updated_model.deliveryChargePerOrder if updated_model.deliveryChargePerOrder is not None else 0.0),
        "returnPickupChargePerOrder": (updated_model.returnPickupChargePerOrder if updated_model.returnPickupChargePerOrder is not None else 0.0),
        "updatedAt": updated_model.updatedAt,
    }


# ── Valet Earnings History ────────────────────────────────────────────────────


async def _compute_valet_earnings(valet_id: str, settings: dict, orders: list, returns: list) -> dict:
    """Compute earnings summary for a valet from their completed orders and return pickups."""
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
        for o in orders
        if o.status == "delivered"
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
        for r in returns
        if r.valet_status in ("collected", "returned") or r.status in ("collected", "returned")
    ]

    total_deliveries = len(delivery_records)
    total_returns = len(return_records)
    total_earned = round(total_deliveries * delivery_rate + total_returns * return_rate, 2)

    return {
        "valetId": valet_id,
        "totalDeliveries": total_deliveries,
        "totalReturnPickups": total_returns,
        "deliveryRatePerOrder": delivery_rate,
        "returnRatePerOrder": return_rate,
        "totalEarned": total_earned,
        "records": delivery_records + return_records,
    }


@router.get("/earnings/me", response_model=ValetEarningsResponse)
async def get_my_valet_earnings(
    current_user: User = Depends(get_current_user),
):
    """Get earnings summary for the currently authenticated valet."""
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
    """Get earnings summary for a specific valet (super admin only)."""
    valet = await user_repository.findById(valet_id)
    if not valet or valet.role != "valet":
        raise HTTPException(status_code=404, detail="Valet not found")

    settings = await _get_settings()
    orders = await order_repository.findAll({"assignedValet": valet_id})
    returns = await return_request_repository.findAll({"valetId": valet_id})

    result = await _compute_valet_earnings(valet_id, settings, orders, returns)
    result["valetName"] = (valet.name or "")
    result["valetPhone"] = (valet.phone or "")
    return result
