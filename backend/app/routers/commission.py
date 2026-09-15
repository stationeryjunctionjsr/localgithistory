from app.models.schemas import UserUpdate
from app.models.user import User
from typing import Dict, Any, List
from app.models.schemas import MessageResponse
"""
Commission management router.

Endpoints:
  GET  /api/commission/tiers                   – Get global commission tiers
  PUT  /api/commission/tiers                   – Replace all tiers (super admin only)
  GET  /api/commission/sellers                 – List sellers with commission info
  PUT  /api/commission/sellers/{id}/override   – Set seller-level fixed commission %
  DELETE /api/commission/sellers/{id}/override – Remove seller-level override
  GET  /api/commission/calculate               – Preview commission for an order value

Commission lifecycle per sub-order:
  pending/processing → (no commission yet)
  delivered          → commissionStatus = 'unrealized', commissionPct + commissionAmount stored
  delivered + returnDays elapsed → commissionStatus = 'realized'
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict

from app.db.storage_factory import get_storage
from app.repositories.return_settings_repository import return_settings_repository
from app.repositories.user_repository import user_repository
from app.utils.auth import require_super_admin

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Storage helper
# ---------------------------------------------------------------------------


def _get_commission_storage():
    return get_storage("commissionSettings")


async def _get_settings() -> dict:
    storage = _get_commission_storage()
    docs = await storage.findAll()
    if docs:
        return docs[0]
    # Create default settings
    default = {
        "tiers": [],
        "defaultCommissionPct": 5.0,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }
    return await storage.create(default)


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class CommissionTier(BaseModel):
    id: Optional[str] = Field(default=None)
    minOrderValue: float = Field(default=0.0, ge=0, alias="min_order_value")
    maxOrderValue: Optional[float] = Field(default=None, ge=0, alias="max_order_value")  # None = unlimited
    commissionPct: float = Field(default=0.0, ge=0, le=100, alias="commission_pct")

    model_config = ConfigDict(populate_by_name=True, extra="forbid")



class TiersResponse(BaseModel):
    tiers: List[CommissionTier]
    defaultCommissionPct: float

class SellerCommissionInfo(BaseModel):
    id: str = Field(alias="_id")
    name: str
    email: str
    phone: Optional[str] = None
    overrideCommissionPct: Optional[float] = None
    effectiveCommissionPct: float
    currentTier: Optional[str] = None


class SellerOverrideResponse(BaseModel):
    id: str
    commissionOverridePct: Optional[float] = None
    message: str

class CommissionPreviewResponse(BaseModel):
    orderValue: float
    commissionPct: float
    commissionAmount: float

class RealizeCommissionResponse(BaseModel):
    processed: int
    realized: int

class TiersPayload(BaseModel):
    tiers: List[CommissionTier]
    defaultCommissionPct: float = Field(default=5.0, ge=0, le=100)


class SellerOverridePayload(BaseModel):
    commissionOverridePct: Optional[float] = Field(default=None, ge=0, le=100)


# ---------------------------------------------------------------------------
# Helper: resolve commission rate for a given order total and seller_id
# ---------------------------------------------------------------------------


async def resolve_commission_pct(order_total: float, seller_id: Optional[str]) -> float:
    """Return the applicable commission percentage for an order."""
    # 1. Check seller-level override
    if seller_id:
        seller = await user_repository.findById(seller_id)
        if seller:
            override = seller.commission_override_pct
            if override is not None:
                return float(override)

    # 2. Fall through to global tiers
    settings = await _get_settings()
    raw_tiers = settings.tiers or []
    tiers: List[CommissionTier] = [t if isinstance(t, CommissionTier) else CommissionTier.model_validate(t) for t in raw_tiers]
    default_pct: float = (settings.default_commission_pct if settings.default_commission_pct is not None else 5.0)

    for tier in sorted(tiers, key=lambda t: (t.minOrderValue if t.minOrderValue is not None else 0)):
        min_v = tier.minOrderValue if tier.minOrderValue is not None else 0.0
        max_v = tier.maxOrderValue  # None = unlimited
        if order_total >= min_v and (max_v is None or order_total <= max_v):
            return float(tier.commissionPct if tier.commissionPct is not None else default_pct)

    return float(default_pct)


# ---------------------------------------------------------------------------
# Helper: check if return window has elapsed for a sub-order
# ---------------------------------------------------------------------------


async def is_return_period_over(sub_order: dict) -> bool:
    delivered_at_raw = sub_order.delivered_at
    if not delivered_at_raw:
        return False

    try:
        delivered_at = datetime.fromisoformat(delivered_at_raw.replace("Z", "+00:00"))
    except ValueError:
        return False

    settings = await return_settings_repository.get_settings()
    return_days: int = int((settings.return_days if settings.return_days is not None else 7))
    realize_at = delivered_at + timedelta(days=return_days)

    now = datetime.now(timezone.utc)
    if delivered_at.tzinfo is None:
        delivered_at = delivered_at.replace(tzinfo=timezone.utc)
        realize_at = delivered_at + timedelta(days=return_days)

    return now >= realize_at


# ---------------------------------------------------------------------------
# Helper: stamp commission fields on a sub-order when delivered
# ---------------------------------------------------------------------------


async def stamp_commission_on_delivery(sub_order: dict) -> dict:
    """
    Called when a sub-order transitions to 'delivered'.
    Returns a dict of fields to merge into the sub-order update payload.
    Only stamps if there is a seller (platform-only orders have no commission).
    """
    seller_id = sub_order.seller_id
    if not seller_id:
        return {"commissionStatus": None, "commissionPct": None, "commissionAmount": None}

    if sub_order.subtotal is None and sub_order.total is None:
        raise ValueError(f"Data Integrity Error: Sub order {sub_order.id} is missing both subtotal and total for commission calculation")
    order_total = float(sub_order.subtotal if sub_order.subtotal is not None else sub_order.total)
    pct = await resolve_commission_pct(order_total, seller_id)
    amount = round(order_total * pct / 100, 2)

    return {
        "commissionStatus": "unrealized",
        "commissionPct": pct,
        "commissionAmount": amount,
    }


# ---------------------------------------------------------------------------
# Helper: maybe promote unrealized → realized (called on read)
# ---------------------------------------------------------------------------


async def maybe_realize_commission(sub_order: dict) -> dict:
    """
    If a sub-order has commissionStatus='unrealized' and the return window has
    elapsed, promote it to 'realized' and persist the change.
    Returns the (potentially updated) sub-order dict.
    """
    if sub_order.commission_status != "unrealized":
        return sub_order

    # Do not realize if a return is in progress or completed for this sub-order
    if sub_order.return_status in ("pending", "pending_valet", "assigned", "collected", "approved", "returned"):
        return sub_order

    if await is_return_period_over(sub_order):
        from app.repositories.sub_order_repository import sub_order_repository

        updated = await sub_order_repository.update(sub_order["_id"], {"commissionStatus": "realized"})
        return updated if updated else {**sub_order, "commissionStatus": "realized"}

    return sub_order


# ---------------------------------------------------------------------------
# GET /tiers — fetch global commission tiers
# ---------------------------------------------------------------------------


@router.get("/tiers", response_model=TiersResponse)
async def get_commission_tiers(current_user: User = Depends(require_super_admin)):
    settings = await _get_settings()
    return {
        "tiers": (settings.tiers or []),
        "defaultCommissionPct": (settings.default_commission_pct if settings.default_commission_pct is not None else 5.0),
    }


# ---------------------------------------------------------------------------
# PUT /tiers — replace all global commission tiers
# ---------------------------------------------------------------------------


@router.put("/tiers", response_model=MessageResponse)
async def update_commission_tiers(
    payload: TiersPayload,
    current_user: User = Depends(require_super_admin),
):
    # Assign stable IDs if missing
    tiers_data: List[CommissionTier] = []
    for t in payload.tiers:
        if not t.id:
            t.id = str(uuid4())
        tiers_data.append(t)

    # Validate no overlaps
    sorted_tiers = sorted(tiers_data, key=lambda t: t.minOrderValue)
    for i in range(len(sorted_tiers) - 1):
        curr_max = sorted_tiers[i].maxOrderValue
        next_min = sorted_tiers[i + 1].minOrderValue
        if curr_max is not None and curr_max > next_min:
            raise HTTPException(
                status_code=400,
                detail=f"Tier ranges overlap: tier ending at {curr_max} overlaps with tier starting at {next_min}.",
            )

    storage = _get_commission_storage()
    settings = await _get_settings()
    updated = await storage.update(
        settings.id,
        {
            "tiers": tiers_data,
            "defaultCommissionPct": payload.defaultCommissionPct,
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        },
    )
    if isinstance(updated, dict):
        updated_tiers = updated["tiers"] if "tiers" in updated else tiers_data
        updated_default = updated["defaultCommissionPct"] if "defaultCommissionPct" in updated else payload.defaultCommissionPct
    else:
        updated_tiers = updated.tiers
        updated_default = updated.default_commission_pct if updated.default_commission_pct is not None else payload.defaultCommissionPct

    return {
        "tiers": updated_tiers if updated_tiers is not None else [],
        "defaultCommissionPct": updated_default if updated_default is not None else 5.0,
    }


# ---------------------------------------------------------------------------
# GET /sellers — list all sellers with commission info
# ---------------------------------------------------------------------------


@router.get("/sellers", response_model=List[SellerCommissionInfo])
async def list_sellers_commission(current_user: User = Depends(require_super_admin)):
    sellers = await user_repository.findAll({"role": "wholesaler", "isSellerAdmin": True})
    settings = await _get_settings()
    tiers = (settings.tiers or [])
    default_pct = (settings.default_commission_pct if settings.default_commission_pct is not None else 5.0)

    result = []
    for s in sellers:
        override = s.commission_override_pct
        result.append(
            {
                "id": str((s.id or "")),
                "name": (s.name or ""),
                "email": (s.email or ""),
                "phone": (s.phone or ""),
                "companyName": (s.company_name or ""),
                "isActive": (s.is_active if s.is_active is not None else True),
                "commissionOverridePct": override,
                "effectiveCommissionType": "override" if override is not None else "tiers",
                "effectiveTiersSummary": (
                    f"{override}% (fixed override)"
                    if override is not None
                    else f"{len(tiers)} tier(s), default {default_pct}%"
                ),
                "createdAt": (s.created_at or ""),
            }
        )
    return result


# ---------------------------------------------------------------------------
# PUT /sellers/{seller_id}/override — set seller-level fixed commission %
# ---------------------------------------------------------------------------


@router.put("/sellers/{seller_id}/override", response_model=SellerOverrideResponse)
async def set_seller_commission_override(
    seller_id: str,
    payload: SellerOverridePayload,
    current_user: User = Depends(require_super_admin),
):
    seller = await user_repository.findById(seller_id)
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    if not seller.is_seller_admin:
        raise HTTPException(status_code=400, detail="User is not a marketplace seller")

    updated = await user_repository.update(seller_id, UserUpdate(commissionOverridePct=payload.commissionOverridePct))
    override_val = updated.commission_override_pct if updated.commission_override_pct is not None else payload.commissionOverridePct
    
    return {
        "id": seller_id,
        "commissionOverridePct": override_val,
        "message": "Commission override updated successfully",
    }


# ---------------------------------------------------------------------------
# DELETE /sellers/{seller_id}/override — remove seller-level override
# ---------------------------------------------------------------------------


@router.delete("/sellers/{seller_id}/override", response_model=MessageResponse)
async def remove_seller_commission_override(
    seller_id: str,
    current_user: User = Depends(require_super_admin),
):
    seller = await user_repository.findById(seller_id)
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")

    await user_repository.update(seller_id, UserUpdate(commissionOverridePct=None))
    return {"id": seller_id, "message": "Commission override removed. Seller will use global tiers."}


# ---------------------------------------------------------------------------
# GET /calculate — preview commission for a given order value + seller
# ---------------------------------------------------------------------------


@router.get("/calculate", response_model=CommissionPreviewResponse)
async def preview_commission(
    order_value: float,
    seller_id: Optional[str] = None,
    current_user: User = Depends(require_super_admin),
):
    pct = await resolve_commission_pct(order_value, seller_id)
    amount = round(order_value * pct / 100, 2)
    return {
        "orderValue": order_value,
        "sellerId": seller_id,
        "commissionPct": pct,
        "commissionAmount": amount,
    }


@router.post("/realize-pending", response_model=RealizeCommissionResponse)
async def realize_pending_commissions(
    current_user: User = Depends(require_super_admin),
):
    """
    Promote unrealized commissions whose return window has elapsed to realized.
    Call this endpoint from a scheduled job (e.g. every 6 hours).
    Safe to call repeatedly — already-realized commissions are skipped.
    """
    from app.db.storage_factory import get_storage

    sub_order_storage = get_storage("subOrders")
    # Only fetch delivered sub-orders with unrealized commission
    candidates = await sub_order_storage.findAll({"commissionStatus": "unrealized", "status": "delivered"})
    promoted = 0
    errors = 0
    for so in candidates:
        try:
            updated = await maybe_realize_commission(so)
            status_val = updated.commission_status
            
            if status_val == "realized":
                so_id = str(updated.id)
                
                await sub_order_storage.update(so_id, updated)
                promoted += 1
        except Exception as e:
            logger.warning("Failed to realize commission for sub-order %s: %s", so.id, e)
            errors += 1
    return {"promoted": promoted, "errors": errors, "checked": len(candidates)}
