"""
Valet payout settings router.

Endpoints:
  GET  /api/valet-payout/settings  – Fetch global per-delivery and per-return charges
  PUT  /api/valet-payout/settings  – Update charges (super admin only)
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.db.storage_factory import get_storage
from app.utils.auth import require_super_admin

router = APIRouter()

COLLECTION = "valetPayoutSettings"


def _storage():
    return get_storage(COLLECTION)


async def _get_settings() -> dict:
    storage = _storage()
    docs = await storage.findAll()
    if docs:
        return docs[0]
    default = {
        "deliveryChargePerOrder": 0.0,
        "returnPickupChargePerOrder": 0.0,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }
    return await storage.create(default)


class ValetPayoutSettingsPayload(BaseModel):
    deliveryChargePerOrder: float = Field(..., ge=0, description="Fixed amount paid to valet per delivered order")
    returnPickupChargePerOrder: float = Field(..., ge=0, description="Fixed amount paid to valet per return pickup")


@router.get("/settings")
async def get_valet_payout_settings(current_user: dict = Depends(require_super_admin)):
    """Fetch global valet payout charge settings."""
    settings = await _get_settings()
    return {
        "deliveryChargePerOrder": settings.get("deliveryChargePerOrder", 0.0),
        "returnPickupChargePerOrder": settings.get("returnPickupChargePerOrder", 0.0),
        "updatedAt": settings.get("updatedAt"),
    }


@router.put("/settings")
async def update_valet_payout_settings(
    payload: ValetPayoutSettingsPayload,
    current_user: dict = Depends(require_super_admin),
):
    """Update global valet payout charge settings."""
    storage = _storage()
    settings = await _get_settings()
    updated = await storage.update(
        settings["_id"],
        {
            "deliveryChargePerOrder": payload.deliveryChargePerOrder,
            "returnPickupChargePerOrder": payload.returnPickupChargePerOrder,
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        },
    )
    return {
        "deliveryChargePerOrder": updated.get("deliveryChargePerOrder", 0.0),
        "returnPickupChargePerOrder": updated.get("returnPickupChargePerOrder", 0.0),
        "updatedAt": updated.get("updatedAt"),
    }


# ── Valet Earnings History ────────────────────────────────────────────────────

from app.utils.auth import get_current_user


async def _compute_valet_earnings(valet_id: str, settings: dict, orders: list, returns: list) -> dict:
    """Compute earnings summary for a valet from their completed orders and return pickups."""
    delivery_rate = float(settings.get("deliveryChargePerOrder", 0.0))
    return_rate = float(settings.get("returnPickupChargePerOrder", 0.0))

    delivery_records = [
        {
            "type": "delivery",
            "orderId": str(o.get("_id")),
            "orderNumber": o.get("orderNumber"),
            "deliveredAt": o.get("deliveredAt"),
            "amount": delivery_rate,
            "status": o.get("status"),
        }
        for o in orders
        if o.get("status") == "delivered"
    ]

    return_records = [
        {
            "type": "return_pickup",
            "returnId": str(r.get("_id")),
            "orderId": r.get("orderId"),
            "collectedAt": r.get("collectedAt"),
            "amount": return_rate,
            "status": r.get("status"),
        }
        for r in returns
        if r.get("valetStatus") in ("collected", "returned") or r.get("status") in ("collected", "returned")
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


@router.get("/earnings/me")
async def get_my_valet_earnings(
    current_user: dict = Depends(get_current_user),
):
    """Get earnings summary for the currently authenticated valet."""
    if current_user.get("role") != "valet":
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Only valets can access this endpoint")

    from app.repositories.order_repository import order_repository
    from app.repositories.return_request_repository import return_request_repository

    valet_id = str(current_user["_id"])
    settings = await _get_settings()
    orders = await order_repository.findAll({"assignedValet": valet_id})
    returns = await return_request_repository.findAll({"valetId": valet_id})

    return await _compute_valet_earnings(valet_id, settings, orders, returns)


@router.get("/earnings/{valet_id}")
async def get_valet_earnings_by_id(
    valet_id: str,
    current_user: dict = Depends(require_super_admin),
):
    """Get earnings summary for a specific valet (super admin only)."""
    from fastapi import HTTPException

    from app.repositories.order_repository import order_repository
    from app.repositories.return_request_repository import return_request_repository
    from app.repositories.user_repository import user_repository

    valet = await user_repository.findById(valet_id)
    if not valet or valet.get("role") != "valet":
        raise HTTPException(status_code=404, detail="Valet not found")

    settings = await _get_settings()
    orders = await order_repository.findAll({"assignedValet": valet_id})
    returns = await return_request_repository.findAll({"valetId": valet_id})

    result = await _compute_valet_earnings(valet_id, settings, orders, returns)
    result["valetName"] = valet.get("name", "")
    result["valetPhone"] = valet.get("phone", "")
    return result
