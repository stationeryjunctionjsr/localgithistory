from app.models.schemas import AnalyticsEventCreate
from app.models.user import User
from typing import Dict, List, Optional
from app.models.schemas import MessageResponse, TrackBeaconRequest, TrackNotifyPincodeRequest, ItemSnippet
from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, Query, Request
from pydantic import BaseModel
from app.models.base import CamelBaseModel
from pydantic import Field, ConfigDict

from app.repositories.tracking_repository import tracking_repository
from app.utils.auth import get_optional_user, get_optional_user_lightweight, require_super_admin
from app.utils.limiter import limiter

router = APIRouter()

def ext_os(p, r): return p.os or "Unknown"
def ext_br(p, r):
    raw = p.browser or (r.headers["user-agent"] if "user-agent" in r.headers else None)
    return raw[:500] if raw else None

def ext_ip(p, r): return p.ip_address or (r.client.host if r.client else None)



def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid date format")


# Tracking request models

class BaseTrackingRequest(CamelBaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    campaign: Optional[str] = None
    source: Optional[str] = None
    os: Optional[str] = None
    browser: Optional[str] = None
    ip_address: Optional[str] = None

class TrackSearchRequest(BaseTrackingRequest):
    search_term: str
    results_count: int = 0
    session_id: Optional[str] = None
    product_ids: Optional[list] = None  # product IDs returned in search (for trending conversion)


class TrackViewRequest(BaseTrackingRequest):
    product_id: str
    product_name: str
    session_id: Optional[str] = None


class TrackClickRequest(BaseTrackingRequest):
    product_id: str
    product_name: str
    source: str = "unknown"
    session_id: Optional[str] = None


class TrackCartAbandonmentRequest(BaseTrackingRequest):
    cart_items: list = []
    cart_value: float = 0
    session_id: Optional[str] = None


class TrackSessionRequest(BaseTrackingRequest):
    session_id: str


class TrackPageViewRequest(BaseTrackingRequest):
    page: str
    session_id: Optional[str] = None


class TrackDropOffRequest(BaseTrackingRequest):
    page: str
    reason: str
    session_id: Optional[str] = None


class TrackErrorRequest(BaseTrackingRequest):
    message: str
    stack: Optional[str] = None
    url: Optional[str] = None
    line: Optional[int] = None
    col: Optional[int] = None
    session_id: Optional[str] = None



class SearchSuggestionsResponse(BaseModel):
    popularTerms: List[str]
    popularCategories: List[str]
    popularBrands: List[str]

class MostSearchedResponse(BaseModel):
    term: str
    count: int
    avgProductsFound: float

class ZeroResultSearchResponse(BaseModel):
    term: str
    count: int

class MostViewedResponse(BaseModel):
    product_id: str
    product_name: str
    count: int

class ReturningUserResponse(BaseModel):
    user_id: str
    name: str
    email: str
    lastSeen: Optional[str] = None

class DropOffPointResponse(BaseModel):
    page: str
    count: int
    reasons: Dict[str, int]

class CartAbandonmentResponse(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    type: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: Optional[str] = None
    cart_items: List[ItemSnippet] = []
    cart_value: Optional[float] = 0.0
    
    model_config = ConfigDict(extra='forbid', populate_by_name=True)

class MostAbandonedProductResponse(BaseModel):
    product_id: str
    product_name: str
    category: str
    abandonCount: int
    quantityAbandoned: int
    valueLost: float

@router.post("/beacon", response_model=MessageResponse)
@limiter.limit("60/minute")
async def track_beacon(
    request: Request,
    payload: TrackBeaconRequest = Body(default_factory=TrackBeaconRequest),
    current_user: Optional[User] = Depends(get_optional_user_lightweight),
):
    """Accept beacon payloads (e.g. from navigator.sendBeacon on page unload)."""
    beacon_data = AnalyticsEventCreate(
        type=payload.type or "beacon",
        user_id=current_user.id if current_user else None,
        session_id=payload.session_id,
        page=payload.page,
        reason=payload.reason,
        timestamp=payload.timestamp,
        os=ext_os(payload, request),
        browser=ext_br(payload, request),
        ip_address=ext_ip(payload, request),
        campaign=payload.campaign,
        source=payload.source
    )
    await tracking_repository.create(beacon_data)
    return {"message": "Beacon tracked"}


@router.post("/search", response_model=MessageResponse)
@limiter.limit("60/minute")
async def track_search(
    request: Request,
    payload: TrackSearchRequest,
    current_user: Optional[User] = Depends(get_optional_user_lightweight),
):
    segment = "wholesaler" if (current_user and current_user.role == "wholesaler") else "customer"
    await tracking_repository.trackSearch(
        current_user.id if current_user else None,
        payload.search_term,
        payload.results_count,
        payload.session_id,
        product_ids=payload.product_ids,
        segment=segment,
    )
    return {"message": "Search tracked"}


@router.post("/view", response_model=MessageResponse)
@limiter.limit("60/minute")
async def track_view(
    request: Request,
    payload: TrackViewRequest,
    current_user: Optional[User] = Depends(get_optional_user_lightweight),
):
    await tracking_repository.trackProductView(
        current_user.id if current_user else None, payload.product_id, payload.product_name, payload.session_id, os=ext_os(payload, request), browser=ext_br(payload, request), ip_address=ext_ip(payload, request), campaign=payload.campaign, source=payload.source)
    return {"message": "View tracked"}


@router.post("/click", response_model=MessageResponse)
@limiter.limit("60/minute")
async def track_click(
    request: Request,
    payload: TrackClickRequest,
    current_user: Optional[User] = Depends(get_optional_user_lightweight),
):
    await tracking_repository.trackProductClick(
        current_user.id if current_user else None,
        payload.product_id,
        payload.product_name,
        session_id=payload.session_id,
        source=payload.source,
    )
    return {"message": "Click tracked"}


@router.post("/cart-abandonment", response_model=MessageResponse)
@limiter.limit("60/minute")
async def track_cart_abandonment(
    request: Request,
    payload: TrackCartAbandonmentRequest,
    current_user: Optional[User] = Depends(get_optional_user_lightweight),
):
    await tracking_repository.trackCartAbandonment(
        current_user.id if current_user else None, payload.cart_items, payload.cart_value, payload.session_id, os=ext_os(payload, request), browser=ext_br(payload, request), ip_address=ext_ip(payload, request), campaign=payload.campaign, source=payload.source)
    return {"message": "Cart abandonment tracked"}


@router.post("/session", response_model=MessageResponse)
@limiter.limit("60/minute")
async def track_session(
    request: Request,
    payload: TrackSessionRequest,
    current_user: Optional[User] = Depends(get_optional_user_lightweight),
):
    await tracking_repository.trackSession(
        current_user.id if current_user else None, payload.session_id, None, os=ext_os(payload, request), browser=ext_br(payload, request), ip_address=ext_ip(payload, request), campaign=payload.campaign, source=payload.source)
    return {"message": "Session tracked"}


@router.post("/page-view", response_model=MessageResponse)
@limiter.limit("60/minute")
async def track_page_view(
    request: Request,
    payload: TrackPageViewRequest,
    current_user: Optional[User] = Depends(get_optional_user_lightweight),
):
    await tracking_repository.trackPageView(
        current_user.id if current_user else None, payload.page, payload.session_id, os=ext_os(payload, request), browser=ext_br(payload, request), ip_address=ext_ip(payload, request), campaign=payload.campaign, source=payload.source)
    return {"message": "Page view tracked"}


@router.post("/drop-off", response_model=MessageResponse)
@limiter.limit("60/minute")
async def track_drop_off(
    request: Request,
    payload: TrackDropOffRequest,
    current_user: Optional[User] = Depends(get_optional_user_lightweight),
):
    await tracking_repository.trackDropOff(
        current_user.id if current_user else None, payload.page, payload.reason, payload.session_id, os=ext_os(payload, request), browser=ext_br(payload, request), ip_address=ext_ip(payload, request), campaign=payload.campaign, source=payload.source)
    return {"message": "Drop-off tracked"}


@router.post("/error", response_model=MessageResponse)
@limiter.limit("60/minute")
async def track_frontend_error(
    request: Request,
    payload: TrackErrorRequest,
    current_user: Optional[User] = Depends(get_optional_user_lightweight),
):
    from app.utils.logger import logger

    user_id = current_user.id if current_user else "anonymous"
    error_msg = (
        f"[FRONTEND] Critical Error from user {user_id}\n"
        f"Message: {payload.message}\n"
        f"URL: {payload.url}\n"
        f"Line: {payload.line}:{payload.col}\n"
        f"Session: {payload.session_id}\n"
        f"Stack: {payload.stack}"
    )
    logger.error(error_msg)
    return {"message": "Frontend error tracked"}


class TrackCartItemRemoveRequest(BaseTrackingRequest):
    product_id: str
    quantity: int = 1
    session_id: Optional[str] = None


class TrackCartItemAddRequest(BaseTrackingRequest):
    product_id: str
    quantity: int = 1
    session_id: Optional[str] = None


class TrackFilterClickRequest(BaseTrackingRequest):
    filter_type: str
    filter_value: str
    session_id: Optional[str] = None


@router.post("/cart-remove", response_model=MessageResponse)
@limiter.limit("60/minute")
async def track_cart_item_remove(
    request: Request,
    payload: TrackCartItemRemoveRequest,
    current_user: Optional[User] = Depends(get_optional_user_lightweight),
):
    await tracking_repository.trackCartItemRemove(
        current_user.id if current_user else None, payload.product_id, payload.quantity, payload.session_id, os=ext_os(payload, request), browser=ext_br(payload, request), ip_address=ext_ip(payload, request), campaign=payload.campaign, source=payload.source)
    return {"message": "Cart item removal tracked"}


@router.post("/cart-add", response_model=MessageResponse)
@limiter.limit("60/minute")
async def track_cart_item_add(
    request: Request,
    payload: TrackCartItemAddRequest,
    current_user: Optional[User] = Depends(get_optional_user_lightweight),
):
    await tracking_repository.trackCartAdd(
        current_user.id if current_user else None, payload.product_id, payload.quantity, payload.session_id, os=ext_os(payload, request), browser=ext_br(payload, request), ip_address=ext_ip(payload, request), campaign=payload.campaign, source=payload.source)
    return {"message": "Cart item addition tracked"}


@router.post("/filter-click", response_model=MessageResponse)
@limiter.limit("60/minute")
async def track_filter_click(
    request: Request,
    payload: TrackFilterClickRequest,
    current_user: Optional[User] = Depends(get_optional_user_lightweight),
):
    await tracking_repository.trackFilterClick(
        current_user.id if current_user else None, payload.filter_type, payload.filter_value, payload.session_id, os=ext_os(payload, request), browser=ext_br(payload, request), ip_address=ext_ip(payload, request), campaign=payload.campaign, source=payload.source)
    return {"message": "Filter click tracked"}


@router.get("/recent", response_model=List[str])
async def get_recent_searches(
    session_id: Optional[str] = None,
    limit: int = Query(5, ge=1, le=20),
    current_user: Optional[User] = Depends(get_optional_user),
    req: Request = None,
):
    user_id = current_user.id if current_user else None
    return await tracking_repository.getRecentUserSearches(user_id, session_id, limit)


@router.delete("/recent", response_model=MessageResponse)
async def clear_recent_searches(
    session_id: Optional[str] = None,
    current_user: Optional[User] = Depends(get_optional_user),
    req: Request = None,
):
    user_id = current_user.id if current_user else None
    await tracking_repository.clearRecentSearches(user_id, session_id)
    return {"ok": True}


@router.get("/suggestions", response_model=SearchSuggestionsResponse)
async def get_search_suggestions(
    limit: int = Query(5, ge=1, le=20), current_user: Optional[User] = Depends(get_optional_user),
    req: Request = None,
):
    # Popular terms
    most_searched = await tracking_repository.getMostSearched(limit)

    # We can also return popular categories/brands if needed
    # For now, let's just return the terms
    return {
        "popularTerms": [item.term for item in most_searched],
        "popularCategories": ["Office Supplies", "Notebooks", "Luxury Pens", "Art Materials"],
        "popularBrands": ["Parker", "Moleskine", "Faber-Castell", "Camel"],
    }


@router.get("/most-searched", response_model=List[MostSearchedResponse])
async def get_most_searched(
    limit: int = Query(5, ge=1, le=100),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_super_admin),
):
    start = parse_date(start_date)
    end = parse_date(end_date)
    most_searched = await tracking_repository.getMostSearched(limit, start, end)
    return most_searched


@router.get("/zero-result-searches", response_model=List[ZeroResultSearchResponse])
async def get_zero_result_searches(
    limit: int = Query(50, ge=1, le=1000),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_super_admin),
):
    start = parse_date(start_date)
    end = parse_date(end_date)
    zero_results = await tracking_repository.getZeroResultSearches(limit, start, end)
    return zero_results


@router.get("/most-viewed", response_model=List[MostViewedResponse])
async def get_most_viewed(
    limit: int = Query(5, ge=1, le=100),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_super_admin),
):
    start = parse_date(start_date)
    end = parse_date(end_date)
    most_viewed = await tracking_repository.getMostViewed(limit, start, end)
    return most_viewed


@router.get("/returning-users", response_model=List[ReturningUserResponse])
async def get_returning_users(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_super_admin),
):
    start = parse_date(start_date)
    end = parse_date(end_date)
    users = await tracking_repository.getReturningUsers(start, end)
    return users


@router.get("/drop-off-points", response_model=List[DropOffPointResponse])
async def get_drop_off_points(
    limit: int = Query(10, ge=1, le=100),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_super_admin),
):
    start = parse_date(start_date)
    end = parse_date(end_date)
    drop_off_points = await tracking_repository.getDropOffs(limit, start, end)
    return drop_off_points


@router.get("/cart-abandonments", response_model=List[CartAbandonmentResponse])
async def get_cart_abandonments(
    limit: int = Query(100, ge=1, le=1000),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_super_admin),
):
    start = parse_date(start_date)
    end = parse_date(end_date)
    abandonments = await tracking_repository.getCartAbandonments(limit, start, end)
    return abandonments


@router.get("/most-abandoned-products", response_model=List[MostAbandonedProductResponse])
async def get_most_abandoned_products(
    limit: int = Query(50, ge=1, le=1000),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_super_admin),
):
    start = parse_date(start_date)
    end = parse_date(end_date)
    products = await tracking_repository.getMostAbandonedProducts(limit, start, end)
    return products




@router.post("/notify-pincode", response_model=MessageResponse)
async def track_notify_pincode(request: Request, data: TrackNotifyPincodeRequest, current_user: Optional[User] = Depends(get_optional_user)):
    user_id = current_user.id if current_user else None
    user_email = current_user.email if current_user else data.email
    
    # Store the notification request
    record = AnalyticsEventCreate(
        type="notify_pincode",
        product_id=data.product_id,
        product_name=data.product_name,
        user_id=user_id,
        filterName="email",
        filter_value=user_email,
        search_term=data.pincode,
        browser=(request.headers["user-agent"][:500] if "user-agent" in request.headers else None),

        ip_address=request.client.host if request.client else None
    )
    await tracking_repository.create(record)
    return {"message": "Notification registered", "success": True}
