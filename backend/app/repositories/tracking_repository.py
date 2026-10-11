import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from app.models.tracking import (
    Tracking,
    RecentlyViewedProductItem,
    TopProductItem,
    DropOffPointItem,
    MostAbandonedProductItem,
    MostSearchedItem,
    ZeroResultSearchItem,
    MostViewedItem,
    ReturningUserItem,
    ProductSearchCount,
)

from app.db.storage_factory import get_storage
from app.models.schemas import AnalyticsEventCreate, AnalyticsSessionCreate
from app.db.mysql_analytics_session_dao import MySQLAnalyticsSessionDAO


class TrackingRepository:
    def __init__(self):
        self.storage = get_storage("tracking")
        self.session_dao = MySQLAnalyticsSessionDAO()
        self._ANALYTICS_LIMIT = 5000  # Default limit for safety

    async def findAll(
        self,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        product_id: Optional[str] = None,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
    ):
        return await self.storage.findAll(
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            product_id=product_id,
            skip=skip,
            limit=limit,
        )

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
        auth_session_id: Optional[str] = None,
        source: Optional[str] = None, page: Optional[str] = None, os: Optional[str] = None, browser: Optional[str] = None,
        ip_address: Optional[str] = None, campaign: Optional[str] = None, device_type: Optional[str] = None,
        device_os_version: Optional[str] = None, device_model: Optional[str] = None, device_app_version: Optional[str] = None
    ):
        await self.session_dao.create_session(
            AnalyticsSessionCreate(
                session_id=session_id,
                user_id=user_id,
                auth_session_id=auth_session_id,
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

    async def getSessionsCount(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> int:
        return await self.storage.get_sessions_count(start_date=start_date, end_date=end_date)

    async def getRecentlyViewedProducts(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 10,
    ) -> list:
        """
        Return the most recently viewed distinct products for a user or session.
        Joins with the products table to pull displayImage and price.
        Falls back gracefully if the product record is not found.
        """
        from app.db.storage_factory import get_storage

        if not user_id and not session_id:
            return []

        return await self.storage.get_recently_viewed_products(
            user_id=str(user_id) if user_id else None,
            session_id=session_id if not user_id else None,
            limit=limit,
        )

    async def getTopProducts(
        self, limit: int = 10, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[TopProductItem]:
        return await self.storage.get_top_products(limit=limit, start_date=start_date, end_date=end_date)

    async def getDropOffs(
        self, limit: int = 10, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[DropOffPointItem]:
        return await self.storage.get_drop_offs(limit=limit, start_date=start_date, end_date=end_date)

    async def getCartAbandonments(
        self, limit: int = 100, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Tracking]:
        return await self.storage.get_cart_abandonments(limit=limit, start_date=start_date, end_date=end_date)

    async def getMostAbandonedProducts(
        self, limit: int = 50, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[MostAbandonedProductItem]:
        return await self.storage.get_most_abandoned_products(limit=limit, start_date=start_date, end_date=end_date)

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
    ) -> List[str]:
        if not user_id and not session_id:
            return []
        return await self.storage.get_recent_user_searches(
            user_id=str(user_id) if user_id else None,
            session_id=str(session_id) if session_id else None,
            limit=limit,
        )

    def _parse_timestamp(self, raw: Optional[str]) -> Optional[datetime]:
        if not raw:
            return None
        try:
            return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid timestamp format: {raw}") from e

    async def get_search_counts_by_product(self, days: int, segment: str) -> List[ProductSearchCount]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        all_searches = await self.storage.find_by_date_range(
            event_type="product_search", start_date=cutoff, segment=segment
        )
        counts = {}
        for doc in all_searches:
            if doc.product_ids:
                for pid in doc.product_ids:
                    if pid:
                        counts[pid] = counts.get(pid, 0) + 1
        return [ProductSearchCount(product_id=pid, count=cnt) for pid, cnt in counts.items()]

    async def get_searches_with_products(self, days: int, segment: str) -> List[Tracking]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        all_searches = await self.storage.find_by_date_range(
            event_type="product_search", start_date=cutoff, segment=segment
        )
        return [doc for doc in all_searches if doc.product_ids]

    async def getMostSearched(
        self, limit: int = 5, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[MostSearchedItem]:
        return await self.storage.get_most_searched(limit=limit, start_date=start_date, end_date=end_date)

    async def getZeroResultSearches(
        self, limit: int = 50, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[ZeroResultSearchItem]:
        return await self.storage.get_zero_result_searches(limit=limit, start_date=start_date, end_date=end_date)

    async def getMostViewed(
        self, limit: int = 5, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[MostViewedItem]:
        return await self.storage.get_most_viewed(limit=limit, start_date=start_date, end_date=end_date)

    async def getReturningUsers(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[ReturningUserItem]:
        seen_items = await self.storage.get_returning_user_ids(
            start_date=start_date, end_date=end_date
        )
        if not seen_items:
            return []
        from app.repositories.user_repository import user_repository
        users = await user_repository.findByIds([item.user_id for item in seen_items])
        return [
            ReturningUserItem(
                user_id=u.id,
                name=u.name or "Unknown",
                email=u.email or "Unknown",
                last_seen=next((item.last_seen for item in seen_items if item.user_id == u.id), None),
            )
            for u in users
        ]

    
tracking_repository = TrackingRepository()
