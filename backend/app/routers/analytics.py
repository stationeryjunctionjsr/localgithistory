from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query

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
        return None


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


@router.post("/events", response_model=Dict)
async def record_event(
    event: Dict[str, Any] = Body(..., description="Analytics event payload"),
    user_info: Optional[dict] = Depends(get_optional_user),
):
    """Record a client-side analytics event (web/mobile). Auth is optional; will attach user if token provided."""

    if not event.get("type"):
        raise HTTPException(status_code=400, detail="Event type is required")

    enriched_event = {
        **event,
        # Never trust a client-supplied userId for unauthenticated requests —
        # only attach the verified userId from the session token.
        "userId": user_info.get("_id") if user_info else None,
        "timestamp": event.get("timestamp") or datetime.now(timezone.utc).isoformat(),
    }

    try:
        stored = await analytics_repository.record_event(enriched_event)

        # Sync/replicate mobile events to tracking repository
        event_type = enriched_event.get("type")
        session_id = enriched_event.get("sessionId")
        user_id = enriched_event.get("userId")
        payload = enriched_event.get("payload") or {}

        try:
            if event_type == "session_start":
                is_returning = payload.get("returning", False)
                await tracking_repository.trackSession(user_id, session_id, is_returning)
            elif event_type == "page_view":
                page = enriched_event.get("page", "/")
                await tracking_repository.trackPageView(user_id, page, session_id)
            elif event_type == "product_view":
                product_id = payload.get("productId")
                product_name = payload.get("productName", "Unknown")
                if product_id:
                    await tracking_repository.trackProductView(user_id, product_id, product_name, session_id)
            elif event_type == "product_click":
                product_id = payload.get("productId")
                product_name = payload.get("productName", "Unknown")
                source = payload.get("source", "mobile_app")
                if product_id:
                    await tracking_repository.trackProductClick(user_id, product_id, product_name, source, session_id)
            elif event_type == "add_to_cart":
                product_id = payload.get("productId")
                quantity = payload.get("quantity", 1)
                if product_id:
                    await tracking_repository.trackCartAdd(user_id, product_id, quantity, session_id)
            elif event_type == "remove_from_cart":
                product_id = payload.get("productId")
                quantity = payload.get("quantity", 1)
                if product_id:
                    await tracking_repository.trackCartItemRemove(user_id, product_id, quantity, session_id)
            elif event_type == "search":
                query = payload.get("query", "")
                results_count = payload.get("resultsCount", 0)
                await tracking_repository.trackSearch(user_id, query, results_count, session_id, segment="customer")
            elif event_type == "add_to_wishlist":
                product_id = payload.get("productId")
                if product_id:
                    await tracking_repository.trackWishlistAdd(user_id, product_id, session_id)
            elif event_type == "session_end":
                reason = payload.get("reason", "unknown")
                await tracking_repository.create(
                    {"type": "session_end", "userId": user_id, "sessionId": session_id, "reason": reason}
                )
            elif event_type == "begin_checkout":
                await tracking_repository.trackPageView(user_id, "/checkout/step1", session_id)
            elif event_type == "purchase":
                await tracking_repository.trackPageView(user_id, "/checkout/complete", session_id)
        except Exception as sync_err:
            # Prevent synchronization issues from failing the main request
            logger.error("Failed to sync event to tracking repository: %s", str(sync_err), exc_info=True)

        return {"status": "ok", "eventId": stored.get("_id")}
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/kpi", response_model=Dict)
async def get_kpi_metrics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin", "admin")),
):
    """Get KPI metrics"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_kpi_metrics(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/dashboard-data", response_model=Dict)
async def get_dashboard_data(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin", "admin")),
):
    """Get aggregated dashboard stats and reports"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_dashboard_data(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")

@router.get("/reports/bundle-performance")
async def get_bundle_performance(current_user: dict = Depends(require_roles("super_admin"))):
    """
    Get detailed bundle performance reports.
    """
    try:
        return await analytics_repository.get_bundle_performance_report()
    except Exception as e:
        logger.error("Error fetching bundle performance: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/sales-over-time", response_model=List[Dict])
async def get_sales_over_time(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    group_by: str = Query("hour", pattern="^(hour|day|month)$"),
    seller_id: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin", "wholesaler")),
):
    """Get sales over time. Sellers are auto-scoped to their own orders."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_sales_over_time(start, end, group_by)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/sales-breakdown", response_model=Dict)
async def get_sales_breakdown(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin")),
):
    """Get sales breakdown"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_sales_breakdown(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/average-order-value", response_model=List[Dict])
async def get_average_order_value(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    group_by: str = Query("hour", pattern="^(hour|day|month)$"),
    current_user: dict = Depends(require_roles("super_admin")),
):
    """Get average order value over time"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_average_order_value_over_time(start, end, group_by)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/sales-by-channel", response_model=List[Dict])
async def get_sales_by_channel(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin")),
):
    """Get sales by channel"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_sales_by_channel(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/sales-by-product", response_model=List[Dict])
async def get_sales_by_product(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    seller_id: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin", "wholesaler")),
):
    """Get top products by sales. Sellers are auto-scoped to their own products."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_sales_by_product(start, end, limit)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/conversion-rate", response_model=Dict)
async def get_conversion_rate(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    group_by: str = Query("day", pattern="^(hour|day|month)$"),
    current_user: dict = Depends(require_roles("super_admin")),
):
    """Get conversion funnel breakdown (sessions → cart → checkout → completed)"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_conversion_rate_over_time(start, end, group_by)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/conversion-breakdown", response_model=Dict)
async def get_conversion_breakdown(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin")),
):
    """Get conversion rate breakdown (alias for conversion-rate funnel data)"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_conversion_rate_over_time(start, end, "day")
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/checkout-funnel", response_model=Dict)
async def get_checkout_funnel(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin")),
):
    """Get detailed checkout funnel breakdown"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_checkout_funnel(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/sessions-by-device", response_model=List[Dict])
async def get_sessions_by_device(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin")),
):
    """Get sessions by device type"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_sessions_by_device_type(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/sessions-by-location", response_model=List[Dict])
async def get_sessions_by_location(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin")),
):
    """Get sessions by location"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_sessions_by_location(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/all-user-engagement", response_model=Dict)
async def get_all_user_engagement(
    current_user: dict = Depends(require_roles("super_admin")),
):
    """
    Get aggregated engagement metrics across all users, bucketed by durations.
    """
    try:
        return await analytics_repository.get_all_user_engagement_aggregate()
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/products-sell-through", response_model=List[Dict])
async def get_products_sell_through(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    seller_id: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin", "wholesaler")),
):
    """Get products by sell-through rate. Sellers are auto-scoped to their own catalogue."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_products_by_sell_through_rate(start, end, limit)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/customer-cohort", response_model=List[Dict])
async def get_customer_cohort(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin")),
):
    """Get customer cohort analysis"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_customer_cohort_analysis(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/sessions-by-landing-page", response_model=List[Dict])
async def get_sessions_by_landing_page(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin")),
):
    """Get sessions by landing page"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_sessions_by_landing_page(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/user-engagement", response_model=Dict)
async def get_my_user_engagement(current_user: dict = Depends(get_current_user)):
    """
    Get engagement metrics for the current user, calculated since registration:
    - averageSessionTimeSeconds: average session duration (all devices)
    - averageDaysBetweenSessions: average days between two consecutive sessions
    - averagePagesPerSession: average pages visited per session
    - sessionOrderRate: share of sessions with at least one order placed (0-1)
    """
    try:
        return await analytics_repository.get_user_engagement_metrics(current_user["_id"])
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/user-engagement/{user_id}", response_model=Dict)
async def get_user_engagement_by_id(
    user_id: str,
    current_user: dict = Depends(require_roles("super_admin")),
):
    """
    Get engagement metrics for a specific user (admin). Same metrics as /user-engagement.
    """
    try:
        result = await analytics_repository.get_user_engagement_metrics(user_id)
        if result.get("error"):
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/top-users", response_model=List[Dict])
async def get_top_users_report(
    role: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(require_roles("super_admin")),
):
    start = parse_date(start_date)
    end = parse_date(end_date)
    return await analytics_repository.get_top_users_by_revenue(role, start, end, limit)


@router.get("/reports/user-order-stats", response_model=List[Dict])
async def get_user_order_stats_report(
    role: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin")),
):
    start = parse_date(start_date)
    end = parse_date(end_date)
    return await analytics_repository.get_user_order_stats(role, start, end)


@router.get("/reports/items-by-user-type", response_model=List[Dict])
async def get_items_by_user_type_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin")),
):
    start = parse_date(start_date)
    end = parse_date(end_date)
    return await analytics_repository.get_items_by_user_type(start, end)


@router.get("/reports/summary", response_model=Dict)
async def get_reports_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin")),
):
    start = parse_date(start_date)
    end = parse_date(end_date)
    return await analytics_repository.get_all_reports_summary(start, end)


@router.get("/reports/returns", response_model=List[Dict])
async def get_returns_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    seller_id: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin", "wholesaler")),
):
    """Get returns and refund requests report. Sellers see only their own returns."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_returns_report(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/payment-methods", response_model=List[Dict])
async def get_payment_methods_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    seller_id: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin", "wholesaler")),
):
    """Get orders and revenue broken down by payment method. Sellers see their own orders."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_payment_methods_report(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/revenue-by-category", response_model=List[Dict])
async def get_revenue_by_category(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    seller_id: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin", "wholesaler")),
):
    """Get revenue broken down by product category. Sellers see their own categories."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_revenue_by_category(start, end, limit)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/inventory-alerts", response_model=List[Dict])
async def get_inventory_alerts(
    threshold: int = Query(10, ge=0, le=1000),
    seller_id: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin", "wholesaler")),
):
    """Get products with stock at or below the given threshold. Sellers see their own products."""
    try:
        return await analytics_repository.get_inventory_alerts(threshold)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/fulfillment-time", response_model=List[Dict])
async def get_fulfillment_time_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    seller_id: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin", "wholesaler")),
):
    """Get average order fulfillment time per order. Sellers see their own orders."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_fulfillment_time_report(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/coupon-usage", response_model=List[Dict])
async def get_coupon_usage_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    seller_id: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin", "wholesaler")),
):
    """Get coupon/discount usage report. Sellers see coupons used on their orders."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_coupon_usage_report(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/sales-by-location", response_model=List[Dict])
async def get_sales_by_location_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    seller_id: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin", "wholesaler")),
):
    """Get sales grouped by location (city/state). Sellers see their own delivery destinations."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_sales_by_location(start, end, limit)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/new-vs-returning", response_model=List[Dict])
async def get_new_vs_returning_customer_sales_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin")),
):
    """Get revenue from new vs returning customers"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_new_vs_returning_customer_sales(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/items-bought-together", response_model=List[Dict])
async def get_items_bought_together_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    current_user: dict = Depends(require_roles("super_admin")),
):
    """Get market basket analysis: products bought together"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_items_bought_together(start, end, limit)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/sales-by-device", response_model=List[Dict])
async def get_sales_by_device_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin")),
):
    """Get sales grouped by device type"""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_sales_by_device_type(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/top-returned-products", response_model=List[Dict])
async def get_top_returned_products_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    seller_id: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin", "wholesaler")),
):
    """Get most frequently returned products. Sellers see only their own products."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_top_returned_products(start, end, limit)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/inventory-value-by-category", response_model=List[Dict])
async def get_inventory_value_by_category_report(
    seller_id: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin", "wholesaler")),
):
    """Get inventory value grouped by category. Sellers see only their own catalogue."""
    try:
        return await analytics_repository.get_inventory_value_by_category()
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


# ── New platform-analytics endpoints (super_admin only) ──────────────────────

@router.get("/reports/sessions-over-time", response_model=List[Dict])
async def get_sessions_over_time_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin")),
):
    """Daily session count and unique visitor trend. Super admin only."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_sessions_over_time(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/visitors-now", response_model=List[Dict])
async def get_visitors_now_report(
    current_user: dict = Depends(require_roles("super_admin")),
):
    """Real-time active sessions in last 15 minutes. Super admin only."""
    try:
        return await analytics_repository.get_active_visitors_now()
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/searches-no-clicks", response_model=List[Dict])
async def get_searches_no_clicks_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin")),
):
    """Search queries with zero product clicks. Super admin only."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_searches_with_no_clicks(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/search-conversion", response_model=List[Dict])
async def get_search_conversion_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin")),
):
    """% of search sessions that produced an order. Super admin only."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_search_conversion_rate(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/bounce-rate", response_model=List[Dict])
async def get_bounce_rate_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin")),
):
    """Daily bounce rate over time. Super admin only."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_bounce_rate_over_time(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/rfm-segments", response_model=List[Dict])
async def get_rfm_segments_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin")),
):
    """RFM customer segmentation. Super admin only."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_rfm_segments(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/customer-frequency", response_model=List[Dict])
async def get_customer_frequency_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin")),
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

@router.get("/reports/net-sales", response_model=List[Dict])
async def get_net_sales_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    seller_id: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin", "wholesaler")),
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


@router.get("/reports/sales-heatmap", response_model=List[Dict])
async def get_sales_heatmap_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    seller_id: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin", "wholesaler")),
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


@router.get("/reports/inventory-runway", response_model=List[Dict])
async def get_inventory_runway_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    seller_id: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin", "wholesaler")),
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

@router.get("/reports/sales-by-channel-detailed", response_model=List[Dict])
async def get_sales_by_channel_detailed_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin")),
):
    """Revenue, order count, and AOV by channel (desktop/mobile web/app). Super admin only."""
    try:
        start = parse_date(start_date)
        end = parse_date(end_date)
        return await analytics_repository.get_sales_by_channel_detailed(start, end)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/reports/discounts-audit", response_model=List[Dict])
async def get_discounts_audit_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    seller_id: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin", "wholesaler")),
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


@router.get("/reports/products-pct-sold", response_model=List[Dict])
async def get_products_pct_sold_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    seller_id: Optional[str] = Query(None),
    current_user: dict = Depends(require_roles("super_admin", "wholesaler")),
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
