"""
zone_seller_cache.py
--------------------
Shared, in-process cache that resolves:
    pincode  ->  delivery zone  ->  set[seller_id]

All availability-filtering paths (autocomplete, check-serviceability) must
use this module so there is a single source of truth.

Data model (seller-declared zones):
    Sellers declare which zones they service via sj_seller_zones.zone_id.
    To find sellers for a pincode:
      1. Resolve pincode -> zone (via zone.pincodes[])
      2. Read zone.externalId
      3. Query sj_seller_zones WHERE zone_id = <externalId>

Cache behaviour
---------------
- Zone-to-seller mapping keyed by zone externalId; TTL = 5 minutes.
- Returns:
    None      -> pincode not in any zone  (no filter: show all products)
    set()     -> zone found but no sellers declared
    set(ids)  -> zone found with sellers
"""

import time
from typing import Dict, Any, Optional, Set, Tuple

from app.db.storage_factory import get_storage
from app.utils.logger import logger

ZONE_CACHE_TTL_S = 300  # 5 minutes

# { zone_external_id: (frozenset[seller_id_str], expiry_monotonic) }
_zone_seller_cache: Dict[str, Tuple[frozenset, float]] = {}

_super_admin_id_cache: Optional[str] = None
_super_admin_cache_expiry: float = 0.0

async def get_super_admin_seller_id() -> Optional[str]:
    global _super_admin_id_cache, _super_admin_cache_expiry
    if _super_admin_id_cache and time.monotonic() < _super_admin_cache_expiry:
        return _super_admin_id_cache
        
    from app.repositories.user_repository import user_repository
    super_admin = await user_repository.findOne({"role": "super_admin"})
    if super_admin:
        _super_admin_id_cache = str(super_admin.id)
        _super_admin_cache_expiry = time.monotonic() + 3600
        return _super_admin_id_cache
    return None

def _is_fresh(expiry: float) -> bool:
    return time.monotonic() < expiry



def _cache_zone(zone) -> frozenset:
    """Kept for backward compatibility — not used in new flow."""
    seller_ids = frozenset(str(s) for s in (zone.sellerIds or []))
    return seller_ids


async def _fetch_all_zones() -> list:
    """Fetch all active zones from storage."""
    storage = get_storage("deliveryZones")
    return await storage.findAll({"isActive": True})


async def _get_sellers_for_zone(zone_external_id: str) -> frozenset:
    """
    Return frozenset of seller user_id strings who declared this zone.
    Queries sj_seller_zones WHERE zone_id = zone_external_id.
    Result is cached for 5 minutes.
    """
    cached = _zone_seller_cache[zone_external_id] if zone_external_id in _zone_seller_cache else None
    if cached and _is_fresh(cached[1]):
        return cached[0]

    try:
        from app.config.database import get_async_session_factory
        from sqlalchemy import text

        factory = get_async_session_factory()
        async with factory() as session:
            res = await session.execute(
                text("SELECT user_id FROM sj_seller_zones WHERE zone_id = :eid"),
                {"eid": zone_external_id},
            )
            rows = res.fetchall()

        seller_ids = frozenset(str(r.user_id) for r in rows)
        _zone_seller_cache[zone_external_id] = (seller_ids, time.monotonic() + ZONE_CACHE_TTL_S)
        return seller_ids
    except Exception as exc:
        logger.error("zone_seller_cache: failed to fetch sellers for zone %s: %s", zone_external_id, exc, exc_info=True)
        return frozenset()


async def get_zone_id_and_seller_ids_for_pincode(pincode: str) -> Tuple[Optional[str], Optional[Set[str]]]:
    """
    Resolve a pincode to its zone ID and the FULL set of seller IDs for its zone.
    Unavailable sellers are intentionally included so their products can be shown
    as greyed-out in the UI rather than hidden completely.

    Returns:
        (None, None)        -> pincode not in any zone
        (zone_id, set())    -> zone found but no sellers declared
        (zone_id, set(ids)) -> zone found with sellers (includes unavailable sellers)
    """
    if not pincode:
        return None, None

    try:
        zones = await _fetch_all_zones()
        for zone in zones:
            pincodes = zone.pincodes or []
            if pincode not in pincodes:
                continue

            # Use the MySQL _id (as string) as the zone identifier.
            # sj_delivery_zones has no external_id column, so we use _id consistently.
            zone_str_id = str((zone.id if zone.id is not None else ""))
            if not zone_str_id:
                logger.warning("zone_seller_cache: zone has no _id: %s", zone)
                return None, None

            # Return the full seller set — unavailable sellers are NOT subtracted here.
            # Use get_unavailable_seller_ids_for_pincode() to find the unavailable subset
            # for UI tagging purposes.
            seller_ids = set(await _get_sellers_for_zone(zone_str_id))
            return zone_str_id, seller_ids

        return None, None
    except Exception as exc:
        logger.error("zone_seller_cache: failed to resolve pincode %s: %s", pincode, exc, exc_info=True)
        return None, None


async def get_seller_ids_for_pincode(pincode: str) -> Optional[Set[str]]:
    """
    Resolve a pincode to the FULL set of seller IDs for its zone, including
    sellers who are currently in an unavailability window. Callers that need
    to filter those out (e.g. autocomplete) should use
    get_unavailable_seller_ids_for_pincode() to subtract the unavailable subset.

    Returns:
        None     -- pincode not in any zone -> callers should apply no filter
        set()    -- zone found but no sellers declared -> nothing available
        set(ids) -- zone found with sellers (includes unavailable sellers)
    """
    _, seller_ids = await get_zone_id_and_seller_ids_for_pincode(pincode)
    return seller_ids


async def get_seller_ids_for_zone_id(zone_id: str) -> Optional[Set[str]]:
    """
    Get the FULL set of seller IDs for a known zone_id directly —
    no pincode resolution needed. Use this inside cached functions
    that already have a resolved zone_id.

    Returns:
        None      -> zone_id is empty/invalid
        set()     -> zone found but no sellers declared
        set(ids)  -> zone found with sellers
    """
    if not zone_id:
        return None
    return set(await _get_sellers_for_zone(zone_id))


async def get_unavailable_seller_ids_for_pincode(pincode: str) -> Set[str]:
    """
    Returns the subset of zone sellers for a pincode who are currently within
    an unavailability window. Use this to tag/grey products in the UI rather
    than to remove them from query results.

    Returns an empty set when:
    - No pincode is provided
    - The pincode is not in any zone
    - No sellers in the zone are currently unavailable
    """
    _, all_seller_ids = await get_zone_id_and_seller_ids_for_pincode(pincode)
    if not all_seller_ids:
        return set()
    from app.routers.seller_availability import get_all_unavailable_seller_ids
    unavailable = await get_all_unavailable_seller_ids()
    return unavailable & all_seller_ids


from app.models.daos_flat import DeliveryZoneInternal
async def get_zone_for_pincode(pincode: str) -> Optional[DeliveryZoneInternal]:
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
            if pincode in (zone.pincodes or []):
                return zone
        return None
    except Exception as exc:
        logger.error("zone_seller_cache: get_zone_for_pincode failed for %s: %s", pincode, exc, exc_info=True)
        return None


def invalidate_zone_cache(zone_id: Optional[str] = None) -> None:
    """
    Invalidate cache entries.
    Pass a zone external_id to evict a specific zone, or None to clear everything.
    Call this from zone create/update/delete routes and when a seller updates their zones.
    """
    if zone_id:
        _zone_seller_cache.pop(str(zone_id), None)
    else:
        _zone_seller_cache.clear()

