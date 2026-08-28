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
        users = await self.user_storage.findAll({"role": "customer"})
        return {u.get("_id") for u in users if u.get("_id")}

    async def _get_user_purchased_product_ids(self, user_id: str, days: int) -> set:
        """Products the user purchased in the last `days` days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        orders = await self.order_storage.findAll({"user": user_id, "startDate": cutoff.isoformat()})
        out = set()
        for order in orders:
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
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        orders = await self.order_storage.findAll({
            "orderNumber_prefix": "ORDER-RT-",
            "startDate": cutoff.isoformat(),
        })
        product_counts: Dict[str, int] = {}
        for order in orders:
            if order.get("user") not in retail_ids:
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
        top_percentile: float = 0.30,
        exclude_product_ids: Optional[Set[str]] = None,
        use_cache: bool = True,
        limit: Optional[int] = None,
    ) -> List[str]:
        """
        Trending Now: search-to-sale journey only.

        Algorithm:
        1. Score every product with ≥ 1 search in the last `days` days:
               score = converted_sales / search_count
           (converted_sales = orders where the same user/session searched this product first).

        2. Compute the (1 - top_percentile) score cutoff across all scored products.
           e.g. top_percentile=0.30 → keep products at or above the 70th-percentile score.
           The bar is always relative to the current window: it rises when many products
           convert well, and falls when traffic is thin — no hardcoded number.

        3. Apply exclude_product_ids to the eligible pool.

        4. Sort the remaining pool by score descending.

        5. Return the eligible pool up to `limit`. The frontend's row-based display logic
           will handle how many rows to show and whether to render a "Show more" button.

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

        # Orders in last `days` days for this segment — filtered at DB level
        orders = await self.order_storage.findAll({
            "orderNumber_prefix": prefix,
            "startDate": cutoff.isoformat(),
        })
        converted_sales_count: Dict[str, int] = {}
        for order in orders:
            order_dt = _parse_order_date(order)
            if not order_dt:
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

        # ── Step 3: search counts per product ───────────────────────────────────
        search_count = await tracking_repository.get_search_counts_by_product(days, segment)

        # ── Step 4: score every product with ≥1 search ──────────────────────────
        # (No subcat grouping — all products compete in one global pool)
        all_scored: List[Tuple[str, float]] = []
        for pid, sc in search_count.items():
            if sc < 1:
                continue
            converted = converted_sales_count.get(pid, 0)
            rate = converted / sc  # conversion score ∈ [0, 1]
            all_scored.append((pid, rate))

        if not all_scored:
            return []

        # ── Step 5: top-percentile cutoff ────────────────────────────────────────
        scores_only = sorted([rate for _, rate in all_scored])  # ascending
        cutoff_index = max(0, int(len(scores_only) * (1.0 - top_percentile)) - 1)
        score_cutoff = scores_only[cutoff_index]  # 70th-percentile value
        logger.info(
            "[Trending] segment=%s scored=%d score_cutoff=%.4f (top %.0f%%)",
            segment, len(all_scored), score_cutoff, top_percentile * 100,
        )

        # ── Step 6: apply exclusion list, then sort by score descending ──────────
        eligible = [
            (pid, rate)
            for pid, rate in all_scored
            if rate >= score_cutoff and pid not in exclude
        ]
        eligible.sort(key=lambda x: x[1], reverse=True)

        # ── Step 7: return eligible pool ─────────────────────────────────────────
        # The full sorted pool is returned so the frontend's row-based display logic
        # (getSectionDisplayConfig) can decide how many rows and whether to show
        # "Show more". The caller's `limit` acts as a safety cap for very large pools.
        result = [pid for pid, _ in eligible]
        return result[:limit] if limit else result

    async def get_trending_product_ids(self, segment: str) -> Set[str]:
        """Set of product IDs that are Trending Now for this segment (for tagging in catalog)."""
        ids = await self.get_trending_by_conversion(
            segment, days=7, top_percentile=0.30, exclude_product_ids=set()
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
        orders, all_products = await asyncio.gather(
            self.order_storage.findAll({
                "orderNumber_prefix": "ORDER-RT-",
                "startDate": cutoff.isoformat(),
            }),
            self.product_storage.findAll({"isActive": True}),
        )
        pid_to_subcat: Dict[str, str] = {
            p.get("_id"): (p.get("subCategory") or "None") for p in all_products if p.get("_id")
        }
        segment_order_count: Dict[str, Dict[str, int]] = {}
        segment_quantity: Dict[str, Dict[str, int]] = {}
        for order in orders:
            if order.get("user") not in retail_ids:
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
        orders, all_products = await asyncio.gather(
            self.order_storage.findAll({
                "orderNumber_prefix": "ORDER-WH-",
                "startDate": cutoff.isoformat(),
            }),
            self.product_storage.findAll({"isActive": True}),
        )
        pid_to_subcat: Dict[str, str] = {
            p.get("_id"): (p.get("subCategory") or "None") for p in all_products if p.get("_id")
        }
        segment_order_count: Dict[str, Dict[str, int]] = {}
        segment_quantity: Dict[str, Dict[str, int]] = {}
        for order in orders:
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

        prefix = "ORDER-RT-" if kind == "customer" else "ORDER-WH-"
        orders = await self.order_storage.findAll({
            "orderNumber_prefix": prefix,
            "startDate": cutoff.isoformat(),
        })
        for order in orders:
            if kind == "customer" and retail_ids and order.get("user") not in retail_ids:
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
        all_products = await self.product_storage.findAll({"isActive": True})
        user_ordered: Set[str] = set()
        if user_id:
            orders = await self.order_storage.findAll({"user": user_id})
            for o in orders:
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
        users = await self.user_storage.findAll({"role": "wholesaler"})
        wholesaler_ids = {u.get("_id") for u in users if u.get("_id") and u.get("_id") != user_id}
        if not wholesaler_ids:
            return []
        orders = await self.order_storage.findAll({
            "orderNumber_prefix": "ORDER-WH-",
            "startDate": cutoff.isoformat(),
        })
        product_counts: Dict[str, int] = {}
        for order in orders:
            if order.get("user") not in wholesaler_ids:
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
        orders = await self.order_storage.findAll({"user": user_id, "startDate": cutoff.isoformat()})
        product_counts: Dict[str, int] = {}
        for order in orders:
            for item in order.get("items", []):
                pid = item.get("product") or item.get("productId")
                if pid:
                    product_counts[pid] = product_counts.get(pid, 0) + item.get("quantity", 1)
        sorted_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [pid for pid, _ in sorted_products]

    async def get_best_selling_from_least_bought_categories(
        self, user_id: str, limit: int = 24, days: int = 60, exclude_product_ids: set = None
    ) -> list[str]:
        """Explore - picks top best-selling products from the user's n/3 neglected subcategories."""
        if exclude_product_ids is None:
            exclude_product_ids = set()

        from datetime import datetime, timedelta, timezone
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        # 1. Fetch user orders in the last 60 days + active products
        user_orders, products = await __import__('asyncio').gather(
            self.order_storage.findAll({"user": user_id, "startDate": cutoff.isoformat()}),
            self.product_storage.findAll({"isActive": True}),
        )
        
        product_by_id = {p.get("_id"): p for p in products if p.get("_id")}

        # 2. Count units purchased per subcategory (fallback to category) for this user
        subcat_counts = {}
        for o in user_orders:
            for item in o.get("items", []):
                pid = item.get("product") or item.get("productId")
                if not pid: continue
                p = product_by_id.get(pid)
                if p:
                    subcat = p.get("subCategory") or p.get("category")
                    if subcat:
                        subcat_counts[subcat] = subcat_counts.get(subcat, 0) + item.get("quantity", 1)

        n = len(subcat_counts)
        if n == 0:
            return []

        # 3. Neglected count = max(1, round(n / 3))
        neglected_count = max(1, round(n / 3.0))
        
        # 4. Products per subcategory = max(1, round(24 / neglected_count))
        # Note: We take 'limit' instead of hardcoded 24 to respect the caller, but limit is usually 24.
        products_per_subcat = max(1, round(limit / neglected_count))

        # Sort subcats ascending by purchase quantity
        sorted_subcats = sorted(subcat_counts.items(), key=lambda x: x[1])
        neglected_set = {subcat for subcat, _ in sorted_subcats[:neglected_count]}

        # 5. Fetch all-time orders to compute best-selling products overall
        # To avoid massive overhead, we filter orders by these neglected subcategories as we iterate.
        all_orders = await self.order_storage.findAll()
        
        subcat_product_sales = {}
        for order in all_orders:
            for item in order.get("items", []):
                pid = item.get("product") or item.get("productId")
                if not pid: continue
                p = product_by_id.get(pid)
                if not p: continue
                
                subcat = p.get("subCategory") or p.get("category")
                if subcat in neglected_set:
                    quantity = item.get("quantity", 1)
                    if subcat not in subcat_product_sales:
                        subcat_product_sales[subcat] = {}
                    subcat_product_sales[subcat][pid] = subcat_product_sales[subcat].get(pid, 0) + quantity

        # 6. For each neglected subcategory, pick the top products_per_subcat best-selling products
        # that are NOT in the exclude set.
        recommended_product_ids = []
        for subcat in neglected_set:
            sales = subcat_product_sales.get(subcat, {})
            # Sort by sales descending
            top_products = sorted(sales.items(), key=lambda x: x[1], reverse=True)
            
            added = 0
            for pid, _ in top_products:
                if pid not in exclude_product_ids:
                    recommended_product_ids.append(pid)
                    added += 1
                    if added >= products_per_subcat:
                        break

        # We return the compiled list. There is NO adaptive refill.
        return recommended_product_ids[:limit]


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

        try:
            pv_docs, atc_docs = await asyncio.gather(
                self.activity_storage.findAll({"action": "recommendation_product_view"}),
                self.activity_storage.findAll({"action": "recommendation_add_to_cart"}),
            )
        except Exception:
            return scores

        for docs, weight in [
            (pv_docs, weights.get("product_view", 1)),
            (atc_docs, weights.get("add_to_cart", 3)),
        ]:
            for doc in docs:
                created = self._parse_created_at(doc)
                if created and created < cutoff:
                    continue
                meta = doc.get("meta") or {}
                pid = meta.get("productId")
                if pid and pid in pid_set:
                    scores[pid] = scores.get(pid, 0) + weight

        return scores

    def _parse_created_at(self, doc) -> Optional[datetime]:
        raw = doc.get("createdAt")
        if not raw:
            return None
        try:
            dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None

    async def _derive_neglected_subcats(self, user_id: str, days: int) -> list:
        """
        Return the list of subcategories the user bought least from in the last `days` days
        (the bottom round(n/3) by purchase count). Used by bundle Explore scoring to test
        whether a bundle's subCategory falls inside the neglected set.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        orders = await self.order_storage.findAll({"user": user_id})
        products = await self.product_storage.findAll()
        product_by_id = {p.get("_id"): p for p in products if p.get("_id")}

        subcat_counts = {}
        for o in orders:
            if o.get("user") != user_id:
                continue
            dt = o.get("createdAt")
            if not dt:
                continue
            try:
                dt = datetime.fromisoformat(str(dt).replace("Z", "+00:00")).replace(tzinfo=None)
            except Exception:
                continue
            if dt < cutoff:
                continue
            for item in o.get("items", []):
                pid = item.get("product") or item.get("productId")
                if not pid:
                    continue
                p = product_by_id.get(pid)
                if not p:
                    continue
                subcat = p.get("subCategory") or p.get("category")
                if subcat:
                    subcat_counts[subcat] = subcat_counts.get(subcat, 0) + item.get("quantity", 1)

        n = len(subcat_counts)
        if n == 0:
            return []
        neglected_count = max(1, round(n / 3))
        sorted_subcats = [sc for sc, _ in sorted(subcat_counts.items(), key=lambda x: x[1])]
        return sorted_subcats[:neglected_count]

    async def _get_bundles_as_items(self, product_map=None):
        """Fetch and enrich active bundles to be treated as products in recommendation lists."""
        from app.repositories.bundle_repository import bundle_repository
        from app.routers.bundles import _enrich_bundle
        import logging
        try:
            bundles = await bundle_repository.get_active_bundles()
            enriched = []
            for b in bundles:
                try:
                    eb = await _enrich_bundle(b)
                    if not eb.get("isAvailable"):
                        continue
                    # Format as a product card for the frontend
                    eb["isBundle"] = True
                    # Resolving subCategory for Explore
                    sub_cat = eb.get("subCategory")
                    if not sub_cat:
                        # Attempt to derive from component products
                        for item in eb.get("items", []):
                            pid = item.get("productId")
                            p = product_map.get(str(pid)) if product_map else None
                            if p and p.get("subCategory"):
                                sc = p.get("subCategory")
                                sub_cat = sc.get("name") if isinstance(sc, dict) else sc
                                break
                    eb["subCategory"] = sub_cat
                    enriched.append(eb)
                except Exception as e:
                    logging.warning(f"Could not enrich bundle {b.get('_id')} for recommendations: {e}")
            return enriched
        except Exception as e:
            logging.error(f"Error fetching bundles for recommendations: {e}")
            return []

    def _is_available_in_zone(self, product: dict, seller_id_set: set) -> bool:
        """True if product has at least one active, in-stock seller in the zone."""
        if seller_id_set is None:
            return True  # no zone filter
        sellers = product.get("sellers") or []
        return any(
            str(s.get("sellerId")) in seller_id_set
            and s.get("isActive")
            and (s.get("stock") or 0) > 0
            and s.get("requestStatus", "approved") == "approved"
            for s in sellers
        )

    async def get_recommendation_components(
        self, user_id: str = None, role: str = None, city: str = None, seller_id_set: set = None
    ) -> dict:
        """
        Return recommendation components by segment (guest, retail, business/wholesaler).
        - Guest: Customer Favourites + Trending Now (retail orders, no exclusions). No Explore. sectionOrder from bandit.
        - Retail: Customer Favourites + Trending Now + Explore (exclude user purchases/cart for CF/TN). sectionOrder from bandit.
        - Wholesaler (business): Customer Favourites (retail), Trending Now (business), Explore (user), Business Favourites (business). sectionOrder from bandit.
        All slots participate in the bandit (epsilon-greedy) for section ordering.
        """
        config = _load_config()
        limits = config.get("strategy_limits", {})
        limit_trending = limits.get("trending", 24)
        limit_explore = limits.get("explore", 24)
        limit_new = limits.get("new_arrivals") or limits.get("user_favorites") or 24
        
        # Fetch all active products once and reuse
        all_products = await self.product_storage.findAll({"isActive": True})
        product_map = {p["_id"]: p for p in all_products if p.get("_id")}

        try:
            bundle_items = await getattr(self, '_get_bundles_as_items', lambda **kw: [])(product_map=product_map)
        except Exception as e:
            import logging
            logging.warning(f"Could not fetch bundles: {e}")
            bundle_items = []

        for _b in bundle_items:
            if _b.get("_id"):
                product_map[_b["_id"]] = _b

        bundle_ids = {_b["_id"] for _b in bundle_items if _b.get("_id")}

        def _bundle_new_arrival_ids(exclude_set):
            from datetime import datetime, timedelta, timezone
            cutoff_na = datetime.now(timezone.utc) - timedelta(days=30)
            qualifying = []
            for _b in bundle_items:
                bid = _b.get("_id")
                if not bid or bid in exclude_set:
                    continue
                created = self._parse_created_at({"createdAt": _b.get("createdAt")}) if _b.get("createdAt") else None
                if created and created >= cutoff_na:
                    qualifying.append((bid, created))
            qualifying.sort(key=lambda x: x[1], reverse=True)
            return [bid for bid, _ in qualifying]

        def _bundle_trending_ids(exclude_set, product_tn_ids):
            if not bundle_items: return []
            counts = [_b.get("salesCount", 0) or 0 for _b in bundle_items]
            max_count = max(counts) if counts else 0
            if max_count == 0: return []
            all_rates = []
            for _b in bundle_items:
                bid = _b.get("_id")
                if not bid or bid in exclude_set: continue
                rate = (_b.get("salesCount", 0) or 0) / max_count
                if rate > 0: all_rates.append((bid, rate))
            if not all_rates: return []
            rate_values = sorted(r for _, r in all_rates)
            cutoff_idx = max(0, int(len(rate_values) * 0.70) - 1)
            score_cutoff = rate_values[cutoff_idx]
            eligible = sorted([(bid, r) for bid, r in all_rates if r >= score_cutoff], key=lambda x: x[1], reverse=True)
            return [bid for bid, _ in eligible]

        def _bundle_favourites_ids(exclude_set):
            scored = sorted([(_b["_id"], _b.get("salesCount", 0) or 0) for _b in bundle_items if _b.get("_id") and _b["_id"] not in exclude_set and (_b.get("salesCount", 0) or 0) > 0], key=lambda x: x[1], reverse=True)
            return [bid for bid, _ in scored]

        def _bundle_explore_ids(neglected_subcats, exclude_set):
            neglected_set = set(neglected_subcats)
            scored = sorted([(_b["_id"], _b.get("salesCount", 0) or 0) for _b in bundle_items if _b.get("_id") and _b["_id"] not in exclude_set and (_b.get("subCategory") or _b.get("category")) in neglected_set], key=lambda x: x[1], reverse=True)
            return [bid for bid, _ in scored]

        def to_products(ids: list[str]) -> list[dict]:
            out = []
            for pid in ids:
                p = product_map.get(pid)
                if p and self._is_available_in_zone(p, seller_id_set):
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

        def to_products_city_only(ids: list) -> list:
            """
            Like to_products but WITHOUT zone filtering.
            Used for Customer Favourites and Business Favourites on the Wholesaler
            dashboard, which are scoped by city only (not by zone).
            This preserves the original city-level intelligence signal — a wholesaler
            should see what is trending in their city regardless of their delivery zone.
            """
            out = []
            for pid in ids:
                p = product_map.get(pid)
                if p:
                    p_copy = dict(p)
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

            import asyncio
            cf_ids_raw, tn_ids_raw, new_ids_raw = await asyncio.gather(
                _cf_or_cached(),
                self.get_trending_by_conversion(
                    "customer",
                    days=trending_days,
                    exclude_product_ids=set(),
                    limit=limit_trending,
                ),
                self.get_new_arrivals(None, None, limit_new),
            )
            
            new_ids = list(new_ids_raw) + _bundle_new_arrival_ids(set(new_ids_raw))
            cf_ids = list(cf_ids_raw) + _bundle_favourites_ids(set(cf_ids_raw))
            tn_ids = list(tn_ids_raw) + _bundle_trending_ids(set(tn_ids_raw), tn_ids_raw)
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
            
            import asyncio
            # Parallel fetch: user purchased IDs + cart IDs
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

            # Sequential Fetch for Cross-Section Deduplication
            # 1. Fetch Trending + New Arrivals in parallel first
            tn_ids_raw, new_ids_raw = await asyncio.gather(
                self.get_trending_by_conversion(
                    "customer",
                    days=trending_days,
                    exclude_product_ids=exclude,
                    limit=limit_trending,
                ),
                self.get_new_arrivals(user_id, role, limit_new),
            )
            
            cf_set = set(cf_ids)
            tn_product_ids = [x for x in tn_ids_raw if x not in cf_set]
            tn_bundle_ids = _bundle_trending_ids(exclude | cf_set | set(tn_product_ids), tn_product_ids)
            tn_ids = tn_product_ids + tn_bundle_ids
            
            new_ids = list(new_ids_raw) + _bundle_new_arrival_ids(exclude | set(new_ids_raw))
            
            cf_ids_bundle = _bundle_favourites_ids(exclude | set(cf_ids))
            cf_ids = cf_ids + cf_ids_bundle
            
            # 2. Build cross-section exclude for Explore
            explore_exclude = exclude | set(cf_ids) | set(tn_ids) | set(new_ids)
            
            # 3. Fetch Explore using the consolidated exclude set
            exp_days = seg.get("explore_days", 60)
            explore_ids_prod = []
            if seg.get("explore_available", True):
                explore_ids_prod = await self.get_best_selling_from_least_bought_categories(
                    user_id, limit_explore, days=exp_days, exclude_product_ids=explore_exclude
                )
                
            _neg = await getattr(self, '_derive_neglected_subcats', lambda u, d: [])(user_id, exp_days) if explore_ids_prod else []
            explore_bundle_ids = _bundle_explore_ids(_neg, explore_exclude | set(explore_ids_prod))
            explore_ids = list(explore_ids_prod) + explore_bundle_ids

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
        
        import asyncio
        purchased_ids = await self._get_user_purchased_product_ids(user_id, bf_days)
        cart_ids = await self._get_user_cart_product_ids(user_id)
        exclude = purchased_ids | cart_ids

        # Normalise city for consistent matching
        city_normalised = city.strip() if city and city.strip() else None

        # Customer Favourites: city-scoped when city provided, else use global cache / compute
        if city_normalised:
            cf_ids_raw = await self.get_customer_favourites_by_subcategory(days=cf_days_config, city=city_normalised)
        elif cf_ids_cached is not None:
            cf_ids_raw = list(cf_ids_cached)
        else:
            cf_ids_raw = await self.get_customer_favourites_by_subcategory(days=cf_days_config)
        cf_ids = [x for x in (cf_ids_raw or []) if x not in exclude]
        cf_ids = cf_ids + _bundle_favourites_ids(exclude | set(cf_ids))

        # Business Favourites: city-scoped when city provided, else use global cache / compute
        if city_normalised:
            bf_ids_raw = await self.get_business_favourites_by_subcategory(days=bf_days, city=city_normalised)
        else:
            bf_cache = _read_business_favourites_cache()
            bf_ids_cached = bf_cache.get("product_ids") if isinstance(bf_cache.get("product_ids"), list) else None
            bf_ids_raw = bf_ids_cached if bf_ids_cached is not None else await self.get_business_favourites_by_subcategory(days=bf_days)

        bf_ids_after_exclude = [x for x in (bf_ids_raw or []) if x not in exclude]

        tn_ids_raw, new_ids_raw = await asyncio.gather(
            self.get_trending_by_conversion(
                "wholesaler",
                days=trending_days,
                exclude_product_ids=exclude,
                limit=limit_trending,
            ),
            self.get_new_arrivals(user_id, role, limit_new),
        )
        
        new_ids = list(new_ids_raw) + _bundle_new_arrival_ids(exclude | set(new_ids_raw))
        
        tn_product_ids = [x for x in tn_ids_raw if x not in set(cf_ids) and x not in set(bf_ids_after_exclude)]
        tn_bundle_ids = _bundle_trending_ids(exclude | set(cf_ids) | set(bf_ids_after_exclude) | set(tn_product_ids), tn_product_ids)
        tn_ids = tn_product_ids + tn_bundle_ids
        
        # Build deduplication exclude for Explore
        explore_exclude = exclude | set(cf_ids) | set(bf_ids_after_exclude) | set(tn_ids) | set(new_ids)
        
        # Fetch Explore sequentially
        exp_days = seg.get("explore_days", 60)
        explore_ids_prod = []
        if seg.get("explore_available", True):
            explore_ids_prod = await self.get_best_selling_from_least_bought_categories(
                user_id, limit_explore, days=exp_days, exclude_product_ids=explore_exclude
            )
            
        _neg = await getattr(self, '_derive_neglected_subcats', lambda u, d: [])(user_id, exp_days) if explore_ids_prod else []
        explore_bundle_ids = _bundle_explore_ids(_neg, explore_exclude | set(explore_ids_prod))
        explore_ids = list(explore_ids_prod) + explore_bundle_ids

        bf_ids_section = [x for x in bf_ids_after_exclude if x not in set(cf_ids)]

        out = {
            "newArrivals": to_products(new_ids),
            # Customer Favourites and Business Favourites are city-scoped, NOT zone-filtered.
            # A wholesaler sees what is trending in their city regardless of their delivery zone.
            "customerFavourites": to_products_city_only(cf_ids),
            "trendingNow": to_products(tn_ids),
            "explore": to_products(explore_ids),
            "wholesalerFavourites": [],
            "businessFavourites": to_products_city_only(bf_ids_section),
            # Pass the city name through so the frontend can show "Popular in {City}"
            "cityName": city_normalised or "",
        }
        out["sectionOrder"] = ["new_arrivals", "customer_favourites", "trending_now", "explore", "business_favourites"]
        return out
recommendation_repository = RecommendationRepository()
