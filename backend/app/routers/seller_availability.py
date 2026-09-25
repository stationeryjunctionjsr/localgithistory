from app.models.user import User
from app.models.schemas import MessageResponse
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
from typing import Dict, Any, List, Any, Dict, List, Optional, Set

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, validator, ConfigDict

from app.db.storage_factory import get_storage
from app.utils.auth import get_current_user, require_super_admin

logger = logging.getLogger(__name__)

router = APIRouter()
storage = get_storage("sellerAvailability")


# ─── Schemas ─────────────────────────────────────────────────────────────────



class SellerAvailabilityItem(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    sellerId: Optional[str] = None
    startAt: Optional[str] = None
    endAt: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    reason: Optional[str] = None
    status: Optional[str] = None
    sellerName: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class SellerAvailabilityResponse(BaseModel):
    id: str = Field(alias="_id")
    sellerId: str
    startAt: str
    endAt: str
    reason: Optional[str] = None
    status: str
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class TickResponse(BaseModel):
    processed: int
    expired: int
    activated: int

class SellerAvailabilityCreate(BaseModel):
    startAt: str  # ISO 8601 datetime, e.g. "2026-08-17T14:00:00"
    endAt: str  # ISO 8601 datetime, e.g. "2026-08-17T18:00:00"
    reason: Optional[str] = None

    @validator("startAt", "endAt")
    def validate_datetime_format(cls, v):
        try:
            datetime.fromisoformat(v.replace("Z", ""))
        except ValueError:
            raise ValueError("Invalid datetime format. Use ISO 8601 (e.g. 2026-08-17T14:00:00)")
        return v


# ─── Helpers ─────────────────────────────────────────────────────────────────

MIN_LEAD_HOURS = 3  # Seller must schedule at least 3 hours before the window starts


def _require_seller(current_user: dict):
    if current_user.role not in ("seller", "super_admin"):
        raise HTTPException(status_code=403, detail="Only seller accounts can access this endpoint")


async def is_seller_currently_unavailable(seller_id: str) -> bool:
    """
    Returns True if the seller has an active unavailability window right now.
    Called by products.py when resolving the winning seller for a pincode.
    """
    now = datetime.now(timezone.utc)
    now.isoformat() + "Z"
    docs = await storage.findAll(
        {
            "sellerId": seller_id,
            "status": {"$in": ["scheduled", "active"]},
        }
    )
    for doc in docs:
        try:
            start = datetime.fromisoformat(doc.startAt.replace("Z", ""))
            end = datetime.fromisoformat(doc.endAt.replace("Z", ""))
            if start <= now <= end:
                return True
        except (ValueError, AttributeError):
            logger.warning("Seller availability doc %r has unparseable startAt/endAt; skipping.", getattr(doc, 'id', '?'), exc_info=True)
            continue
    return False


_unavailable_cache = {"data": None, "expires": 0.0}


async def get_all_unavailable_seller_ids() -> Set[str]:
    now = time.monotonic()
    if _unavailable_cache["expires"] > now and _unavailable_cache["data"] is not None:
        return _unavailable_cache["data"]

    all_docs = await storage.findAll({"status": {"$in": ["scheduled", "active"]}})

    unavailable_sellers = set()
    current_utc = datetime.now(timezone.utc)

    for doc in all_docs:
        try:
            start = datetime.fromisoformat(doc.startAt.replace("Z", ""))
            end = datetime.fromisoformat(doc.endAt.replace("Z", ""))
            if start <= current_utc <= end:
                seller_id = doc.seller_id
                if seller_id:
                    unavailable_sellers.add(str(seller_id))
        except (ValueError, AttributeError):
            logger.warning("Seller availability doc %r has unparseable startAt/endAt; skipping from unavailable set.", getattr(doc, 'id', '?'), exc_info=True)
            continue

    _unavailable_cache["data"] = unavailable_sellers
    _unavailable_cache["expires"] = now + 60.0
    return unavailable_sellers


async def get_seller_unavailable_until(seller_ids: Set[str]) -> Optional[str]:
    """
    Given a set of seller IDs that are known to be unavailable, return the latest
    ``endAt`` ISO string across all their active unavailability windows.

    This is used by the products listing / detail endpoints to populate the
    ``sellerUnavailableUntil`` field so the frontend can display a
    "Back at {date/time}" message to customers.

    Returns None if no active window can be found (graceful fallback).
    """
    if not seller_ids:
        return None

    current_utc = datetime.now(timezone.utc)
    latest_end: Optional[datetime] = None

    try:
        all_docs = await storage.findAll({"status": {"$in": ["scheduled", "active"]}})
        for doc in all_docs:
            if str(doc.seller_id) not in seller_ids:
                continue
            try:
                start = datetime.fromisoformat(doc.startAt.replace("Z", ""))
                end = datetime.fromisoformat(doc.endAt.replace("Z", ""))
                if start <= current_utc <= end:
                    if latest_end is None or end > latest_end:
                        latest_end = end
            except (ValueError, AttributeError):
                logger.warning("Seller availability doc %r has unparseable startAt/endAt; skipping from unavailable-until lookup.", getattr(doc, 'id', '?'), exc_info=True)
                continue
    except Exception:
        logger.warning("Failed to fetch seller availability docs for unavailable-until lookup; returning None.", exc_info=True)
        return None

    if latest_end is None:
        return None
    # Return as UTC ISO string with Z suffix for easy frontend parsing
    return latest_end.strftime("%Y-%m-%dT%H:%M:%SZ")




async def _enrich_with_seller_name(docs: list) -> list:
    """Add sellerName to each doc for admin display."""
    from app.repositories.user_repository import user_repository

    seller_ids = list({doc.seller_id for doc in docs if doc.seller_id})
    sellers_map: Dict[str, dict] = {}
    for sid in seller_ids:
        seller = await user_repository.findById(sid)
        if seller:
            sellers_map[sid] = seller
    enriched = []
    for doc in docs:
        sid = (doc.seller_id or "")
        seller = (sellers_map[sid] if sid in sellers_map else {})
        enriched.append(
            {
                **doc,
                "sellerName": (seller.name or ""),
                "sellerEmail": (seller.email or ""),
            }
        )
    return enriched



# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/zone-status")
async def get_zone_seller_availability_status(pincode: Optional[str] = None):
    """
    Public endpoint — returns a map of { sellerId: unavailableUntil (ISO string) }
    for all sellers in the given pincode's zone who are currently in an unavailability
    window.

    The frontend uses this to grey-out product cards and show "Back at {time}" badges
    without touching the cached product listing responses.

    Returns {} (empty object) when:
    - No pincode is provided
    - Pincode is not in any zone
    - No sellers in the zone are currently unavailable
    """
    if not pincode:
        return {"unavailableSellers": {}}

    from app.repositories.zone_seller_cache import get_unavailable_seller_ids_for_pincode
    unavailable_ids = await get_unavailable_seller_ids_for_pincode(pincode)
    if not unavailable_ids:
        return {"unavailableSellers": {}}

    # Build {sellerId: endAt} for each unavailable seller
    result: Dict[str, str] = {}
    current_utc = datetime.now(timezone.utc)
    try:
        all_docs = await storage.findAll({"status": {"$in": ["scheduled", "active"]}})
        for doc in all_docs:
            sid = str(doc.seller_id or "")
            if sid not in unavailable_ids:
                continue
            try:
                start = datetime.fromisoformat(doc.startAt.replace("Z", ""))
                end = datetime.fromisoformat(doc.endAt.replace("Z", ""))
                if start <= current_utc <= end:
                    end_str = end.strftime("%Y-%m-%dT%H:%M:%SZ")
                    # Keep the latest endAt if there are multiple windows
                    if sid not in result or end_str > result[sid]:
                        result[sid] = end_str
            except (ValueError, AttributeError):
                logger.warning("Seller availability doc %r has unparseable startAt/endAt in zone-status; skipping.", getattr(doc, 'id', '?'), exc_info=True)
                continue
    except Exception:
        logger.warning("Failed to fetch seller availability docs for zone-status pincode=%r; returning empty.", None, exc_info=True)
        return {"unavailableSellers": {}}

    return {"unavailableSellers": result}




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
    from app.models.daos_flat import SellerAvailabilityInternalCreate
    created = await storage.create(SellerAvailabilityInternalCreate(
        sellerId=seller_id,
        startAt=data.startAt,
        endAt=data.endAt,
        reason=data.reason,
        status="scheduled",
        createdAt=now.isoformat() + "Z"
    ))
    # Invalidate unavailability cache so next request sees the new window immediately
    _unavailable_cache["expires"] = 0.0
    # Also invalidate product listing cache so pincode-filtered results refresh
    from app.routers.products import get_public_products
    from app.utils.cache import cache as _cache

    await _cache.invalidate(get_public_products)
    return created


@router.get("/my", response_model=List[SellerAvailabilityResponse])
async def get_my_availability_windows(
    current_user: User = Depends(get_current_user),
):
    """Return own upcoming and recent availability windows."""
    _require_seller(current_user)
    seller_id = str(current_user.id)
    docs = await storage.findAll({"sellerId": seller_id})
    # Sort by startAt descending (most recent first)
    parsed_docs = [
        d if isinstance(d, SellerAvailabilityItem) else SellerAvailabilityItem.model_validate(d, from_attributes=True)
        for d in docs
    ]
    parsed_docs.sort(key=lambda d: (d.startAt or d.start_date or ""), reverse=True)
    return parsed_docs


@router.get("", response_model=List[SellerAvailabilityResponse])
@router.get("/", response_model=List[SellerAvailabilityResponse])
async def get_all_seller_availability(
    sellerId: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(require_super_admin),
):
    """Admin: view all sellers' availability windows."""
    query: Dict[str, Any] = {}
    if sellerId:
        query["sellerId"] = sellerId
    if status:
        query["status"] = status
    docs = await storage.findAll(query)
    enriched = await _enrich_with_seller_name(docs)
    parsed_enriched = [
        d if isinstance(d, SellerAvailabilityItem) else SellerAvailabilityItem.model_validate(d, from_attributes=True)
        for d in enriched
    ]
    parsed_enriched.sort(key=lambda d: (d.startAt or d.start_date or ""), reverse=True)
    return parsed_enriched


@router.delete("/{window_id}", response_model=MessageResponse)
async def cancel_availability_window(
    window_id: str,
    current_user: User = Depends(get_current_user),
):
    """Cancel a scheduled availability window. Only allowed before it becomes active."""
    _require_seller(current_user)

    doc = await storage.findById(window_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Availability window not found")

    if str(doc.seller_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="You can only cancel your own windows")

    if doc.status == "active":
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel a window that is already active. It will expire automatically.",
        )
    if doc.status in ("ended", "cancelled"):
        raise HTTPException(status_code=400, detail="This window has already ended or been cancelled.")

    await storage.update(window_id, {"status": "cancelled"})
    # Invalidate unavailability cache
    _unavailable_cache["expires"] = 0.0
    # Also invalidate product listing cache so pincode-filtered results refresh
    from app.routers.products import get_public_products
    from app.utils.cache import cache as _cache

    await _cache.invalidate(get_public_products)
    return {"message": "Availability window cancelled"}


@router.post("/tick", include_in_schema=False, response_model=TickResponse)
async def tick_availability_statuses(
    current_user: User = Depends(require_super_admin),
):
    """
    Internal: advance status transitions for scheduled/active windows.
    Call via cron every 15 minutes.
    scheduled -> active (if startAt has passed)
    active -> ended (if endAt has passed)
    """
    now = datetime.now(timezone.utc)
    docs = await storage.findAll({"status": {"$in": ["scheduled", "active"]}})
    updated = 0
    for doc in docs:
        try:
            start_dt = datetime.fromisoformat(doc.startAt.replace("Z", ""))
            end_dt = datetime.fromisoformat(doc.endAt.replace("Z", ""))
            doc_id = str(doc.id)
            if doc.status == "scheduled" and now >= start_dt:
                await storage.update(doc_id, {"status": "active"})
                updated += 1
            elif doc.status == "active" and now >= end_dt:
                await storage.update(doc_id, {"status": "ended"})
                updated += 1
        except Exception:
            logger.warning("tick: failed to process seller availability doc %r; skipping.", getattr(doc, 'id', '?'), exc_info=True)
            continue
    return {"updated": updated, "checked": len(docs)}
