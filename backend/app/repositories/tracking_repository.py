import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

from app.db.storage_factory import get_storage
from app.models.schemas import AnalyticsEventCreate


class TrackingRepository:
    def __init__(self):
        self.storage = get_storage("tracking")
        self._ANALYTICS_LIMIT = 5000  # Default limit for safety

    async def findAll(self, query: Optional[Dict] = None, skip: Optional[int] = None, limit: Optional[int] = None):
        return await self.storage.findAll(query or {}, skip=skip, limit=limit)

    async def create(self, tracking_data: AnalyticsEventCreate):
        if tracking_data.timestamp is None:
            tracking_data.timestamp = self._get_current_timestamp()

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
    ):
        payload = AnalyticsEventCreate(
            type="product_search",
            userId=user_id,
            searchTerm=search_term,
            resultsCount=results_count,
            sessionId=session_id,
            segment=segment,
            productIds=product_ids,
        )
        return await self.create(payload)

    async def trackProductView(
        self, user_id: Optional[str], product_id: str, product_name: str, session_id: Optional[str] = None, os=None, browser=None, ipAddress=None, campaign=None, source=None
    ):
        return await self.create(
            AnalyticsEventCreate(
                type="product_view", os=os, browser=browser, ipAddress=ipAddress, campaign=campaign, source=source,
                userId=user_id,
                productId=product_id,
                productName=product_name,
                sessionId=session_id
            )
        )

    async def trackAddToCart(
        self,
        user_id: Optional[str],
        product_id: str,
        product_name: str,
        quantity: int,
        price: float,
        session_id: Optional[str] = None,
        os=None, browser=None, ipAddress=None, campaign=None, source=None
    ):
        return await self.create(
            AnalyticsEventCreate(
                type="cart_add",
                userId=user_id,
                productId=product_id,
                productName=product_name,
                quantity=quantity,
                price=price,
                sessionId=session_id,
            )
        )

    async def trackRemoveFromCart(
        self,
        user_id: Optional[str],
        product_id: str,
        product_name: str,
        quantity: int,
        price: float,
        session_id: Optional[str] = None,
        os=None, browser=None, ipAddress=None, campaign=None, source=None
    ):
        return await self.create(
            AnalyticsEventCreate(
                type="cart_item_remove",
                userId=user_id,
                productId=product_id,
                productName=product_name,
                quantity=quantity,
                price=price,
                sessionId=session_id,
            )
        )

    async def trackCheckout(self, user_id: Optional[str], cart_value: float, session_id: Optional[str] = None, os=None, browser=None, ipAddress=None, campaign=None, source=None):
        return await self.create(
            AnalyticsEventCreate(
                type="checkout", os=os, browser=browser, ipAddress=ipAddress, campaign=campaign, source=source,
                userId=user_id,
                cartValue=cart_value,
                sessionId=session_id,
            )
        )

    async def trackProductClick(self, user_id, product_id, product_name, source=None, session_id=None, os=None, browser=None, ipAddress=None, campaign=None):
        return await self.create(AnalyticsEventCreate(
            type="product_click", os=os, browser=browser, ipAddress=ipAddress, campaign=campaign, userId=user_id, productId=product_id, productName=product_name, source=source, sessionId=session_id
        ))

    async def trackCartAdd(self, user_id, product_id, quantity, session_id=None, os=None, browser=None, ipAddress=None, campaign=None, source=None):
        return await self.trackAddToCart(user_id, product_id, "Unknown", quantity, 0, session_id, os=os, browser=browser, ipAddress=ipAddress, campaign=campaign, source=source)

    async def trackCartItemRemove(self, user_id, product_id, quantity, session_id=None, os=None, browser=None, ipAddress=None, campaign=None, source=None):
        return await self.trackRemoveFromCart(user_id, product_id, "Unknown", quantity, 0, session_id, os=os, browser=browser, ipAddress=ipAddress, campaign=campaign, source=source)

    async def trackFilterClick(self, user_id, filter_name, filter_value, session_id=None, os=None, browser=None, ipAddress=None, campaign=None, source=None):
        return await self.create(AnalyticsEventCreate(
            type="filter_click", os=os, browser=browser, ipAddress=ipAddress, campaign=campaign, source=source, userId=user_id, sessionId=session_id,
            filterName=filter_name, filterValue=filter_value
        ))

    async def trackWishlistAdd(self, user_id, product_id, product_name, session_id=None, os=None, browser=None, ipAddress=None, campaign=None, source=None):
        return await self.create(AnalyticsEventCreate(
            type="wishlist_add", os=os, browser=browser, ipAddress=ipAddress, campaign=campaign, source=source, userId=user_id, sessionId=session_id,
            productId=product_id, productName=product_name
        ))

    async def trackSession(self, user_id: Optional[str], session_id: str, is_returning: bool, os=None, browser=None, ipAddress=None, campaign=None, source=None):
        return await self.create(
            AnalyticsEventCreate(
                type="session", os=os, browser=browser, ipAddress=ipAddress, campaign=campaign, source=source, userId=user_id, sessionId=session_id, isReturning=is_returning, pageViews=1
            )
        )

    async def trackPageView(self, user_id: Optional[str], page: str, session_id: Optional[str] = None, os=None, browser=None, ipAddress=None, campaign=None, source=None):
        return await self.create(AnalyticsEventCreate(type="page_view", os=os, browser=browser, ipAddress=ipAddress, campaign=campaign, source=source, userId=user_id, page=page, sessionId=session_id))

    async def trackDropOff(self, user_id: Optional[str], page: str, reason: str, session_id: Optional[str] = None, os=None, browser=None, ipAddress=None, campaign=None, source=None):
        return await self.create(
            AnalyticsEventCreate(type="drop_off", os=os, browser=browser, ipAddress=ipAddress, campaign=campaign,
                                 source=source, userId=user_id, page=page, reason=reason, sessionId=session_id)
        )

    async def trackPurchase(
        self, user_id: Optional[str], order_id: str, order_value: float, session_id: Optional[str] = None, os=None, browser=None, ipAddress=None, campaign=None, source=None
    ):
        return await self.create(
            AnalyticsEventCreate(
                type="purchase", os=os, browser=browser, ipAddress=ipAddress, campaign=campaign, source=source, userId=user_id, orderId=order_id, orderValue=order_value, sessionId=session_id
            )
        )

    async def trackCartAbandonment(self, user_id: Optional[str], cart_items: List[Any], cart_value: Optional[float], session_id: Optional[str] = None, os=None, browser=None, ipAddress=None, campaign=None, source=None):
        return await self.create(
            AnalyticsEventCreate(type="cart_abandonment", os=os, browser=browser, ipAddress=ipAddress, campaign=campaign,
                                 source=source, userId=user_id, cartItems=cart_items, cartValue=cart_value, sessionId=session_id)
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

            pid = v.productId
            name = v.productName if v.productName is not None else "Unknown"
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
                pid = item.product if item.product else item.productId

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
            userId=user_id,
            sessionId=session_id
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
            term = (s.searchTerm if s.searchTerm is not None else "").strip().lower()
            if term and term not in seen:
                seen.add(term)
                unique_searches.append(s.searchTerm)
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
            for pid in doc.productIds if doc.productIds is not None else []:
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
            pids = doc.productIds if doc.productIds is not None else []
            if not pids:
                continue
            out.append(
                {
                    "userId": doc.userId,
                    "sessionId": doc.sessionId,
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
            term = track.searchTerm or ""
            term = term.lower()
            if term:
                if term not in search_stats:
                    search_stats[term] = {"count": 0, "total_results": 0}
                search_stats[term]["count"] += 1
                search_stats[term]["total_results"] += track.resultsCount or 0

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
            if (track.resultsCount or 0) == 0:
                term = (track.searchTerm or "").lower()
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
            product_id = (track.productIds[0] if track.productIds else None)
            if product_id:
                if product_id not in view_counts:
                    view_counts[product_id] = {
                        "productId": product_id,
                        "productName": (track.productName or "Unknown"),
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
