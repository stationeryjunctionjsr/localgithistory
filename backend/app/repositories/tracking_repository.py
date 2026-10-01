import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

from app.db.storage_factory import get_storage
from app.models.schemas import AnalyticsEventCreate, AnalyticsSessionCreate
from app.db.mysql_analytics_session_dao import MySQLAnalyticsSessionDAO


class TrackingRepository:
    def __init__(self):
        self.storage = get_storage("tracking")
        self.session_dao = MySQLAnalyticsSessionDAO()
        self._ANALYTICS_LIMIT = 5000  # Default limit for safety

    async def findAll(self, query: Optional[Dict] = None, skip: Optional[int] = None, limit: Optional[int] = None):
        return await self.storage.findAll(query or {}, skip=skip, limit=limit)

    async def create(self, tracking_data: AnalyticsEventCreate):
        if tracking_data.timestamp is None:
            tracking_data.timestamp = self._get_current_timestamp()

        # Update the time spent for this session on every event
        if tracking_data.session_id and tracking_data.type != "session":
            event_time = datetime.fromisoformat(str(tracking_data.timestamp).replace("Z", "+00:00"))
            await self.session_dao.update_session_time(tracking_data.session_id, event_time)

        return await self.storage.create(tracking_data)

    def _get_current_timestamp(self):
        return datetime.now(timezone.utc).isoformat()

    async def trackSearch(
        self,
        user_id: Optional[str],
        search_term: str,
        results_count: int,
        session_id: Optional[str] = None,
        product_ids: Optional[List[str]] = None,
        segment: str = "customer",
        source: Optional[str] = None, os: Optional[str] = None, browser: Optional[str] = None,
        ip_address: Optional[str] = None, campaign: Optional[str] = None, device_type: Optional[str] = None,
        device_os_version: Optional[str] = None, device_model: Optional[str] = None, device_app_version: Optional[str] = None
    ):
        payload = AnalyticsEventCreate(
            type="product_search",
            source=source, os=os, browser=browser, ip_address=ip_address, campaign=campaign,
            device_type=device_type, device_os_version=device_os_version, device_model=device_model, device_app_version=device_app_version,
            user_id=user_id,
            search_term=search_term,
            results_count=results_count,
            session_id=session_id,
            segment=segment,
            product_ids=product_ids
        )
        return await self.create(payload)

    async def trackProductView(
        self, user_id: Optional[str], product_id: str, product_name: str, session_id: Optional[str] = None,
        source: Optional[str] = None, page: Optional[str] = None, os: Optional[str] = None, browser: Optional[str] = None,
        ip_address: Optional[str] = None, campaign: Optional[str] = None, device_type: Optional[str] = None,
        device_os_version: Optional[str] = None, device_model: Optional[str] = None, device_app_version: Optional[str] = None
    ):
        return await self.create(
            AnalyticsEventCreate(
                type="product_view",
                source=source, page=page, os=os, browser=browser, ip_address=ip_address, campaign=campaign,
                device_type=device_type, device_os_version=device_os_version, device_model=device_model, device_app_version=device_app_version,
                user_id=user_id,
                product_id=product_id,
                product_name=product_name,
                session_id=session_id
            )
        )

    async def trackAddToCart(
        self,
        user_id: Optional[str],
        product_id: str,
        product_name: str,
        quantity: int,
        price: float,
        session_id: Optional[str] = None
    ):
        return await self.create(
            AnalyticsEventCreate(
                type="cart_add",
                user_id=user_id,
                product_id=product_id,
                product_name=product_name,
                quantity=quantity,
                price=price,
                session_id=session_id,
            )
        )

    async def trackRemoveFromCart(
        self,
        user_id: Optional[str],
        product_id: str,
        product_name: str,
        quantity: int,
        price: float,
        session_id: Optional[str] = None
    ):
        return await self.create(
            AnalyticsEventCreate(
                type="cart_item_remove",
                user_id=user_id,
                product_id=product_id,
                product_name=product_name,
                quantity=quantity,
                price=price,
                session_id=session_id,
            )
        )

    async def trackCheckout(
        self, user_id: Optional[str], cart_value: float, session_id: Optional[str] = None,
        source: Optional[str] = None, os: Optional[str] = None, browser: Optional[str] = None,
        ip_address: Optional[str] = None, campaign: Optional[str] = None, device_type: Optional[str] = None,
        device_os_version: Optional[str] = None, device_model: Optional[str] = None, device_app_version: Optional[str] = None
    ):
        return await self.create(
            AnalyticsEventCreate(
                type="checkout",
                source=source, os=os, browser=browser, ip_address=ip_address, campaign=campaign,
                device_type=device_type, device_os_version=device_os_version, device_model=device_model, device_app_version=device_app_version,
                user_id=user_id,
                cart_value=cart_value,
                session_id=session_id,
            )
        )

    async def trackProductClick(self, user_id, product_id, product_name, session_id=None,
                                source=None, page=None,
                                os=None, browser=None, ip_address=None, campaign=None,
                                device_type=None, device_os_version=None, device_model=None, device_app_version=None):
        return await self.create(AnalyticsEventCreate(
            type="product_click", user_id=user_id, product_id=product_id, product_name=product_name, session_id=session_id,
            source=source, page=page,
            os=os, browser=browser, ip_address=ip_address, campaign=campaign,
            device_type=device_type, device_os_version=device_os_version, device_model=device_model, device_app_version=device_app_version
        ))

    async def trackCartAdd(self, user_id, product_id, quantity, session_id=None,
                           source=None, page=None,
                           os=None, browser=None, ip_address=None, campaign=None,
                           device_type=None, device_os_version=None, device_model=None, device_app_version=None):
        from app.models.schemas import ItemSnippet
        return await self.create(AnalyticsEventCreate(
            type="cart_add",
            user_id=user_id,
            session_id=session_id,
            cart_items=[ItemSnippet(product_id=product_id, quantity=quantity)],
            source=source, page=page,
            os=os, browser=browser, ip_address=ip_address, campaign=campaign,
            device_type=device_type, device_os_version=device_os_version, device_model=device_model, device_app_version=device_app_version
        ))

    async def trackCartItemRemove(
        self, user_id, product_id, quantity, session_id=None,
        source: Optional[str] = None, page: Optional[str] = None, os: Optional[str] = None, browser: Optional[str] = None,
        ip_address: Optional[str] = None, campaign: Optional[str] = None, device_type: Optional[str] = None,
        device_os_version: Optional[str] = None, device_model: Optional[str] = None, device_app_version: Optional[str] = None
    ):
        from app.models.schemas import ItemSnippet
        return await self.create(AnalyticsEventCreate(
            type="cart_item_remove",
            source=source, page=page, os=os, browser=browser, ip_address=ip_address, campaign=campaign,
            device_type=device_type, device_os_version=device_os_version, device_model=device_model, device_app_version=device_app_version,
            user_id=user_id,
            session_id=session_id,
            cart_items=[ItemSnippet(product_id=product_id, quantity=quantity)]
        ))

    async def trackFilterClick(
        self, user_id, filter_name, filter_value, session_id=None,
        source: Optional[str] = None, os: Optional[str] = None, browser: Optional[str] = None,
        ip_address: Optional[str] = None, campaign: Optional[str] = None, device_type: Optional[str] = None,
        device_os_version: Optional[str] = None, device_model: Optional[str] = None, device_app_version: Optional[str] = None
    ):
        return await self.create(AnalyticsEventCreate(
            type="filter_click",
            source=source, os=os, browser=browser, ip_address=ip_address, campaign=campaign,
            device_type=device_type, device_os_version=device_os_version, device_model=device_model, device_app_version=device_app_version,
            user_id=user_id, session_id=session_id,
            filter_name=filter_name, filter_value=filter_value
        ))

    async def trackWishlistAdd(self, user_id, product_id, product_name, session_id=None,
                               source=None, page=None,
                               os=None, browser=None, ip_address=None, campaign=None,
                               device_type=None, device_os_version=None, device_model=None, device_app_version=None):
        return await self.create(AnalyticsEventCreate(
            type="wishlist_add", user_id=user_id, session_id=session_id,
            product_id=product_id, product_name=product_name,
            source=source, page=page,
            os=os, browser=browser, ip_address=ip_address, campaign=campaign,
            device_type=device_type, device_os_version=device_os_version, device_model=device_model, device_app_version=device_app_version
        ))

    async def trackSession(
        self, user_id: Optional[str], session_id: str,
        source: Optional[str] = None, page: Optional[str] = None, os: Optional[str] = None, browser: Optional[str] = None,
        ip_address: Optional[str] = None, campaign: Optional[str] = None, device_type: Optional[str] = None,
        device_os_version: Optional[str] = None, device_model: Optional[str] = None, device_app_version: Optional[str] = None
    ):
        await self.session_dao.create_session(
            AnalyticsSessionCreate(
                session_id=session_id,
                user_id=user_id,
                source=source,
                os=os,
                browser=browser,
                ip_address=ip_address,
                device_type=device_type,
                device_os_version=device_os_version,
                device_model=device_model,
                device_app_version=device_app_version,
                campaign=campaign,
                start_time=datetime.now(timezone.utc)
            )
        )
        return await self.create(
            AnalyticsEventCreate(
                type="session",
                source=source, page=page,
                user_id=user_id, session_id=session_id
            )
        )

    async def trackPageView(
        self, user_id: Optional[str], page: str, session_id: Optional[str] = None,
        source: Optional[str] = None, os: Optional[str] = None, browser: Optional[str] = None,
        ip_address: Optional[str] = None, campaign: Optional[str] = None, device_type: Optional[str] = None,
        device_os_version: Optional[str] = None, device_model: Optional[str] = None, device_app_version: Optional[str] = None
    ):
        return await self.create(AnalyticsEventCreate(
            type="page_view",
            source=source, os=os, browser=browser, ip_address=ip_address, campaign=campaign,
            device_type=device_type, device_os_version=device_os_version, device_model=device_model, device_app_version=device_app_version,
            user_id=user_id, page=page, session_id=session_id
        ))

    async def trackDropOff(
        self, user_id: Optional[str], page: str, reason: str, session_id: Optional[str] = None,
        source: Optional[str] = None, os: Optional[str] = None, browser: Optional[str] = None,
        ip_address: Optional[str] = None, campaign: Optional[str] = None, device_type: Optional[str] = None,
        device_os_version: Optional[str] = None, device_model: Optional[str] = None, device_app_version: Optional[str] = None
    ):
        return await self.create(
            AnalyticsEventCreate(
                type="drop_off", user_id=user_id,
                source=source, os=os, browser=browser, ip_address=ip_address, campaign=campaign,
                device_type=device_type, device_os_version=device_os_version, device_model=device_model, device_app_version=device_app_version,
                page=page, reason=reason, session_id=session_id
            )
        )

    async def trackPurchase(
        self, user_id: Optional[str], order_id: str, order_value: float, session_id: Optional[str] = None,
        source: Optional[str] = None, os: Optional[str] = None, browser: Optional[str] = None,
        ip_address: Optional[str] = None, campaign: Optional[str] = None, device_type: Optional[str] = None,
        device_os_version: Optional[str] = None, device_model: Optional[str] = None, device_app_version: Optional[str] = None
    ):
        return await self.create(
            AnalyticsEventCreate(
                type="purchase",
                source=source, os=os, browser=browser, ip_address=ip_address, campaign=campaign,
                device_type=device_type, device_os_version=device_os_version, device_model=device_model, device_app_version=device_app_version,
                user_id=user_id, order_id=order_id, order_value=order_value, session_id=session_id
            )
        )

    async def trackCartAbandonment(
        self, user_id: Optional[str], cart_items: List['CartItemInternal'], cart_value: Optional[float], session_id: Optional[str] = None,
        source: Optional[str] = None, os: Optional[str] = None, browser: Optional[str] = None,
        ip_address: Optional[str] = None, campaign: Optional[str] = None, device_type: Optional[str] = None,
        device_os_version: Optional[str] = None, device_model: Optional[str] = None, device_app_version: Optional[str] = None
    ):
        return await self.create(
            AnalyticsEventCreate(
                type="cart_abandonment", user_id=user_id,
                source=source, os=os, browser=browser, ip_address=ip_address, campaign=campaign,
                device_type=device_type, device_os_version=device_os_version, device_model=device_model, device_app_version=device_app_version,
                cart_items=cart_items, cart_value=cart_value, session_id=session_id
            )
        )

    async def trackAuthEvent(
        self, user_id: Optional[str], session_id: Optional[str], action: str,
        source: Optional[str] = None, page: Optional[str] = None
    ):
        """Track login/register/logout events in the unified sj_tracking table."""
        return await self.create(
            AnalyticsEventCreate(
                type=action,
                user_id=user_id,
                session_id=session_id,
                source=source,
                page=page,
            )
        )

    async def trackRecommendationEvent(
        self, user_id: Optional[str], session_id: Optional[str], action: str,
        product_id: Optional[str] = None, product_name: Optional[str] = None,
        source: Optional[str] = None, page: Optional[str] = None,
        segment: Optional[str] = None,
    ):
        """Track recommendation interactions (section_view, product_view, add_to_cart) in sj_tracking."""
        return await self.create(
            AnalyticsEventCreate(
                type=action,
                user_id=user_id,
                session_id=session_id,
                product_id=product_id,
                product_name=product_name,
                source=source,
                page=page,
                segment=segment,
            )
        )

    async def getSessionsCount(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
        sessions = await self.findAll({"type": "session"}, limit=self._ANALYTICS_LIMIT)

        count = 0
        for s in sessions:
            ts = self._parse_timestamp(s.timestamp)
            if start_date and ts and ts < start_date:
                continue
            if end_date and ts and ts > end_date:
                continue
            count += 1
        return count

    async def getTopProducts(
        self, limit: int = 10, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ):
        views = await self.findAll({"type": "product_view"}, limit=self._ANALYTICS_LIMIT)
        product_counts: dict = {}

        for v in views:
            ts = self._parse_timestamp(v.timestamp)
            if start_date and ts and ts < start_date:
                continue
            if end_date and ts and ts > end_date:
                continue

            pid = v.product_id
            name = v.product_name if v.product_name is not None else "Unknown"
            if pid:
                if pid not in product_counts:
                    product_counts[pid] = {
                        "productId": pid, "productName": name, "views": 0}
                product_counts[pid]["views"] += 1

        return sorted(product_counts.values(), key=lambda x: x["views"], reverse=True)[:limit]

    async def getDropOffs(
        self, limit: int = 10, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ):
        drop_offs = await self.findAll({"type": "drop_off"}, limit=self._ANALYTICS_LIMIT)
        drop_off_counts: dict = {}

        for d in drop_offs:
            ts = self._parse_timestamp(d.timestamp)
            if start_date and ts and ts < start_date:
                continue
            if end_date and ts and ts > end_date:
                continue

            page = d.page
            if page not in drop_off_counts:
                drop_off_counts[page] = {
                    "page": page, "count": 0, "reasons": {}}
            drop_off_counts[page]["count"] += 1

            reason = d.reason if d.reason is not None else None
            if reason:
                if reason not in drop_off_counts[page]["reasons"]:
                    drop_off_counts[page]["reasons"][reason] = 0
                drop_off_counts[page]["reasons"][reason] += 1

        return sorted(drop_off_counts.values(), key=lambda x: x["count"], reverse=True)[:limit]

    async def getCartAbandonments(
        self, limit: int = 100, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ):
        abandonments = await self.findAll({"type": "cart_abandonment"}, limit=self._ANALYTICS_LIMIT)

        filtered = []
        for a in abandonments:
            ts = self._parse_timestamp(a.timestamp)
            if start_date and ts and ts < start_date:
                continue
            if end_date and ts and ts > end_date:
                continue
            filtered.append(a)

        return sorted(filtered, key=lambda x: x.timestamp or "", reverse=True)[:limit]

    async def getMostAbandonedProducts(
        self, limit: int = 50, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ):
        abandonments = await self.findAll({"type": "cart_abandonment"}, limit=self._ANALYTICS_LIMIT)

        from app.db.storage_factory import get_storage

        abandoned_products: dict = {}
        for a in abandonments:
            ts = self._parse_timestamp(a.timestamp)
            if start_date and ts and ts < start_date:
                continue
            if end_date and ts and ts > end_date:
                continue

            items = a.cartItems if a.cartItems is not None else []
            for item in items:
                # Zero Data Stripping: Strict dot notation
                pid = item.product if item.product else item.product_id

                if not pid:
                    continue

                if pid not in abandoned_products:
                    abandoned_products[pid] = {
                        "productId": pid,
                        "abandonCount": 0,
                        "quantityAbandoned": 0,
                        "valueLost": 0.0,
                    }

                q = item.quantity if item.quantity is not None else 1
                p = item.price if item.price is not None else 0

                abandoned_products[pid]["abandonCount"] += 1
                abandoned_products[pid]["quantityAbandoned"] += q
                abandoned_products[pid]["valueLost"] += q * p

        product_ids_seen = list(abandoned_products.keys())
        product_map: dict = {}
        if product_ids_seen:
            product_storage = get_storage("products")
            products = await product_storage.findAll({"_id": {"$in": product_ids_seen}})
            product_map = {str(p.id): p for p in products}

        result = []
        for pid, stats in abandoned_products.items():
            product = product_map[str(pid)] if str(
                pid) in product_map else None
            product_name = product.name if product else "Unknown"
            product_category = product.category if product else "Uncategorized"

            result.append(
                {
                    "productId": pid,
                    "productName": product_name,
                    "category": product_category,
                    "abandonCount": stats["abandonCount"],
                    "quantityAbandoned": stats["quantityAbandoned"],
                    "valueLost": round(stats["valueLost"], 2),
                }
            )

        return sorted(result, key=lambda x: x["abandonCount"], reverse=True)[:limit]

    async def clearRecentSearches(self, user_id: Optional[str] = None, session_id: Optional[str] = None) -> None:
        if not user_id and not session_id:
            return
        marker = AnalyticsEventCreate(
            type="search_history_clear",
            timestamp=self._get_current_timestamp(),
            user_id=user_id,
            session_id=session_id
        )
        await self.storage.create(marker)

    async def getRecentUserSearches(
        self, user_id: Optional[str] = None, session_id: Optional[str] = None, limit: int = 5
    ):
        query = {"type": "product_search"}
        if user_id:
            query["userId"] = user_id
        elif session_id:
            query["sessionId"] = session_id
        else:
            return []

        clear_query = {"type": "search_history_clear"}
        if user_id:
            clear_query["userId"] = user_id
        elif session_id:
            clear_query["sessionId"] = session_id

        clear_events = await self.findAll(clear_query)
        last_cleared = ""
        if clear_events:
            last_cleared = max((e.timestamp or "") for e in clear_events)

        all_searches = await self.findAll(query)
        if last_cleared:
            all_searches = [s for s in all_searches if (
                s.timestamp or "") > last_cleared]

        all_searches.sort(key=lambda x: x.timestamp or "", reverse=True)

        seen = set()
        unique_searches = []
        for s in all_searches:
            term = (s.search_term if s.search_term is not None else "").strip().lower()
            if term and term not in seen:
                seen.add(term)
                unique_searches.append(s.search_term)
                if len(unique_searches) >= limit:
                    break

        return unique_searches

    def _parse_timestamp(self, raw: Optional[str]) -> Optional[datetime]:
        if not raw:
            return None
        try:
            return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid timestamp format: {raw}") from e

    async def get_search_counts_by_product(self, days: int, segment: str) -> Dict[str, int]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        all_searches = await self.findAll({"type": "product_search", "segment": segment}, limit=self._ANALYTICS_LIMIT)
        counts: Dict[str, int] = {}
        for doc in all_searches:
            ts = self._parse_timestamp(doc.timestamp)
            if not ts or ts < cutoff:
                continue
            for pid in doc.product_ids if doc.product_ids is not None else []:
                if pid:
                    counts[pid] = (counts[pid] if pid in counts else 0) + 1
        return counts

    async def get_searches_with_products(self, days: int, segment: str) -> List[Dict]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        all_searches = await self.findAll({"type": "product_search", "segment": segment}, limit=self._ANALYTICS_LIMIT)
        out: List[Dict] = []
        for doc in all_searches:
            ts = self._parse_timestamp(doc.timestamp)
            if not ts or ts < cutoff:
                continue
            pids = doc.product_ids if doc.product_ids is not None else []
            if not pids:
                continue
            out.append(
                {
                    "userId": doc.userId,
                    "sessionId": doc.session_id,
                    "productIds": list(pids),
                    "timestamp": ts,
                }
            )
        return out

    async def getMostSearched(
        self, limit: int = 5, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ):
        all_tracking = await self.findAll({"type": "search"})

        filtered_tracking = []
        for track in all_tracking:
            ts = self._parse_timestamp(track.timestamp)
            if not ts: continue
            if start_date and ts < start_date: continue
            if end_date and ts > end_date: continue
            filtered_tracking.append(track)

        search_stats = {}
        for track in filtered_tracking:
            term = track.search_term or ""
            term = term.lower()
            if term:
                if term not in search_stats:
                    search_stats[term] = {"count": 0, "total_results": 0}
                search_stats[term]["count"] += 1
                search_stats[term]["total_results"] += track.results_count or 0

        sorted_searches = sorted(search_stats.items(
        ), key=lambda x: x[1]["count"], reverse=True)[:limit]
        return [
            {
                "term": term,
                "count": stats["count"],
                "avgProductsFound": round(stats["total_results"] / stats["count"], 1) if stats["count"] > 0 else 0,
            }
            for term, stats in sorted_searches
        ]


    async def getZeroResultSearches(
        self, limit: int = 50, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ):
        all_tracking = await self.findAll({"type": "product_search"})

        filtered_tracking = []
        for track in all_tracking:
            ts = self._parse_timestamp(track.timestamp)
            if not ts:
                continue
            if start_date and ts < start_date:
                continue
            if end_date and ts > end_date:
                continue
            filtered_tracking.append(track)

        search_stats = {}
        for track in filtered_tracking:
            if (track.results_count or 0) == 0:
                term = (track.search_term or "").lower()
                if term:
                    if term not in search_stats:
                        search_stats[term] = {"count": 0}
                    search_stats[term]["count"] += 1

        return [
            {
                "term": term,
                "count": stats["count"],
            }
            for term, stats in sorted(search_stats.items(), key=lambda x: x[1]["count"], reverse=True)[:limit]
        ]

    async def getMostViewed(
        self, limit: int = 5, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ):
        all_tracking = await self.findAll({"type": "product_view"})

        # Filter by date
        filtered_tracking = []
        for track in all_tracking:
            ts = self._parse_timestamp(track.timestamp)
            if not ts:
                continue
            if start_date and ts < start_date:
                continue
            if end_date and ts > end_date:
                continue
            filtered_tracking.append(track)

        view_counts = {}
        for track in filtered_tracking:
            product_id = (track.product_ids[0] if track.product_ids else None)
            if product_id:
                if product_id not in view_counts:
                    view_counts[product_id] = {
                        "productId": product_id,
                        "productName": (track.product_name or "Unknown"),
                        "count": 0,
                    }
                view_counts[product_id]["count"] += 1

        return sorted(view_counts.values(), key=lambda x: x["count"], reverse=True)[:limit]

    async def getReturningUsers(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
        sessions = await self.findAll({"type": "session"})
        returning_user_ids = set()
        user_last_seen = {}

        for session in sessions:
            ts = self._parse_timestamp(session.get("timestamp"))
            if start_date and ts and ts < start_date:
                continue
            if end_date and ts and ts > end_date:
                continue

            uid = session.get("userId")
            if session.get("isReturning") and uid:
                returning_user_ids.add(uid)
                if ts:
                    if uid not in user_last_seen or ts > user_last_seen[uid]:
                        user_last_seen[uid] = ts

        # Get user details
        from app.db.storage_factory import get_storage

        user_storage = get_storage("users")
        users = await user_storage.findAll({"_id": {"$in": list(returning_user_ids)}})

        return [
            {
                "userId": u.get("_id"),
                "name": u.get("name", "Unknown"),
                "email": u.get("email", "Unknown"),
                "lastSeen": user_last_seen.get(u.get("_id")).isoformat() if user_last_seen.get(u.get("_id")) else None,
            }
            for u in users
        ]

    
tracking_repository = TrackingRepository()
