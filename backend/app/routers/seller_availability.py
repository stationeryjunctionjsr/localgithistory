"""
Seller Store Availability Router

Sellers can schedule time-off windows (e.g. half-day, full-day) for their store.
During these windows:
  - Their products are NOT shown for their pincodes
  - New orders are NOT routed to them
  - Existing pending/processing orders are STILL fulfilled

Endpoints:
  POST   /seller-availability          - Schedule an unavailability window (seller)
  GET    /seller-availability/my       - List own windows (seller)
  DELETE /seller-availability/{id}     - Cancel a scheduled window (seller, only if not yet active)
  GET    /seller-availability          - View all sellers' windows (admin only)
"""

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Set

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from app.db.storage_factory import get_storage
from app.models.base import CamelBaseModel
from app.models.user import User
from app.models.schemas import MessageResponse
from app.models.daos_flat import (
    SellerAvailabilityFilter,
    SellerAvailabilityInternalCreate,
    SellerAvailabilityInternalUpdate,
)
from app.utils.auth import get_current_user, require_super_admin

logger = logging.getLogger(__name__)

router = APIRouter()
storage = get_storage("sellerAvailability")


# ─── Schemas ─────────────────────────────────────────────────────────────────


class SellerAvailabilityResponse(CamelBaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    seller_id: str
    status: str
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    reason: Optional[str] = None
    seller_name: Optional[str] = None
    seller_email: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TickResponse(BaseModel):
    updated: int = 0
    checked: int = 0
    processed: int = 0
    expired: int = 0
    activated: int = 0


class SellerAvailabilityCreate(BaseModel):
    startAt: str  # ISO 8601 datetime, e.g. "2026-08-17T14:00:00"
    endAt: str  # ISO 8601 datetime, e.g. "2026-08-17T18:00:00"
    reason: Optional[str] = None

    @field_validator("startAt", "endAt")
    @classmethod
    def validate_datetime_format(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v.replace("Z", ""))
        except ValueError:
            raise ValueError("Invalid datetime format. Use ISO 8601 (e.g. 2026-08-17T14:00:00)")
        return v


# ─── Helpers ─────────────────────────────────────────────────────────────────

MIN_LEAD_HOURS = 3  # Seller must schedule at least 3 hours before the window starts


def _require_seller(current_user: User):
    if current_user.role not in ("seller", "super_admin"):
        raise HTTPException(status_code=403, detail="Only seller accounts can access this endpoint")


async def is_seller_currently_unavailable(seller_id: str) -> bool:
    """
    Returns True if the seller has an active unavailability window right now.
    Called by products.py when resolving the winning seller for a pincode.
    Pushdown SQL query.
    """
    return await storage.is_seller_currently_unavailable(seller_id)


_unavailable_cache: dict[str, object] = {"data": None, "expires": 0.0}


async def get_all_unavailable_seller_ids() -> Set[str]:
    now = time.monotonic()
    cache_expires = float(_unavailable_cache["expires"])
    cached_data = _unavailable_cache["data"]
    if cache_expires > now and cached_data is not None:
        return cached_data  # type: ignore

    unavailable_sellers = await storage.get_currently_unavailable_seller_ids()
    _unavailable_cache["data"] = unavailable_sellers
    _unavailable_cache["expires"] = now + 60.0
    return unavailable_sellers


async def get_seller_unavailable_until(seller_ids: Set[str]) -> Optional[str]:
    """
    Given a set of seller IDs that are known to be unavailable, return the latest
    ``endAt`` ISO string across all their active unavailability windows.
    Pushdown SQL query with MAX(end_at).
    """
    if not seller_ids:
        return None
    try:
        return await storage.get_latest_unavailable_until(seller_ids)
    except Exception:
        logger.warning("Failed to fetch seller availability records for unavailable-until lookup; returning None.", exc_info=True)
        return None


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/zone-status")
async def get_zone_seller_availability_status(pincode: Optional[str] = None):
    """
    Public endpoint — returns a map of { sellerId: unavailableUntil (ISO string) }
    for all sellers in the given pincode's zone who are currently in an unavailability window.
    Pushdown SQL GROUP BY query.
    """
    if not pincode:
        return {"unavailableSellers": {}}

    from app.repositories.zone_seller_cache import get_unavailable_seller_ids_for_pincode
    unavailable_ids = await get_unavailable_seller_ids_for_pincode(pincode)
    if not unavailable_ids:
        return {"unavailableSellers": {}}

    try:
        result = await storage.get_zone_unavailable_sellers_map(unavailable_ids)
        return {"unavailableSellers": result}
    except Exception:
        logger.warning("Failed to fetch seller availability records for zone-status pincode=%r; returning empty.", pincode, exc_info=True)
        return {"unavailableSellers": {}}


@router.post("", response_model=SellerAvailabilityResponse, status_code=201)
@router.post("/", response_model=SellerAvailabilityResponse, status_code=201)
async def schedule_unavailability(
    data: SellerAvailabilityCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Schedule a store unavailability window.
    Must be submitted at least 3 hours before the start time.
    """
    _require_seller(current_user)

    try:
        start_dt = datetime.fromisoformat(data.startAt.replace("Z", ""))
        end_dt = datetime.fromisoformat(data.endAt.replace("Z", ""))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format.")

    now = datetime.now(timezone.utc)

    # Enforce 3-hour minimum lead time
    if start_dt - now < timedelta(hours=MIN_LEAD_HOURS):
        raise HTTPException(
            status_code=400,
            detail=f"Unavailability must be scheduled at least {MIN_LEAD_HOURS} hours before the start time. "
            f"Earliest allowed start: {(now + timedelta(hours=MIN_LEAD_HOURS)).strftime('%Y-%m-%d %H:%M UTC')}",
        )

    if end_dt <= start_dt:
        raise HTTPException(status_code=400, detail="End time must be after start time.")

    if start_dt < now:
        raise HTTPException(status_code=400, detail="Cannot schedule unavailability in the past.")

    seller_id = str(current_user.id)
    created = await storage.create(SellerAvailabilityInternalCreate(
        seller_id=seller_id,
        start_at=data.startAt,
        end_at=data.endAt,
        reason=data.reason,
        status="scheduled",
        created_at=now,
    ))
    # Invalidate unavailability cache so next request sees the new window immediately
    _unavailable_cache["expires"] = 0.0
    # Also invalidate product listing cache so pincode-filtered results refresh
    from app.routers.products import get_public_products
    from app.utils.cache import cache as _cache

    _cache.invalidate(get_public_products)
    return created


@router.get("/my", response_model=list[SellerAvailabilityResponse])
async def get_my_availability_windows(
    current_user: User = Depends(get_current_user),
):
    """Return own upcoming and recent availability windows, ordered by start_at DESC in SQL."""
    _require_seller(current_user)
    seller_id = str(current_user.id)
    return await storage.findAll(SellerAvailabilityFilter(seller_id=seller_id))


@router.get("", response_model=list[SellerAvailabilityResponse])
@router.get("/", response_model=list[SellerAvailabilityResponse])
async def get_all_seller_availability(
    sellerId: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(require_super_admin),
):
    """Admin: view all sellers' availability windows with joined seller details in SQL."""
    filters = SellerAvailabilityFilter(seller_id=sellerId, status=status)
    return await storage.find_all_with_seller_details(filters)


@router.delete("/{window_id}", response_model=MessageResponse)
async def cancel_availability_window(
    window_id: str,
    current_user: User = Depends(get_current_user),
):
    """Cancel a scheduled availability window. Only allowed before it becomes active."""
    _require_seller(current_user)

    record = await storage.findById(window_id)
    if not record:
        raise HTTPException(status_code=404, detail="Availability window not found")

    if str(record.seller_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="You can only cancel your own windows")

    if record.status == "active":
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel a window that is already active. It will expire automatically.",
        )
    if record.status in ("ended", "cancelled"):
        raise HTTPException(status_code=400, detail="This window has already ended or been cancelled.")

    await storage.update(
        window_id,
        SellerAvailabilityInternalUpdate(status="cancelled"),
    )
    # Invalidate unavailability cache
    _unavailable_cache["expires"] = 0.0
    # Also invalidate product listing cache so pincode-filtered results refresh
    from app.routers.products import get_public_products
    from app.utils.cache import cache as _cache

    _cache.invalidate(get_public_products)
    return {"message": "Availability window cancelled"}


@router.post("/tick", include_in_schema=False, response_model=TickResponse)
async def tick_availability_statuses(
    current_user: User = Depends(require_super_admin),
):
    """
    Internal: advance status transitions for scheduled/active windows via atomic batch SQL.
    Call via cron every 15 minutes.
    scheduled -> active (if startAt has passed)
    active -> ended (if endAt has passed)
    """
    activated, ended = await storage.advance_availability_statuses()
    return {
        "updated": activated + ended,
        "checked": activated + ended,
        "activated": activated,
        "expired": ended,
        "processed": activated + ended,
    }
