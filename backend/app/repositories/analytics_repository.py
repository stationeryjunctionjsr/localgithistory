from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.utils.cache import cache

from app.db.storage_factory import get_storage


class AnalyticsRepository:
    def __init__(self):
        self.order_storage = get_storage("orders")
        self.product_storage = get_storage("products")
        self.user_storage = get_storage("users")
        self.cart_storage = get_storage("carts")
        self.event_storage = get_storage("events")
        self.session_storage = get_storage("sessions")
        self.tracking_storage = get_storage("tracking")

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str:
            return None
        try:
            # Handle ISO format with or without Z
            date_str = date_str.replace("Z", "+00:00")
            return datetime.fromisoformat(date_str)
        except Exception:
            return None

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
                item_date = self._parse_date(item.createdAt if item.createdAt is not None else "")
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
        orders = await self.order_storage.findAll()
        orders = self._filter_by_date_range(orders, start_date, end_date)

        await self.user_storage.findAll()

        # Gross sales (total revenue)
        gross_sales = sum(order.total for order in orders)

        # Orders
        total_orders = len(orders)

        # Orders fulfilled (completed orders)
        orders_fulfilled = len([o for o in orders if o.status in ["delivered", "completed", "dispatched"]])

        # Returning customer rate
        user_order_counts = defaultdict(int)
        for order in orders:
            user_id = order.user
            if user_id:
                user_order_counts[user_id] += 1

        returning_customers = len([uid for uid, count in user_order_counts.items() if count > 1])
        total_customers = len(user_order_counts)
        returning_customer_rate = (returning_customers / total_customers * 100) if total_customers > 0 else 0

        return {
            "gross_sales": gross_sales,
            "returning_customer_rate": round(returning_customer_rate, 2),
            "orders_fulfilled": orders_fulfilled,
            "orders": total_orders,
        }

    @cache.ttl_cache(ttl=300)
    async def get_sales_over_time(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, group_by: str = "hour"
    ) -> List[Dict]:
        """Get sales over time, grouped by hour, day, or month"""
        orders = await self.order_storage.findAll()
        orders = self._filter_by_date_range(orders, start_date, end_date)

        sales_by_period = {}

        for order in orders:
            order_date = self._parse_date(order.createdAt)
            if not order_date:
                continue

            if group_by == "hour":
                period_key = order_date.strftime("%Y-%m-%d %H:00")
            elif group_by == "day":
                period_key = order_date.strftime("%Y-%m-%d")
            elif group_by == "month":
                period_key = order_date.strftime("%Y-%m")
            else:
                period_key = order_date.strftime("%Y-%m-%d")

            if period_key not in sales_by_period:
                sales_by_period[period_key] = {"sales": 0.0, "orderCount": 0}

            sales_by_period[period_key]["sales"] += order.total
            sales_by_period[period_key]["orderCount"] += 1

        # Convert to list and sort
        result = []
        for period, data in sorted(sales_by_period.items()):
            sales = round(data.sales, 2)
            orders_count = data.orderCount
            aov = round(sales / orders_count, 2) if orders_count > 0 else 0
            result.append({"period": period, "sales": sales, "orderCount": orders_count, "aov": aov})

        return result

    @cache.ttl_cache(ttl=300)
    async def get_sales_breakdown(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict:
        """Get sales breakdown: Gross sales, Discounts, Returns, Net sales, Shipping, Taxes"""
        orders = await self.order_storage.findAll()
        orders = self._filter_by_date_range(orders, start_date, end_date)

        gross_sales = 0
        total_discounts = 0
        total_shipping = 0
        total_taxes = 0

        for order in orders:
            gross_sales += order.total
            if order.discount is None:
                raise ValueError('Order discount is None')
            total_discounts += order.discount
            if order.deliveryCharge is None:
                raise ValueError('Order deliveryCharge is None')
            total_shipping += order.deliveryCharge
            if order.tax is None:
                raise ValueError('Order tax is None')
            total_taxes += order.tax

        # Returns (orders with status 'returned' or 'cancelled')
        returned_orders = [o for o in orders if o.status in ["returned", "cancelled"]]
        returns = sum(o.total for o in returned_orders)

        net_sales = gross_sales - total_discounts - returns

        return {
            "gross_sales": gross_sales,
            "discounts": total_discounts,
            "returns": returns,
            "net_sales": net_sales,
            "shipping_charges": total_shipping,
            "return_fees": 0,  # Can be calculated if return fees are tracked
            "taxes": total_taxes,
            "total_sales": gross_sales,
        }

    @cache.ttl_cache(ttl=300)
    async def get_average_order_value_over_time(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, group_by: str = "hour"
    ) -> List[Dict]:
        """Get average order value over time"""
        orders = await self.order_storage.findAll()
        orders = self._filter_by_date_range(orders, start_date, end_date)

        from pydantic import BaseModel
        class OrderPeriodStats(BaseModel):
            total: float = 0.0
            count: int = 0

        orders_by_period = defaultdict(OrderPeriodStats)

        for order in orders:
            order_date = self._parse_date(order.createdAt)
            if not order_date:
                continue

            if group_by == "hour":
                period_key = order_date.strftime("%Y-%m-%d %H:00")
            elif group_by == "day":
                period_key = order_date.strftime("%Y-%m-%d")
            elif group_by == "month":
                period_key = order_date.strftime("%Y-%m")
            else:
                period_key = order_date.strftime("%Y-%m-%d")

            orders_by_period[period_key].total += order.total
            orders_by_period[period_key].count += 1

        result = [
            {"period": period, "average_order_value": data.total / data.count if data.count > 0 else 0}
            for period, data in sorted(orders_by_period.items())
        ]

        return result

    @cache.ttl_cache(ttl=300)
    async def get_sales_by_channel(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Get sales by sales channel"""
        orders = await self.order_storage.findAll()
        orders = self._filter_by_date_range(orders, start_date, end_date)

        sales_by_channel = {"desktop_web": 0, "mobile_web": 0, "mobile_app": 0}

        for order in orders:
            # Determine channel from order data
            channel = order.channel
            if channel not in sales_by_channel:
                channel = "desktop_web"
            sales_by_channel[channel] += order.total

        result = [{"channel": channel, "sales": sales} for channel, sales in sales_by_channel.items()]

        return result

    @cache.ttl_cache(ttl=300)
    async def get_sales_by_product(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, limit: int = 10
    ) -> List[Dict]:
        """Get top products by sales"""
        orders = await self.order_storage.findAll()
        orders = self._filter_by_date_range(orders, start_date, end_date)

        products = await self.product_storage.findAll()
        product_map = {p.id: p for p in products}

        from pydantic import BaseModel
        class ProductSalesStats(BaseModel):
            quantity: int = 0
            revenue: float = 0.0
            name: str = "Unknown Product"

        product_sales = defaultdict(ProductSalesStats)

        for order in orders:
            for item in order.items:
                product_id = item.product or item.productId
                if not product_id:
                    continue

                product = product_map.get(product_id)
                quantity = item.quantity
                subtotal = (item.price * item.quantity)

                product_sales[product_id].quantity += quantity
                product_sales[product_id].revenue += subtotal
                product_sales[product_id].name = product.name

        result = [
            {
                "product_id": product_id,
                "productId": product_id,
                "name": data.name,
                "productName": data.name,
                "quantity": data.quantity,
                "revenue": data.revenue,
            }
            for product_id, data in sorted(
                product_sales.items(),
                key=lambda x: (x[1].quantity, x[1].revenue),
                reverse=True,
            )
        ][:limit]

        return result

    @cache.ttl_cache(ttl=300)
    async def get_conversion_rate_over_time(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, group_by: str = "hour"
    ) -> Dict:
        """Get conversion rate over time (orders / sessions) calculated from actual tracking events"""
        orders = await self.order_storage.findAll()
        orders = self._filter_by_date_range(orders, start_date, end_date)

        # 1. Sessions count (unique sessions in the date range)
        sessions_tracking = await self.tracking_storage.findAll({"type": "session"})
        sessions_tracking = self._filter_by_date_range(sessions_tracking, start_date, end_date, "timestamp")
        session_count = len(set(s.sessionId for s in sessions_tracking if s.sessionId))

        # Fallback to estimated sessions if zero tracking traffic exists
        if session_count == 0:
            session_count = len(orders) * 10 if orders else 10

        # 2. Cart Additions (unique sessions adding items to cart)
        cart_add_tracking = await self.tracking_storage.findAll({"type": "cart_add"})
        cart_add_tracking = self._filter_by_date_range(cart_add_tracking, start_date, end_date, "timestamp")
        added_to_cart_count = len(set(c.sessionId for c in cart_add_tracking if c.sessionId))

        # Fallback if no cart additions tracked
        if added_to_cart_count == 0:
            carts = await self.cart_storage.findAll()
            carts = self._filter_by_date_range(carts, start_date, end_date)
            added_to_cart_count = len(carts) + len([o for o in orders if o.status not in ["cancelled"]])

        # Enforce valid funnel hierarchy
        added_to_cart_count = min(session_count, added_to_cart_count)

        # 3. Reached Checkout (unique sessions landing on checkout page step 1)
        checkout_tracking = await self.tracking_storage.findAll({"type": "page_view", "page": "/checkout/step1"})
        checkout_tracking = self._filter_by_date_range(checkout_tracking, start_date, end_date, "timestamp")
        reached_checkout_count = len(set(c.sessionId for c in checkout_tracking if c.sessionId))

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
        orders = await self.order_storage.findAll()
        orders = self._filter_by_date_range(orders, start_date, end_date)

        async def get_unique_sessions_for_page(page_path: str) -> int:
            events = await self.tracking_storage.findAll({"type": "page_view", "page": page_path})
            events = self._filter_by_date_range(events, start_date, end_date, "timestamp")
            return len(set(e.sessionId for e in events if e.sessionId))

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

        def make_stage(count, total):
            pct = (count / total * 100) if total > 0 else 0
            return {"count": count, "percentage": pct}

        drop_cart_to_step1 = ((cart_sessions - step1_sessions) / cart_sessions * 100) if cart_sessions > 0 else 0
        drop_step1_to_step2 = ((step1_sessions - step2_sessions) / step1_sessions * 100) if step1_sessions > 0 else 0
        drop_step2_to_step3 = ((step2_sessions - step3_sessions) / step2_sessions * 100) if step2_sessions > 0 else 0
        drop_step3_to_complete = (
            ((step3_sessions - completed_sessions) / step3_sessions * 100) if step3_sessions > 0 else 0
        )

        return {
            "cart": make_stage(cart_sessions, cart_sessions),
            "shipping": {**make_stage(step1_sessions, cart_sessions), "drop_percentage": drop_cart_to_step1},
            "review": {**make_stage(step2_sessions, cart_sessions), "drop_percentage": drop_step1_to_step2},
            "payment": {**make_stage(step3_sessions, cart_sessions), "drop_percentage": drop_step2_to_step3},
            "completed": {**make_stage(completed_sessions, cart_sessions), "drop_percentage": drop_step3_to_complete},
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
            device_type = s.device.get("type", "desktop") if s.device else "desktop"
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
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, limit: int = 10
    ) -> List[Dict]:
        """Get products by sell-through rate"""
        orders = await self.order_storage.findAll()
        orders = self._filter_by_date_range(orders, start_date, end_date)

        products = await self.product_storage.findAll()
        {p.id: p for p in products}

        from pydantic import BaseModel
        class ProductStats(BaseModel):
            sold: int = 0
            stock: int = 0
            name: str = "Unknown"

        product_stats = defaultdict(ProductStats)

        for product in products:
            product_id = product.id
            product_stats[product_id].stock = product.stock
            product_stats[product_id].name = product.name

        for order in orders:
            for item in order.items:
                product_id = item.product or item.productId
                if product_id:
                    product_stats[product_id].sold += item.quantity

        result = []
        for product_id, stats in product_stats.items():
            total_available = stats.stock + stats.sold
            sell_through_rate = (stats.sold / total_available * 100) if total_available > 0 else 0

            result.append(
                {
                    "product_id": product_id,
                    "name": stats.name,
                    "sold": stats.sold,
                    "stock": stats.stock,
                    "sell_through_rate": round(sell_through_rate, 2),
                }
            )

        result = sorted(result, key=lambda x: x["sell_through_rate"], reverse=True)[:limit]
        return result

    @cache.ttl_cache(ttl=300)
    async def get_customer_cohort_analysis(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Get customer cohort analysis"""
        orders = await self.order_storage.findAll()
        await self.user_storage.findAll()

        # Group users by acquisition month (first order month)
        user_first_order = {}
        for order in orders:
            user_id = order.user
            if not user_id:
                continue

            order_date = self._parse_date(order.createdAt)
            if not order_date:
                continue

            if user_id not in user_first_order:
                user_first_order[user_id] = order_date
            elif order_date < user_first_order[user_id]:
                user_first_order[user_id] = order_date

        # Group by cohort month
        cohorts = defaultdict(lambda: defaultdict(int))

        for user_id, first_order_date in user_first_order.items():
            cohort_month = first_order_date.strftime("%Y-%m")

            # Count orders in subsequent months
            for order in orders:
                if order.user != user_id:
                    continue

                order_date = self._parse_date(order.createdAt)
                if not order_date:
                    continue

                order_month = order_date.strftime("%Y-%m")
                if order_month >= cohort_month:
                    month_index = (order_date.year - first_order_date.year) * 12 + (
                        order_date.month - first_order_date.month
                    )
                    cohorts[cohort_month][month_index] += 1

        # Format for display
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
        tracking = await self.tracking_storage.findAll({"type": "page_view"})
        tracking = self._filter_by_date_range(tracking, start_date, end_date, "timestamp")

        session_landing = {}
        for t in tracking:
            sid = t.sessionId
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

        user_map = {u.id: u for u in users}
        valid_sessions = [s for s in sessions if not s.isGuest]

        user_durations = defaultdict(list)
        user_session_counts = defaultdict(int)
        for s in valid_sessions:
            uid = s.userId
            if not uid:
                continue
            user_session_counts[uid] += 1
            start_dt = self._parse_date(s.createdAt)
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
        for uid in user_map.keys():
            durations = user_durations.get(uid, [])
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
                    "name": user_map[uid].name if user_map[uid].name else "Unknown",
                    "email": user_map[uid].email if user_map[uid].email else "Unknown",
                    "averageSessionTimeSeconds": round(avg_duration, 2),
                    "totalSessions": user_session_counts.get(uid, 0),
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
        sessions = [s for s in all_sessions if s.userId == user_id and not s.isGuest]
        if reg_naive is not None:
            sessions = [
                s
                for s in sessions
                if self._to_naive_utc(self._parse_date(s.createdAt)) is not None
                and self._to_naive_utc(self._parse_date(s.createdAt)) >= reg_naive
            ]

        total_sessions = len(sessions)
        registration_date_str = user.created_at

        # 1) Average session time (all devices): end = revokedAt or lastActiveAt, start = createdAt
        session_durations_sec = []
        for s in sessions:
            start_dt = self._to_naive_utc(self._parse_date(s.createdAt))
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
            [s for s in sessions if s.createdAt],
            key=lambda s: s.createdAt,
        )
        gaps_days = []
        for i in range(len(sorted_sessions) - 1):
            d1 = self._to_naive_utc(self._parse_date(sorted_sessions[i].createdAt))
            d2 = self._to_naive_utc(self._parse_date(sorted_sessions[i + 1].createdAt))
            if d1 and d2:
                gaps_days.append((d2 - d1).total_seconds() / 86400.0)
        average_days_between_sessions = round(sum(gaps_days) / len(gaps_days), 2) if gaps_days else None

        # 3) Average pages per session (page_view events from tracking, by sessionId)
        session_ids = {s.id for s in sessions if s.id}
        all_tracking = await self.tracking_storage.findAll()
        page_views_by_session = {sid: 0 for sid in session_ids}
        for t in all_tracking:
            if t.type != "page_view":
                continue
            sid = t.sessionId
            if sid in session_ids:
                page_views_by_session[sid] = page_views_by_session.get(sid, 0) + 1
        page_counts = list(page_views_by_session.values())
        average_pages_per_session = round(sum(page_counts) / len(page_counts), 2) if page_counts else None

        # 4) Average number of sessions with orders placed (rate: sessions with ≥1 order / total sessions)
        all_orders = await self.order_storage.findAll()
        orders_for_user = []
        for o in all_orders:
            if o.user != user_id:
                continue
            if reg_naive is not None:
                o_dt = self._to_naive_utc(self._parse_date(o.createdAt))
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

    async def record_event(self, event: Any) -> Dict:
        """Record an analytics event"""
        return await self.event_storage.create(event)

    @cache.ttl_cache(ttl=300)
    async def get_top_users_by_revenue(
        self,
        role: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """Get top users by revenue, optionally filtered by role"""
        orders = await self.order_storage.findAll()
        orders = self._filter_by_date_range(orders, start_date, end_date)

        users = await self.user_storage.findAll()
        user_map = {u.id: u for u in users}

        user_revenue = defaultdict(float)
        for order in orders:
            uid = order.user
            if not uid:
                continue
            user_revenue[uid] += order.total

        result = []
        for uid, revenue in user_revenue.items():
            user = user_map.get(uid)
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
        user_map = {u.id: u for u in users}

        user_orders_map = defaultdict(list)
        for order in orders:
            uid = order.user
            if not uid:
                continue
            user_orders_map[uid].append(order)

        result = []
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        for uid, u_orders in user_orders_map.items():
            user = user_map.get(uid)
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
            order_dates = [self._to_naive_utc(self._parse_date(o.createdAt)) for o in u_orders]
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
        all_tracking = await self.tracking_storage.findAll()

        # Filter by date
        filtered_tracking = []
        for t in all_tracking:
            ts = self._parse_date(t.timestamp or t.createdAt)
            if start_date and ts and ts < start_date:
                continue
            if end_date and ts and ts > end_date:
                continue
            filtered_tracking.append(t)

        users = await self.user_storage.findAll()
        user_role_map = {u.id: u.role for u in users}

        from pydantic import BaseModel
        class RoleStats(BaseModel):
            searches: int = 0
            views: int = 0

        role_stats = defaultdict(RoleStats)
        for t in filtered_tracking:
            uid = t.userId
            role = user_role_map.get(uid, "guest" if not uid else "customer")

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
        drop_offs = await tracking_repository.getDropOffPoints(1000, start_date, end_date)
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
            "user_engagement": len(engagement.get("user_metrics", [])),
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
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Aggregate returns/refund requests with order value and status."""
        from app.repositories.return_request_repository import return_request_repository

        all_returns = await return_request_repository.findAll()
        orders = await self.order_storage.findAll()
        order_map = {o._id: o for o in orders}
        users = await self.user_storage.findAll()
        user_map = {u.id: u for u in users}

        result = []
        for ret in all_returns:
            created = self._parse_date(ret.createdAt)
            if start_date and created and created < start_date:
                continue
            if end_date and created and created > end_date:
                continue

            order = order_map.get(ret.orderId)
            user = user_map.get(ret.userId)
            items = ret.items
            refund_value = sum((i.subtotal or i.price) * i.quantity for i in items)

            result.append(
                {
                    "returnId": ret.id,
                    "orderId": ret.orderId,
                    "orderTotal": order.total,
                    "userName": user.name,
                    "userEmail": user.email,
                    "status": ret.status,
                    "refundValue": round(refund_value, 2),
                    "itemCount": len(items),
                    "paymentMethod": ret.paymentMethod,
                    "createdAt": ret.createdAt,
                }
            )

        result.sort(key=lambda x: x.get("createdAt") or "", reverse=True)
        return result

    @cache.ttl_cache(ttl=300)
    async def get_payment_methods_report(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Aggregate order count and revenue by payment method."""
        orders = await self.order_storage.findAll()
        orders = self._filter_by_date_range(orders, start_date, end_date)

        method_stats: dict = {}
        for order in orders:
            method = order.paymentMethod or "unknown"
            if method not in method_stats:
                method_stats[method] = {"orderCount": 0, "revenue": 0.0, "avgOrderValue": 0.0}
            method_stats[method]["orderCount"] += 1
            method_stats[method]["revenue"] += order.total

        result = []
        for method, stats in method_stats.items():
            count = stats["orderCount"]
            result.append(
                {
                    "paymentMethod": method,
                    "orderCount": count,
                    "revenue": round(stats["revenue"], 2),
                    "avgOrderValue": round(stats["revenue"] / count, 2) if count > 0 else 0,
                }
            )

        return sorted(result, key=lambda x: x["revenue"], reverse=True)

    @cache.ttl_cache(ttl=300)
    async def get_revenue_by_category(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, limit: int = 20
    ) -> List[Dict]:
        """Aggregate revenue, quantity and order count by product category."""
        orders = await self.order_storage.findAll()
        orders = self._filter_by_date_range(orders, start_date, end_date)
        products = await self.product_storage.findAll()
        product_map = {p.id: p for p in products}

        category_stats: dict = {}
        for order in orders:
            for item in order.items:
                product_id = item.product or item.productId
                product = product_map.get(product_id)
                category = product.category or "Uncategorized"

                if category not in category_stats:
                    category_stats[category] = {"revenue": 0.0, "quantity": 0, "orders": set()}
                category_stats[category]["revenue"] += item.subtotal
                category_stats[category]["quantity"] += item.quantity
                category_stats[category]["orders"].add(order.id)

        result = [
            {
                "category": cat,
                "revenue": round(stats["revenue"], 2),
                "quantity": stats["quantity"],
                "orderCount": len(stats["orders"]),
            }
            for cat, stats in category_stats.items()
        ]

        return sorted(result, key=lambda x: x["revenue"], reverse=True)[:limit]

    @cache.ttl_cache(ttl=300)
    async def get_inventory_alerts(self, threshold: int = 10) -> List[Dict]:
        """Return products whose current stock is at or below `threshold`."""
        products = await self.product_storage.findAll()

        result = []
        for product in products:
            stock = product.stock or 0
            if stock <= threshold:
                result.append(
                    {
                        "productId": product.id,
                        "name": product.name,
                        "sku": product.sku,
                        "category": product.category,
                        "stock": stock,
                        "status": "out_of_stock" if stock == 0 else "low_stock",
                    }
                )

        return sorted(result, key=lambda x: x["stock"])

    @cache.ttl_cache(ttl=300)
    async def get_fulfillment_time_report(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Calculate fulfillment times for completed/delivered orders."""
        orders = await self.order_storage.findAll()
        orders = self._filter_by_date_range(orders, start_date, end_date)
        users = await self.user_storage.findAll()
        user_map = {u.id: u for u in users}

        TERMINAL_STATUSES = {"delivered", "completed", "cancelled", "returned"}

        result = []
        for order in orders:
            status = order.status
            if status not in TERMINAL_STATUSES:
                continue

            created_dt = self._to_naive_utc(self._parse_date(order.createdAt))
            updated_dt = self._to_naive_utc(self._parse_date(order.updatedAt))

            if not created_dt or not updated_dt:
                continue

            delta_hours = round((updated_dt - created_dt).total_seconds() / 3600, 1)
            if delta_hours < 0:
                continue

            user = user_map.get(order.user)
            result.append(
                {
                    "orderId": order.id,
                    "orderNumber": order.orderNumber,
                    "userName": user.name,
                    "status": status,
                    "fulfillmentHours": delta_hours,
                    "fulfillmentDays": round(delta_hours / 24, 1),
                    "orderTotal": order.total,
                    "createdAt": order.createdAt,
                }
            )

        result.sort(key=lambda x: x["createdAt"] or "", reverse=True)
        return result

    @cache.ttl_cache(ttl=300)
    async def get_coupon_usage_report(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Aggregate coupon usage: how many orders used each coupon and total discount given."""
        orders = await self.order_storage.findAll()
        orders = self._filter_by_date_range(orders, start_date, end_date)

        coupon_stats: dict = {}
        for order in orders:
            code = order.couponCode
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
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, limit: int = 100
    ) -> List[Dict]:
        """Aggregate sales by shipping address city/state."""
        orders = await self.order_storage.findAll()
        orders = self._filter_by_date_range(orders, start_date, end_date)

        location_stats: dict = {}
        for order in orders:
            # We only count completed/delivered/shipped orders
            if order.status not in ["delivered", "completed", "shipped", "dispatched"]:
                continue

            shipping = order.shippingAddress or {}
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
        orders = await self.order_storage.findAll()
        orders = self._filter_by_date_range(orders, start_date, end_date)

        products = await self.product_storage.findAll()
        product_map = {p.id: p for p in products}

        pair_counts = defaultdict(int)

        for order in orders:
            # We only count active orders
            if order.status in ["cancelled", "declined"]:
                continue

            items = order.items
            # Extract unique product IDs in this order
            product_ids = list(
                set(
                    item.product or item.productId
                    for item in items
                    if (item.product or item.productId)
                )
            )

            # Generate all unique pairs
            for i in range(len(product_ids)):
                for j in range(i + 1, len(product_ids)):
                    # Sort to ensure (A,B) is the same as (B,A)
                    pair = tuple(sorted([product_ids[i], product_ids[j]]))
                    pair_counts[pair] += 1

        result = []
        for pair, count in pair_counts.items():
            product_a = product_map.get(pair[0])
            product_b = product_map.get(pair[1])

            # Skip if products are deleted/missing
            if not product_a or not product_b:
                continue

            result.append(
                {
                    "productAId": pair[0],
                    "productAName": product_a.name,
                    "productBId": pair[1],
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
        orders = await self.order_storage.findAll()
        orders = self._filter_by_date_range(orders, start_date, end_date)

        sessions = await self.session_storage.findAll()
        session_map = {s.sessionId: s for s in sessions}

        stats = {
            "desktop": {"deviceType": "desktop", "revenue": 0.0, "orderCount": 0},
            "mobile": {"deviceType": "mobile", "revenue": 0.0, "orderCount": 0},
            "tablet": {"deviceType": "tablet", "revenue": 0.0, "orderCount": 0},
            "unknown": {"deviceType": "unknown", "revenue": 0.0, "orderCount": 0},
        }

        for order in orders:
            if order.status in ["cancelled", "declined"]:
                continue

            session_id = order.sessionId
            device_type = "unknown"
            if session_id and session_id in session_map:
                s_device = session_map[session_id].device or {}
                device_type = s_device.get("type", "unknown").lower()

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
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, limit: int = 50
    ) -> List[Dict]:
        """Find products that are returned the most."""
        from app.repositories.return_request_repository import return_request_repository

        returns = await return_request_repository.findAll()

        products = await self.product_storage.findAll()
        product_map = {p.id: p for p in products}

        product_returns = {}
        for req in returns:
            created = self._parse_date(req.createdAt)
            if start_date and created and created < start_date:
                continue
            if end_date and created and created > end_date:
                continue

            for item in req.items:
                pid = item.product or item.productId
                if not pid:
                    continue

                if pid not in product_returns:
                    product_returns[pid] = {
                        "productId": pid,
                        "returnCount": 0,
                        "quantityReturned": 0,
                        "revenueLost": 0.0,
                    }

                product_returns[pid]["returnCount"] += 1
                q = item.quantity
                product_returns[pid]["quantityReturned"] += q
                product_returns[pid]["revenueLost"] += q * item.price

        result = []
        for pid, stats in product_returns.items():
            product = product_map.get(pid)
            result.append(
                {
                    "productId": pid,
                    "productName": product.name,
                    "category": product.category,
                    "returnCount": stats["returnCount"],
                    "quantityReturned": stats["quantityReturned"],
                    "revenueLost": round(stats["revenueLost"], 2),
                }
            )

        return sorted(result, key=lambda x: x["returnCount"], reverse=True)[:limit]

    @cache.ttl_cache(ttl=300)
    async def get_inventory_value_by_category(self) -> List[Dict]:
        """Calculate total tied up capital in inventory grouped by category."""
        products = await self.product_storage.findAll()

        category_stats = {}
        for p in products:
            cat = p.category or "Uncategorized"
            if cat not in category_stats:
                category_stats[cat] = {"category": cat, "totalStock": 0, "inventoryValue": 0.0, "productCount": 0}

            stock = p.stock or 0
            # Assuming price is the value or mrp. If costPrice is absent, use price
            price = p.price or p.mrp or 0

            category_stats[cat]["totalStock"] += stock
            category_stats[cat]["inventoryValue"] += stock * price
            category_stats[cat]["productCount"] += 1

        result = list(category_stats.values())
        for item in result:
            item.inventoryValue = round(item.inventoryValue, 2)

        return sorted(result, key=lambda x: x["inventoryValue"], reverse=True)

    async def get_dashboard_data(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict:
        """Aggregated dashboard stats for the admin panel."""
        from app.repositories.tracking_repository import tracking_repository

        # Fetch raw collections (all cached individually by their methods)
        orders = await self.order_storage.findAll()
        users = await self.user_storage.findAll()
        products = await self.product_storage.findAll()

        filtered_orders = self._filter_by_date_range(orders, start_date, end_date)

        total_orders = len(filtered_orders)
        total_revenue = sum(o.total for o in filtered_orders)
        total_products = len(products)
        total_customers = sum(1 for u in users if u.role == "customer")
        total_wholesalers = sum(1 for u in users if u.role == "wholesaler")
        total_valets = sum(1 for u in users if u.role == "valet")

        top_products = await self.get_sales_by_product(start_date, end_date, 10)
        top_wholesalers = await self.get_top_users_by_revenue("wholesaler", start_date, end_date, 10)
        top_customers = await self.get_top_users_by_revenue("customer", start_date, end_date, 10)

        try:
            most_searched = await tracking_repository.getMostSearched(10, start_date, end_date)
        except Exception:
            most_searched = []
        try:
            most_viewed = await tracking_repository.getMostViewed(10, start_date, end_date)
        except Exception:
            most_viewed = []

        return {
            "stats": {
                "totalProducts": total_products,
                "totalWholesalers": total_wholesalers,
                "totalCustomers": total_customers,
                "totalValets": total_valets,
                "totalOrders": total_orders,
                "totalRevenue": round(total_revenue, 2),
            },
            "topProducts": top_products,
            "topWholesalers": top_wholesalers,
            "topCustomers": top_customers,
            "mostSearched": most_searched,
            "mostViewed": most_viewed,
        }

    async def get_bundle_performance_report(self) -> Dict:
        """
        Generate a performance report for all bundles.
        Returns total copies sold, order count, total revenue, and monthly trends per bundle.
        """
        from app.repositories.bundle_repository import bundle_repository
        
        bundles = await bundle_repository.findAll({})
        bundle_map = {str(b.id): b for b in bundles if b.id}
        
        # Initialize stats map
        # { bundle_id: { "order_count": int, "copies_sold": int, "revenue": float, "monthly": { "YYYY-MM": revenue } } }
        stats = {
            bid: {
                "bundle": b,
                "order_count": 0,
                "copies_sold": 0,
                "revenue": 0.0,
                "monthly": defaultdict(float)
            }
            for bid, b in bundle_map.items()
        }
        
        # Fetch all completed orders
        orders = await self.order_storage.find({"status": "completed"})
        for order in orders:
            items = order.items
            order_date = order.createdAt
            month_key = None
            if order_date:
                # parse date
                try:
                    if isinstance(order_date, str):
                        dt = datetime.fromisoformat(order_date.replace("Z", "+00:00"))
                    else:
                        dt = order_date
                    month_key = dt.strftime("%Y-%m")
                except:
                    pass
                    
            # Group items by bundleId in this order
            order_bundles = defaultdict(list)
            for item in items:
                b_id = item.bundleId
                if b_id:
                    order_bundles[b_id].append(item)
                    
            for b_id, b_items in order_bundles.items():
                if b_id not in stats:
                    continue
                b_def = bundle_map.get(b_id)
                if not b_def:
                    continue
                    
                b_specs = b_def.get("items", [])
                copies = 1
                if b_specs and b_items:
                    spec = b_specs[0]
                    spec_qty = max(1, spec.get("quantity", 1) or 1)
                    spec_pid = str(spec.get("productId", ""))
                    ref_item = next(
                        (i for i in b_items if str(i.product) == spec_pid or str(i.productId) == spec_pid),
                        b_items[0]
                    )
                    copies = max(1, ref_item.get("quantity", spec_qty) // spec_qty)
                
                b_price = b_def.get("price", 0.0)
                b_revenue = copies * b_price
                
                stats[b_id]["order_count"] += 1
                stats[b_id]["copies_sold"] += copies
                stats[b_id]["revenue"] += b_revenue
                if month_key:
                    stats[b_id]["monthly"][month_key] += b_revenue
                    
        # Format the result
        result = []
        for b_id, data in stats.items():
            b = data.bundle
            result.append({
                "bundleId": b_id,
                "name": b.name,
                "price": b.price,
                "isActive": b.isActive,
                "orderCount": data.order_count,
                "copiesSold": data.copies_sold,
                "totalRevenue": round(data.revenue, 2),
                "monthlyRevenue": {k: round(v, 2) for k, v in data.monthly.items()}
            })
            
        # Sort by revenue descending
        result.sort(key=lambda x: x["totalRevenue"], reverse=True)
        return {"report": result}

    # ─────────────────────────────────────────────────────────────────────────
    # ADDITIONAL REPORTS
    # ─────────────────────────────────────────────────────────────────────────

    @cache.ttl_cache(ttl=60)
    async def get_sessions_over_time(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        seller_id: Optional[str] = None,
    ) -> List[Dict]:
        """Daily session count and unique visitor count from tracking data."""
        sessions = await self.tracking_storage.findAll({"type": "session"})
        sessions = self._filter_by_date_range(sessions, start_date, end_date, "timestamp")

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
    async def get_active_visitors_now(self, seller_id: Optional[str] = None) -> List[Dict]:
        """Count of unique sessions active in the last 15 minutes."""
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=15)
        sessions = await self.tracking_storage.findAll({"type": "session"})

        active, logged_in, guest = set(), set(), set()
        for s in sessions:
            ts = self._to_naive_utc(self._parse_date(s.timestamp))
            if not ts or ts < cutoff:
                continue
            sid = s.sessionId
            if not sid:
                continue
            active.add(sid)
            if s.userId:
                logged_in.add(sid)
            else:
                guest.add(sid)

        return [
            {
                "activeVisitors": len(active),
                "loggedInSessions": len(logged_in),
                "guestSessions": len(guest),
                "windowMinutes": 15,
            }
        ]

    @cache.ttl_cache(ttl=300)
    async def get_searches_with_no_clicks(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        seller_id: Optional[str] = None,
    ) -> List[Dict]:
        """Search terms whose sessions never produced a product_click event."""
        searches = await self.tracking_storage.findAll({"type": "product_search"})
        searches = self._filter_by_date_range(searches, start_date, end_date, "timestamp")

        clicks = await self.tracking_storage.findAll({"type": "product_click"})
        clicked_sessions = {c.sessionId for c in clicks if c.sessionId}

        term_stats: dict = {}
        for s in searches:
            sid = s.sessionId
            if sid in clicked_sessions:
                continue  # this session had a click — skip
            term = (s.searchTerm or "").strip().lower()
            if not term:
                continue
            if term not in term_stats:
                term_stats[term] = {"searchCount": 0, "totalResults": 0}
            term_stats[term]["searchCount"] += 1
            term_stats[term]["totalResults"] += s.resultsCount

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
        seller_id: Optional[str] = None,
    ) -> List[Dict]:
        """Percentage of sessions that searched AND placed an order."""
        searches = await self.tracking_storage.findAll({"type": "product_search"})
        searches = self._filter_by_date_range(searches, start_date, end_date, "timestamp")
        search_sessions = {s.sessionId for s in searches if s.sessionId}

        orders = await self.order_storage.findAll()
        orders = self._filter_by_date_range(orders, start_date, end_date)
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
        seller_id: Optional[str] = None,
    ) -> List[Dict]:
        """Daily bounce rate: sessions with only 1 page view / total sessions."""
        page_views = await self.tracking_storage.findAll({"type": "page_view"})
        page_views = self._filter_by_date_range(page_views, start_date, end_date, "timestamp")

        # Count page views per (day, sessionId)
        session_day: dict = {}  # sid -> day
        session_views: dict = {}  # sid -> count
        for pv in page_views:
            sid = pv.sessionId
            ts = self._parse_date(pv.timestamp)
            if not sid or not ts:
                continue
            day = ts.strftime("%Y-%m-%d")
            session_day.setdefault(sid, day)
            session_views[sid] = session_views.get(sid, 0) + 1

        by_day: dict = {}
        for sid, day in session_day.items():
            if day not in by_day:
                by_day[day] = {"total": 0, "bounced": 0}
            by_day[day]["total"] += 1
            if session_views.get(sid, 0) <= 1:
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
        seller_id: Optional[str] = None,
    ) -> List[Dict]:
        """RFM segmentation: Champions, Loyal, Promising, At Risk, Dormant."""
        from datetime import timedelta

        orders = await self.order_storage.findAll()
        orders = self._filter_by_date_range(orders, start_date, end_date)
        users = await self.user_storage.findAll()
        user_map = {u.id: u for u in users}

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Per-customer stats
        stats: dict = {}
        for order in orders:
            uid = order.user
            if not uid:
                continue
            dt = self._to_naive_utc(self._parse_date(order.createdAt))
            if not dt:
                continue
            if uid not in stats:
                stats[uid] = {"lastOrder": dt, "count": 0, "spend": 0.0}
            if dt > stats[uid]["lastOrder"]:
                stats[uid]["lastOrder"] = dt
            stats[uid]["count"] += 1
            stats[uid]["spend"] += order.total

        result = []
        for uid, data in stats.items():
            recency_days = (now - data.lastOrder).days
            freq = data.count
            spend = round(data.spend, 2)

            # Simple rule-based RFM segment
            if recency_days <= 30 and freq >= 5:
                segment = "Champion"
            elif recency_days <= 60 and freq >= 3:
                segment = "Loyal"
            elif recency_days <= 90 and freq >= 2:
                segment = "Promising"
            elif recency_days <= 180:
                segment = "At Risk"
            else:
                segment = "Dormant"

            user = user_map.get(uid)
            result.append(
                {
                    "userId": uid,
                    "name": user.name,
                    "email": user.email,
                    "segment": segment,
                    "recencyDays": recency_days,
                    "orderCount": freq,
                    "totalSpend": spend,
                }
            )

        return sorted(result, key=lambda x: x["totalSpend"], reverse=True)

    @cache.ttl_cache(ttl=600)
    async def get_customer_frequency_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        seller_id: Optional[str] = None,
    ) -> List[Dict]:
        """Split of one-time vs repeat buyers with revenue per group."""
        orders = await self.order_storage.findAll()
        orders = self._filter_by_date_range(orders, start_date, end_date)

        user_stats: dict = {}
        for order in orders:
            uid = order.user
            if not uid:
                continue
            if uid not in user_stats:
                user_stats[uid] = {"orders": 0, "revenue": 0.0}
            user_stats[uid]["orders"] += 1
            user_stats[uid]["revenue"] += order.total

        one_time = [v for v in user_stats.values() if v["orders"] == 1]
        repeat = [v for v in user_stats.values() if v["orders"] > 1]
        total_customers = len(user_stats)

        def pct(n: int) -> str:
            return f"{round(n / total_customers * 100, 1)}" if total_customers else "0"

        return [
            {
                "type": "One-Time Buyers",
                "customers": len(one_time),
                "customerPct": pct(len(one_time)),
                "orders": sum(v["orders"] for v in one_time),
                "avgOrders": 1,
                "revenue": round(sum(v["revenue"] for v in one_time), 2),
            },
            {
                "type": "Repeat Buyers",
                "customers": len(repeat),
                "customerPct": pct(len(repeat)),
                "orders": sum(v["orders"] for v in repeat),
                "avgOrders": round(
                    sum(v["orders"] for v in repeat) / len(repeat), 1
                ) if repeat else 0,
                "revenue": round(sum(v["revenue"] for v in repeat), 2),
            },
        ]

    @cache.ttl_cache(ttl=300)
    async def get_net_sales_by_order(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        seller_id: Optional[str] = None,
    ) -> List[Dict]:
        """Per-order breakdown: gross sales → discounts → tax → shipping → net sales."""
        orders = await self.order_storage.findAll()
        orders = self._filter_by_date_range(orders, start_date, end_date)

        if seller_id:
            orders = [o for o in orders if str(o.sellerId) == str(seller_id)]

        users = await self.user_storage.findAll()
        user_map = {u.id: u for u in users}

        result = []
        for order in orders:
            if order.subtotal is None:
                raise ValueError('Order subtotal is None')
            subtotal = float(order.subtotal)
            if order.discount is None:
                raise ValueError('Order discount is None')
            discount = float(order.discount)
            if order.tax is None:
                raise ValueError('Order tax is None')
            tax = float(order.tax)
            shipping = float(order.shipping or order.deliveryCharge or 0)
            net = round(subtotal - discount + tax + shipping, 2)

            user = user_map.get(order.user)
            result.append(
                {
                    "orderId": order.id,
                    "orderNumber": order.orderNumber,
                    "customerName": user.name,
                    "grossSales": round(subtotal, 2),
                    "discount": round(discount, 2),
                    "tax": round(tax, 2),
                    "shipping": round(shipping, 2),
                    "netSales": net,
                    "status": order.status,
                    "createdAt": order.createdAt,
                }
            )

        return sorted(result, key=lambda x: x.get("createdAt") or "" or "", reverse=True)

    @cache.ttl_cache(ttl=300)
    async def get_sales_heatmap(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        seller_id: Optional[str] = None,
    ) -> List[Dict]:
        """Order volume and revenue grouped by day-of-week (0=Mon) and hour-of-day (0-23)."""
        DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        orders = await self.order_storage.findAll()
        orders = self._filter_by_date_range(orders, start_date, end_date)

        if seller_id:
            orders = [o for o in orders if str(o.sellerId) == str(seller_id)]

        heat: dict = {}
        for order in orders:
            dt = self._parse_date(order.createdAt)
            if not dt:
                continue
            key = (dt.weekday(), dt.hour)
            if key not in heat:
                heat[key] = {"orderCount": 0, "revenue": 0.0}
            heat[key]["orderCount"] += 1
            heat[key]["revenue"] += order.total

        return [
            {
                "dayOfWeek": DAY_NAMES[dow],
                "hour": hour,
                "orderCount": data.orderCount,
                "revenue": round(data.revenue, 2),
            }
            for (dow, hour), data in sorted(heat.items())
        ]

    @cache.ttl_cache(ttl=300)
    async def get_inventory_runway(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        seller_id: Optional[str] = None,
    ) -> List[Dict]:
        """Days of stock remaining per product based on 30-day average daily sales velocity."""
        from datetime import timedelta

        # 30-day window for velocity
        window_end = datetime.now(timezone.utc).replace(tzinfo=None)
        window_start = window_end - timedelta(days=30)

        orders = await self.order_storage.findAll()
        products = await self.product_storage.findAll()

        if seller_id:
            products = [p for p in products if str(p.sellerId) == str(seller_id)]

        product_map = {p.id: p for p in products}

        # Units sold per product in the last 30 days
        units_sold: dict = defaultdict(int)
        for order in orders:
            dt = self._to_naive_utc(self._parse_date(order.createdAt))
            if not dt or dt < window_start:
                continue
            for item in order.items:
                pid = item.product or item.productId
                if pid and str(pid) in {str(k) for k in product_map}:
                    units_sold[str(pid)] += item.quantity

        result = []
        for product in products:
            pid = str(product.id)
            stock = int(product.stock or 0)
            sold_30d = units_sold.get(pid, 0)
            avg_daily = round(sold_30d / 30, 2)
            days_remaining = round(stock / avg_daily) if avg_daily > 0 else None

            result.append(
                {
                    "productId": pid,
                    "name": product.name,
                    "category": product.category,
                    "currentStock": stock,
                    "unitsSold30d": sold_30d,
                    "avgDailySales": avg_daily,
                    "daysRemaining": days_remaining,
                }
            )

        # Sort: products running out soonest first; None (no sales) at the end
        return sorted(
            result,
            key=lambda x: (x["daysRemaining"] is None, x["daysRemaining"] if x["daysRemaining"] is not None else 9999),
        )


    # ─────────────────────────────────────────────────────────────────────────
    # BATCH 2 ADDITIONAL REPORTS
    # ─────────────────────────────────────────────────────────────────────────

    @cache.ttl_cache(ttl=300)
    async def get_sales_by_channel_detailed(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict]:
        """Revenue, order count, and AOV broken down by sales channel (desktop_web / mobile_web / mobile_app)."""
        orders = await self.order_storage.findAll()
        orders = self._filter_by_date_range(orders, start_date, end_date)

        CHANNELS = ["desktop_web", "mobile_web", "mobile_app"]
        stats: dict = {ch: {"revenue": 0.0, "orderCount": 0} for ch in CHANNELS}

        for order in orders:
            channel = order.channel or "desktop_web"
            if channel not in stats:
                channel = "desktop_web"
            stats[channel]["revenue"] += order.total
            stats[channel]["orderCount"] += 1

        result = []
        for channel, data in stats.items():
            count = data.orderCount
            rev = round(data.revenue, 2)
            result.append(
                {
                    "channel": channel,
                    "channelLabel": channel.replace("_", " ").title(),
                    "orderCount": count,
                    "revenue": rev,
                    "aov": round(rev / count, 2) if count > 0 else 0.0,
                    "revenuePct": 0.0,  # filled below
                }
            )

        total_rev = sum(r.revenue for r in result)
        for r in result:
            r.revenuePct = round(r.revenue / total_rev * 100, 1) if total_rev > 0 else 0.0

        return sorted(result, key=lambda x: x["revenue"], reverse=True)

    @cache.ttl_cache(ttl=300)
    async def get_discounts_audit(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        seller_id: Optional[str] = None,
    ) -> List[Dict]:
        """Per-order line-item audit: coupon code, discount type/value, gross, discount applied, net."""
        orders = await self.order_storage.findAll()
        orders = self._filter_by_date_range(orders, start_date, end_date)

        if seller_id:
            orders = [o for o in orders if str(o.sellerId) == str(seller_id)]

        users = await self.user_storage.findAll()
        user_map = {u.id: u for u in users}

        result = []
        for order in orders:
            if order.discount is None:
                raise ValueError('Order discount is None')
            discount = float(order.discount)
            if discount == 0 and not order.couponCode:
                continue  # skip orders with no discount at all

            coupon_info = order.couponInfo or {}
            user = user_map.get(order.user)
            gross = float(order.subtotal or order.total or 0)
            net = round(gross - discount, 2)

            result.append(
                {
                    "orderId": order.id,
                    "orderNumber": order.orderNumber,
                    "customerName": user.name,
                    "couponCode": order.couponCode or "—",
                    "discountType": coupon_info.discountType,
                    "discountValue": coupon_info.discountValue,
                    "grossSales": round(gross, 2),
                    "discountApplied": round(discount, 2),
                    "netAfterDiscount": net,
                    "discountPct": round(discount / gross * 100, 1) if gross > 0 else 0.0,
                    "createdAt": order.createdAt,
                }
            )

        return sorted(result, key=lambda x: x.get("createdAt") or "" or "", reverse=True)

    @cache.ttl_cache(ttl=300)
    async def get_products_pct_sold(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        seller_id: Optional[str] = None,
    ) -> List[Dict]:
        """Units sold in the period as a % of current stock (sell-through by quantity)."""
        orders = await self.order_storage.findAll()
        orders = self._filter_by_date_range(orders, start_date, end_date)

        products = await self.product_storage.findAll()
        if seller_id:
            products = [p for p in products if str(p.sellerId) == str(seller_id)]

        product_map = {str(p.id): p for p in products}

        units_sold: dict = defaultdict(int)
        for order in orders:
            for item in order.items:
                pid = str(item.product or item.productId or "")
                if pid and pid in product_map:
                    units_sold[pid] += item.quantity

        result = []
        for pid, product in product_map.items():
            stock = int(product.stock or 0)
            sold = units_sold.get(pid, 0)
            total = stock + sold  # opening stock approximation
            pct = round(sold / total * 100, 1) if total > 0 else 0.0

            result.append(
                {
                    "productId": pid,
                    "name": product.name,
                    "category": product.category,
                    "sku": product.sku,
                    "unitsSold": sold,
                    "currentStock": stock,
                    "openingStock": total,
                    "pctSold": pct,
                }
            )

        return sorted(result, key=lambda x: x["pctSold"], reverse=True)


analytics_repository = AnalyticsRepository()

