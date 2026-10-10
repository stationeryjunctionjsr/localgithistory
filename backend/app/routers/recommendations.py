from app.models.user import User
from typing import Dict, List
from app.models.schemas import RecommendationResponse, MessageResponse
import asyncio
import time as _time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from app.models.product import Product
from pydantic import BaseModel

class SlotMetrics(BaseModel):
    section_view: int = 0
    product_view: int = 0
    add_to_cart: int = 0

class RecommendationMetricsResponse(BaseModel):
    days: int
    section_views: int
    product_views: int
    add_to_carts: int
    by_slot: Dict[str, SlotMetrics] = {}

class EventTrackResponse(BaseModel):
    ok: bool = True


from app.repositories.recommendation_repository import recommendation_repository
from app.repositories.tracking_repository import tracking_repository
from app.repositories.user_repository import user_repository
from app.utils.auth import get_optional_user, require_super_admin
from app.utils.cache import cache
from app.utils.device import parse_device
from app.utils.logger import logger

# Avoid 307 redirect when clients call /api/recommendations without a trailing slash.
router = APIRouter(redirect_slashes=False)

# Lock to prevent cache stampede for guest recommendations
_guest_rec_lock = asyncio.Lock()

# Short-lived server-side cache for guest recommendations (same result for all guests, 300s TTL)
_guest_rec_cache: dict = {}
_GUEST_REC_TTL = 300.0  # seconds


class RecommendationEventBody(BaseModel):
    eventType: str  # 'section_view' | 'product_view' | 'add_to_cart'
    slot: str
    productId: Optional[str] = None
    productName: Optional[str] = None
    strategy: Optional[str] = None  # 'trending' | 'user_favorites' | 'explore' for bandit reward update


@router.get("", )
@router.get("/", )
async def get_recommendations(
    current_user: Optional[dict] = Depends(get_optional_user),
    pincode: Optional[str] = Query(None),
    category_tag: Optional[str] = Query(None, description="Filter recommendations to a specific category tag (e.g. 'Stationery'). Case-insensitive.")
):
    """
    Get recommendation components by segment. Auth optional (guests get Customer Favourites + Trending Now only).
    Pass ?categoryTag=Stationery to restrict all sections to products belonging to that tag's categories.
    """
    try:
        user_id = current_user.id if current_user else None
        role = None
        if current_user:
            role = (current_user.effective_role or current_user.role or "").strip()
            if role not in ("wholesaler", "customer"):
                role = "customer"

        # Resolve sellers for this request.
        # Rules:
        #   Wholesaler         → Super Admin products only
        #   Retail hyperlocal  → sellers in the pincode's zone
        #   Retail pan-india   → Super Admin products only  (pincode given but no zone)
        #   Guest / no pincode → no filter (show all)
        from app.repositories.zone_seller_cache import (
            get_retail_seller_set,
            get_super_admin_seller_id,
        )
        zone_id, seller_id_set = None, None

        if role == "wholesaler":
            sa_id = await get_super_admin_seller_id()
            seller_id_set = {sa_id} if sa_id else set()
            location_key = "wholesaler"
        else:
            # Retail customer or unauthenticated guest.
            # get_retail_seller_set() handles hyperlocal / pan-india / no-pincode internally.
            seller_id_set, location_key = await get_retail_seller_set(
                pincode, subtract_unavailable=True
            )

        # Normalise category_tag for consistent cache keying and lookup
        tag_key = (category_tag or "").strip().lower() or None

        # Guest path: serve from 300-second server-side cache (keyed by location + tag)
        if not user_id:
            now = _time.monotonic()
            guest_key = f"guest_{location_key}_{tag_key or 'all'}"
            entry = (_guest_rec_cache[guest_key] if guest_key in _guest_rec_cache else None)
            if entry and now < entry[1]:
                return entry[0]

            async with _guest_rec_lock:
                # Re-check after acquiring lock
                entry = (_guest_rec_cache[guest_key] if guest_key in _guest_rec_cache else None)
                if entry and now < entry[1]:
                    return entry[0]

                result = await recommendation_repository.get_recommendation_components(
                    user_id=None, role=None, seller_id_set=seller_id_set, category_tag=tag_key
                )
                _guest_rec_cache[guest_key] = (result, _time.monotonic() + _GUEST_REC_TTL)
                return result

        # For wholesalers, resolve their city from their profile address so we can
        # return city-scoped Customer Favourites and Business Favourites.
        city: Optional[str] = None
        if role == "wholesaler":
            try:
                user_doc = await user_repository.findById(user_id)
                if user_doc:
                    addr = user_doc.address
                    raw_city = addr.city or ""
                    
                    city = (raw_city or "").strip() or None
            except Exception:
                logger.warning("Could not resolve city for wholesaler %s", user_id, exc_info=True)

        # Authenticated user path: cache per-user (and per-city for wholesalers, and per-tag) for 180 seconds
        city_key = city or "all"
        user_cache_key = f"rec_{role}_{user_id}_{city_key}_{location_key}_{tag_key or 'all'}"
        cached_res = cache.get(user_cache_key)  # BUG-4 fix: use cache.get(), not cache[key]
        if cached_res:
            return cached_res

        result = await recommendation_repository.get_recommendation_components(
            user_id=user_id, role=role, city=city, seller_id_set=seller_id_set, category_tag=tag_key
        )
        cache.set(user_cache_key, result, ttl=180.0)
        return result
    except Exception as e:
        logger.error("get_recommendations failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/favourites")
async def get_favourites_page(
    type: str = "customer",
    state: Optional[str] = None,
    city: Optional[str] = None,
    category: Optional[str] = None,
    sub_category: Optional[str] = None,
    brand: Optional[str] = None,
    available: Optional[str] = None,  # "true" | "false"
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    days: int = 60,
    current_user: User = Depends(get_optional_user),
):
    """
    Full ranked favourites list for the wholesaler 'View All' pages.
    Requires a logged-in wholesaler. Returns products sorted by sales score
    (highest to lowest), plus available filter option lists.

    When `city` is not supplied, the wholesaler's profile city is used automatically.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    role = (current_user.effective_role or current_user.role or "").strip()
    if role != "wholesaler":
        raise HTTPException(status_code=403, detail="Wholesaler access only")

    user_id = current_user.id
    kind = "customer" if type == "customer" else "business"

    # Auto-resolve city from profile when not explicitly provided
    resolved_city = city
    if not resolved_city:
        try:
            user_doc = await user_repository.findById(user_id)
            if user_doc:
                addr = user_doc.address
                raw_city = addr.city or ""
                
                resolved_city = (raw_city or "").strip() or None
        except Exception:
            logger.warning("Could not resolve city for wholesaler %s", user_id)

    try:
        ranked_data = await recommendation_repository.get_favourites_ranked(
            kind=kind,
            days=days,
            state=state or None,
            city=resolved_city,
        )
    except Exception as e:
        logger.error("get_favourites_ranked failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")

    ranked_ids: list = ranked_data["ranked_ids"]  # [(pid, score), ...]
    all_states: list = ranked_data["states"]
    all_cities: list = ranked_data["cities"]

    # Fetch all active products once and build a lookup map
    from app.db.storage_factory import get_storage as _get_storage

    product_storage = _get_storage("products")
    all_products = await product_storage.findAll({"isActive": True})
    product_map: dict = {p.id: p for p in all_products if p.id}

    # Collect filter option lists from the full ranked set (before product-level filters)
    categories_seen: set = set()
    sub_categories_seen: set = set()
    brands_seen: set = set()
    for pid, _ in ranked_ids:
        p = (product_map[pid] if pid in product_map else None)
        if not p:
            continue
        if p.category:
            categories_seen.add(p.category)
        if p.sub_category:
            sub_categories_seen.add(p.sub_category)
        if p.brand:
            brands_seen.add(p.brand)

    # Apply product-level filters and build response
    products_out = []
    category_lower = category.strip().lower() if category and category.strip() else None
    sub_category_lower = sub_category.strip().lower() if sub_category and sub_category.strip() else None
    brand_lower = brand.strip().lower() if brand and brand.strip() else None
    want_available = None
    if available is not None:
        want_available = available.lower() == "true"

    for pid, _score in ranked_ids:
        p = (product_map[pid] if pid in product_map else None)
        if not p:
            continue
        # Product-level filters
        if category_lower and (p.category or "").lower() != category_lower:
            continue
        if sub_category_lower and (p.sub_category or "").lower() != sub_category_lower:
            continue
        if brand_lower and (p.brand or "").lower() != brand_lower:
            continue
        if want_available is not None:
            in_stock = (p.stock or 0) > 0
            if in_stock != want_available:
                continue
        price = p.price or 0
        if min_price is not None and price < min_price:
            continue
        if max_price is not None and price > max_price:
            continue

        # We no longer cast to dict. We return the strict Product model and let FastAPI's response_model strip fields if needed.
        # Wait, if we return Product, we can just append p.
        
        products_out.append(p)

    return {
        "products": products_out,
        "total": len(products_out),
        "cityName": resolved_city or "",
        "filters": {
            "categories": sorted(categories_seen),
            "subCategories": sorted(sub_categories_seen),
            "brands": sorted(brands_seen),
            "states": all_states,
            "cities": all_cities,
        },
    }


@router.get("/metrics")
async def get_recommendation_metrics(days: int = 30, current_user: User = Depends(require_super_admin)):
    """
    Return recommendation engagement metrics for the last N days.
    Use this to see if the section is viewed, and if product views / add-to-cart are healthy.
    Helps decide whether to tune the algorithm (e.g. change strategy_limits or engagement_weights).
    """
    from datetime import datetime, timedelta, timezone

    from app.db.storage_factory import get_storage

    storage = get_storage("activities")
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    section_views = 0
    product_views = 0
    add_to_carts = 0
    by_slot: dict = {}

    for action in ("recommendation_section_view", "recommendation_product_view", "recommendation_add_to_cart"):
        try:
            activities = await storage.findAll({"action": action})
            for doc in activities:
                created = doc.created_at or ""
                if created < cutoff:
                    continue
                meta_list = doc.meta or []
                slot = "unknown"
                for m in meta_list:
                    if m.key == "slot":
                        slot = m.value
                        break
                
                if slot not in by_slot:
                    by_slot[slot] = {"section_view": 0, "product_view": 0, "add_to_cart": 0}
                if action == "recommendation_section_view":
                    section_views += 1
                    by_slot[slot]["section_view"] += 1
                elif action == "recommendation_product_view":
                    product_views += 1
                    by_slot[slot]["product_view"] += 1
                else:
                    add_to_carts += 1
                    by_slot[slot]["add_to_cart"] += 1
        except Exception:
            logger.exception(f"Error processing metrics for action: {action}")
            continue

    return {
        "days": days,
        "section_views": section_views,
        "product_views": product_views,
        "add_to_carts": add_to_carts,
        "by_slot": by_slot,
    }


@router.post("/events", response_model=EventTrackResponse)
async def track_recommendation_event(
    body: RecommendationEventBody,
    request: Request,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """
    Track recommendation engagement for analytics.
    - section_view: user reached the recommendation section (e.g. scrolled into view).
    - product_view: user clicked/viewed a recommended product.
    - add_to_cart: user added a recommended product to cart.
    Stored in activities so you can measure: section views vs product views vs add-to-cart and tune the algorithm.
    """
    session_id = (request.headers["x-session-id"] if "x-session-id" in request.headers else None)
    if not session_id:
        raise HTTPException(status_code=400, detail="x-session-id header is required")
    if body.eventType not in ("section_view", "product_view", "add_to_cart"):
        raise HTTPException(status_code=400, detail="eventType must be section_view, product_view, or add_to_cart")
    action = f"recommendation_{body.eventType}"
    meta = {"slot": body.slot}
    if body.product_id:
        meta["productId"] = body.product_id
    if body.product_name:
        meta["productName"] = body.product_name
    device = parse_device(request, default_type="web")
    user_id = current_user.id if current_user else None
    await tracking_repository.trackRecommendationEvent(
        user_id=str(user_id) if user_id else None,
        session_id=session_id,
        action=action,
        product_id=body.product_id if body.product_id else None,
        product_name=body.product_name if body.product_name else None,
        source=body.slot,
    )
    # Update Multi-Armed Bandit rewards (all slots participate); use slot as strategy when strategy not provided
    if body.eventType in ("product_view", "add_to_cart"):
        from app.repositories.recommendation_repository import BANDIT_STRATEGIES, get_recommendation_config

        strategy = body.strategy or body.slot
        if strategy in BANDIT_STRATEGIES:
            config = get_recommendation_config()
            section_wise = config.section_wise_weights
            engagement = config.engagement_weights
            section_weights = section_wise[body.slot] if body.slot in section_wise else engagement
            
            if body.eventType == "add_to_cart":
                weight = section_weights.add_to_cart
            else:
                weight = section_weights.product_view
                
            await recommendation_repository.append_reward(user_id, strategy, float(weight), body.slot)
    return {"ok": True}
