import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.repositories.customer_segments_repository import customer_segments_repository
from app.utils.auth import require_super_admin
from app.utils.logger import logger

router = APIRouter()


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


@router.get("")
@router.get("/")
async def get_segments(type: Optional[str] = None, admin: dict = Depends(require_super_admin)):
    segments = await customer_segments_repository.get_all(type)
    return segments


@router.get("/{segment_id}")
async def get_segment(segment_id: str, admin: dict = Depends(require_super_admin)):
    segment = await customer_segments_repository.get_by_id(segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    return segment


@router.post("")
@router.post("/")
async def create_segment(segment: CustomerSegmentCreate, admin: dict = Depends(require_super_admin)):
    data = segment.model_dump()
    data["_id"] = str(uuid.uuid4())
    data["isActive"] = True
    created = await customer_segments_repository.create(data)
    return created


@router.put("/{segment_id}")
async def update_segment(segment_id: str, segment: CustomerSegmentUpdate, admin: dict = Depends(require_super_admin)):
    existing = await customer_segments_repository.get_by_id(segment_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Segment not found")

    update_data = {k: v for k, v in segment.model_dump(exclude_unset=True).items()}
    # Support direct toggle of isActive if passed in extra data
    # Note: request.json() is async and needs the actual request object injected in the route
    # For now, we'll rely on the schema or a more explicit approach.
    # The current line was referencing an undefined global 'Request'.
    # Since we use CustomerSegmentUpdate model, if isActive is not in it, we might need to handle it.
    # Let's add isActive to CustomerSegmentUpdate.
    updated = await customer_segments_repository.update(segment_id, update_data)
    return updated


@router.delete("/{segment_id}")
async def delete_segment(segment_id: str, admin: dict = Depends(require_super_admin)):
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
    import datetime

    from app.repositories.order_repository import order_repository
    from app.repositories.user_repository import user_repository

    users = await user_repository.findAll({"role": criteria.role})

    needs_orders = any(
        x is not None
        for x in [
            criteria.minAverageOrderValue,
            criteria.maxAverageOrderValue,
            criteria.minOrderFrequency,
            criteria.maxOrderFrequency,
            criteria.startDate,
            criteria.endDate,
            criteria.behavior,
        ]
    )

    user_order_stats = {}
    user_orders_map = {}
    if needs_orders:
        all_orders = await order_repository.findAll()
        if criteria.startDate or criteria.endDate:
            filtered_orders = []
            for o in all_orders:
                c_at_str = o.get("createdAt")
                if not c_at_str:
                    continue
                try:
                    c_at = datetime.datetime.fromisoformat(c_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
                    if criteria.startDate:
                        start_dt = datetime.datetime.fromisoformat(criteria.startDate.replace("Z", "+00:00")).replace(
                            tzinfo=None
                        )
                        if c_at < start_dt:
                            continue
                    if criteria.endDate:
                        end_dt = datetime.datetime.fromisoformat(criteria.endDate.replace("Z", "+00:00")).replace(
                            tzinfo=None
                        )
                        end_dt = end_dt.replace(hour=23, minute=59, second=59)
                        if c_at > end_dt:
                            continue
                    filtered_orders.append(o)
                except ValueError as e:
                    logger.warning("Invalid date format for order %s in segment filter: %s", o.get("_id"), str(e))
                except Exception as e:
                    logger.error("Unexpected error parsing date for order %s in segment filter: %s", o.get("_id"), str(e), exc_info=True)
            all_orders = filtered_orders

        for o in all_orders:
            uid = str(o.get("user"))
            if not uid:
                continue
            if uid not in user_order_stats:
                user_order_stats[uid] = {"count": 0, "total": 0.0}
            if uid not in user_orders_map:
                user_orders_map[uid] = []
            user_order_stats[uid]["count"] += 1
            user_order_stats[uid]["total"] += o.get("total", 0.0)
            user_orders_map[uid].append(o)

        for _uid, stat in user_order_stats.items():
            stat["avg"] = stat["total"] / stat["count"] if stat["count"] > 0 else 0.0

    app_user_map = {}
    if criteria.appUser is not None or (criteria.behavior and criteria.behavior != "none"):
        from app.db.storage_factory import get_storage

        device_storage = get_storage("deviceSubscriptions")
        devices = await device_storage.findAll()
        for d in devices:
            uid = d.get("userId")
            if uid:
                app_user_map[str(uid)] = True

    filtered_users = []
    from app.repositories.coupon_repository import coupon_repository

    for u in users:
        uid = str(u.get("_id", u.get("id")))

        # Location
        if criteria.state or criteria.district:
            addr = u.get("address", {})
            if criteria.state and addr.get("state") != criteria.state:
                continue
            if (
                criteria.district
                and addr.get("city") != criteria.district
                and addr.get("district") != criteria.district
            ):
                continue

        # Orders
        if needs_orders:
            stats = user_order_stats.get(uid, {"count": 0, "avg": 0.0})
            if criteria.minOrderFrequency is not None and stats["count"] < criteria.minOrderFrequency:
                continue
            if criteria.maxOrderFrequency is not None and stats["count"] > criteria.maxOrderFrequency:
                continue
            if criteria.minAverageOrderValue is not None and stats["avg"] < criteria.minAverageOrderValue:
                continue
            if criteria.maxAverageOrderValue is not None and stats["avg"] > criteria.maxAverageOrderValue:
                continue

            # Additional pre-defined behaviors logic
            if criteria.behavior and criteria.behavior != "none":
                matches = await coupon_repository._user_matches_behavior(
                    uid,
                    criteria.behavior,
                    user_orders=user_orders_map.get(uid, []),
                    has_app=app_user_map.get(uid, False),
                )
                if not matches:
                    continue

        # App user
        if criteria.appUser is not None:
            is_app = app_user_map.get(uid, False)
            if is_app != criteria.appUser:
                continue

        u_copy = dict(u)
        u_copy["id"] = uid
        filtered_users.append(u_copy)

    return filtered_users


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
                user_ids = [str(u.get("_id", u.get("id"))) for u in users]

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


@router.post("/filter")
async def filter_users(criteria: FilterCriteria, admin: dict = Depends(require_super_admin)):
    return await run_segment_filter(criteria)


@router.post("/{segment_id}/refresh")
async def refresh_segment(segment_id: str, admin: dict = Depends(require_super_admin)):
    segment = await customer_segments_repository.get_by_id(segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    filters = segment.get("filters", {})
    if not filters:
        return {"status": "success", "message": "No filters to re-apply", "userIds": segment.get("userIds", [])}

    role = "customer" if segment.get("type") == "retail" else "wholesaler"
    criteria = FilterCriteria(role=role, **filters)

    users = await run_segment_filter(criteria)
    user_ids = [str(u.get("_id", u.get("id"))) for u in users]

    import datetime

    await customer_segments_repository.update(
        segment_id, {"userIds": user_ids, "lastRefreshedAt": datetime.datetime.utcnow().isoformat()}
    )

    return {"status": "success", "count": len(user_ids), "userIds": user_ids}
