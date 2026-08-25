import asyncio
import json
import random
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from app.db.storage_factory import get_storage
from app.repositories.tracking_repository import tracking_repository
from app.utils.logger import logger

# Default config path (same dir as other data)
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_CONFIG_PATH = _DATA_DIR / "recommendationConfig.json"
_REWARDS_PATH = _DATA_DIR / "recommendationRewards.json"
_TRENDING_CACHE_PATH = _DATA_DIR / "trending_cache.json"
_CUSTOMER_FAVOURITES_CACHE_PATH = _DATA_DIR / "customer_favourites_cache.json"
_BUSINESS_FAVOURITES_CACHE_PATH = _DATA_DIR / "business_favourites_cache.json"

# ------- Lightweight config / file cache (avoids repeated disk I/O) -------
_config_cache: Optional[Dict] = None
_config_cache_ts: float = 0.0
_CONFIG_CACHE_TTL = 60.0  # seconds – config rarely changes

_trending_cache_store: Optional[Dict] = None
_trending_cache_ts: float = 0.0
_CF_CACHE_STORE: Optional[Dict] = None
_CF_CACHE_TS: float = 0.0
_BF_CACHE_STORE: Optional[Dict] = None
_BF_CACHE_TS: float = 0.0
_FILE_CACHE_TTL = 30.0  # seconds for JSON result caches

# Arms of the bandit = recommendation slots (all slots participate in bandit)
BANDIT_STRATEGIES = [
    "customer_favourites",
    "trending_now",
    "explore",
    "wholesaler_favourites",
    "business_favourites",
]


def _load_config() -> Dict:
    global _config_cache, _config_cache_ts
    now = time.monotonic()
    if _config_cache is not None and (now - _config_cache_ts) < _CONFIG_CACHE_TTL:
        return _config_cache
    _defaults = {
        "engagement_days": 30,
        "engagement_weights": {"product_view": 1, "add_to_cart": 3},
        "strategy_limits": {"trending": 10, "user_favorites": 5, "explore": 5},
        "total_limit": 20,
        "bandit": {"epsilon": 0.2, "personal_threshold": 10},
        "customer_favourites_weights": {"frequency": 0.7, "quantity": 0.3},
        "business_favourites_weights": {"frequency": 0.7, "quantity": 0.3},
        "segments": {
            "guest": {"trending_now_days": 14, "customer_favourites_days": 60, "explore_available": False},
            "retail": {
                "trending_now_days": 14,
                "customer_favourites_days": 60,
                "explore_days": 60,
                "exclude_user_purchases_days": 60,
                "explore_available": True,
            },
            "wholesaler": {
                "trending_now_days": 14,
                "customer_favourites_days": 60,
                "wholesaler_favourites_days": 5,
                "business_favourites_days": 60,
                "explore_days": 60,
                "exclude_user_purchases_days": 60,
                "explore_available": True,
            },
        },
    }
    # JSON config file read is disabled — Oracle is the only supported backend.
    # File-based recommendationConfig.json is no longer used.
    # try:
    #     if _CONFIG_PATH.exists():
    #         loaded = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    #         _config_cache = loaded
    #         _config_cache_ts = now
    #         return loaded
    # except Exception:
    #     logger.exception("Error loading recommendation config from file")
    _config_cache = _defaults
    _config_cache_ts = now
    return _defaults


def _segment_config(segment: str) -> Dict:
    config = _load_config()
    segments = config.get("segments") or {}
    return segments.get(segment) or {}


def _get_favourites_weights(kind: str) -> Tuple[float, float]:
    """
    Get (frequency_weight, quantity_weight) for Customer or Business Favourites scoring.
    kind: 'customer_favourites' | 'business_favourites'
    Score = frequency_weight * order_count + quantity_weight * quantity.
    Defaults: (0.7, 0.3).
    """
    config = _load_config()
    key = "customer_favourites_weights" if kind == "customer_favourites" else "business_favourites_weights"
    weights = config.get(key) or {}
    w_freq = float(weights.get("frequency", 0.7))
    w_qty = float(weights.get("quantity", 0.3))
    return (w_freq, w_qty)


def _strategy_to_key(strategy: str) -> str:
    """Map bandit strategy (slot) name to response key."""
    return {
        "new_arrivals": "newArrivals",
        "customer_favourites": "customerFavourites",
        "trending_now": "trendingNow",
        "explore": "explore",
        "wholesaler_favourites": "wholesalerFavourites",
        "business_favourites": "businessFavourites",
    }.get(strategy, "customerFavourites")


def get_recommendation_config() -> Dict:
    """Expose config for routers (e.g. bandit reward weights)."""
    return _load_config()


def _parse_order_date(order: Dict) -> Optional[datetime]:
    raw = order.get("createdAt")
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _read_trending_cache() -> Dict:
    """Read precomputed trending list (written by scheduled job) with short-lived in-memory TTL."""
    global _trending_cache_store, _trending_cache_ts
    now = time.monotonic()
    if _trending_cache_store is not None and (now - _trending_cache_ts) < _FILE_CACHE_TTL:
        return _trending_cache_store
    try:
        if _TRENDING_CACHE_PATH.exists():
            data = json.loads(_TRENDING_CACHE_PATH.read_text(encoding="utf-8"))
            _trending_cache_store = data
            _trending_cache_ts = now
            return data
    except Exception:
        logger.exception("Error reading trending cache")
    return {}


def _write_trending_cache(data: Dict) -> None:
    """Write trending cache — disabled: JSON file cache is no longer used (Oracle is the only backend)."""
    global _trending_cache_store, _trending_cache_ts
    # _DATA_DIR.mkdir(parents=True, exist_ok=True)
    # _TRENDING_CACHE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    _trending_cache_store = data
    _trending_cache_ts = time.monotonic()


def _read_customer_favourites_cache() -> Dict:
    """Read precomputed Customer Favourites list with short-lived in-memory TTL."""
    global _CF_CACHE_STORE, _CF_CACHE_TS
    now = time.monotonic()
    if _CF_CACHE_STORE is not None and (now - _CF_CACHE_TS) < _FILE_CACHE_TTL:
        return _CF_CACHE_STORE
    try:
        if _CUSTOMER_FAVOURITES_CACHE_PATH.exists():
            data = json.loads(_CUSTOMER_FAVOURITES_CACHE_PATH.read_text(encoding="utf-8"))
            _CF_CACHE_STORE = data
            _CF_CACHE_TS = now
            return data
    except Exception:
        logger.exception("Error reading customer favourites cache")
    return {}


def _write_customer_favourites_cache(data: Dict) -> None:
    """Write Customer Favourites cache — disabled: JSON file cache is no longer used (Oracle is the only backend)."""
    global _CF_CACHE_STORE, _CF_CACHE_TS
    # _DATA_DIR.mkdir(parents=True, exist_ok=True)
    # _CUSTOMER_FAVOURITES_CACHE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    _CF_CACHE_STORE = data
    _CF_CACHE_TS = time.monotonic()


def _read_business_favourites_cache() -> Dict:
    global _BF_CACHE_STORE, _BF_CACHE_TS
    now = time.monotonic()
    if _BF_CACHE_STORE is not None and (now - _BF_CACHE_TS) < _FILE_CACHE_TTL:
        return _BF_CACHE_STORE
    try:
        if _BUSINESS_FAVOURITES_CACHE_PATH.exists():
            data = json.loads(_BUSINESS_FAVOURITES_CACHE_PATH.read_text(encoding="utf-8"))
            _BF_CACHE_STORE = data
            _BF_CACHE_TS = now
            return data
    except Exception:
        logger.exception("Error reading business favourites cache")
    return {}


def _write_business_favourites_cache(data: Dict) -> None:
    """Write Business Favourites cache — disabled: JSON file cache is no longer used (Oracle is the only backend)."""
    global _BF_CACHE_STORE, _BF_CACHE_TS
    # _DATA_DIR.mkdir(parents=True, exist_ok=True)
    # _BUSINESS_FAVOURITES_CACHE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    _BF_CACHE_STORE = data
    _BF_CACHE_TS = time.monotonic()


class RecommendationRepository:
    def __init__(self):
        self.order_storage = get_storage("orders")
        self.product_storage = get_storage("products")
        self.activity_storage = get_storage("activities")
        self.user_storage = get_storage("users")
        self.cart_storage = get_storage("carts")
        self._rewards_lock = asyncio.Lock()

    async def _get_retail_customer_ids(self) -> set:
        """User IDs with role customer (retail)."""
        users = await self.user_storage.findAll()
        return {
            u.get("_id")
            for u in users
            if u.get("_id") and (u.get("role") == "customer" or u.get("effectiveRole") == "customer")
        }

    async def _get_user_purchased_product_ids(self, user_id: str, days: int) -> set:
        """Products the user purchased in the last `days` days."""
        # Use database-side filtering to only fetch relevant orders
        query = {"user": user_id}
        orders = await self.order_storage.findAll(query)

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        out = set()
        for order in orders:
            dt = _parse_order_date(order)
            if not dt or dt < cutoff:
                continue
            for item in order.get("items", []):
                pid = item.get("product") or item.get("productId")
                if pid:
                    out.add(pid)
        return out

    async def _get_user_cart_product_ids(self, user_id: str) -> set:
        """Products currently in the user's cart."""
        cart = await self.cart_storage.findOne({"user": user_id})
        if not cart:
            return set()
        out = set()
        for item in cart.get("items", []):
            pid = item.get("product") or item.get("productId")
            if pid:
                out.add(pid)
        return out

    async def _get_retail_bestsellers_or_trending(
        self, days: int, limit: int, exclude_product_ids: Optional[set] = None
    ) -> List[str]:
        """Bestsellers (or trending) from retail customer orders only, last `days` days. Optionally exclude product IDs."""
        retail_ids = await self._get_retail_customer_ids()
        if not retail_ids:
            return []
        exclude = exclude_product_ids or set()
        orders = await self.order_storage.findAll()
        product_counts: Dict[str, int] = {}
        for order in orders:
            if order.get("user") not in retail_ids:
                continue
            dt = _parse_order_date(order)
            if not dt:
                continue
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            if dt < cutoff:
                continue
            for item in order.get("items", []):
                pid = item.get("product") or item.get("productId")
                if pid and pid not in exclude:
                    product_counts[pid] = product_counts.get(pid, 0) + item.get("quantity", 1)
        sorted_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [pid for pid, _ in sorted_products]

    def _order_segment_prefix(self, segment: str) -> Optional[str]:
        """Order number prefix for segment: customer -> ORDER-RT, wholesaler -> ORDER-WH."""
        if segment == "customer":
            return "ORDER-RT-"
        if segment == "wholesaler":
            return "ORDER-WH-"
        return None

    async def get_trending_by_conversion(
        self,
        segment: str,
        days: int = 7,
        min_search_count: int = 10,
        top_per_subcategory: int = 5,
        exclude_product_ids: Optional[Set[str]] = None,
        use_cache: bool = True,
    ) -> List[str]:
        """
        Trending Now: search-to-sale journey only. Per subcategory, top products by
        conversion_rate = converted_sales_count / search_count (last `days`).
        - search_count = number of searches that included this product (segment).
        - converted_sales_count = number of orders containing this product where the same
          user/session had searched for this product within 7 days before the order (search then sold within 7 days).
        - Skip if search_count < min_search_count.
        - Sort by conversion_rate descending, take top_per_subcategory per subcategory.
        If use_cache=True, returns from cache when available (written by scheduled job).
        """
        if use_cache:
            cached = _read_trending_cache()
            seg_data = cached.get(segment, {})
            ids = seg_data.get("product_ids")
            if ids is not None and isinstance(ids, list):
                exclude = exclude_product_ids or set()
                return [x for x in ids if x not in exclude]  # cache is already in descending rank order
        prefix = self._order_segment_prefix(segment)
        if not prefix:
            return []
        exclude = exclude_product_ids or set()
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Search events (last 7 days) with productIds for linking
        searches = await tracking_repository.get_searches_with_products(days, segment)

        # Orders in last 7 days (segment)
        # Use database-side filtering for date and possibly segment if supported
        # Note: OracleOrderDAO supports filtering by user, but maybe not by date in a generic way yet.
        # But we can at least pass an empty query to trigger the optimized findAll.
        orders = await self.order_storage.findAll()
        converted_sales_count: Dict[str, int] = {}
        for order in orders:
            # Filtering still needed in Python if DAO doesn't support date range yet,
            # but at least we've optimized the underlying query execution.
            if not (order.get("orderNumber") or str(order.get("orderNumber", "")).startswith(prefix)):
                continue
            order_dt = _parse_order_date(order)
            if not order_dt or order_dt < cutoff:
                continue
            if order.get("status") == "cancelled":
                continue
            order_user = order.get("user")
            order_session = order.get("sessionId")
            order_start = order_dt - timedelta(days=days)
            pids_in_order = set()
            for item in order.get("items", []):
                pid = item.get("product") or item.get("productId")
                if pid:
                    pids_in_order.add(pid)
            for pid in pids_in_order:
                # Count only if this order is linked to a search for P within 7 days before order
                linked = False
                for s in searches:
                    if pid not in (s.get("productIds") or []):
                        continue
                    st = s.get("timestamp")
                    if not st:
                        continue
                    if st > order_dt or st < order_start:
                        continue
                    if order_user and s.get("userId") == order_user:
                        linked = True
                        break
                    if order_session and s.get("sessionId") == order_session:
                        linked = True
                        break
                if linked:
                    converted_sales_count[pid] = converted_sales_count.get(pid, 0) + 1

        # Search counts per product (segment)
        search_count = await tracking_repository.get_search_counts_by_product(days, segment)

        # Products and subcategories - ONLY fetch active products
        all_products = await self.product_storage.findAll({"isActive": True})
        pid_to_subcat: Dict[str, str] = {}
        for p in all_products:
            pid = p.get("_id")
            if pid:
                pid_to_subcat[pid] = p.get("subCategory") or "None"

        # Build candidates: (pid, subcat, conversion_rate); skip if search_count < min_search_count
        candidates: List[Tuple[str, str, float]] = []
        for pid, sc in search_count.items():
            if sc < min_search_count or pid in exclude:
                continue
            subcat = pid_to_subcat.get(pid, "None")
            converted = converted_sales_count.get(pid, 0)
            rate = converted / sc if sc else 0.0
            candidates.append((pid, subcat, rate))

        # Include products that have sales but no search data? No - we require search_count >= 10.

        # Group by subcategory, sort by conversion desc, take top_per_subcategory per subcategory
        by_subcat: Dict[str, List[Tuple[str, float]]] = {}
        for pid, subcat, rate in candidates:
            by_subcat.setdefault(subcat, []).append((pid, rate))
        # Flatten to (pid, rate), sort by rate descending so rank 1 (highest) is first
        flat: List[Tuple[str, float]] = []
        for subcat in sorted(by_subcat.keys()):
            sorted_pids = sorted(by_subcat[subcat], key=lambda x: x[1], reverse=True)[:top_per_subcategory]
            flat.extend(sorted_pids)
        flat.sort(key=lambda x: x[1], reverse=True)
        return [pid for pid, _ in flat]

    async def get_trending_product_ids(self, segment: str) -> Set[str]:
        """Set of product IDs that are Trending Now for this segment (for tagging in catalog)."""
        ids = await self.get_trending_by_conversion(
            segment, days=7, min_search_count=10, top_per_subcategory=5, exclude_product_ids=set()
        )
        return set(ids)

    async def get_customer_favourites_by_subcategory(self, days: int = 60, city: Optional[str] = None) -> List[str]:
        """
        Tag-based Customer Favourites: top 1 product per subcategory by weighted score.
        Score = frequency_weight * order_count + quantity_weight * quantity (from config).
        Frequency = number of orders containing the product; quantity = total units.
        Retail orders only, last `days` days. Returns list in descending score order (best first).
        If `city` is provided (non-empty), only orders whose shippingAddress.city matches
        (case-insensitive) are counted. The all-orders logic is preserved when city is None/empty.
        """
        w_freq, w_qty = _get_favourites_weights("customer_favourites")
        retail_ids = await self._get_retail_customer_ids()
        if not retail_ids:
            return []
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        city_filter = city.strip().lower() if city and city.strip() else None
        orders = await self.order_storage.findAll()
        all_products = await self.product_storage.findAll()
        pid_to_subcat: Dict[str, str] = {
            p.get("_id"): (p.get("subCategory") or "None") for p in all_products if p.get("_id")
        }
        segment_order_count: Dict[str, Dict[str, int]] = {}
        segment_quantity: Dict[str, Dict[str, int]] = {}
        for order in orders:
            if order.get("user") not in retail_ids:
                continue
            if not (order.get("orderNumber") or str(order.get("orderNumber", "")).startswith("ORDER-RT-")):
                continue
            dt = _parse_order_date(order)
            if not dt or dt < cutoff:
                continue
            if order.get("status") == "cancelled":
                continue
            # City filter: match against the order's delivery city (shippingAddress.city)
            if city_filter:
                order_city = (order.get("shippingAddress") or {}).get("city", "")
                if not order_city or order_city.strip().lower() != city_filter:
                    continue
            pids_in_order = set()
            for item in order.get("items", []):
                pid = item.get("product") or item.get("productId")
                if not pid:
                    continue
                subcat = pid_to_subcat.get(pid, "None")
                if subcat not in segment_order_count:
                    segment_order_count[subcat] = {}
                    segment_quantity[subcat] = {}
                segment_quantity[subcat][pid] = segment_quantity[subcat].get(pid, 0) + item.get("quantity", 1)
                pids_in_order.add((subcat, pid))
            for subcat, pid in pids_in_order:
                segment_order_count[subcat][pid] = segment_order_count[subcat].get(pid, 0) + 1
        # Top 1 per subcategory by weighted score; then sort by score descending
        top_per_subcat: List[Tuple[str, float]] = []  # (pid, score)
        for subcat in segment_order_count:
            candidates = [
                (pid, segment_order_count[subcat][pid], segment_quantity[subcat].get(pid, 0))
                for pid in segment_order_count[subcat]
                if segment_quantity[subcat].get(pid, 0) > 1
            ]
            if not candidates:
                continue

            def _score(x):  # (pid, order_count, quantity)
                return w_freq * x[1] + w_qty * x[2]

            top = max(candidates, key=_score)
            top_per_subcat.append((top[0], _score(top)))
        top_per_subcat.sort(key=lambda x: x[1], reverse=True)
        return [pid for pid, _ in top_per_subcat]

    async def get_customer_favourites_product_ids(self) -> Set[str]:
        """Set of product IDs that are Customer Favourites (top 1 per subcategory, retail, 60d). For tagging in catalog. Reads cache when present."""
        cached = _read_customer_favourites_cache()
        ids = cached.get("product_ids")
        if ids is not None and isinstance(ids, list):
            return set(ids)
        ids = await self.get_customer_favourites_by_subcategory(days=60)
        return set(ids)

    async def compute_customer_favourites_for_cache(self, days: int = 60) -> Dict:
        """Compute Customer Favourites (top 1 per subcategory by quantity+frequency, retail, 60d) for the job."""
        ids = await self.get_customer_favourites_by_subcategory(days=days)
        return {
            "product_ids": ids,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def get_business_favourites_by_subcategory(self, days: int = 60, city: Optional[str] = None) -> List[str]:
        """
        Business Favourites: top 1 product per subcategory by weighted score from
        wholesaler orders (ORDER-WH-) only, last `days`.
        Score = frequency_weight * order_count + quantity_weight * quantity (from config).
        Returns list in descending score order.
        If `city` is provided (non-empty), only orders whose shippingAddress.city matches
        (case-insensitive) are counted. The all-orders logic is preserved when city is None/empty.
        """
        w_freq, w_qty = _get_favourites_weights("business_favourites")
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        city_filter = city.strip().lower() if city and city.strip() else None
        orders = await self.order_storage.findAll()
        all_products = await self.product_storage.findAll()
        pid_to_subcat: Dict[str, str] = {
            p.get("_id"): (p.get("subCategory") or "None") for p in all_products if p.get("_id")
        }
        segment_order_count: Dict[str, Dict[str, int]] = {}
        segment_quantity: Dict[str, Dict[str, int]] = {}
        for order in orders:
            if not (order.get("orderNumber") or str(order.get("orderNumber", "")).startswith("ORDER-WH-")):
                continue
            dt = _parse_order_date(order)
            if not dt or dt < cutoff:
                continue
            if order.get("status") == "cancelled":
                continue
            # City filter: match against the order's delivery city (shippingAddress.city)
            if city_filter:
                order_city = (order.get("shippingAddress") or {}).get("city", "")
                if not order_city or order_city.strip().lower() != city_filter:
                    continue
            pids_in_order = set()
            for item in order.get("items", []):
                pid = item.get("product") or item.get("productId")
                if not pid:
                    continue
                subcat = pid_to_subcat.get(pid, "None")
                if subcat not in segment_order_count:
                    segment_order_count[subcat] = {}
                    segment_quantity[subcat] = {}
                segment_quantity[subcat][pid] = segment_quantity[subcat].get(pid, 0) + item.get("quantity", 1)
                pids_in_order.add((subcat, pid))
            for subcat, pid in pids_in_order:
                segment_order_count[subcat][pid] = segment_order_count[subcat].get(pid, 0) + 1
        top_per_subcat: List[Tuple[str, float]] = []
        for subcat in segment_order_count:
            candidates = [
                (pid, segment_order_count[subcat][pid], segment_quantity[subcat].get(pid, 0))
                for pid in segment_order_count[subcat]
                if segment_quantity[subcat].get(pid, 0) > 1
            ]
            if not candidates:
                continue

            def _score(x):
                return w_freq * x[1] + w_qty * x[2]

            top = max(candidates, key=_score)
            top_per_subcat.append((top[0], _score(top)))
        top_per_subcat.sort(key=lambda x: x[1], reverse=True)
        return [pid for pid, _ in top_per_subcat]

    async def get_business_favourites_product_ids(self) -> Set[str]:
        """Set of product IDs that are Business Favourites (for tagging). Reads cache when present."""
        cached = _read_business_favourites_cache()
        ids = cached.get("product_ids")
        if ids is not None and isinstance(ids, list):
            return set(ids)
        ids = await self.get_business_favourites_by_subcategory(days=60)
        return set(ids)

    async def compute_business_favourites_for_cache(self, days: int = 60) -> Dict:
        """Compute Business Favourites (top 1 per subcategory by quantity+frequency, wholesaler orders, 60d) for the job."""
        ids = await self.get_business_favourites_by_subcategory(days=days)
        return {
            "product_ids": ids,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def get_favourites_ranked(
        self,
        kind: str = "customer",
        days: int = 60,
        state: Optional[str] = None,
        city: Optional[str] = None,
    ) -> Dict:
        """
        Return ALL products ranked by weighted sales score (highest → lowest).
        Unlike get_customer/business_favourites_by_subcategory, this does NOT limit to
        top-1 per subcategory — it returns every product that appears in matching orders.

        kind: 'customer' (retail ORDER-RT- orders) | 'business' (wholesaler ORDER-WH- orders)
        state/city: optional case-insensitive filters on shippingAddress.state / .city

        Returns:
          {
            "ranked_ids": [(product_id, score), ...],   # sorted descending
            "states": ["Maharashtra", ...],              # distinct states from matching orders
            "cities": ["Mumbai", ...],                   # distinct cities from matching orders
          }
        """
        if kind == "customer":
            w_freq, w_qty = _get_favourites_weights("customer_favourites")
            retail_ids = await self._get_retail_customer_ids()
        else:
            w_freq, w_qty = _get_favourites_weights("business_favourites")
            retail_ids = None  # business: no user-role filter, rely on order number prefix

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        state_filter = state.strip().lower() if state and state.strip() else None
        city_filter = city.strip().lower() if city and city.strip() else None

        order_count: Dict[str, int] = {}
        quantity_map: Dict[str, int] = {}
        states_seen: set = set()
        cities_seen: set = set()

        orders = await self.order_storage.findAll()
        for order in orders:
            # Role / type filter
            order_num = order.get("orderNumber") or ""
            if kind == "customer":
                if retail_ids and order.get("user") not in retail_ids:
                    continue
                if not order_num.startswith("ORDER-RT-"):
                    continue
            else:
                if not order_num.startswith("ORDER-WH-"):
                    continue

            dt = _parse_order_date(order)
            if not dt or dt < cutoff:
                continue
            if order.get("status") == "cancelled":
                continue

            shipping = order.get("shippingAddress") or {}
            order_state = (shipping.get("state") or "").strip()
            order_city = (shipping.get("city") or "").strip()

            # State / city filter
            if state_filter and order_state.lower() != state_filter:
                continue
            if city_filter and order_city.lower() != city_filter:
                continue

            # Collect geo values for filter options
            if order_state:
                states_seen.add(order_state)
            if order_city:
                cities_seen.add(order_city)

            pids_in_order: set = set()
            for item in order.get("items", []):
                pid = item.get("product") or item.get("productId")
                if not pid:
                    continue
                quantity_map[pid] = quantity_map.get(pid, 0) + item.get("quantity", 1)
                pids_in_order.add(pid)
            for pid in pids_in_order:
                order_count[pid] = order_count.get(pid, 0) + 1

        # Score and rank
        ranked = sorted(
            [(pid, w_freq * order_count[pid] + w_qty * quantity_map.get(pid, 0)) for pid in order_count],
            key=lambda x: x[1],
            reverse=True,
        )

        return {
            "ranked_ids": ranked,
            "states": sorted(states_seen),
            "cities": sorted(cities_seen),
        }

    async def get_new_arrivals(self, user_id: Optional[str], role: Optional[str], limit: int = 10) -> List[str]:
        """New Arrivals: products created in last 30 days. For retail, exclude products user already bought (any time)."""
        _load_config()
        days_new = 30  # same as add_dynamic_tags "new" tag
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_new)
        all_products = await self.product_storage.findAll()
        user_ordered: Set[str] = set()
        if user_id:
            orders = await self.order_storage.findAll()
            for o in orders:
                if o.get("user") != user_id:
                    continue
                for item in o.get("items", []):
                    pid = item.get("product") or item.get("productId")
                    if pid:
                        user_ordered.add(pid)
        candidates: List[Tuple[str, Optional[datetime]]] = []
        for p in all_products:
            pid = p.get("_id")
            if not pid or pid in user_ordered:
                continue
            created = _parse_order_date({"createdAt": p.get("createdAt")}) if p.get("createdAt") else None
            if created and created >= cutoff:
                candidates.append((pid, created))
        candidates.sort(key=lambda x: x[1] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        return [pid for pid, _ in candidates[:limit]]

    def _load_rewards(self) -> Dict:
        # Rewards are stored in-memory only (JSON file storage disabled).
        # try:
        #     if _REWARDS_PATH.exists():
        #         return json.loads(_REWARDS_PATH.read_text(encoding="utf-8"))
        # except Exception:
        #     logger.exception("Error loading rewards from file")
        return {"global": {s: [] for s in BANDIT_STRATEGIES}, "users": {}}

    def _save_rewards(self, data: Dict) -> None:
        # Rewards file write disabled — Oracle is the only supported backend.
        # _REWARDS_PATH.parent.mkdir(parents=True, exist_ok=True)
        # _REWARDS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
        pass  # In-memory only; rewards reset on restart.

    async def append_reward(self, user_id: Optional[str], strategy: str, reward: float, slot: str = "") -> None:
        """Append a reward to Personal (if user_id) and Global matrices for the given strategy (arm)."""
        if strategy not in BANDIT_STRATEGIES:
            return
        config = _load_config()
        bandit_cfg = config.get("bandit", {})
        max_user = bandit_cfg.get("max_rewards_per_user_strategy", 500)
        max_global = bandit_cfg.get("max_rewards_per_global_strategy", 10000)
        async with self._rewards_lock:
            data = self._load_rewards()
            # Global
            data.setdefault("global", {s: [] for s in BANDIT_STRATEGIES})
            data["global"].setdefault(strategy, [])
            data["global"][strategy].append(reward)
            if len(data["global"][strategy]) > max_global:
                data["global"][strategy] = data["global"][strategy][-max_global:]
            # Personal
            if user_id:
                data.setdefault("users", {})
                data["users"].setdefault(user_id, {s: [] for s in BANDIT_STRATEGIES})
                data["users"][user_id].setdefault(strategy, [])
                data["users"][user_id][strategy].append(reward)
                if len(data["users"][user_id][strategy]) > max_user:
                    data["users"][user_id][strategy] = data["users"][user_id][strategy][-max_user:]
            self._save_rewards(data)

    def _average_rewards(
        self, rewards_by_strategy: Dict[str, List[float]], strategies: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """Compute average reward per strategy (arm). If strategies given, only those."""
        strategies = strategies or BANDIT_STRATEGIES
        out = {}
        for s in strategies:
            lst = rewards_by_strategy.get(s) or []
            out[s] = sum(lst) / len(lst) if lst else 0.0
        return out

    def _total_personal_rewards(
        self, rewards_by_strategy: Dict[str, List[float]], strategies: Optional[List[str]] = None
    ) -> int:
        strategies = strategies or BANDIT_STRATEGIES
        return sum(len(rewards_by_strategy.get(s) or []) for s in strategies)

    async def get_arm_order_epsilon_greedy(
        self, user_id: Optional[str], applicable_strategies: Optional[List[str]] = None
    ) -> List[str]:
        """
        Epsilon-greedy: with prob epsilon explore (random order), else exploit (best arms first).
        Use Personal rewards if user has enough data (>= personal_threshold), else Global.
        applicable_strategies: only these arms are considered and returned (e.g. segment's slots).
        For guest (user_id None), uses global rewards only.
        """
        strategies = applicable_strategies or BANDIT_STRATEGIES

        # Bandit mechanism disabled as per request
        return list(strategies)

        config = _load_config()
        bandit_cfg = config.get("bandit", {})
        epsilon = bandit_cfg.get("epsilon", 0.2)
        personal_threshold = bandit_cfg.get("personal_threshold", 10)
        async with self._rewards_lock:
            data = self._load_rewards()
        global_rewards = data.get("global", {})
        for s in strategies:
            global_rewards.setdefault(s, [])
        user_rewards = (
            (data.get("users") or {}).get(user_id) or {s: [] for s in BANDIT_STRATEGIES}
            if user_id
            else {s: [] for s in strategies}
        )
        personal_total = self._total_personal_rewards(user_rewards, strategies)
        use_personal = user_id and personal_total >= personal_threshold
        rewards_dict = user_rewards if use_personal else global_rewards
        avg = self._average_rewards(rewards_dict, strategies)
        if random.random() < epsilon:
            order = list(strategies)
            random.shuffle(order)
            return order
        return sorted(strategies, key=lambda s: avg.get(s, 0.0), reverse=True)

    async def get_most_bought_by_wholesalers(self, user_id: str, limit: int = 10, days: int = 5) -> List[str]:
        """Products most frequently bought by other wholesalers. Used only when caller is wholesaler."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        users = await self.user_storage.findAll()
        wholesaler_ids = {u.get("_id") for u in users if u.get("role") == "wholesaler" and u.get("_id") != user_id}
        if not wholesaler_ids:
            return []
        orders = await self.order_storage.findAll()
        product_counts: Dict[str, int] = {}
        for order in orders:
            if order.get("user") not in wholesaler_ids:
                continue
            dt = _parse_order_date(order)
            if not dt or dt < cutoff:
                continue
            for item in order.get("items", []):
                pid = item.get("product") or item.get("productId")
                if pid:
                    product_counts[pid] = product_counts.get(pid, 0) + item.get("quantity", 1)
        sorted_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [pid for pid, _ in sorted_products]

    async def get_most_bought_by_user(self, user_id: str, limit: int = 5, days: int = 60) -> List[str]:
        """Top products bought by same user in last `days` days (for wholesaler 'your favourites')."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        orders = await self.order_storage.findAll()
        product_counts: Dict[str, int] = {}
        for order in orders:
            if order.get("user") != user_id:
                continue
            dt = _parse_order_date(order)
            if not dt or dt < cutoff:
                continue
            for item in order.get("items", []):
                pid = item.get("product") or item.get("productId")
                if pid:
                    product_counts[pid] = product_counts.get(pid, 0) + item.get("quantity", 1)
        sorted_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [pid for pid, _ in sorted_products]

    async def get_best_selling_from_least_bought_categories(
        self, user_id: str, limit: int = 5, days: int = 60
    ) -> List[str]:
        """Best selling products from categories this user bought least from (Explore – based on logged-in user orders)."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        # Fetch orders and products once each (avoids duplicate full-table scans)
        orders, products = await asyncio.gather(
            self.order_storage.findAll(),
            self.product_storage.findAll(),
        )
        # Build product lookup: id -> product
        product_by_id: Dict[str, Dict] = {p.get("_id"): p for p in products if p.get("_id")}

        user_product_ids: set = set()
        for o in orders:
            if o.get("user") != user_id:
                continue
            dt = _parse_order_date(o)
            if not dt or dt < cutoff:
                continue
            for item in o.get("items", []):
                product_id = item.get("product") or item.get("productId")
                if product_id:
                    user_product_ids.add(product_id)

        # Count categories from products this user purchased
        category_counts: Dict[str, int] = {}
        for pid in user_product_ids:
            p = product_by_id.get(pid)
            if p:
                cat = p.get("category")
                if cat:
                    category_counts[cat] = category_counts.get(cat, 0) + 1

        # Find categories with least purchases (at least 1 purchase)
        categories_with_purchases = [
            category for category, count in sorted(category_counts.items(), key=lambda x: x[1]) if count > 0
        ][:5]

        # Get best selling products from these categories using the already-loaded orders
        category_product_sales: Dict[str, Dict[str, int]] = {}
        cat_set = set(categories_with_purchases)
        for order in orders:
            for item in order.get("items", []):
                product_id = item.get("product") or item.get("productId")
                if not product_id:
                    continue
                p = product_by_id.get(product_id)
                if not p:
                    continue
                category = p.get("category")
                if category not in cat_set:
                    continue
                quantity = item.get("quantity", 1)
                category_product_sales.setdefault(category, {})[product_id] = (
                    category_product_sales[category].get(product_id, 0) + quantity
                )

        # Get top 5 products from least bought categories
        recommended_product_ids = []
        for category in categories_with_purchases:
            if category in category_product_sales:
                top_products = sorted(category_product_sales[category].items(), key=lambda x: x[1], reverse=True)[:1]
                recommended_product_ids.extend([pid for pid, _ in top_products])

        return recommended_product_ids[:limit]

    def _parse_created_at(self, doc: Dict) -> Optional[datetime]:
        raw = doc.get("createdAt")
        if not raw:
            return None
        try:
            return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except Exception:
            return None

    async def _get_engagement_scores(self, product_ids: List[str]) -> Dict[str, float]:
        """
        Score each product by recommendation engagement in the last N days:
        product_view counts as 1, add_to_cart as 3 (configurable).
        Used to boost products that users actually click or add.
        """
        if not product_ids:
            return {}
        config = _load_config()
        days = config.get("engagement_days", 30)
        weights = config.get("engagement_weights", {"product_view": 1, "add_to_cart": 3})
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        pid_set = set(product_ids)
        scores: Dict[str, float] = {pid: 0.0 for pid in product_ids}

        for action, weight in [
            ("recommendation_product_view", weights.get("product_view", 1)),
            ("recommendation_add_to_cart", weights.get("add_to_cart", 3)),
        ]:
            try:
                activities = await self.activity_storage.findAll({"action": action})
                for doc in activities:
                    created = self._parse_created_at(doc)
                    if created and created < cutoff:
                        continue
                    meta = doc.get("meta") or {}
                    pid = meta.get("productId")
                    if pid and pid in pid_set:
                        scores[pid] = scores.get(pid, 0) + weight
            except Exception:
                continue

        return scores

    async def get_recommendation_components(
        self, user_id: Optional[str] = None, role: Optional[str] = None, city: Optional[str] = None
    ) -> Dict[str, List[Dict]]:
        """
        Return recommendation components by segment (guest, retail, business/wholesaler).
        - Guest: Customer Favourites + Trending Now (retail orders, no exclusions). No Explore. sectionOrder from bandit.
        - Retail: Customer Favourites + Trending Now + Explore (exclude user purchases/cart for CF/TN). sectionOrder from bandit.
        - Wholesaler (business): Customer Favourites (retail), Trending Now (business), Explore (user), Business Favourites (business). sectionOrder from bandit.
        All slots participate in the bandit (epsilon-greedy) for section ordering.
        """
        config = _load_config()
        limits = config.get("strategy_limits", {})
        limits.get("trending", 10)
        limit_explore = limits.get("explore", 5)
        limit_new = limits.get("new_arrivals") or limits.get("user_favorites") or 10
        # Fetch all products once and reuse — avoid repeated full table scans
        all_products = await self.product_storage.findAll()
        product_map = {p["_id"]: p for p in all_products}

        def to_products(ids: List[str]) -> List[Dict]:
            out = []
            for pid in ids:
                p = product_map.get(pid)
                if p:
                    p_copy = dict(p)
                    # Convert to skinny payload to reduce size (keep images array since hover card cycles images)
                    p_copy["displayImage"] = p_copy.get("displayImage") or (
                        p_copy.get("images")[0] if p_copy.get("images") else None
                    )
                    p_copy.pop("description", None)
                    p_copy.pop("variantCombinations", None)
                    p_copy.pop("videos", None)
                    p_copy.pop("applicableDiscounts", None)
                    p_copy.pop("variations", None)
                    p_copy.pop("variantAttributes", None)
                    out.append(p_copy)
            return out

        trending_days = 7
        trending_top_per_subcat = 5
        cf_days_config = _segment_config("guest").get("customer_favourites_days", 60)

        # Customer Favourites: from cache (job at 12 AM IST) or compute on the fly
        cf_cache = _read_customer_favourites_cache()
        cf_ids_cached = cf_cache.get("product_ids") if isinstance(cf_cache.get("product_ids"), list) else None

        # Guest: no user_id
        if not user_id:
            # Always run trending + new arrivals in parallel; CF from cache or computed
            async def _cf_or_cached():
                if cf_ids_cached is not None:
                    return cf_ids_cached
                return await self.get_customer_favourites_by_subcategory(days=cf_days_config)

            cf_ids, tn_ids, new_ids = await asyncio.gather(
                _cf_or_cached(),
                self.get_trending_by_conversion(
                    "customer",
                    days=trending_days,
                    top_per_subcategory=trending_top_per_subcat,
                    exclude_product_ids=set(),
                ),
                self.get_new_arrivals(None, None, limit_new),
            )
            out = {
                "newArrivals": to_products(new_ids),
                "customerFavourites": to_products(cf_ids),
                "trendingNow": to_products(tn_ids),
                "explore": [],
                "wholesalerFavourites": [],
                "businessFavourites": [],
            }
            out["sectionOrder"] = ["new_arrivals", "customer_favourites", "trending_now"]
            return out

        # Retail (logged-in customer or any non-wholesaler)
        if role != "wholesaler":
            seg = _segment_config("retail")
            exclude_days = seg.get("exclude_user_purchases_days", 60)
            # Parallel fetch: user purchased IDs + cart IDs + trending (independent)
            purchased_task = self._get_user_purchased_product_ids(user_id, exclude_days)
            cart_task = self._get_user_cart_product_ids(user_id)

            purchased_ids, cart_ids = await asyncio.gather(purchased_task, cart_task)
            exclude = purchased_ids | cart_ids

            cf_ids_raw = (
                cf_ids_cached
                if cf_ids_cached is not None
                else await self.get_customer_favourites_by_subcategory(days=cf_days_config)
            )
            cf_ids = [x for x in (cf_ids_raw or []) if x not in exclude]

            # Now fetch trending + explore + new arrivals in parallel
            exp_days = seg.get("explore_days", 60)

            async def _explore_retail():
                if seg.get("explore_available", True):
                    return await self.get_best_selling_from_least_bought_categories(
                        user_id, limit_explore, days=exp_days
                    )
                return []

            tn_ids, explore_ids, new_ids = await asyncio.gather(
                self.get_trending_by_conversion(
                    "customer",
                    days=trending_days,
                    top_per_subcategory=trending_top_per_subcat,
                    exclude_product_ids=exclude,
                ),
                _explore_retail(),
                self.get_new_arrivals(user_id, role, limit_new),
            )
            # Exclude products that are in Customer Favourites from Trending Now section (tag unchanged)
            tn_ids = [x for x in tn_ids if x not in set(cf_ids)]
            out = {
                "newArrivals": to_products(new_ids),
                "customerFavourites": to_products(cf_ids),
                "trendingNow": to_products(tn_ids),
                "explore": to_products(explore_ids),
                "wholesalerFavourites": [],
                "businessFavourites": [],
            }
            out["sectionOrder"] = ["new_arrivals", "customer_favourites", "trending_now", "explore"]
            return out

        # Business (wholesaler)
        seg = _segment_config("wholesaler")
        bf_days = seg.get("business_favourites_days", seg.get("wholesaler_favourites_days", 60))
        exclude = await self._get_user_purchased_product_ids(user_id, bf_days)
        exclude |= await self._get_user_cart_product_ids(user_id)

        # Normalise city for consistent matching
        city_normalised = city.strip() if city and city.strip() else None

        # Customer Favourites: city-scoped when city provided, else use global cache / compute
        if city_normalised:
            cf_ids = await self.get_customer_favourites_by_subcategory(days=cf_days_config, city=city_normalised)
        elif cf_ids_cached is not None:
            cf_ids = list(cf_ids_cached)
        else:
            cf_ids = await self.get_customer_favourites_by_subcategory(days=cf_days_config)

        # Business Favourites: city-scoped when city provided, else use global cache / compute
        if city_normalised:
            bf_ids_raw = await self.get_business_favourites_by_subcategory(days=bf_days, city=city_normalised)
        else:
            bf_cache = _read_business_favourites_cache()
            bf_ids_raw = bf_cache.get("product_ids") if isinstance(bf_cache.get("product_ids"), list) else None
            if bf_ids_raw is None:
                bf_ids_raw = await self.get_business_favourites_by_subcategory(days=bf_days)

        bf_ids_after_exclude = [x for x in (bf_ids_raw or []) if x not in exclude]
        # Business dashboard overlapping rules (tags stay intact; only section membership changes):
        # 1. Products in Customer Favourites and Trending Now → removed from Trending Now.
        # 2. Products in Trending Now and Business Favourites → removed from Trending Now.
        # 3. Products in Customer Favourites and Business Favourites → removed from Business Favourites.
        bf_ids_section = [x for x in bf_ids_after_exclude if x not in set(cf_ids)]

        async def _explore_business():
            if seg.get("explore_available", True):
                return await self.get_best_selling_from_least_bought_categories(
                    user_id, limit_explore, days=seg.get("explore_days", 60)
                )
            return []

        tn_ids, explore_ids, new_ids = await asyncio.gather(
            self.get_trending_by_conversion(
                "wholesaler",
                days=trending_days,
                top_per_subcategory=trending_top_per_subcat,
                exclude_product_ids=exclude,
            ),
            _explore_business(),
            self.get_new_arrivals(user_id, role, limit_new),
        )
        tn_ids = [x for x in tn_ids if x not in set(cf_ids) and x not in set(bf_ids_raw or [])]

        out = {
            "newArrivals": to_products(new_ids),
            "customerFavourites": to_products(cf_ids),
            "trendingNow": to_products(tn_ids),
            "explore": to_products(explore_ids),
            "wholesalerFavourites": [],
            "businessFavourites": to_products(bf_ids_section),
            # Pass the city name through so the frontend can show "Popular in {City}"
            "cityName": city_normalised or "",
        }
        out["sectionOrder"] = ["new_arrivals", "customer_favourites", "trending_now", "explore", "business_favourites"]
        return out


recommendation_repository = RecommendationRepository()
