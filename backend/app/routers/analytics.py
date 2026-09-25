import json
from app.models.analytics_schemas import (
    UserOrderStatsResponse, ItemsByUserTypeResponse, ReturnsReportResponse,
    PaymentMethodsReportResponse, RevenueByCategoryResponse, InventoryAlertResponse,
    FulfillmentTimeReportResponse, CouponUsageReportResponse, SalesByLocationReportResponse,
    NewVsReturningCustomerSalesResponse, ItemsBoughtTogetherResponse, SalesByDeviceReportResponse,
    TopReturnedProductsResponse, InventoryValueByCategoryResponse, SessionsOverTimeResponse,
    VisitorsNowResponse, SearchesNoClicksResponse, SearchConversionResponse,
    BounceRateResponse, RFMSegmentsResponse, CustomerFrequencyResponse,
    NetSalesResponse, SalesHeatmapResponse, InventoryRunwayResponse,
    DiscountsAuditResponse, ProductsPctSoldResponse, BundlePerformanceReportResponse,
    SalesByChannelDetailedResponse, AllReportsSummaryResponse
)
from app.db.mysql_events_dao import EventCreate, EventPayloadItem
from app.models.user import User
from app.models.schemas import MessageResponse, AnalyticsEventCreate, AnalyticsEventPayload
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request

from app.repositories.analytics_repository import analytics_repository
from app.repositories.tracking_repository import tracking_repository
from app.utils.auth import get_current_user, get_optional_user, require_roles
from app.utils.logger import logger

router = APIRouter()


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse date string to datetime"""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except Exception as e:
        logger.warning("Failed to parse date string '%s': %s", date_str, str(e))
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid date format")


def _resolve_seller_id(current_user: dict, requested_seller_id: Optional[str] = None) -> Optional[str]:
    """
    Resolves the effective seller_id for a request.
    - Sellers (wholesaler role): always scoped to their own _id, ignores any requested_seller_id.
    - Super admin: uses requested_seller_id if provided, otherwise None (all sellers).
    """
    role = (current_user.role or "")
    if role == "wholesaler":
        return current_user.id
    # super_admin / admin
    return requested_seller_id



from pydantic import BaseModel, Field, ConfigDict, RootModel
from typing import List, Dict, Any, Optional

class RecordEventResponse(BaseModel):
    status: str
    eventId: Optional[str] = None

class KPIMetricsResponse(BaseModel):
    gross_sales: float
    returning_customer_rate: float
    orders_fulfilled: int
    orders: int

class DashboardStats(BaseModel):
    model_config = ConfigDict(extra='forbid')
    totalProducts: int
    totalWholesalers: int
    totalCustomers: int
    totalValets: int
    totalOrders: int
    totalRevenue: float

class TopProductResponse(BaseModel):
    productId: str
    productName: str
    quantity: int
    revenue: float

class TopCustomerResponse(BaseModel):
    userId: str
    name: str
    orderCount: int
    revenue: float

class MostSearchedResponse(BaseModel):
    term: str
    searchCount: int
    resultsCount: int

class MostViewedResponse(BaseModel):
    productId: str
    productName: str
    viewCount: int

class DashboardDataResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')
    stats: DashboardStats
    topProducts: List[TopProductResponse]
    topWholesalers: List[TopCustomerResponse]
    topCustomers: List[TopCustomerResponse]
    mostSearched: List[MostSearchedResponse]
    mostViewed: List[MostViewedResponse]


class SalesOverTimeResponse(BaseModel):
    period: str
    sales: float
    orderCount: int
    aov: float

class SalesBreakdownResponse(BaseModel):
    gross_sales: float
    discounts: float
    returns: float
    net_sales: float
    shipping_charges: float
    return_fees: float
    taxes: float
    total_sales: float

class AverageOrderValueResponse(BaseModel):
    period: str
    average_order_value: float

class SalesByChannelResponse(BaseModel):
    channel: str
    sales: float

class SalesByProductResponse(BaseModel):
    product_id: str
    productId: str
    name: str
    productName: str
    quantity: int
    revenue: float

class FunnelStage(BaseModel):
    count: int
    percentage: float
    drop_percentage: float

class FunnelStageNoDrop(BaseModel):
    count: int
    percentage: float

class ConversionRateResponse(BaseModel):
    sessions: FunnelStageNoDrop
    added_to_cart: FunnelStage
    reached_checkout: FunnelStage
    completed: FunnelStage
    overall_conversion_rate: float

class CheckoutFunnelResponse(BaseModel):
    cart: FunnelStageNoDrop
    shipping: FunnelStage
    review: FunnelStage
    payment: FunnelStage
    completed: FunnelStage
    overall_checkout_conversion: float

class SessionsByDeviceResponse(BaseModel):
    device: str
    sessions: int

class SessionsByLocationResponse(BaseModel):
    location: str
    sessions: int

class DurationBucket(BaseModel):
    range: str
    count: int

class UserMetric(BaseModel):
    userId: str
    name: str
    email: str
    averageSessionTimeSeconds: float
    totalSessions: int

class AllUserEngagementResponse(BaseModel):
    duration_buckets: List[DurationBucket]
    user_metrics: List[UserMetric]

class ProductsSellThroughResponse(BaseModel):
    product_id: str
    name: str
    sold: int
    stock: int
    sell_through_rate: float

class CustomerCohortResponse(BaseModel):
    cohort: str
    months: List[int]

class SessionsByLandingPageResponse(BaseModel):
    landing_page: str
    sessions: int

class UserEngagementResponse(BaseModel):
    userId: Optional[str] = None
    registrationDate: Optional[str] = None
    totalSessions: Optional[int] = None
    averageSessionTimeSeconds: Optional[float] = None
    averageDaysBetweenSessions: Optional[float] = None
    averagePagesPerSession: Optional[float] = None
    sessionsWithOrder: Optional[int] = None
    sessionOrderRate: Optional[float] = None
    error: Optional[str] = None

class TopUsersReportResponse(BaseModel):
    userId: str
    name: str
    userName: str
    email: str
    userEmail: str
    role: str
    revenue: float

    

@router.post("/events", response_model=RecordEventResponse)
async def record_event(
    request: Request,
    event: AnalyticsEventCreate = Body(..., description="Analytics event payload"),
    user_info: Optional[User] = Depends(get_optional_user),
):
    """Record a client-side analytics event (web/mobile). Auth is optional; will attach user if token provided."""

    if not event.type:
        raise HTTPException(status_code=400, detail="Event type is required")

    user_id = str(user_info.id) if user_info else None

    payload_items = []
    if event.payload:
        if event.payload.returning is not None:
            payload_items.append(EventPayloadItem(key="returning", value=str(event.payload.returning)))
        if event.payload.product_id is not None:
            payload_items.append(EventPayloadItem(key="productId", value=str(event.payload.product_id)))
        if event.payload.productName is not None:
            payload_items.append(EventPayloadItem(key="productName", value=str(event.payload.productName)))
        if event.payload.source is not None:
            payload_items.append(EventPayloadItem(key="source", value=str(event.payload.source)))
        if event.payload.quantity is not None:
            payload_items.append(EventPayloadItem(key="quantity", value=str(event.payload.quantity)))
        if event.payload.query is not None:
            payload_items.append(EventPayloadItem(key="query", value=str(event.payload.query)))
        if event.payload.resultsCount is not None:
            payload_items.append(EventPayloadItem(key="resultsCount", value=str(event.payload.resultsCount)))
        if event.payload.reason is not None:
            payload_items.append(EventPayloadItem(key="reason", value=str(event.payload.reason)))
        if event.payload.testRunId is not None:
            payload_items.append(EventPayloadItem(key="testRunId", value=str(event.payload.testRunId)))
        if event.payload.screen is not None:
            payload_items.append(EventPayloadItem(key="screen", value=str(event.payload.screen)))
    

    payload_items.append(EventPayloadItem(key="userId", value=str(user_id) if user_id else ""))
    payload_items.append(EventPayloadItem(key="sessionId", value=str(event.session_id) if event.session_id else ""))
    payload_items.append(EventPayloadItem(key="timestamp", value=str(event.timestamp) if event.timestamp else datetime.now(timezone.utc).isoformat()))
    if event.os:
        payload_items.append(EventPayloadItem(key="os", value=str(event.os)))
    if event.browser:
        payload_items.append(EventPayloadItem(key="browser", value=str(event.browser)))
    if event.campaign:
        payload_items.append(EventPayloadItem(key="campaign", value=str(event.campaign)))
    if event.ip_address:
        payload_items.append(EventPayloadItem(key="ipAddress", value=str(event.ip_address)))
    elif request.client and request.client.host:
        payload_items.append(EventPayloadItem(key="ipAddress", value=str(request.client.host)))



    if event.device:
        payload_items.append(EventPayloadItem(key="device_model", value=str(event.device)))



    try:
        if event.page:
            payload_items.append(EventPayloadItem(key="page", value=str(event.page)))
    except AttributeError:
        pass

    event_create = EventCreate(
        eventType=event.type,
        payload=payload_items
    )


    try:
        event_type = event.type
        session_id = event.session_id
        raw_payload = event.payload
        payload_obj = raw_payload or AnalyticsEventPayload()
        tracking_obj = None

        # Unify OS
        final_os = event.os
        final_browser = event.browser
        final_device_type = event.deviceType
        final_device_os_version = event.deviceOsVersion
        final_device_model = event.deviceModel or event.device
        final_device_app_version = event.deviceAppVersion

        # Determine IP Address
        final_ip = event.ip_address
        if not final_ip and request.client and request.client.host:
            final_ip = request.client.host

        final_campaign = event.campaign
        final_source = event.source

        kwargs = {
            "os": final_os,
            "browser": final_browser,
            "ipAddress": final_ip,
            "campaign": final_campaign,
            "source": final_source,
            "deviceType": final_device_type,
            "deviceOsVersion": final_device_os_version,
            "deviceModel": final_device_model,
            "deviceAppVersion": final_device_app_version
        }

        try:
            if event_type == "session_start":
                is_returning = bool(payload_obj.returning) if payload_obj.returning is not None else False
                tracking_obj = await tracking_repository.trackSession(user_id, session_id, is_returning, **kwargs)
            elif event_type == "page_view":
                page = event.page if event.page is not None else "/"
                tracking_obj = await tracking_repository.trackPageView(user_id, page, session_id, **kwargs)
            elif event_type == "product_view":
                product_id = payload_obj.product_id
                product_name = payload_obj.productName if payload_obj.productName is not None else "Unknown"
                if product_id:
                    tracking_obj = await tracking_repository.trackProductView(user_id, product_id, product_name, session_id, **kwargs)
            elif event_type == "product_click":
                product_id = payload_obj.product_id
                product_name = payload_obj.productName if payload_obj.productName is not None else "Unknown"
                p_source = payload_obj.source if payload_obj.source is not None else (final_source or "mobile_app")
                if product_id:
                    tracking_obj = await tracking_repository.trackProductClick(user_id, product_id, product_name, session_id, **{**kwargs, "source": p_source})
            elif event_type == "add_to_cart":
                product_id = payload_obj.product_id
                quantity = payload_obj.quantity if payload_obj.quantity is not None else 1
                if product_id:
                    tracking_obj = await tracking_repository.trackCartAdd(user_id, product_id, quantity, session_id, **kwargs)
            elif event_type == "remove_from_cart":
                product_id = payload_obj.product_id
                quantity = payload_obj.quantity if payload_obj.quantity is not None else 1
                if product_id:
                    tracking_obj = await tracking_repository.trackCartItemRemove(user_id, product_id, quantity, session_id, **kwargs)
            elif event_type == "search":
                query = payload_obj.query if payload_obj.query is not None else ""
                results_count = payload_obj.resultsCount if payload_obj.resultsCount is not None else 0
                tracking_obj = await tracking_repository.trackSearch(user_id, query, results_count, session_id, segment="customer", **kwargs)
            elif event_type == "add_to_wishlist":

                product_id = payload_obj.product_id
                if product_id:
                    tracking_obj = await tracking_repository.trackWishlistAdd(user_id, product_id, "Unknown", session_id)
            elif event_type == "session_end":
                reason = payload_obj.reason if payload_obj.reason is not None else "unknown"
                from app.models.schemas import AnalyticsEventCreate
                tracking_obj = await tracking_repository.create(
                    AnalyticsEventCreate(type="session_end", userId=user_id, sessionId=session_id, reason=reason)
                )
            elif event_type == "begin_checkout":
                tracking_obj = await tracking_repository.trackPageView(user_id, "/checkout/step1", session_id)
            elif event_type == "purchase":
                tracking_obj = await tracking_repository.trackPageView(user_id, "/checkout/complete", session_id)
        except Exception as sync_err:
            logger.error("Failed to sync event to tracking repository: %s", str(sync_err), exc_info=True)

        if tracking_obj:
            event_create.tracking_id = int(tracking_obj.id)
            
        stored = await analytics_repository.record_event(event_create)



        event_id = str(stored.id) if stored else None
        return {"status": "ok", "eventId": event_id}
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/kpi", response_model=KPIMetricsResponse)
async def get_kpi_metrics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin", "admin")),
):
    """Get KPI metrics"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_kpi_metrics(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/dashboard-data", response_model=DashboardDataResponse)
async def get_dashboard_data(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin", "admin")),
):
    """Get aggregated dashboard stats and reports"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_dashboard_data(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")

@router.get("/reports/bundle-performance", response_model=List[UserOrderStatsResponse])
async def get_bundle_performance(current_user: User = Depends(require_roles("super_admin"))):
    """
    Get detailed bundle performance reports.
    """
    try:
        return await analytics_repository.get_bundle_performance_report()
    except Exception as e:
        logger.error("Error fetching bundle performance: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/sales-over-time", response_model=List[SalesOverTimeResponse])
async def get_sales_over_time(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    group_by: str = Query("hour", pattern="^(hour|day|month)$"),
    seller_id: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin", "wholesaler")),
):
    """Get sales over time. Sellers are auto-scoped to their own orders."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_sales_over_time(start, end, group_by)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/sales-breakdown", response_model=SalesBreakdownResponse)
async def get_sales_breakdown(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin")),
):
    """Get sales breakdown"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_sales_breakdown(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/average-order-value", response_model=List[AverageOrderValueResponse])
async def get_average_order_value(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    group_by: str = Query("hour", pattern="^(hour|day|month)$"),
    current_user: User = Depends(require_roles("super_admin")),
):
    """Get average order value over time"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_average_order_value_over_time(start, end, group_by)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/sales-by-channel", response_model=List[ItemsByUserTypeResponse])
async def get_sales_by_channel(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin")),
):
    """Get sales by channel"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_sales_by_channel(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/sales-by-product", response_model=List[SalesByProductResponse])
async def get_sales_by_product(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    seller_id: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin", "wholesaler")),
):
    """Get top products by sales. Sellers are auto-scoped to their own products."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_sales_by_product(start, end, limit)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/conversion-rate", response_model=ConversionRateResponse)
async def get_conversion_rate(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    group_by: str = Query("day", pattern="^(hour|day|month)$"),
    current_user: User = Depends(require_roles("super_admin")),
):
    """Get conversion funnel breakdown (sessions → cart → checkout → completed)"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_conversion_rate_over_time(start, end, group_by)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/conversion-breakdown", response_model=ConversionRateResponse)
async def get_conversion_breakdown(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin")),
):
    """Get conversion rate breakdown (alias for conversion-rate funnel data)"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_conversion_rate_over_time(start, end, "day")
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/checkout-funnel", response_model=CheckoutFunnelResponse)
async def get_checkout_funnel(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin")),
):
    """Get detailed checkout funnel breakdown"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_checkout_funnel(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/sessions-by-device", response_model=List[SessionsByDeviceResponse])
async def get_sessions_by_device(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin")),
):
    """Get sessions by device type"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_sessions_by_device_type(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/sessions-by-location", response_model=List[SessionsByLocationResponse])
async def get_sessions_by_location(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin")),
):
    """Get sessions by location"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_sessions_by_location(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/all-user-engagement", response_model=AllUserEngagementResponse)
async def get_all_user_engagement(
    current_user: User = Depends(require_roles("super_admin")),
):
    """
    Get aggregated engagement metrics across all users, bucketed by durations.
    """
    try:
        return await analytics_repository.get_all_user_engagement_aggregate()
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/products-sell-through", response_model=List[ProductsSellThroughResponse])
async def get_products_sell_through(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    seller_id: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin", "wholesaler")),
):
    """Get products by sell-through rate. Sellers are auto-scoped to their own catalogue."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_products_by_sell_through_rate(start, end, limit)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/customer-cohort", response_model=List[CustomerCohortResponse])
async def get_customer_cohort(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin")),
):
    """Get customer cohort analysis"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_customer_cohort_analysis(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/sessions-by-landing-page", response_model=List[SessionsByLandingPageResponse])
async def get_sessions_by_landing_page(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin")),
):
    """Get sessions by landing page"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_sessions_by_landing_page(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/user-engagement", response_model=UserEngagementResponse)
async def get_my_user_engagement(current_user: User = Depends(get_current_user)):
    """
    Get engagement metrics for the current user, calculated since registration:
    - averageSessionTimeSeconds: average session duration (all devices)
    - averageDaysBetweenSessions: average days between two consecutive sessions
    - averagePagesPerSession: average pages visited per session
    - sessionOrderRate: share of sessions with at least one order placed (0-1)
    """
    try:
        return await analytics_repository.get_user_engagement_metrics(current_user.id)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/user-engagement/{user_id}", response_model=UserEngagementResponse)
async def get_user_engagement_by_id(
    user_id: str,
    current_user: User = Depends(require_roles("super_admin")),
):
    """
    Get engagement metrics for a specific user (admin). Same metrics as /user-engagement.
    """
    try:
        result = await analytics_repository.get_user_engagement_metrics(user_id)
        if "error" in result and result["error"]:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/top-users", response_model=List[TopUsersReportResponse])
async def get_top_users_report(
    role: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_roles("super_admin")),
):
    start = parse_date(start_date)
    end = parse_date(end_date)
    return await analytics_repository.get_top_users_by_revenue(role, start, end, limit)


@router.get("/reports/user-order-stats", response_model=List[UserOrderStatsResponse])
async def get_user_order_stats_report(
    role: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin")),
):
    start = parse_date(start_date)
    end = parse_date(end_date)
    return await analytics_repository.get_user_order_stats(role, start, end)


@router.get("/reports/items-by-user-type", response_model=List[ItemsByUserTypeResponse])
async def get_items_by_user_type_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin")),
):
    start = parse_date(start_date)
    end = parse_date(end_date)
    return await analytics_repository.get_items_by_user_type(start, end)


@router.get("/reports/summary", response_model=AllReportsSummaryResponse)
async def get_reports_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin")),
):
    start = parse_date(start_date)
    end = parse_date(end_date)
    return await analytics_repository.get_all_reports_summary(start, end)


@router.get("/reports/returns", response_model=List[ReturnsReportResponse])
async def get_returns_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    seller_id: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin", "wholesaler")),
):
    """Get returns and refund requests report. Sellers see only their own returns."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_returns_report(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/payment-methods", response_model=List[PaymentMethodsReportResponse])
async def get_payment_methods_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    seller_id: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin", "wholesaler")),
):
    """Get orders and revenue broken down by payment method. Sellers see their own orders."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_payment_methods_report(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/revenue-by-category", response_model=List[PaymentMethodsReportResponse])
async def get_revenue_by_category(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    seller_id: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin", "wholesaler")),
):
    """Get revenue broken down by product category. Sellers see their own categories."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_revenue_by_category(start, end, limit)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/inventory-alerts", response_model=List[RevenueByCategoryResponse])
async def get_inventory_alerts(
    threshold: int = Query(10, ge=0, le=1000),
    seller_id: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin", "wholesaler")),
):
    """Get products with stock at or below the given threshold. Sellers see their own products."""
    try:
        return await analytics_repository.get_inventory_alerts(threshold)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/fulfillment-time", response_model=List[InventoryAlertResponse])
async def get_fulfillment_time_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    seller_id: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin", "wholesaler")),
):
    """Get average order fulfillment time per order. Sellers see their own orders."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_fulfillment_time_report(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/coupon-usage", response_model=List[FulfillmentTimeReportResponse])
async def get_coupon_usage_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    seller_id: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin", "wholesaler")),
):
    """Get coupon/discount usage report. Sellers see coupons used on their orders."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_coupon_usage_report(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/sales-by-location", response_model=List[CouponUsageReportResponse])
async def get_sales_by_location_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    seller_id: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin", "wholesaler")),
):
    """Get sales grouped by location (city/state). Sellers see their own delivery destinations."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_sales_by_location(start, end, limit)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/new-vs-returning", response_model=List[SalesByLocationReportResponse])
async def get_new_vs_returning_customer_sales_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin")),
):
    """Get revenue from new vs returning customers"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_new_vs_returning_customer_sales(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/items-bought-together", response_model=List[NewVsReturningCustomerSalesResponse])
async def get_items_bought_together_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    current_user: User = Depends(require_roles("super_admin")),
):
    """Get market basket analysis: products bought together"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_items_bought_together(start, end, limit)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/sales-by-device", response_model=List[ItemsBoughtTogetherResponse])
async def get_sales_by_device_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin")),
):
    """Get sales grouped by device type"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_sales_by_device_type(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/top-returned-products", response_model=List[SalesByDeviceReportResponse])
async def get_top_returned_products_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    seller_id: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin", "wholesaler")),
):
    """Get most frequently returned products. Sellers see only their own products."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_top_returned_products(start, end, limit)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/inventory-value-by-category", response_model=List[TopReturnedProductsResponse])
async def get_inventory_value_by_category_report(
    seller_id: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin", "wholesaler")),
):
    """Get inventory value grouped by category. Sellers see only their own catalogue."""
    try:
        return await analytics_repository.get_inventory_value_by_category()
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


# ── New platform-analytics endpoints (super_admin only) ──────────────────────

@router.get("/reports/sessions-over-time", response_model=List[InventoryValueByCategoryResponse])
async def get_sessions_over_time_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin")),
):
    """Daily session count and unique visitor trend. Super admin only."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_sessions_over_time(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/visitors-now", response_model=List[SessionsOverTimeResponse])
async def get_visitors_now_report(
    current_user: User = Depends(require_roles("super_admin")),
):
    """Real-time active sessions in last 15 minutes. Super admin only."""
    try:
        return await analytics_repository.get_active_visitors_now()
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/searches-no-clicks", response_model=List[VisitorsNowResponse])
async def get_searches_no_clicks_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin")),
):
    """Search queries with zero product clicks. Super admin only."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_searches_with_no_clicks(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/search-conversion", response_model=List[SearchesNoClicksResponse])
async def get_search_conversion_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin")),
):
    """% of search sessions that produced an order. Super admin only."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_search_conversion_rate(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/bounce-rate", response_model=List[SearchConversionResponse])
async def get_bounce_rate_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin")),
):
    """Daily bounce rate over time. Super admin only."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_bounce_rate_over_time(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/rfm-segments", response_model=List[BounceRateResponse])
async def get_rfm_segments_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin")),
):
    """RFM customer segmentation. Super admin only."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_rfm_segments(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/customer-frequency", response_model=List[RFMSegmentsResponse])
async def get_customer_frequency_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin")),
):
    """One-time vs repeat buyer split. Super admin only."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_customer_frequency_report(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


# ── New seller-accessible endpoints (wholesaler + super_admin, seller-scoped) ─

@router.get("/reports/net-sales", response_model=List[CustomerFrequencyResponse])
async def get_net_sales_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    seller_id: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin", "wholesaler")),
):
    """Per-order gross-to-net breakdown. Sellers see only their own orders."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        eff_seller_id = _resolve_seller_id(current_user, seller_id)
        return await analytics_repository.get_net_sales_by_order(start, end, seller_id=eff_seller_id)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/sales-heatmap", response_model=List[NetSalesResponse])
async def get_sales_heatmap_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    seller_id: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin", "wholesaler")),
):
    """Orders by day-of-week x hour-of-day. Sellers see only their own orders."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        eff_seller_id = _resolve_seller_id(current_user, seller_id)
        return await analytics_repository.get_sales_heatmap(start, end, seller_id=eff_seller_id)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/inventory-runway", response_model=List[SalesHeatmapResponse])
async def get_inventory_runway_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    seller_id: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin", "wholesaler")),
):
    """Days of stock remaining per product. Sellers see only their own products."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        eff_seller_id = _resolve_seller_id(current_user, seller_id)
        return await analytics_repository.get_inventory_runway(start, end, seller_id=eff_seller_id)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


# ── Batch 2 new endpoints ────────────────────────────────────────────────────

@router.get("/reports/sales-by-channel-detailed", response_model=List[InventoryRunwayResponse])
async def get_sales_by_channel_detailed_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin")),
):
    """Revenue, order count, and AOV by channel (desktop/mobile web/app). Super admin only."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_sales_by_channel_detailed(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/discounts-audit", response_model=List[DiscountsAuditResponse])
async def get_discounts_audit_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    seller_id: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin", "wholesaler")),
):
    """Per-order discount/coupon audit. Sellers see only their own orders."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        eff_seller_id = _resolve_seller_id(current_user, seller_id)
        return await analytics_repository.get_discounts_audit(start, end, seller_id=eff_seller_id)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/products-pct-sold", response_model=List[DiscountsAuditResponse])
async def get_products_pct_sold_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    seller_id: Optional[str] = Query(None),
    current_user: User = Depends(require_roles("super_admin", "wholesaler")),
):
    """Units sold as % of opening stock. Sellers see only their own catalogue."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        eff_seller_id = _resolve_seller_id(current_user, seller_id)
        return await analytics_repository.get_products_pct_sold(start, end, seller_id=eff_seller_id)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")

