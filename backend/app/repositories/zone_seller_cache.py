"""
zone_seller_cache.py
--------------------
Shared, in-process cache that resolves:
    pincode  ->  delivery zone  ->  set[seller_id]

All availability-filtering paths (autocomplete, check-serviceability) must
use this module so there is a single source of truth.

Cache behaviour
---------------
- Keyed by zone _id; TTL = 5 minutes (ZONE_CACHE_TTL_S).
- On a cache miss the module fetches ALL active zones once and walks them.
- Returns:
    None      -> pincode not in any zone  (no filter: show all products)
    set()     -> zone found but sellerIds = []  (nothing available)
    set(ids)  -> zone found with sellers
"""

import time
from typing import Dict, Optional, Set, Tuple

from app.db.storage_factory import get_storage
from app.utils.logger import logger

ZONE_CACHE_TTL_S = 300  # 5 minutes

# { zone_id: (frozenset[seller_id], expiry_monotonic) }
_zone_cache: Dict[str, Tuple[frozenset, float]] = {}


def _is_fresh(expiry: float) -> bool:
    return time.monotonic() < expiry


def _cache_zone(zone: dict) -> frozenset:
    """Store a zone's seller IDs in the cache and return them."""
    seller_ids = frozenset(str(s) for s in (zone.get("sellerIds") or []))
    zone_id = str(zone["_id"])
    _zone_cache[zone_id] = (seller_ids, time.monotonic() + ZONE_CACHE_TTL_S)
    return seller_ids


async def _fetch_all_zones() -> list:
    """Fetch all active zones from storage."""
    storage = get_storage("deliveryZones")
    return await storage.findAll({"isActive": True})


async def get_zone_id_and_seller_ids_for_pincode(pincode: str) -> Tuple[Optional[str], Optional[Set[str]]]:
    """
    Resolve a pincode to its zone ID and the set of seller IDs for its zone.
    Returns:
        (None, None) -> pincode not in any zone
        (zone_id, set()) -> zone found but no sellers assigned
        (zone_id, set(ids)) -> zone found with sellers
    """
    if not pincode:
        return None, None

    try:
        zones = await _fetch_all_zones()
        for zone in zones:
            pincodes = zone.get("pincodes") or []
            if pincode not in pincodes:
                continue

            zone_id = str(zone["_id"])
            if zone_id in _zone_cache:
                cached_ids, expiry = _zone_cache[zone_id]
                if _is_fresh(expiry):
                    return zone_id, set(cached_ids)

            return zone_id, set(_cache_zone(zone))
        return None, None
    except Exception as exc:
        logger.error("zone_seller_cache: failed to resolve pincode %s: %s", pincode, exc, exc_info=True)
        return None, None

async def get_seller_ids_for_pincode(pincode: str) -> Optional[Set[str]]:
    """
    Resolve a pincode to the set of seller IDs for its zone.

    Returns:
        None     -- pincode not in any zone -> callers should apply no filter
        set()    -- zone found but no sellers assigned -> nothing available
        set(ids) -- zone found with sellers -> filter to these IDs
    """
    _, seller_ids = await get_zone_id_and_seller_ids_for_pincode(pincode)
    return seller_ids

async def get_zone_for_pincode(pincode: str) -> Optional[dict]:
    """
    Return the full zone document for a pincode, or None.
    Useful when callers need zone metadata (name, urgentDeliveryAvailable, etc.)
    alongside seller IDs.
    """
    if not pincode:
        return None

    try:
        zones = await _fetch_all_zones()
        for zone in zones:
            if pincode in (zone.get("pincodes") or []):
                return zone
        return None
    except Exception as exc:
        logger.error("zone_seller_cache: get_zone_for_pincode failed for %s: %s", pincode, exc, exc_info=True)
        return None


def invalidate_zone_cache(zone_id: Optional[str] = None) -> None:
    """
    Invalidate cache entries.
    Pass a zone_id to evict a specific zone, or None to clear everything.
    Call this from zone create/update/delete routes for instant consistency.
    """
    if zone_id:
        _zone_cache.pop(str(zone_id), None)
    else:
        _zone_cache.clear()
