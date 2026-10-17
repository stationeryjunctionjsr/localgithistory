"""
zone_seller_cache.py
--------------------
Shared, in-process cache that resolves:
    pincode  ->  delivery zone  ->  set[seller_id]

All availability-filtering paths (recommendations, product listing, search,
autocomplete) must use this module so there is a single source of truth.

Seller visibility rules
-----------------------
  Hyperlocal retail  (pincode in a delivery zone):
      seller_id_set = sellers declared for that zone
  Pan-India / no-pincode retail:
      seller_id_set = {super_admin_id}   (SA catalog; add-to-cart gated by FE)
  Wholesale:
      seller_id_set = {super_admin_id}   (always SA only)

  The backend NEVER returns an empty product list due to missing pincode.
  The frontend is responsible for:
    - Enforcing pincode entry via the modal gate
    - Disabling add-to-cart / checkout until pincode is confirmed
    - Showing a "not serviceable" banner when needed

Cache behaviour
---------------
- Zone-to-seller mapping keyed by zone id; TTL = 5 minutes.
- get_zone_id_and_seller_ids_for_pincode() returns:
    (None, None)        -> pincode not in any zone
    (zone_id, set())    -> zone found but no sellers declared
    (zone_id, set(ids)) -> zone found with sellers
- get_retail_seller_set() is the recommended high-level entry point; it
  applies the hyperlocal / pan-india / no-pincode decision automatically.
"""

import time
from typing import Dict, Any, Optional, Set, Tuple

from app.db.storage_factory import get_storage
from app.utils.logger import logger

ZONE_CACHE_TTL_S = 300  # 5 minutes

# { zone_id: (frozenset[seller_id_str], expiry_monotonic) }
_zone_seller_cache: Dict[int, Tuple[frozenset, float]] = {}

_super_admin_id_cache: Optional[str] = None
_super_admin_cache_expiry: float = 0.0

# Module-level cache for the full zones list — avoids a DB round-trip on every
# pincode lookup. Both get_zone_id_and_seller_ids_for_pincode() and
# get_zone_for_pincode() call _fetch_all_zones(); without this cache, every
# request that does pincode resolution (product listing, search, etc.) would
# hit the DB just to scan the zones list.
_all_zones_cache: Optional[list] = None
_all_zones_expiry: float = 0.0
_all_zones_lock: Optional[Any] = None  # asyncio.Lock created lazily

# O(1) pincode lookup index — built from _all_zones_cache whenever it is refreshed.
# Maps pincode (str) → zone object. Same TTL as _all_zones_cache.
# Eliminates the `for zone in zones: if pincode in zone.pincodes` O(n) linear scan.
_pincode_to_zone: Dict[str, Any] = {}


async def get_super_admin_seller_id() -> Optional[str]:
    global _super_admin_id_cache, _super_admin_cache_expiry
    if _super_admin_id_cache and time.monotonic() < _super_admin_cache_expiry:
        return _super_admin_id_cache
        
    from app.repositories.user_repository import user_repository
    super_admin = await user_repository.findSuperAdmin()
    if super_admin:
        _super_admin_id_cache = str(super_admin.id)
        _super_admin_cache_expiry = time.monotonic() + 3600
        return _super_admin_id_cache
    return None

def _is_fresh(expiry: float) -> bool:
    return time.monotonic() < expiry



def _cache_zone(zone) -> frozenset:
    """Kept for backward compatibility — not used in new flow."""
    seller_ids = frozenset(str(s) for s in (zone.seller_ids or []))
    return seller_ids


async def _fetch_all_zones() -> list:
    """Fetch all active zones from storage, with a module-level TTL cache.

    The zone list changes rarely (admin-driven) so caching for ZONE_CACHE_TTL_S
    (5 min) is safe.  Call invalidate_zone_cache() after any zone mutation to
    force an immediate refresh.

    Also builds _pincode_to_zone — a pincode→zone dict for O(1) lookups —
    eliminating the previous O(n) linear scan on every pincode resolution request.
    """
    global _all_zones_cache, _all_zones_expiry, _all_zones_lock, _pincode_to_zone
    import asyncio

    # Fast path: cache is warm (index is warm too — built at the same time)
    if _all_zones_cache is not None and time.monotonic() < _all_zones_expiry:
        return _all_zones_cache

    # Lazy-create the lock (cannot create at module level — no event loop yet)
    if _all_zones_lock is None:
        _all_zones_lock = asyncio.Lock()

    async with _all_zones_lock:
        # Double-checked: another coroutine may have populated it while we waited
        if _all_zones_cache is not None and time.monotonic() < _all_zones_expiry:
            return _all_zones_cache

        storage = get_storage("deliveryZones")
        zones = await storage.findAll(is_active=True)

        # Build the O(1) pincode → zone index atomically with the zone list.
        # Each zone's pincodes list is iterated once here so every subsequent
        # request pays O(1) dict lookup cost instead of O(zones × pincodes).
        # Values are DeliveryZoneInternal Pydantic models (from storage.findAll).
        new_index: Dict[str, Any] = {}
        for zone in zones:
            for pincode in (zone.pincodes or []):
                if pincode:
                    new_index[str(pincode)] = zone  # later zone wins on duplicate pincodes

        _pincode_to_zone = new_index
        _all_zones_cache = zones
        _all_zones_expiry = time.monotonic() + ZONE_CACHE_TTL_S
        return _all_zones_cache


async def _get_sellers_for_zone(zone_id: int) -> frozenset:
    """
    Return frozenset of seller user_id strings who declared this zone.
    Queries sj_seller_zones WHERE zone_id = :zid.
    Result is cached for 5 minutes.
    """
    cached = _zone_seller_cache.get(zone_id)
    if cached and _is_fresh(cached[1]):
        return cached[0]

    try:
        from app.config.database import get_async_session_factory
        from sqlalchemy import text

        factory = get_async_session_factory()
        async with factory() as session:
            res = await session.execute(
                text("SELECT user_id FROM sj_seller_zones WHERE zone_id = :zid"),
                {"zid": zone_id},
            )
            rows = res.fetchall()

        seller_ids = frozenset(str(r.user_id) for r in rows)
        _zone_seller_cache[zone_id] = (seller_ids, time.monotonic() + ZONE_CACHE_TTL_S)
        return seller_ids
    except Exception as exc:
        logger.error("zone_seller_cache: failed to fetch sellers for zone %s: %s", zone_id, exc, exc_info=True)
        return frozenset()


async def get_zone_id_and_seller_ids_for_pincode(pincode: str) -> Tuple[Optional[int], Optional[Set[str]]]:
    """
    Resolve a pincode to its zone ID and the FULL set of seller IDs for its zone.
    Unavailable sellers are intentionally included so their products can be shown
    as greyed-out in the UI rather than hidden completely.

    O(1) lookup via _pincode_to_zone index built when the zone list is cached.
    Previous implementation: O(n) loop over all zones per request.

    Returns:
        (None, None)        -> pincode not in any zone
        (zone_id, set())    -> zone found but no sellers declared
        (zone_id, set(ids)) -> zone found with sellers (includes unavailable sellers)
    """
    if not pincode:
        return None, None

    try:
        # Ensure cache and index are warm — fast no-op when already fresh
        await _fetch_all_zones()

        # O(1) dict lookup — replaces `for zone in zones: if pincode in zone.pincodes`
        zone = _pincode_to_zone.get(str(pincode))
        if zone is None:
            return None, None

        if zone.id is None:
            logger.warning("zone_seller_cache: zone has no id: %s", zone)
            return None, None

        # Return the full seller set — unavailable sellers are NOT subtracted here.
        # Use get_unavailable_seller_ids_for_pincode() to find the unavailable subset.
        seller_ids = set(await _get_sellers_for_zone(zone.id))
        return zone.id, seller_ids

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


async def get_seller_ids_for_zone_id(zone_id: int) -> Optional[Set[str]]:
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
        # Ensure cache and index are warm — fast no-op when already fresh
        await _fetch_all_zones()
        # O(1) dict lookup — replaces O(n) `for zone in zones: if pincode in zone.pincodes`
        return _pincode_to_zone.get(str(pincode))
    except Exception as exc:
        logger.error("zone_seller_cache: get_zone_for_pincode failed for %s: %s", pincode, exc, exc_info=True)
        return None


def invalidate_zone_cache(zone_id: Optional[int] = None) -> None:
    """
    Invalidate cache entries.
    Pass a zone_id to evict a specific zone, or None to clear everything.
    Call this from zone create/update/delete routes and when a seller updates their zones.
    Also clears the cached zone list and the O(1) pincode index so the next lookup
    fetches a fresh copy from the DB.
    """
    global _all_zones_cache, _all_zones_expiry, _pincode_to_zone
    # Always clear the zone list cache — a mutation invalidates the full list
    _all_zones_cache = None
    _all_zones_expiry = 0.0
    # Clear the O(1) pincode→zone index — it must be rebuilt from the fresh zone list
    _pincode_to_zone = {}
    if zone_id is not None:
        _zone_seller_cache.pop(zone_id, None)
    else:
        _zone_seller_cache.clear()


async def get_retail_seller_set(
    pincode: Optional[str],
    subtract_unavailable: bool = False,
) -> Tuple[Set[str], str, Optional[int]]:
    """
    Single authoritative entry point for resolving which sellers a RETAIL
    customer can see, given their pincode.

    Decision tree
    -------------
    pincode is None / empty
        -> ({super_admin_id}, "pan_india", None)
           No pincode yet — show SA catalog as the default.
           The frontend enforces the pincode gate (modal) and disables
           add-to-cart / checkout until a valid pincode is entered.
    pincode resolves to a hyperlocal zone
        -> (zone_sellers, "hyperlocal", zone_id)   hyperlocal — only sellers in that zone
    pincode provided but NOT in any zone
        -> ({super_admin_id}, "pan_india", None)  pan-india — SA products only (3PL)

    In every non-hyperlocal case, the customer sees the Super Admin (1P)
    catalog. Transactional actions are gated by the frontend.

    Parameters
    ----------
    pincode             : The customer's delivery pincode (may be None).
    subtract_unavailable: When True, removes sellers currently in a time-off
                          window from the returned set (use for recommendations
                          where greyed-out products should be hidden entirely;
                          for product listings use False so they show greyed-out).

    Returns
    -------
    (seller_id_set, fulfillment_type, zone_id)
        seller_id_set   : set of allowed seller ID strings.
        fulfillment_type: "hyperlocal" or "pan_india".
        zone_id         : int ID if in a hyperlocal zone, None for pan-india / unzoned.
    """
    if zone_id_and_sellers := (
        await get_zone_id_and_seller_ids_for_pincode(pincode) if pincode else (None, None)
    ):
        zone_id, seller_id_set = zone_id_and_sellers
    else:
        zone_id, seller_id_set = None, None

    if zone_id is not None:
        # ── Hyperlocal zone found ──────────────────────────────────────────
        if subtract_unavailable and seller_id_set:
            try:
                from app.routers.seller_availability import get_all_unavailable_seller_ids
                unavailable = await get_all_unavailable_seller_ids()
                if unavailable:
                    seller_id_set = seller_id_set - unavailable
            except Exception as exc:
                logger.warning("get_retail_seller_set: could not subtract unavailable sellers: %s", exc)
        return seller_id_set, "hyperlocal", zone_id

    # ── No pincode, unzoned pincode, or unserviceable pincode → SA only ───
    # All these cases show the Super Admin (pan-india) catalog.
    # The frontend is responsible for disabling add-to-cart when pincode
    # is absent or when the zone is not active.
    sa_id = await get_super_admin_seller_id()
    pan_india_set: Set[str] = {sa_id} if sa_id else set()
    return pan_india_set, "pan_india", None

