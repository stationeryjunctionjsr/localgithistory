from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.db.storage_factory import get_storage


class TrackingRepository:
    def __init__(self):
        self.storage = get_storage("tracking")

    async def findAll(self, query: Optional[Dict] = None, skip: Optional[int] = None, limit: Optional[int] = None):
        return await self.storage.findAll(query or {}, skip=skip, limit=limit)

    async def create(self, tracking_data: Any):
        from app.models.daos import TrackingInternalCreate
        tracking_data_dict = tracking_data if isinstance(tracking_data, dict) else dict(tracking_data)
        tracking_data_dict["timestamp"] = tracking_data_dict.get("timestamp") or self._get_current_timestamp()
        
        return await self.storage.create(TrackingInternalCreate.model_validate(tracking_data_dict))

    def _get_current_timestamp(self):
        from datetime import datetime

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
        payload = {
            "type": "product_search",
            "userId": user_id,
            "searchTerm": search_term,
            "resultsCount": results_count,
            "sessionId": session_id,
            "segment": segment,
        }
        if product_ids is not None:
            payload.productIds = product_ids
        return await self.create(payload)

    async def trackProductView(
        self, user_id: Optional[str], product_id: str, product_name: str, session_id: Optional[str] = None
    ):
        return await self.create(
            {
                "type": "product_view",
                "userId": user_id,
                "productId": product_id,
                "productName": product_name,
                "sessionId": session_id,
            }
        )

    async def trackProductClick(
        self, user_id: Optional[str], product_id: str, product_name: str, source: str, session_id: Optional[str] = None
    ):
        return await self.create(
            {
                "type": "product_click",
                "userId": user_id,
                "productId": product_id,
                "productName": product_name,
                "source": source,
                "sessionId": session_id,
            }
        )

    async def trackCartAbandonment(
        self, user_id: Optional[str], cart_items: List, cart_value: float, session_id: Optional[str] = None
    ):
        return await self.create(
            {
                "type": "cart_abandonment",
                "userId": user_id,
                "cartItems": cart_items,
                "cartValue": cart_value,
                "sessionId": session_id,
            }
        )

    async def trackSession(self, user_id: Optional[str], session_id: str, is_returning: bool):
        return await self.create(
            {"type": "session", "userId": user_id, "sessionId": session_id, "isReturning": is_returning, "pageViews": 1}
        )

    async def trackPageView(self, user_id: Optional[str], page: str, session_id: Optional[str] = None):
        return await self.create({"type": "page_view", "userId": user_id, "page": page, "sessionId": session_id})

    async def trackDropOff(self, user_id: Optional[str], page: str, reason: str, session_id: Optional[str] = None):
        return await self.create(
            {"type": "drop_off", "userId": user_id, "page": page, "reason": reason, "sessionId": session_id}
        )

    async def trackCartItemRemove(
        self, user_id: Optional[str], product_id: str, quantity: int, session_id: Optional[str] = None
    ):
        return await self.create(
            {
                "type": "cart_item_remove",
                "userId": user_id,
                "productId": product_id,
                "quantity": quantity,
                "sessionId": session_id,
            }
        )

    async def trackCartAdd(
        self, user_id: Optional[str], product_id: str, quantity: int, session_id: Optional[str] = None
    ):
        return await self.create(
            {
                "type": "cart_add",
                "userId": user_id,
                "productId": product_id,
                "quantity": quantity,
                "sessionId": session_id,
            }
        )

    async def trackWishlistAdd(self, user_id: Optional[str], product_id: str, session_id: Optional[str] = None):
        return await self.create(
            {"type": "wishlist_add", "userId": user_id, "productId": product_id, "sessionId": session_id}
        )

    async def trackFilterClick(
        self, user_id: Optional[str], filter_type: str, filter_value: str, session_id: Optional[str] = None
    ):
        """
        Track clicks on categories, brands, tags, etc.
        filter_type: 'category', 'brand', 'tag', 'sort', etc.
        """
        return await self.create(
            {
                "type": "filter_click",
                "userId": user_id,
                "filterType": filter_type,
                "filterValue": filter_value,
                "sessionId": session_id,
            }
        )

    # Maximum rows to pull for analytics queries. Prevents OOM on large tables.
    # Admin-only endpoints so a reasonable cap is acceptable.
    _ANALYTICS_LIMIT = 100_000

    async def getMostSearched(
        self, limit: int = 5, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ):
        all_tracking = await self.findAll({"type": "product_search"}, limit=self._ANALYTICS_LIMIT)

        # Filter by date
        filtered_tracking = []
        for track in all_tracking:
            ts = self._parse_timestamp(track.get("timestamp"))
            if not ts:
                continue
            if start_date and ts < start_date:
                continue
            if end_date and ts > end_date:
                continue
            filtered_tracking.append(track)

        search_stats = {}
        for track in filtered_tracking:
            term = track.get("searchTerm", "").lower()
            if term:
                if term not in search_stats:
                    search_stats[term] = {"count": 0, "total_results": 0}
                search_stats[term]["count"] += 1
                search_stats[term]["total_results"] += track.get("resultsCount", 0)

        return [
            {
                "term": term,
                "count": stats["count"],
                "avgProductsFound": round(stats["total_results"] / stats["count"], 1) if stats["count"] > 0 else 0,
            }
            for term, stats in sorted(search_stats.items(), key=lambda x: x[1]["count"], reverse=True)[:limit]
        ]

    async def getZeroResultSearches(
        self, limit: int = 50, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ):
        all_tracking = await self.findAll({"type": "product_search"}, limit=self._ANALYTICS_LIMIT)

        filtered_tracking = []
        for track in all_tracking:
            ts = self._parse_timestamp(track.get("timestamp"))
            if not ts:
                continue
            if start_date and ts < start_date:
                continue
            if end_date and ts > end_date:
                continue
            filtered_tracking.append(track)

        search_stats = {}
        for track in filtered_tracking:
            if track.get("resultsCount", 0) == 0:
                term = track.get("searchTerm", "").lower()
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
        all_tracking = await self.findAll({"type": "product_view"}, limit=self._ANALYTICS_LIMIT)

        # Filter by date
        filtered_tracking = []
        for track in all_tracking:
            ts = self._parse_timestamp(track.get("timestamp"))
            if not ts:
                continue
            if start_date and ts < start_date:
                continue
            if end_date and ts > end_date:
                continue
            filtered_tracking.append(track)

        view_counts = {}
        for track in filtered_tracking:
            product_id = track.get("productId")
            if product_id:
                if product_id not in view_counts:
                    view_counts[product_id] = {
                        "productId": product_id,
                        "productName": track.get("productName", "Unknown"),
                        "count": 0,
                    }
                view_counts[product_id]["count"] += 1

        return sorted(view_counts.values(), key=lambda x: x["count"], reverse=True)[:limit]

    async def getReturningUsers(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
        sessions = await self.findAll({"type": "session"}, limit=self._ANALYTICS_LIMIT)
        returning_user_ids = set()
        user_last_seen = {}

        for session in sessions:
            ts = self._parse_timestamp(getattr(session, "timestamp", None))
            if start_date and ts and ts < start_date:
                continue
            if end_date and ts and ts > end_date:
                continue

            uid = getattr(session, "user_id", None)
            if getattr(session, "is_returning", None) and uid:
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

    async def getDropOffPoints(
        self, limit: int = 10, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ):
        drop_offs = await self.findAll({"type": "drop_off"}, limit=self._ANALYTICS_LIMIT)
        drop_off_counts = {}

        for drop_off in drop_offs:
            ts = self._parse_timestamp(drop_off.get("timestamp"))
            if start_date and ts and ts < start_date:
                continue
            if end_date and ts and ts > end_date:
                continue

            page = drop_off.get("page", "unknown")
            if page not in drop_off_counts:
                drop_off_counts[page] = {"page": page, "count": 0, "reasons": {}}
            drop_off_counts[page]["count"] += 1
            reason = drop_off.get("reason")
            if reason:
                drop_off_counts[page]["reasons"][reason] = drop_off_counts[page]["reasons"].get(reason, 0) + 1

        return sorted(drop_off_counts.values(), key=lambda x: x["count"], reverse=True)[:limit]

    async def getCartAbandonments(
        self, limit: int = 100, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ):
        abandonments = await self.findAll({"type": "cart_abandonment"}, limit=self._ANALYTICS_LIMIT)

        # Filter by date
        filtered = []
        for a in abandonments:
            ts = self._parse_timestamp(a.get("timestamp"))
            if start_date and ts and ts < start_date:
                continue
            if end_date and ts and ts > end_date:
                continue
            filtered.append(a)

        return sorted(filtered, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]

    async def getMostAbandonedProducts(
        self, limit: int = 50, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ):
        abandonments = await self.findAll({"type": "cart_abandonment"}, limit=self._ANALYTICS_LIMIT)

        from app.db.storage_factory import get_storage

        # Collect product IDs first, then fetch only those products (avoids full product table scan)
        abandoned_products: dict = {}
        for a in abandonments:
            ts = self._parse_timestamp(a.get("timestamp"))
            if start_date and ts and ts < start_date:
                continue
            if end_date and ts and ts > end_date:
                continue

            for item in a.get("cartItems", []):
                pid = getattr(item, "product", None) or getattr(item, "productId", None)
                if not pid:
                    continue

                if pid not in abandoned_products:
                    abandoned_products[pid] = {
                        "productId": pid,
                        "abandonCount": 0,
                        "quantityAbandoned": 0,
                        "valueLost": 0.0,
                    }

                q = getattr(item, 'quantity', 1)
                abandoned_products[pid]["abandonCount"] += 1
                abandoned_products[pid]["quantityAbandoned"] += q
                abandoned_products[pid]["valueLost"] += q * getattr(item, 'price', 0)

        # Fetch only the products that actually appeared in abandonment events
        product_ids_seen = list(abandoned_products.keys())
        product_map: dict = {}
        if product_ids_seen:
            product_storage = get_storage("products")
            products = await product_storage.findAll({"_id": {"$in": product_ids_seen}})
            product_map = {p.get("_id"): p for p in products}

        result = []
        for pid, stats in abandoned_products.items():
            product = product_map.get(pid, {})
            result.append(
                {
                    "productId": pid,
                    "productName": product.get("name", "Unknown"),
                    "category": product.get("category", "Uncategorized"),
                    "abandonCount": stats["abandonCount"],
                    "quantityAbandoned": stats["quantityAbandoned"],
                    "valueLost": round(stats["valueLost"], 2),
                }
            )

        return sorted(result, key=lambda x: x["abandonCount"], reverse=True)[:limit]

    async def clearRecentSearches(self, user_id: Optional[str] = None, session_id: Optional[str] = None) -> None:
        """
        Soft-clear: insert a marker record so that searches before this moment
        are hidden for this user/session. No tracking data is deleted.
        """
        if not user_id and not session_id:
            return
        marker = {
            "type": "search_history_clear",
            "timestamp": self._get_current_timestamp(),
        }
        if user_id:
            marker["userId"] = user_id
        if session_id:
            marker["sessionId"] = session_id
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

        # Find the most recent clear marker for this user/session
        clear_query = {"type": "search_history_clear"}
        if user_id:
            clear_query["userId"] = user_id
        elif session_id:
            clear_query["sessionId"] = session_id
        clear_events = await self.findAll(clear_query)
        last_cleared = ""
        if clear_events:
            last_cleared = max(e.get("timestamp", "") for e in clear_events)

        all_searches = await self.findAll(query)
        # Exclude searches that happened before the last clear event
        if last_cleared:
            all_searches = [s for s in all_searches if s.get("timestamp", "") > last_cleared]

        # Sort by timestamp descending and remove duplicates
        all_searches.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        seen = set()
        unique_searches = []
        for s in all_searches:
            term = s.get("searchTerm", "").strip().lower()
            if term and term not in seen:
                seen.add(term)
                unique_searches.append(s.get("searchTerm"))
                if len(unique_searches) >= limit:
                    break

        return unique_searches

    def _parse_timestamp(self, raw: Optional[str]) -> Optional[datetime]:
        if not raw:
            return None
        try:
            return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except Exception:
            return None

    async def get_search_counts_by_product(self, days: int, segment: str) -> Dict[str, int]:
        """Count how many searches (last `days`) included each product, for the given segment (customer/wholesaler)."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        # Use database-side filtering for type and segment
        all_searches = await self.findAll({"type": "product_search", "segment": segment}, limit=self._ANALYTICS_LIMIT)
        counts: Dict[str, int] = {}
        for doc in all_searches:
            ts = self._parse_timestamp(doc.get("timestamp"))
            if not ts or ts < cutoff:
                continue
            for pid in doc.get("productIds") or []:
                if pid:
                    counts[pid] = counts.get(pid, 0) + 1
        return counts

    async def get_searches_with_products(self, days: int, segment: str) -> List[Dict]:
        """
        Return all search events (last `days`) for segment that have productIds.
        Each item: { userId, sessionId, productIds, timestamp } (timestamp as datetime).
        Used to link search -> sale within 7 days for trending.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        # Use database-side filtering for type and segment
        all_searches = await self.findAll({"type": "product_search", "segment": segment}, limit=self._ANALYTICS_LIMIT)
        out: List[Dict] = []
        for doc in all_searches:
            ts = self._parse_timestamp(doc.get("timestamp"))
            if not ts or ts < cutoff:
                continue
            pids = doc.get("productIds") or []
            if not pids:
                continue
            out.append(
                {
                    "userId": doc.get("userId"),
                    "sessionId": doc.get("sessionId"),
                    "productIds": list(pids),
                    "timestamp": ts,
                }
            )
        return out


tracking_repository = TrackingRepository()


