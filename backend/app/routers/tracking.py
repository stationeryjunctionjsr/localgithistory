from app.models.user import User
from typing import Dict, Any, List
from app.models.schemas import MessageResponse
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, Query, Request
from pydantic import BaseModel, Field, ConfigDict

from app.repositories.tracking_repository import tracking_repository
from app.utils.auth import get_optional_user, require_super_admin
from app.utils.limiter import limiter

router = APIRouter()


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


# Tracking request models
class TrackSearchRequest(BaseModel):
    searchTerm: str
    resultsCount: int = 0
    sessionId: Optional[str] = None
    productIds: Optional[list] = None  # product IDs returned in search (for trending conversion)


class TrackViewRequest(BaseModel):
    productId: str
    productName: str
    sessionId: Optional[str] = None


class TrackClickRequest(BaseModel):
    productId: str
    productName: str
    source: str = "unknown"
    sessionId: Optional[str] = None


class TrackCartAbandonmentRequest(BaseModel):
    cartItems: list = []
    cartValue: float = 0
    sessionId: Optional[str] = None


class TrackSessionRequest(BaseModel):
    sessionId: str
    isReturning: bool = False


class TrackPageViewRequest(BaseModel):
    page: str
    sessionId: Optional[str] = None


class TrackDropOffRequest(BaseModel):
    page: str
    reason: str
    sessionId: Optional[str] = None


class TrackErrorRequest(BaseModel):
    message: str
    stack: Optional[str] = None
    url: Optional[str] = None
    line: Optional[int] = None
    col: Optional[int] = None
    sessionId: Optional[str] = None



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
    productId: str
    productName: str
    count: int

class ReturningUserResponse(BaseModel):
    userId: str
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
    userId: Optional[str] = None
    sessionId: Optional[str] = None
    timestamp: Optional[str] = None
    cartItems: List[Any] = []
    cartValue: Optional[float] = 0.0
    
    model_config = ConfigDict(extra='allow', populate_by_name=True)

class MostAbandonedProductResponse(BaseModel):
    productId: str
    productName: str
    category: str
    abandonCount: int
    quantityAbandoned: int
    valueLost: float

@router.post("/beacon", response_model=MessageResponse)
@limiter.limit("60/minute")
async def track_beacon(
    request: Request,
    payload: Dict[str, Any] = Body(default_factory=dict),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """Accept beacon payloads (e.g. from navigator.sendBeacon on page unload)."""
    await tracking_repository.create(
        {
            "type": "beacon",
            "userId": current_user.id if current_user else None,
            **payload,
        }
    )
    return {"message": "Beacon tracked"}


@router.post("/search", response_model=MessageResponse)
@limiter.limit("60/minute")
async def track_search(
    request: Request,
    payload: TrackSearchRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    segment = "wholesaler" if (current_user and current_user.role == "wholesaler") else "customer"
    await tracking_repository.trackSearch(
        current_user.id if current_user else None,
        payload.searchTerm,
        payload.resultsCount,
        payload.sessionId,
        product_ids=payload.productIds,
        segment=segment,
    )
    return {"message": "Search tracked"}


@router.post("/view", response_model=MessageResponse)
@limiter.limit("60/minute")
async def track_view(
    request: Request,
    payload: TrackViewRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    await tracking_repository.trackProductView(
        current_user.id if current_user else None, payload.productId, payload.productName, payload.sessionId
    )
    return {"message": "View tracked"}


@router.post("/click", response_model=MessageResponse)
@limiter.limit("60/minute")
async def track_click(
    request: Request,
    payload: TrackClickRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    await tracking_repository.trackProductClick(
        current_user.id if current_user else None,
        payload.productId,
        payload.productName,
        payload.source,
        payload.sessionId,
    )
    return {"message": "Click tracked"}


@router.post("/cart-abandonment", response_model=MessageResponse)
@limiter.limit("60/minute")
async def track_cart_abandonment(
    request: Request,
    payload: TrackCartAbandonmentRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    await tracking_repository.trackCartAbandonment(
        current_user.id if current_user else None, payload.cartItems, payload.cartValue, payload.sessionId
    )
    return {"message": "Cart abandonment tracked"}


@router.post("/session", response_model=MessageResponse)
@limiter.limit("60/minute")
async def track_session(
    request: Request,
    payload: TrackSessionRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    await tracking_repository.trackSession(
        current_user.id if current_user else None, payload.sessionId, payload.isReturning
    )
    return {"message": "Session tracked"}


@router.post("/page-view", response_model=MessageResponse)
@limiter.limit("60/minute")
async def track_page_view(
    request: Request,
    payload: TrackPageViewRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    await tracking_repository.trackPageView(
        current_user.id if current_user else None, payload.page, payload.sessionId
    )
    return {"message": "Page view tracked"}


@router.post("/drop-off", response_model=MessageResponse)
@limiter.limit("60/minute")
async def track_drop_off(
    request: Request,
    payload: TrackDropOffRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    await tracking_repository.trackDropOff(
        current_user.id if current_user else None, payload.page, payload.reason, payload.sessionId
    )
    return {"message": "Drop-off tracked"}


@router.post("/error", response_model=MessageResponse)
@limiter.limit("60/minute")
async def track_frontend_error(
    request: Request,
    payload: TrackErrorRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    from app.utils.logger import logger

    user_id = current_user.id if current_user else "anonymous"
    error_msg = (
        f"[FRONTEND] Critical Error from user {user_id}\n"
        f"Message: {payload.message}\n"
        f"URL: {payload.url}\n"
        f"Line: {payload.line}:{payload.col}\n"
        f"Session: {payload.sessionId}\n"
        f"Stack: {payload.stack}"
    )
    logger.error(error_msg)
    return {"message": "Frontend error tracked"}


class TrackCartItemRemoveRequest(BaseModel):
    productId: str
    quantity: int = 1
    sessionId: Optional[str] = None


class TrackCartItemAddRequest(BaseModel):
    productId: str
    quantity: int = 1
    sessionId: Optional[str] = None


class TrackFilterClickRequest(BaseModel):
    filterType: str
    filterValue: str
    sessionId: Optional[str] = None


@router.post("/cart-remove", response_model=MessageResponse)
@limiter.limit("60/minute")
async def track_cart_item_remove(
    request: Request,
    payload: TrackCartItemRemoveRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    await tracking_repository.trackCartItemRemove(
        current_user.id if current_user else None, payload.productId, payload.quantity, payload.sessionId
    )
    return {"message": "Cart item removal tracked"}


@router.post("/cart-add", response_model=MessageResponse)
@limiter.limit("60/minute")
async def track_cart_item_add(
    request: Request,
    payload: TrackCartItemAddRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    await tracking_repository.trackCartAdd(
        current_user.id if current_user else None, payload.productId, payload.quantity, payload.sessionId
    )
    return {"message": "Cart item addition tracked"}


@router.post("/filter-click", response_model=MessageResponse)
@limiter.limit("60/minute")
async def track_filter_click(
    request: Request,
    payload: TrackFilterClickRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    await tracking_repository.trackFilterClick(
        current_user.id if current_user else None, payload.filterType, payload.filterValue, payload.sessionId
    )
    return {"message": "Filter click tracked"}


@router.get("/recent", response_model=List[str])
async def get_recent_searches(
    sessionId: Optional[str] = None,
    limit: int = Query(5, ge=1, le=20),
    current_user: Optional[dict] = Depends(get_optional_user),
    req: Request = None,
):
    user_id = current_user.id if current_user else None
    return await tracking_repository.getRecentUserSearches(user_id, sessionId, limit)


@router.delete("/recent", response_model=MessageResponse)
async def clear_recent_searches(
    sessionId: Optional[str] = None,
    current_user: Optional[dict] = Depends(get_optional_user),
    req: Request = None,
):
    user_id = current_user.id if current_user else None
    await tracking_repository.clearRecentSearches(user_id, sessionId)
    return {"ok": True}


@router.get("/suggestions", response_model=SearchSuggestionsResponse)
async def get_search_suggestions(
    limit: int = Query(5, ge=1, le=20), current_user: Optional[dict] = Depends(get_optional_user),
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
    drop_off_points = await tracking_repository.getDropOffPoints(limit, start, end)
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
async def track_notify_pincode(data: dict, current_user: Optional[dict] = Depends(get_optional_user)):
    user_id = current_user.id if current_user else None
    user_email = current_user.email if current_user else data.get("email")
    
    # Store the notification request
    record = {
        "event": "notify_pincode",
        "productId": data.get("productId"),
        "productName": data.get("productName"),
        "pincode": data.get("pincode"),
        "userId": user_id,
        "email": user_email,
        "createdAt": datetime.now(timezone.utc).isoformat()
    }
    await tracking_repository.create(record)
    return {"success": True}
