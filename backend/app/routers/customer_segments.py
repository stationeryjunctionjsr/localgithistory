from app.models.user import User
from typing import Dict, Any, List
from app.models.schemas import MessageResponse
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.repositories.customer_segments_repository import customer_segments_repository
from app.utils.auth import require_super_admin
from app.utils.logger import logger

router = APIRouter()



class CustomerSegmentResponse(BaseModel):
    id: str = Field(alias="_id")
    name: str
    type: str
    userIds: List[str]
    filters: Optional[Dict[str, Any]] = None
    isActive: bool
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class RefreshSegmentResponse(BaseModel):
    matchedUsersCount: int
    matchedUserIds: List[str]

class FilterSegmentResponse(BaseModel):
    users: List[Dict[str, Any]]

class CustomerSegmentCreate(BaseModel):
    name: str
    type: str  # 'retail' | 'business'
    userIds: List[str]
    filters: Optional[Dict[str, Any]] = None


class CustomerSegmentUpdate(BaseModel):
    name: Optional[str] = None
    userIds: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    isActive: Optional[bool] = None


@router.get("", response_model=List[CustomerSegmentResponse])
@router.get("/", response_model=List[CustomerSegmentResponse])
async def get_segments(type: Optional[str] = None, admin: User = Depends(require_super_admin)):
    segments = await customer_segments_repository.get_all(type)
    return segments


@router.get("/{segment_id}", response_model=CustomerSegmentResponse)
async def get_segment(segment_id: str, admin: User = Depends(require_super_admin)):
    segment = await customer_segments_repository.get_by_id(segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    return segment


@router.post("", response_model=CustomerSegmentResponse)
@router.post("/", response_model=CustomerSegmentResponse)
async def create_segment(segment: CustomerSegmentCreate, admin: User = Depends(require_super_admin)):
    data = segment
    data._id = str(uuid.uuid4())
    data.isActive = True
    created = await customer_segments_repository.create(data)
    return created


@router.put("/{segment_id}", response_model=CustomerSegmentResponse)
async def update_segment(segment_id: str, segment: CustomerSegmentUpdate, admin: User = Depends(require_super_admin)):
    existing = await customer_segments_repository.get_by_id(segment_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Segment not found")

    update_data = {k: v for k, v in segment.items()}
    # Support direct toggle of isActive if passed in extra data
    # Note: request.json() is async and needs the actual request object injected in the route
    # For now, we'll rely on the schema or a more explicit approach.
    # The current line was referencing an undefined global 'Request'.
    # Since we use CustomerSegmentUpdate model, if isActive is not in it, we might need to handle it.
    # Let's add isActive to CustomerSegmentUpdate.
    updated = await customer_segments_repository.update(segment_id, update_data)
    return updated


@router.delete("/{segment_id}", response_model=MessageResponse)
async def delete_segment(segment_id: str, admin: User = Depends(require_super_admin)):
    success = await customer_segments_repository.delete(segment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Segment not found")
    return {"status": "success"}


class FilterCriteria(BaseModel):
    minAverageOrderValue: Optional[float] = None
    maxAverageOrderValue: Optional[float] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    minOrderFrequency: Optional[int] = None
    maxOrderFrequency: Optional[int] = None
    state: Optional[str] = None
    district: Optional[str] = None
    appUser: Optional[bool] = None
    behavior: Optional[str] = None
    role: str


async def run_segment_filter(criteria: FilterCriteria):
    from app.config.database import get_async_session_factory
    from sqlalchemy import text
    
    factory = get_async_session_factory()
    
    # We will build a single SQL query
    select_clause = "SELECT u.id FROM sj_users u"
    
    joins = []
    where_clauses = ["u.role = :role"]
    params = {"role": criteria.role}
    
    # 1. Location filters
    if criteria.state:
        where_clauses.append("u.state = :state")
        params["state"] = criteria.state
        
    if criteria.district:
        where_clauses.append("(u.city = :district OR u.district = :district)")
        params["district"] = criteria.district
        
    # 2. App User filter
    if criteria.appUser is True:
        joins.append("JOIN sj_device_subscriptions ds ON ds.user_id = u.id")
    elif criteria.appUser is False:
        joins.append("LEFT JOIN sj_device_subscriptions ds ON ds.user_id = u.id")
        where_clauses.append("ds.id IS NULL")
        
    # 3. Order-based filters
    needs_orders = any(x is not None for x in [
        criteria.minAverageOrderValue, criteria.maxAverageOrderValue,
        criteria.minOrderFrequency, criteria.maxOrderFrequency
    ]) or (criteria.behavior == "coupon_user")
    
    if needs_orders:
        joins.append("LEFT JOIN sj_orders o ON o.user = u.id")
        
        # Order Date filters
        if criteria.startDate:
            where_clauses.append("(o.created_at >= :start_date OR o.id IS NULL)")
            params["start_date"] = criteria.startDate.replace("Z", "+00:00")
        if criteria.endDate:
            where_clauses.append("(o.created_at <= :end_date OR o.id IS NULL)")
            params["end_date"] = criteria.endDate.replace("Z", "+00:00")
            
        # Behavior: coupon_user
        if criteria.behavior == "coupon_user":
            where_clauses.append("(o.coupon_code IS NOT NULL AND o.coupon_code != '')")
            
    # Behavior: abandoned_cart
    if criteria.behavior == "abandoned_cart":
        joins.append("JOIN sj_carts c ON c.user_id = u.id")
        where_clauses.append("(c.items IS NOT NULL AND c.items != '[]')")
        # Ensure they haven't ordered recently
        if "LEFT JOIN sj_orders o ON o.user = u.id" not in joins:
            joins.append("LEFT JOIN sj_orders o ON o.user = u.id")
            if criteria.endDate:
                where_clauses.append("(o.created_at <= :end_date OR o.id IS NULL)")
                params["end_date"] = criteria.endDate.replace("Z", "+00:00")
    
    # Build query
    sql = select_clause + " " + " ".join(joins)
    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)
        
    # Group by
    sql += " GROUP BY u.id"
    
    # Having clauses (Order frequency and AOV)
    having_clauses = []
    if criteria.minOrderFrequency is not None:
        having_clauses.append("COUNT(o.id) >= :min_freq")
        params["min_freq"] = criteria.minOrderFrequency
    if criteria.maxOrderFrequency is not None:
        having_clauses.append("COUNT(o.id) <= :max_freq")
        params["max_freq"] = criteria.maxOrderFrequency
        
    if criteria.minAverageOrderValue is not None:
        having_clauses.append("AVG(o.total) >= :min_aov")
        params["min_aov"] = criteria.minAverageOrderValue
    if criteria.maxAverageOrderValue is not None:
        having_clauses.append("AVG(o.total) <= :max_aov")
        params["max_aov"] = criteria.maxAverageOrderValue
        
    if having_clauses:
        sql += " HAVING " + " AND ".join(having_clauses)
        
    async with factory() as session:
        result = await session.execute(text(sql), params)
        rows = result.fetchall()
        
    return [{"_id": str(r.id)} for r in rows]


async def seed_system_segments():
    """Ensure pre-defined system segments exist in the database."""
    import asyncio

    # Quick-exit: if any system segment already exists, all 16 were seeded before.
    try:
        first_id = "system_retail_registered_no_order"
        existing = await customer_segments_repository.get_by_id(first_id)
        if existing:
            logger.info("System segments already seeded — skipping.")
            return
        # Fallback: count all segments; >0 means at least one boot already seeded them
        total = await customer_segments_repository.storage.count({})
        if total > 0:
            logger.info("System segments already present (%d total) — skipping.", total)
            return
    except Exception as e:
        logger.warning("Could not check existing segments (will attempt re-seed): %s", e)

    system_behaviors = [
        ("registered_no_order", "Registered but did not order"),
        ("registered_one_order", "Registered and ordered once"),
        ("regular_registered", "Regular Registered (Avg >= 4 orders/month)"),
        ("registered_irregular", "Registered and irregular (>1 order and <=3 orders per month)"),
        ("downloaded_no_order", "Downloaded but did not order"),
        ("downloaded_one_order", "Downloaded and ordered once"),
        ("regular_app_user", "Regular App User (Avg >= 4 orders/month)"),
        ("downloaded_irregular", "Downloaded and irregular (>1 order and <=3 orders per month)"),
    ]

    for seg_type in ["retail", "business"]:
        role = "customer" if seg_type == "retail" else "wholesaler"
        for behavior_id, behavior_name in system_behaviors:
            full_id = f"system_{seg_type}_{behavior_id}"
            existing = await customer_segments_repository.get_by_id(full_id)

            if not existing:
                logger.info("Seeding system segment: %s (%s)", behavior_name, seg_type)
                criteria = FilterCriteria(role=role, behavior=behavior_id)
                users = await run_segment_filter(criteria)
                user_ids = [str((u.id if u.id is not None else u.id)) for u in users]

                await customer_segments_repository.create(
                    {
                        "_id": full_id,
                        "name": behavior_name,
                        "type": seg_type,
                        "userIds": user_ids,
                        "filters": {"behavior": behavior_id},
                        "isActive": True,
                        "isSystem": True,
                    }
                )
            # Yield the event loop between iterations so incoming requests
            # aren't starved of DB pool connections.
            await asyncio.sleep(0.5)


@router.post("/filter", response_model=FilterSegmentResponse)
async def filter_users(criteria: FilterCriteria, admin: User = Depends(require_super_admin)):
    return await run_segment_filter(criteria)


@router.post("/{segment_id}/refresh", response_model=RefreshSegmentResponse)
async def refresh_segment(segment_id: str, admin: User = Depends(require_super_admin)):
    segment = await customer_segments_repository.get_by_id(segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    filters = (segment.filters or {})
    if not filters:
        return {"status": "success", "message": "No filters to re-apply", "userIds": (segment.user_ids or [])}

    role = "customer" if segment.type == "retail" else "wholesaler"
    criteria = FilterCriteria(role=role, **filters)

    users = await run_segment_filter(criteria)
    user_ids = [str((u.id if u.id is not None else u.id)) for u in users]

    from datetime import datetime, timezone

    await customer_segments_repository.update(
        segment_id, {"userIds": user_ids, "lastRefreshedAt": datetime.now(timezone.utc).isoformat()}
    )

    return {"status": "success", "count": len(user_ids), "userIds": user_ids}
