from typing import Any
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pathlib import Path
import json
import time
from datetime import timedelta
from app.models.daos import OrderFilter
from app.utils.logger import logger

from app.utils.cache import cache

from app.db.storage_factory import get_storage

from app.models.base import CamelBaseModel
from pydantic import Field, BaseModel
from app.models.analytics_schemas import (
    RFMSegmentsResponse,
    CustomerFrequencyResponse,
    InventoryRunwayResponse,
    DiscountsAuditResponse,
    ProductsPctSoldResponse,
    SalesByChannelDetailedResponse,
    ProductsSellThroughResponse,
    MonthlyRevenueItem,
    BundlePerformanceReportResponse,
    TopReturnedProductsResponse,
    InventoryValueByCategoryResponse,
    InventoryAlertResponse,
    NetSalesResponse,
    SalesHeatmapResponse,
    SalesOverTimeResponse,
    AverageOrderValueResponse,
    SalesByChannelResponse,
    SalesByProductResponse,
    VisitorsNowResponse,
    ReturnsReportResponse,
    PaymentMethodsReportResponse,
    RevenueByCategoryResponse,
    FulfillmentTimeReportResponse,
    SalesBreakdownResponse,
)

IST = timezone(timedelta(hours=5, minutes=30))
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_ANALYTICS_CACHE_PATH = _DATA_DIR / "analytics_reports_cache.json"


class DashboardReportsCache(CamelBaseModel):
    last_updated_at_ist: Optional[str] = None
    top_products: list[Any] = Field(default_factory=list)
    top_wholesalers: list[Any] = Field(default_factory=list)
    top_customers: list[Any] = Field(default_factory=list)
    most_searched: list[Any] = Field(default_factory=list)
    most_viewed: list[Any] = Field(default_factory=list)


_analytics_reports_cache_store: Optional[DashboardReportsCache] = None
_analytics_reports_cache_ts: float = 0.0

def _get_current_ist_timestamp() -> str:
    now_ist = datetime.now(IST)
    return now_ist.strftime("%d %b %Y, %I:%M %p IST")

def _read_analytics_reports_cache() -> Optional[DashboardReportsCache]:
    global _analytics_reports_cache_store, _analytics_reports_cache_ts
    now = time.monotonic()
    if _analytics_reports_cache_store is not None and (now - _analytics_reports_cache_ts) < 60:
        return _analytics_reports_cache_store
    try:
        if _ANALYTICS_CACHE_PATH.exists():
            data = DashboardReportsCache.model_validate_json(_ANALYTICS_CACHE_PATH.read_text(encoding="utf-8"))
            _analytics_reports_cache_store = data
            _analytics_reports_cache_ts = now
            return data
    except Exception:
        logger.exception("Error reading analytics reports cache")
    return None

def _write_analytics_reports_cache(data: DashboardReportsCache) -> None:
    global _analytics_reports_cache_store, _analytics_reports_cache_ts
    _analytics_reports_cache_store = data
    _analytics_reports_cache_ts = time.monotonic()
    try:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        _ANALYTICS_CACHE_PATH.write_text(data.model_dump_json(by_alias=True), encoding="utf-8")
    except Exception:
        logger.exception("Error writing analytics reports cache")


class AnalyticsRepository:
    def __init__(self):
        self.order_storage = get_storage("orders")
        self.product_storage = get_storage("products")
        self.user_storage = get_storage("users")
        self.cart_storage = get_storage("carts")
        self.session_storage = get_storage("sessions")
        self.tracking_storage = get_storage("tracking")

    def _build_order_filter(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[OrderFilter]:
        if not start_date and not end_date and not status and not user_id:
            return None
        return OrderFilter(
            start_date=start_date,
            end_date=end_date,
            status=status,
            user_id=str(user_id) if user_id else None,
        )

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid date format: {date_str}") from e

    def _to_naive_utc(self, dt: Optional[datetime]) -> Optional[datetime]:
        """Normalize to naive UTC for consistent arithmetic."""
        if not dt:
            return None
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc)
            return dt.replace(tzinfo=None)
        return dt

    def _filter_by_date_range(
        self,
        items: List[Dict],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        date_field: str = "createdAt",
    ) -> List[Dict]:
        """Filter items by date range"""
        if not start_date and not end_date:
            return items

        filtered = []
        for item in items:
            if date_field == "createdAt":
                item_date = self._parse_date(item.created_at if item.created_at is not None else "")
            elif date_field == "timestamp":
                item_date = self._parse_date(item.timestamp if item.timestamp is not None else "")
            else:
                item_date = None
            if not item_date:
                continue

            if start_date and item_date < start_date:
                continue
            if end_date and item_date > end_date:
                continue

            filtered.append(item)

        return filtered

    @cache.ttl_cache(ttl=300)
    async def get_kpi_metrics(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict:
        """Get KPI metrics: Gross sales, Returning customer rate, Orders fulfilled, Orders"""
        order_filter = self._build_order_filter(start_date=start_date, end_date=end_date)
        return await self.order_storage.get_kpi_stats(order_filter)

    def _filter_by_seller(self, orders: list, seller_id: Optional[int]) -> list:
        """Filter orders to those belonging to a specific seller."""
        if not seller_id:
            return orders
        filtered = []
        for order in orders:
            if order.seller_id == seller_id:
                filtered.append(order)
                continue
            sub_orders = order.sub_orders or []
            for so in sub_orders:
                if so.seller_id == seller_id:
                    filtered.append(order)
                    break
        return filtered

    @cache.ttl_cache(ttl=300)
    async def get_sales_over_time(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "hour",
        seller_id: Optional[int] = None,
    ) -> List[SalesOverTimeResponse]:
        """Get sales over time, grouped by hour, day, or month"""
        return await self.order_storage.get_sales_over_time_stats(
            start_date=start_date, end_date=end_date, group_by=group_by, seller_id=seller_id
        )

    @cache.ttl_cache(ttl=300)
    async def get_sales_breakdown(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> SalesBreakdownResponse:
        """Get sales breakdown: Gross sales, Discounts, Returns, Net sales, Shipping, Taxes"""
        return await self.order_storage.get_sales_breakdown_stats(
            start_date=start_date, end_date=end_date
        )

    @cache.ttl_cache(ttl=300)
    async def get_average_order_value_over_time(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "hour",
        seller_id: Optional[int] = None,
    ) -> List[AverageOrderValueResponse]:
        """Get average order value over time"""
        return await self.order_storage.get_average_order_value_over_time_stats(
            start_date=start_date, end_date=end_date, group_by=group_by, seller_id=seller_id
        )

    @cache.ttl_cache(ttl=300)
    async def get_sales_by_channel(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        seller_id: Optional[int] = None,
    ) -> List[SalesByChannelResponse]:
        """Get sales by sales channel"""
        return await self.order_storage.get_sales_by_channel_stats(
            start_date=start_date, end_date=end_date, seller_id=seller_id
        )

    @cache.ttl_cache(ttl=300)
    async def get_sales_by_product(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10,
        seller_id: Optional[int] = None,
    ) -> List[SalesByProductResponse]:
        """Get top products by sales"""
        return await self.order_storage.get_sales_by_product_stats(
            start_date=start_date, end_date=end_date, limit=limit, seller_id=seller_id
        )

    @cache.ttl_cache(ttl=300)
    async def get_conversion_rate_over_time(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, group_by: str = "hour"
    ) -> Dict:
        """Get conversion rate over time (orders / sessions) calculated from actual tracking events"""
        order_filter = self._build_order_filter(start_date=start_date, end_date=end_date)
        orders = await self.order_storage.findAll(order_filter)

        # 1. Sessions count (unique sessions in the date range)
        sessions_tracking = await self.tracking_storage.find_by_date_range("session", start_date, end_date)
        session_count = len(set(s.session_id for s in sessions_tracking if s.session_id))

        # Fallback to estimated sessions if zero tracking traffic exists
        if session_count == 0:
            session_count = len(orders) * 10 if orders else 10

        # 2. Cart Additions (unique sessions adding items to cart)
        cart_add_tracking = await self.tracking_storage.find_by_date_range("cart_add", start_date, end_date)
        added_to_cart_count = len(set(c.session_id for c in cart_add_tracking if c.session_id))

        # Fallback if no cart additions tracked
        if added_to_cart_count == 0:
            carts = await self.cart_storage.findAll()
            carts = self._filter_by_date_range(carts, start_date, end_date)
            added_to_cart_count = len(carts) + len([o for o in orders if o.status not in ["cancelled"]])

        # Enforce valid funnel hierarchy
        added_to_cart_count = min(session_count, added_to_cart_count)

        # 3. Reached Checkout (unique sessions landing on checkout page step 1)
        all_checkout_tracking = await self.tracking_storage.find_by_date_range("page_view", start_date, end_date)
        checkout_tracking = [e for e in all_checkout_tracking if e.page == "/checkout/step1"]
        reached_checkout_count = len(set(c.session_id for c in checkout_tracking if c.session_id))

        # Fallback if zero tracking events exist
        if reached_checkout_count == 0:
            reached_checkout_count = len(
                [
                    o
                    for o in orders
                    if o.status in ["pending", "confirmed", "processing", "dispatched", "delivered", "completed"]
                ]
            )

        reached_checkout_count = min(added_to_cart_count, reached_checkout_count)

        # 4. Completed purchases (unique sessions with order placement)
        completed_orders_list = [o for o in orders if o.status not in ["cancelled"]]
        completed_count = len(set(o.session_id for o in completed_orders_list if o.session_id))

        if completed_count == 0:
            completed_count = len(completed_orders_list)

        completed_count = min(reached_checkout_count, completed_count)

        return {
            "sessions": {"count": session_count, "percentage": 100.0, "drop_percentage": 0.0},
            "added_to_cart": {
                "count": added_to_cart_count,
                "percentage": (added_to_cart_count / session_count * 100) if session_count > 0 else 0,
                "drop_percentage": ((session_count - added_to_cart_count) / session_count * 100)
                if session_count > 0
                else 0,
            },
            "reached_checkout": {
                "count": reached_checkout_count,
                "percentage": (reached_checkout_count / session_count * 100) if session_count > 0 else 0,
                "drop_percentage": ((added_to_cart_count - reached_checkout_count) / added_to_cart_count * 100)
                if added_to_cart_count > 0
                else 0,
            },
            "completed": {
                "count": completed_count,
                "percentage": (completed_count / session_count * 100) if session_count > 0 else 0,
                "drop_percentage": ((reached_checkout_count - completed_count) / reached_checkout_count * 100)
                if reached_checkout_count > 0
                else 0,
            },
            "overall_conversion_rate": (completed_count / session_count * 100) if session_count > 0 else 0,
        }

    @cache.ttl_cache(ttl=300)
    async def get_checkout_funnel(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict:
        """Get detailed checkout funnel stages breakdown"""
        order_filter = self._build_order_filter(start_date=start_date, end_date=end_date)
        orders = await self.order_storage.findAll(order_filter)

        async def get_unique_sessions_for_page(page_path: str) -> int:
            events = await self.tracking_storage.find_by_date_range("page_view", start_date, end_date)
            events = [e for e in events if e.page == page_path]
            return len(set(e.session_id for e in events if e.session_id))

        cart_sessions = await get_unique_sessions_for_page("/customer/cart")
        step1_sessions = await get_unique_sessions_for_page("/checkout/step1")
        step2_sessions = await get_unique_sessions_for_page("/checkout/step2")
        step3_sessions = await get_unique_sessions_for_page("/checkout/step3")

        completed_orders = [o for o in orders if o.status not in ["cancelled"]]
        completed_sessions = len(set(o.session_id for o in completed_orders if o.session_id))
        if completed_sessions == 0:
            completed_sessions = len(completed_orders)

        # Fallbacks for dev preview
        if cart_sessions == 0:
            cart_sessions = int(max(10, completed_sessions * 3))
        if step1_sessions == 0:
            step1_sessions = int(max(0, min(cart_sessions, completed_sessions * 2)))
        if step2_sessions == 0:
            step2_sessions = int(max(0, min(step1_sessions, completed_sessions * 1.5)))
        if step3_sessions == 0:
            step3_sessions = int(max(0, min(step2_sessions, completed_sessions * 1.1)))

        # Enforce valid hierarchy bounds
        step3_sessions = min(step2_sessions, step3_sessions)
        step2_sessions = min(step1_sessions, step2_sessions)
        step1_sessions = min(cart_sessions, step1_sessions)
        completed_sessions = min(step3_sessions, completed_sessions)

        def make_stage(count, total, drop_percentage=None):
            pct = (count / total * 100) if total > 0 else 0
            if drop_percentage is not None:
                return {"count": count, "percentage": pct, "drop_percentage": drop_percentage}
            return {"count": count, "percentage": pct}

        drop_cart_to_step1 = ((cart_sessions - step1_sessions) / cart_sessions * 100) if cart_sessions > 0 else 0
        drop_step1_to_step2 = ((step1_sessions - step2_sessions) / step1_sessions * 100) if step1_sessions > 0 else 0
        drop_step2_to_step3 = ((step2_sessions - step3_sessions) / step2_sessions * 100) if step2_sessions > 0 else 0
        drop_step3_to_complete = (
            ((step3_sessions - completed_sessions) / step3_sessions * 100) if step3_sessions > 0 else 0
        )

        return {
            "cart": make_stage(cart_sessions, cart_sessions),
            "shipping": make_stage(step1_sessions, cart_sessions, drop_cart_to_step1),
            "review": make_stage(step2_sessions, cart_sessions, drop_step1_to_step2),
            "payment": make_stage(step3_sessions, cart_sessions, drop_step2_to_step3),
            "completed": make_stage(completed_sessions, cart_sessions, drop_step3_to_complete),
            "overall_checkout_conversion": (completed_sessions / cart_sessions * 100) if cart_sessions > 0 else 0,
        }

    @cache.ttl_cache(ttl=300)
    async def get_sessions_by_device_type(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Get sessions by device type"""
        sessions = await self.session_storage.findAll()
        sessions = self._filter_by_date_range(sessions, start_date, end_date)
        device_counts = defaultdict(int)
        for s in sessions:
            device_type = (s.device["type"] if "type" in s.device else "desktop") if s.device else "desktop"
            device_counts[device_type] += 1
        return [{"device": k, "sessions": v} for k, v in device_counts.items()]

    @cache.ttl_cache(ttl=300)
    async def get_sessions_by_location(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Get sessions by location"""
        sessions = await self.session_storage.findAll()
        sessions = self._filter_by_date_range(sessions, start_date, end_date)
        location_counts = defaultdict(int)
        for s in sessions:
            location = s.location
            location_counts[location] += 1
        return [{"location": k, "sessions": v} for k, v in location_counts.items()]

    @cache.ttl_cache(ttl=300)
    async def get_products_by_sell_through_rate(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10,
        seller_id: Optional[int] = None,
    ) -> List[ProductsSellThroughResponse]:
        """Get products by sell-through rate"""
        return await self.order_storage.get_products_sell_through_stats(
            start_date=start_date, end_date=end_date, limit=limit, seller_id=seller_id
        )

    @cache.ttl_cache(ttl=300)
    async def get_customer_cohort_analysis(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Get customer cohort analysis"""
        orders = await self.order_storage.findAll()

        # Pre-group orders by user_id so inner lookup is O(1) not O(N)
        orders_by_user: Dict[str, list] = defaultdict(list)
        for order in orders:
            if order.user:
                orders_by_user[order.user].append(order)

        # Find each user's first order date
        user_first_order: Dict[str, datetime] = {}
        for user_id, user_orders in orders_by_user.items():
            for order in user_orders:
                order_date = self._parse_date(order.created_at)
                if not order_date:
                    continue
                if user_id not in user_first_order or order_date < user_first_order[user_id]:
                    user_first_order[user_id] = order_date

        # Build cohort matrix — O(total orders) not O(users × orders)
        cohorts: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        for user_id, first_order_date in user_first_order.items():
            cohort_month = first_order_date.strftime("%Y-%m")
            for order in orders_by_user[user_id]:
                order_date = self._parse_date(order.created_at)
                if not order_date or order_date < first_order_date:
                    continue
                month_index = (order_date.year - first_order_date.year) * 12 + (
                    order_date.month - first_order_date.month
                )
                cohorts[cohort_month][month_index] += 1

        result = []
        for cohort_month in sorted(cohorts.keys()):
            cohort_data = cohorts[cohort_month]
            max_months = max(cohort_data.keys()) if cohort_data else 0
            result.append({"cohort": cohort_month, "months": [(cohort_data[i] if i in cohort_data else 0) for i in range(max_months + 1)]})

        return result

    @cache.ttl_cache(ttl=300)
    async def get_sessions_by_landing_page(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Get sessions by landing page"""
        tracking = await self.tracking_storage.find_by_date_range("page_view", start_date, end_date)

        session_landing = {}
        for t in tracking:
            sid = t.session_id
            if not sid:
                continue
            ts = self._parse_date(t.timestamp)
            if sid not in session_landing or ts < session_landing[sid]["ts"]:
                session_landing[sid] = {"ts": ts, "page": t.page}

        landing_counts = defaultdict(int)
        for val in session_landing.values():
            landing_counts[val["page"]] += 1

        return [{"landing_page": k, "sessions": v} for k, v in landing_counts.items()]

    @cache.ttl_cache(ttl=300)
    async def get_all_user_engagement_aggregate(self) -> Dict:
        """Get aggregated engagement metrics across all users, bucketed by durations."""
        users = await self.user_storage.findAll()
        sessions = await self.session_storage.findAll()

        valid_sessions = [s for s in sessions if not s.is_guest]

        user_durations = defaultdict(list)
        user_session_counts = defaultdict(int)
        for s in valid_sessions:
            uid = s.userId
            if not uid:
                continue
            user_session_counts[uid] += 1
            start_dt = self._parse_date(s.created_at)
            end_dt = self._parse_date(s.revokedAt or s.lastActiveAt)
            if not start_dt:
                continue
            if not end_dt:
                end_dt = datetime.now(timezone.utc)
            start_naive = self._to_naive_utc(start_dt)
            end_naive = self._to_naive_utc(end_dt)
            if start_naive and end_naive:
                delta = (end_naive - start_naive).total_seconds()
                if delta >= 0:
                    user_durations[uid].append(delta)

        buckets = {"0-60s": 0, "60-300s": 0, "300-600s": 0, "600s+": 0}

        user_metrics = []
        for u in users:
            uid = u.id
            durations = (user_durations[uid] if uid in user_durations else [])
            avg_duration = sum(durations) / len(durations) if durations else 0

            # Bucketing
            if avg_duration <= 60:
                buckets["0-60s"] += 1
            elif avg_duration <= 300:
                buckets["60-300s"] += 1
            elif avg_duration <= 600:
                buckets["300-600s"] += 1
            else:
                buckets["600s+"] += 1

            user_metrics.append(
                {
                    "userId": uid,
                    "name": u.name if u.name else "Unknown",
                    "email": u.email if u.email else "Unknown",
                    "averageSessionTimeSeconds": round(avg_duration, 2),
                    "totalSessions": (user_session_counts[uid] if uid in user_session_counts else 0),
                }
            )

        return {
            "duration_buckets": [{"range": k, "count": v} for k, v in buckets.items()],
            "user_metrics": user_metrics,
        }

    @cache.ttl_cache(ttl=300)
    async def get_user_engagement_metrics(self, user_id: str) -> Dict:
        """
        Per-user engagement metrics calculated since the user's registration date.
        All sessions (all devices) are included.
        Returns:
          - averageSessionTimeSeconds: average session duration in seconds
          - averageDaysBetweenSessions: average days between two consecutive sessions
          - averagePagesPerSession: average number of pages visited per session
          - sessionOrderRate: share of sessions that had at least one order (0-1)
          - totalSessions, sessionsWithOrder, registrationDate for context
        """
        user = await self.user_storage.findById(user_id)
        if not user:
            return {
                "error": "User not found",
                "averageSessionTimeSeconds": None,
                "averageDaysBetweenSessions": None,
                "averagePagesPerSession": None,
                "sessionOrderRate": None,
                "totalSessions": 0,
                "sessionsWithOrder": 0,
                "registrationDate": None,
            }

        registration_dt = self._parse_date(user.created_at)
        reg_naive = self._to_naive_utc(registration_dt) if registration_dt else None
        all_sessions = await self.session_storage.findAll()
        # Non-guest sessions for this user; optionally since registration
        sessions = [s for s in all_sessions if s.userId == user_id and not s.is_guest]
        if reg_naive is not None:
            sessions = [
                s
                for s in sessions
                if self._to_naive_utc(self._parse_date(s.created_at)) is not None
                and self._to_naive_utc(self._parse_date(s.created_at)) >= reg_naive
            ]

        total_sessions = len(sessions)
        registration_date_str = user.created_at

        # 1) Average session time (all devices): end = revokedAt or lastActiveAt, start = createdAt
        session_durations_sec = []
        for s in sessions:
            start_dt = self._to_naive_utc(self._parse_date(s.created_at))
            end_dt = self._to_naive_utc(self._parse_date(s.revokedAt or s.lastActiveAt))
            if not start_dt:
                continue
            if not end_dt:
                end_dt = datetime.now(timezone.utc)
            delta = (end_dt - start_dt).total_seconds()
            if delta >= 0:
                session_durations_sec.append(delta)
        average_session_time_seconds = (
            round(sum(session_durations_sec) / len(session_durations_sec), 2) if session_durations_sec else None
        )

        # 2) Average days between two consecutive sessions
        sorted_sessions = sorted(
            [s for s in sessions if s.created_at],
            key=lambda s: s.created_at,
        )
        gaps_days = []
        for i in range(len(sorted_sessions) - 1):
            d1 = self._to_naive_utc(self._parse_date(sorted_sessions[i].created_at))
            d2 = self._to_naive_utc(self._parse_date(sorted_sessions[i + 1].created_at))
            if d1 and d2:
                gaps_days.append((d2 - d1).total_seconds() / 86400.0)
        average_days_between_sessions = round(sum(gaps_days) / len(gaps_days), 2) if gaps_days else None

        # 3) Average pages per session — only fetch page_view events (not whole table)
        session_ids = {s.id for s in sessions if s.id}
        page_view_events = await self.tracking_storage.find_by_date_range("page_view", None, None)
        page_views_by_session: Dict[str, int] = {sid: 0 for sid in session_ids}
        for t in page_view_events:
            sid = t.session_id
            if sid in session_ids:
                page_views_by_session[sid] += 1
        page_counts = list(page_views_by_session.values())
        average_pages_per_session = round(sum(page_counts) / len(page_counts), 2) if page_counts else None

        # 4) Sessions with orders — only load orders for this user
        all_orders = await self.order_storage.findAll(self._build_order_filter(user_id=user_id))
        orders_for_user = []
        for o in all_orders:
            if o.user != user_id:
                continue
            if reg_naive is not None:
                o_dt = self._to_naive_utc(self._parse_date(o.created_at))
                if not o_dt or o_dt < reg_naive:
                    continue
            orders_for_user.append(o)
        order_session_ids = {o.session_id for o in orders_for_user if o.session_id}
        sessions_with_order = len(order_session_ids)
        session_order_rate = round(sessions_with_order / total_sessions, 4) if total_sessions > 0 else None

        return {
            "userId": user_id,
            "registrationDate": registration_date_str,
            "totalSessions": total_sessions,
            "averageSessionTimeSeconds": average_session_time_seconds,
            "averageDaysBetweenSessions": average_days_between_sessions,
            "averagePagesPerSession": average_pages_per_session,
            "sessionsWithOrder": sessions_with_order,
            "sessionOrderRate": session_order_rate,
        }

    async def record_event(self, event) -> None:
        """
        DEPRECATED — sj_events table has been dropped. Mobile events are now
        written directly to sj_tracking via tracking_repository in the
        /api/analytics/events endpoint. This stub is kept to prevent import
        errors during the transition; callers in analytics.py have been removed.
        """
        pass

    @cache.ttl_cache(ttl=300)
    async def get_top_users_by_revenue(
        self,
        role: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """Get top users by revenue, optionally filtered by role"""
        order_filter = self._build_order_filter(start_date=start_date, end_date=end_date)
        orders = await self.order_storage.findAll(order_filter)

        users = await self.user_storage.findAll()

        user_revenue = defaultdict(float)
        user_orders = defaultdict(int)
        for order in orders:
            uid = order.user
            if not uid:
                continue
            user_revenue[uid] += order.total
            user_orders[uid] += 1

        result = []
        for uid, revenue in user_revenue.items():
            user = next((u for u in users if u.id == uid), None)
            if not user:
                continue
            if role and user.role != role:
                continue

            result.append(
                {
                    "userId": uid,
                    "name": user.name,
                    "userName": user.name,
                    "email": user.email,
                    "userEmail": user.email,
                    "role": user.role,
                    "revenue": revenue,
                    "orderCount": user_orders[uid],
                }
            )

        return sorted(result, key=lambda x: x["revenue"], reverse=True)[:limit]

    @cache.ttl_cache(ttl=300)
    async def get_user_order_stats(
        self, role: Optional[str] = None, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Get order statistics for users, optionally filtered by role"""
        orders = await self.order_storage.findAll()
        users = await self.user_storage.findAll()

        user_orders_map = defaultdict(list)
        for order in orders:
            uid = order.user
            if not uid:
                continue
            user_orders_map[uid].append(order)

        result = []
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        for uid, u_orders in user_orders_map.items():
            user = next((u for u in users if u.id == uid), None)
            if not user:
                continue
            if role and user.role != role:
                continue

            # 1. Orders in the filtered range
            u_orders_filtered = self._filter_by_date_range(u_orders, start_date, end_date)

            if not u_orders_filtered and (start_date or end_date):
                continue

            total_orders = len(u_orders_filtered)
            total_revenue = sum(o.total for o in u_orders_filtered)
            aov = round(total_revenue / total_orders, 2) if total_orders > 0 else 0

            # 2. Average orders in a month (Overall frequency sejak awal)
            order_dates = [self._to_naive_utc(self._parse_date(o.created_at)) for o in u_orders]
            order_dates = [d for d in order_dates if d]

            avg_orders_per_month = 0
            days_since_last = 0

            if order_dates:
                first_order_date = min(order_dates)
                last_order_date = max(order_dates)
                delta_total = now - first_order_date
                months_active = max(1, delta_total.days / 30.44)
                avg_orders_per_month = round(len(u_orders) / months_active, 2)
                days_since_last = (now - last_order_date).days

            result.append(
                {
                    "userId": uid,
                    "name": user.name,
                    "email": user.email,
                    "totalOrders": total_orders,
                    "avgOrdersPerMonth": avg_orders_per_month,
                    "daysSinceLastOrder": days_since_last,
                    "averageOrderValue": aov,
                }
            )

        return result

    @cache.ttl_cache(ttl=300)
    async def get_items_by_user_type(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Get engagement counts (searches, views) broken down by user role"""
        # Use find_by_date_range with no event_type to push date filtering to SQL
        filtered_tracking = await self.tracking_storage.find_by_date_range(None, start_date, end_date)

        users = await self.user_storage.findAll()

        from pydantic import BaseModel
        class RoleStats(BaseModel):
            searches: int = 0
            views: int = 0

        role_stats = defaultdict(RoleStats)
        for t in filtered_tracking:
            uid = t.userId
            user = next((u for u in users if u.id == uid), None) if uid else None
            role = user.role if user and user.role else ("guest" if not uid else "customer")

            if t.type == "product_search":
                role_stats[role].searches += 1
            elif t.type == "product_view":
                role_stats[role].views += 1

        return [
            {"role": role, "searches": stats.searches, "views": stats.views} for role, stats in role_stats.items()
        ]

    @cache.ttl_cache(ttl=300)
    async def get_all_reports_summary(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict:
        """Get counts for all report types to display in dropdown labels"""
        from app.repositories.tracking_repository import tracking_repository

        searched = await tracking_repository.getMostSearched(1000, start_date, end_date)
        viewed = await tracking_repository.getMostViewed(1000, start_date, end_date)
        drop_offs = await tracking_repository.getDropOffs(1000, start_date, end_date)
        abandonments = await tracking_repository.getCartAbandonments(1000, start_date, end_date)
        returning = await tracking_repository.getReturningUsers(start_date, end_date)
        user_type_items = await self.get_items_by_user_type(start_date, end_date)
        top_products = await self.get_sales_by_product(start_date, end_date, 1000)
        top_business = await self.get_top_users_by_revenue("wholesaler", start_date, end_date, 1000)
        top_retail = await self.get_top_users_by_revenue("customer", start_date, end_date, 1000)
        engagement = await self.get_all_user_engagement_aggregate()
        returns = await self.get_returns_report(start_date, end_date)
        payment_methods = await self.get_payment_methods_report(start_date, end_date)
        revenue_by_cat = await self.get_revenue_by_category(start_date, end_date, 100)
        inventory = await self.get_inventory_alerts(10)
        fulfillment = await self.get_fulfillment_time_report(start_date, end_date)
        coupon_usage = await self.get_coupon_usage_report(start_date, end_date)
        sales_by_loc = await self.get_sales_by_location(start_date, end_date)
        new_vs_ret = await self.get_new_vs_returning_customer_sales(start_date, end_date)
        items_bought = await self.get_items_bought_together(start_date, end_date)
        zero_searches = await tracking_repository.getZeroResultSearches(100, start_date, end_date)
        sales_device = await self.get_sales_by_device_type(start_date, end_date)
        sell_through = await self.get_products_by_sell_through_rate(start_date, end_date, 50)
        aov_time = await self.get_sales_over_time(start_date, end_date, "day")
        top_returned = await self.get_top_returned_products(start_date, end_date)
        inventory_val = await self.get_inventory_value_by_category()
        most_abandoned = await tracking_repository.getMostAbandonedProducts(100, start_date, end_date)

        return {
            "searched_products": len(searched),
            "viewed_products": len(viewed),
            "drop_off_points": len(drop_offs),
            "cart_abandonments": len(abandonments),
            "returning_users": len(returning),
            "items_by_user_type": len(user_type_items),
            "highest_selling_products": len(top_products),
            "top_business_customers": len(top_business),
            "top_retail_customers": len(top_retail),
            "user_engagement": len((engagement["user_metrics"] if "user_metrics" in engagement else [])),
            "returns": len(returns),
            "payment_methods": len(payment_methods),
            "revenue_by_category": len(revenue_by_cat),
            "inventory_alerts": len(inventory),
            "fulfillment_time": len(fulfillment),
            "coupon_usage": len(coupon_usage),
            "sales_by_location": len(sales_by_loc),
            "new_vs_returning": len(new_vs_ret),
            "items_bought_together": len(items_bought),
            "zero_result_searches": len(zero_searches),
            "sales_by_device": len(sales_device),
            "products_sell_through": len(sell_through),
            "aov_over_time": len(aov_time),
            "top_returned_products": len(top_returned),
            "inventory_value": len(inventory_val),
            "most_abandoned_products": len(most_abandoned),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # NEW REPORT METHODS
    # ─────────────────────────────────────────────────────────────────────────

    @cache.ttl_cache(ttl=300)
    async def get_returns_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        seller_id: Optional[int] = None,
    ) -> List[ReturnsReportResponse]:
        """Aggregate returns/refund requests with order value and status."""
        return await self.order_storage.get_returns_report_stats(
            start_date=start_date, end_date=end_date, seller_id=seller_id
        )

    @cache.ttl_cache(ttl=300)
    async def get_payment_methods_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        seller_id: Optional[int] = None,
    ) -> List[PaymentMethodsReportResponse]:
        """Aggregate order count and revenue by payment method."""
        return await self.order_storage.get_payment_methods_report_stats(
            start_date=start_date, end_date=end_date, seller_id=seller_id
        )

    @cache.ttl_cache(ttl=300)
    async def get_revenue_by_category(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 20,
        seller_id: Optional[int] = None,
    ) -> List[RevenueByCategoryResponse]:
        """Aggregate revenue, quantity and order count by product category."""
        return await self.order_storage.get_revenue_by_category_stats(
            start_date=start_date, end_date=end_date, limit=limit, seller_id=seller_id
        )

    @cache.ttl_cache(ttl=300)
    async def get_inventory_alerts(
        self,
        threshold: int = 10,
        seller_id: Optional[int] = None,
    ) -> List[InventoryAlertResponse]:
        """Return products whose current stock is at or below `threshold`."""
        return await self.order_storage.get_inventory_alerts_stats(
            threshold=threshold, seller_id=seller_id
        )

    @cache.ttl_cache(ttl=300)
    async def get_fulfillment_time_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        seller_id: Optional[int] = None,
    ) -> List[FulfillmentTimeReportResponse]:
        """Calculate fulfillment times for completed/delivered orders."""
        return await self.order_storage.get_fulfillment_time_report_stats(
            start_date=start_date, end_date=end_date, seller_id=seller_id
        )

    @cache.ttl_cache(ttl=300)
    async def get_coupon_usage_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        seller_id: Optional[int] = None,
    ) -> List[Dict]:
        """Aggregate coupon usage: how many orders used each coupon and total discount given."""
        order_filter = self._build_order_filter(start_date=start_date, end_date=end_date)
        orders = await self.order_storage.findAll(order_filter)
        orders = self._filter_by_seller(orders, seller_id)

        coupon_stats: dict = {}
        for order in orders:
            code = order.coupon_code
            if not code:
                continue
            if code not in coupon_stats:
                coupon_info = order.couponInfo or {}
                coupon_stats[code] = {
                    "couponCode": code,
                    "discountType": coupon_info.discountType,
                    "discountValue": coupon_info.discountValue,
                    "usageCount": 0,
                    "totalDiscountGiven": 0.0,
                    "totalRevenue": 0.0,
                }
            coupon_stats[code]["usageCount"] += 1
            coupon_stats[code]["totalDiscountGiven"] += order.discount or 0
            coupon_stats[code]["totalRevenue"] += order.total

        result = list(coupon_stats.values())
        for item in result:
            item.totalDiscountGiven = round(item.totalDiscountGiven, 2)
            item.totalRevenue = round(item.totalRevenue, 2)

        return sorted(result, key=lambda x: x["usageCount"], reverse=True)

    @cache.ttl_cache(ttl=300)
    async def get_sales_by_location(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        seller_id: Optional[int] = None,
    ) -> List[Dict]:
        """Aggregate sales by shipping address city/state."""
        order_filter = self._build_order_filter(start_date=start_date, end_date=end_date)
        orders = await self.order_storage.findAll(order_filter)
        orders = self._filter_by_seller(orders, seller_id)

        location_stats: dict = {}
        for order in orders:
            # We only count completed/delivered/shipped orders
            if order.status not in ["delivered", "completed", "shipped", "dispatched"]:
                continue

            shipping = order.shipping_address or {}
            city = shipping.city
            state = shipping.state

            if not city and not state:
                location = "Unknown"
            elif city and state:
                location = f"{city}, {state}"
            else:
                location = city or state

            if location not in location_stats:
                location_stats[location] = {"location": location, "revenue": 0.0, "orderCount": 0, "quantity": 0}

            location_stats[location]["revenue"] += order.total
            location_stats[location]["orderCount"] += 1
            for item in order.items:
                location_stats[location]["quantity"] += item.quantity

        result = list(location_stats.values())
        for item in result:
            item.revenue = round(item.revenue, 2)

        return sorted(result, key=lambda x: x["revenue"], reverse=True)[:limit]

    @cache.ttl_cache(ttl=300)
    async def get_new_vs_returning_customer_sales(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Compare revenue and orders from new customers (1 order) vs returning customers (>1 order)."""
        orders = await self.order_storage.findAll()
        # Find all orders ever to determine user's global order count
        user_total_orders = defaultdict(int)
        for order in orders:
            user_id = order.user
            if user_id:
                user_total_orders[user_id] += 1

        # Now filter for the period
        period_orders = self._filter_by_date_range(orders, start_date, end_date)

        stats = {
            "New Customers": {"customerType": "New Customers", "revenue": 0.0, "orderCount": 0},
            "Returning Customers": {"customerType": "Returning Customers", "revenue": 0.0, "orderCount": 0},
        }

        for order in period_orders:
            # We only count active orders
            if order.status in ["cancelled", "declined"]:
                continue

            user_id = order.user
            if not user_id:
                continue

            ctype = "New Customers" if user_total_orders[user_id] == 1 else "Returning Customers"
            stats[ctype]["revenue"] += order.total
            stats[ctype]["orderCount"] += 1

        result = [stats["New Customers"], stats["Returning Customers"]]
        for item in result:
            item.revenue = round(item.revenue, 2)

        return result

    @cache.ttl_cache(ttl=300)
    async def get_items_bought_together(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, limit: int = 50
    ) -> List[Dict]:
        """Market basket analysis: find pairs of products frequently bought together."""
        order_filter = self._build_order_filter(start_date=start_date, end_date=end_date)
        orders = await self.order_storage.findAll(order_filter)

        products = await self.product_storage.findAll()

        pair_counts = defaultdict(int)

        for order in orders:
            # We only count active orders
            if order.status in ["cancelled", "declined"]:
                continue

            items = order.items
            # Extract unique product IDs in this order
            product_ids = list(
                set(
                    item.product or item.product_id
                    for item in items
                    if (item.product or item.product_id)
                )
            )

            # Generate all unique pairs
            for i in range(len(product_ids)):
                for j in range(i + 1, len(product_ids)):
                    # Sort to ensure (A,B) is the same as (B,A)
                    pair = tuple(sorted([product_ids[i], product_ids[j]]))
                    pair_counts[pair] += 1

        result = []
        for (prod_a_id, prod_b_id), count in pair_counts.items():
            product_a = next((p for p in products if p.id == prod_a_id), None) if prod_a_id else None
            product_b = next((p for p in products if p.id == prod_b_id), None) if prod_b_id else None
            if not product_a or not product_b:
                continue

            result.append(
                {
                    "productAId": prod_a_id,
                    "productAName": product_a.name,
                    "productBId": prod_b_id,
                    "productBName": product_b.name,
                    "frequency": count,
                }
            )

        return sorted(result, key=lambda x: x["frequency"], reverse=True)[:limit]

    @cache.ttl_cache(ttl=300)
    async def get_sales_by_device_type(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Aggregate sales by the user's device type. Note: Depends on device tracking mapping to orders."""
        # For this we need to match orders to sessions or user agents.
        # Since orders don't directly store deviceType, we can try to find a session match or fallback
        # Let's see if orders have sessionId
        order_filter = self._build_order_filter(start_date=start_date, end_date=end_date)
        orders = await self.order_storage.findAll(order_filter)

        sessions = await self.session_storage.findAll()

        stats = {
            "desktop": {"deviceType": "desktop", "revenue": 0.0, "orderCount": 0},
            "mobile": {"deviceType": "mobile", "revenue": 0.0, "orderCount": 0},
            "tablet": {"deviceType": "tablet", "revenue": 0.0, "orderCount": 0},
            "unknown": {"deviceType": "unknown", "revenue": 0.0, "orderCount": 0},
        }

        for order in orders:
            if order.status in ["cancelled", "declined"]:
                continue

            session_id = order.session_id
            device_type = "unknown"
            session_obj = next((s for s in sessions if s.session_id == session_id), None) if session_id else None
            if session_obj:
                s_device = session_obj.device or {}
                device_type = (s_device["type"] if "type" in s_device else "unknown").lower()

            if device_type not in stats:
                device_type = "unknown"

            stats[device_type]["revenue"] += order.total
            stats[device_type]["orderCount"] += 1

        result = list(stats.values())
        # Filter out zeroes
        result = [r for r in result if r.orderCount > 0]
        for item in result:
            item.revenue = round(item.revenue, 2)

        return sorted(result, key=lambda x: x["revenue"], reverse=True)

    @cache.ttl_cache(ttl=300)
    async def get_top_returned_products(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        seller_id: Optional[int] = None,
    ) -> List[TopReturnedProductsResponse]:
        """Find products that are returned the most."""
        return await self.order_storage.get_top_returned_products_stats(
            start_date=start_date, end_date=end_date, limit=limit, seller_id=seller_id
        )

    @cache.ttl_cache(ttl=300)
    async def get_inventory_value_by_category(
        self,
        seller_id: Optional[int] = None,
    ) -> List[InventoryValueByCategoryResponse]:
        """Calculate total tied up capital in inventory grouped by category."""
        return await self.order_storage.get_inventory_value_by_category_stats(
            seller_id=seller_id
        )

    async def precompute_dashboard_reports(self, ist_timestamp: Optional[str] = None) -> DashboardReportsCache:
        """Precomputes the heavy reporting metrics and writes to the cache."""
        from app.repositories.tracking_repository import tracking_repository

        ist_ts = ist_timestamp or _get_current_ist_timestamp()
        top_products = await self.get_sales_by_product(None, None, 10)
        top_wholesalers = await self.get_top_users_by_revenue("wholesaler", None, None, 10)
        top_customers = await self.get_top_users_by_revenue("customer", None, None, 10)
        most_searched = await tracking_repository.getMostSearched(10, None, None)
        most_viewed = await tracking_repository.getMostViewed(10, None, None)

        payload = DashboardReportsCache(
            last_updated_at_ist=ist_ts,
            top_products=top_products,
            top_wholesalers=top_wholesalers,
            top_customers=top_customers,
            most_searched=[s.model_dump() for s in most_searched],
            most_viewed=[v.model_dump() for v in most_viewed],
        )
        _write_analytics_reports_cache(payload)
        return payload

    async def get_dashboard_data(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict:
        """Aggregated dashboard stats for the admin panel.
        Live orders, users, and product metrics are pushed to SQL.
        Reporting and analytics sections use scheduled 6-hour cache.
        """
        from app.repositories.tracking_repository import tracking_repository

        _order_filter = self._build_order_filter(start_date=start_date, end_date=end_date)

        # 1. LIVE Orders Data (via SQL pushdown)
        summary_stats = await self.order_storage.get_summary_stats(_order_filter)
        total_orders = summary_stats.total_orders
        total_revenue = summary_stats.total_revenue

        # 2. LIVE Users Data (via SQL pushdown)
        user_counts = await self.user_storage.get_user_counts_by_role()
        total_customers = user_counts.customer
        total_wholesalers = user_counts.wholesaler
        total_valets = user_counts.valet

        # 3. LIVE Products Count (via SQL pushdown)
        total_products = await self.product_storage.get_active_products_count()

        # 4. REPORTING & ANALYTICS (Stale / Scheduled Cache)
        last_updated_at_ist = None
        if not start_date and not end_date:
            cached = _read_analytics_reports_cache()
            if not cached:
                cached = await self.precompute_dashboard_reports()
            top_products = cached.top_products
            top_wholesalers = cached.top_wholesalers
            top_customers = cached.top_customers
            most_searched = cached.most_searched
            most_viewed = cached.most_viewed
            last_updated_at_ist = cached.last_updated_at_ist
        else:
            top_products = await self.get_sales_by_product(start_date, end_date, 10)
            top_wholesalers = await self.get_top_users_by_revenue("wholesaler", start_date, end_date, 10)
            top_customers = await self.get_top_users_by_revenue("customer", start_date, end_date, 10)
            most_searched = await tracking_repository.getMostSearched(10, start_date, end_date)
            most_viewed = await tracking_repository.getMostViewed(10, start_date, end_date)
            last_updated_at_ist = _get_current_ist_timestamp()

        from app.routers.analytics import DashboardDataResponse, DashboardStats
        return DashboardDataResponse(
            stats=DashboardStats(
                totalProducts=total_products,
                totalWholesalers=total_wholesalers,
                totalCustomers=total_customers,
                totalValets=total_valets,
                totalOrders=total_orders,
                totalRevenue=round(total_revenue, 2),
            ),
            top_products=top_products,
            top_wholesalers=top_wholesalers,
            top_customers=top_customers,
            most_searched=most_searched,
            most_viewed=most_viewed,
            last_updated_at_ist=last_updated_at_ist,
        )

    @cache.ttl_cache(ttl=300)
    async def get_bundle_performance_report(self) -> Dict:
        """
        Generate a performance report for all bundles.
        Returns total copies sold, order count, total revenue, and monthly trends per bundle.
        """
        return {"report": await self.order_storage.get_bundle_performance_report_stats()}

    # ─────────────────────────────────────────────────────────────────────────
    # ADDITIONAL REPORTS
    # ─────────────────────────────────────────────────────────────────────────

    @cache.ttl_cache(ttl=60)
    async def get_sessions_over_time(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        seller_id: Optional[int] = None,
    ) -> List[Dict]:
        """Daily session count and unique visitor count from tracking data."""
        sessions = await self.tracking_storage.find_by_date_range("session", start_date, end_date)

        by_day: dict = {}
        for s in sessions:
            ts = self._parse_date(s.timestamp)
            if not ts:
                continue
            day = ts.strftime("%Y-%m-%d")
            if day not in by_day:
                by_day[day] = {"sessions": 0, "visitors": set()}
            by_day[day]["sessions"] += 1
            uid = s.userId
            if uid:
                by_day[day]["visitors"].add(uid)

        return [
            {"period": day, "sessions": data.sessions, "uniqueVisitors": len(data.visitors)}
            for day, data in sorted(by_day.items())
        ]

    @cache.ttl_cache(ttl=30)
    async def get_active_visitors_now(self, seller_id: Optional[int] = None) -> VisitorsNowResponse:
        """Count of unique sessions active in the last 15 minutes."""
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=15)
        sessions = await self.tracking_storage.findAll({"type": "session"})

        active, logged_in, guest = set(), set(), set()
        for s in sessions:
            ts = self._to_naive_utc(self._parse_date(s.timestamp))
            if not ts or ts < cutoff:
                continue
            sid = s.session_id
            if not sid:
                continue
            active.add(sid)
            if s.userId:
                logged_in.add(sid)
            else:
                guest.add(sid)

        return VisitorsNowResponse(
            activeVisitors=len(active),
            loggedInSessions=len(logged_in),
            guestSessions=len(guest),
            windowMinutes=15,
        )

    @cache.ttl_cache(ttl=300)
    async def get_searches_with_no_clicks(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        seller_id: Optional[int] = None,
    ) -> List[Dict]:
        """Search terms whose sessions never produced a product_click event."""
        searches = await self.tracking_storage.find_by_date_range("product_search", start_date, end_date)

        clicks = await self.tracking_storage.findAll({"type": "product_click"})
        clicked_sessions = {c.session_id for c in clicks if c.session_id}

        term_stats: dict = {}
        for s in searches:
            sid = s.session_id
            if sid in clicked_sessions:
                continue  # this session had a click — skip
            term = (s.search_term or "").strip().lower()
            if not term:
                continue
            if term not in term_stats:
                term_stats[term] = {"searchCount": 0, "totalResults": 0}
            term_stats[term]["searchCount"] += 1
            term_stats[term]["totalResults"] += s.results_count

        result = [
            {
                "term": term,
                "searchCount": data.searchCount,
                "avgResults": round(data.totalResults / data.searchCount, 1) if data.searchCount else 0,
            }
            for term, data in term_stats.items()
        ]
        return sorted(result, key=lambda x: x["searchCount"], reverse=True)

    @cache.ttl_cache(ttl=300)
    async def get_search_conversion_rate(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        seller_id: Optional[int] = None,
    ) -> List[Dict]:
        """Percentage of sessions that searched AND placed an order."""
        searches = await self.tracking_storage.find_by_date_range("product_search", start_date, end_date)
        search_sessions = {s.session_id for s in searches if s.session_id}

        order_filter = self._build_order_filter(start_date=start_date, end_date=end_date)
        orders = await self.order_storage.findAll(order_filter)
        order_sessions = {o.session_id for o in orders if o.session_id}

        total = len(search_sessions)
        converted = len(search_sessions & order_sessions)
        not_converted = total - converted
        rate = round(converted / total * 100, 2) if total > 0 else 0.0

        return [
            {
                "totalSearchSessions": total,
                "convertedSessions": converted,
                "nonConvertedSessions": not_converted,
                "conversionRate": rate,
            }
        ]

    @cache.ttl_cache(ttl=300)
    async def get_bounce_rate_over_time(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        seller_id: Optional[int] = None,
    ) -> List[Dict]:
        """Daily bounce rate: sessions with only 1 page view / total sessions."""
        page_views = await self.tracking_storage.find_by_date_range("page_view", start_date, end_date)

        # Count page views per (day, sessionId)
        session_day: dict = {}  # sid -> day
        session_views: dict = {}  # sid -> count
        for pv in page_views:
            sid = pv.session_id
            ts = self._parse_date(pv.timestamp)
            if not sid or not ts:
                continue
            day = ts.strftime("%Y-%m-%d")
            session_day.setdefault(sid, day)
            session_views[sid] = (session_views[sid] if sid in session_views else 0) + 1

        by_day: dict = {}
        for sid, day in session_day.items():
            if day not in by_day:
                by_day[day] = {"total": 0, "bounced": 0}
            by_day[day]["total"] += 1
            if (session_views[sid] if sid in session_views else 0) <= 1:
                by_day[day]["bounced"] += 1

        return [
            {
                "period": day,
                "totalSessions": data.total,
                "bouncedSessions": data.bounced,
                "bounceRate": round(data.bounced / data.total * 100, 1) if data.total else 0.0,
            }
            for day, data in sorted(by_day.items())
        ]

    @cache.ttl_cache(ttl=600)
    async def get_rfm_segments(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        seller_id: Optional[int] = None,
    ) -> List[RFMSegmentsResponse]:
        """RFM segmentation: Champions, Loyal, Promising, At Risk, Dormant."""
        return await self.order_storage.get_rfm_segments_stats(
            start_date=start_date, end_date=end_date, seller_id=seller_id
        )

    @cache.ttl_cache(ttl=600)
    async def get_customer_frequency_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        seller_id: Optional[int] = None,
    ) -> List[CustomerFrequencyResponse]:
        """Split of one-time vs repeat buyers with revenue per group."""
        return await self.order_storage.get_customer_frequency_stats(
            start_date=start_date, end_date=end_date, seller_id=seller_id
        )

    @cache.ttl_cache(ttl=300)
    async def get_net_sales_by_order(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        seller_id: Optional[int] = None,
    ) -> List[NetSalesResponse]:
        """Per-order breakdown: gross sales → discounts → tax → shipping → net sales."""
        return await self.order_storage.get_net_sales_by_order_stats(
            start_date=start_date, end_date=end_date, seller_id=seller_id
        )

    @cache.ttl_cache(ttl=300)
    async def get_sales_heatmap(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        seller_id: Optional[int] = None,
    ) -> List[SalesHeatmapResponse]:
        """Order volume and revenue grouped by day-of-week (0=Mon) and hour-of-day (0-23)."""
        return await self.order_storage.get_sales_heatmap_stats(
            start_date=start_date, end_date=end_date, seller_id=seller_id
        )

    @cache.ttl_cache(ttl=300)
    async def get_inventory_runway(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        seller_id: Optional[int] = None,
    ) -> List[InventoryRunwayResponse]:
        """Days of stock remaining per product based on 30-day average daily sales velocity."""
        return await self.order_storage.get_inventory_runway_stats(
            start_date=start_date, end_date=end_date, seller_id=seller_id
        )

    @cache.ttl_cache(ttl=300)
    async def get_sales_by_channel_detailed(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[SalesByChannelDetailedResponse]:
        """Revenue, order count, and AOV broken down by sales channel (desktop_web / mobile_web / mobile_app)."""
        return await self.order_storage.get_sales_by_channel_detailed_stats(
            start_date=start_date, end_date=end_date
        )

    @cache.ttl_cache(ttl=300)
    async def get_discounts_audit(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        seller_id: Optional[int] = None,
    ) -> List[DiscountsAuditResponse]:
        """Per-order line-item audit: coupon code, discount type/value, gross, discount applied, net."""
        return await self.order_storage.get_discounts_audit_stats(
            start_date=start_date, end_date=end_date, seller_id=seller_id
        )

    @cache.ttl_cache(ttl=300)
    async def get_products_pct_sold(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        seller_id: Optional[int] = None,
    ) -> List[ProductsPctSoldResponse]:
        """Units sold in the period as a % of current stock (sell-through by quantity)."""
        return await self.order_storage.get_products_pct_sold_stats(
            start_date=start_date, end_date=end_date, seller_id=seller_id
        )


analytics_repository = AnalyticsRepository()


