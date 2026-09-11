from typing import Dict, Any, List
from app.models.schemas import MessageResponse
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.db.storage_factory import get_storage
from app.utils.auth import get_optional_user, require_super_admin
from app.utils.logger import logger

router = APIRouter(prefix="/ads", tags=["Ads"])
storage = get_storage("ads")
events_storage = get_storage("tracking")


@router.get("/summary", response_model=Dict[str, Any])
async def get_ads_summary(_: dict = Depends(require_super_admin)):
    ads = await storage.findAll({})
    total_views = sum([(ad.stats or {}).get("impressions", 0) for ad in ads])
    total_clicks = sum([(ad.stats or {}).get("clicks", 0) for ad in ads])
    active_campaigns = len([ad for ad in ads if ad.status == "active"])

    return {
        "total_ads": len(ads),
        "active": active_campaigns,
        "paused": len([ad for ad in ads if ad.status == "paused"]),
        "draft": len([ad for ad in ads if ad.status == "draft"]),
        "total_impressions": total_views,
        "total_clicks": total_clicks,
        "total_conversions": sum([(ad.stats or {}).get("conversions", 0) for ad in ads]),
        "total_spend_estimate": sum([(ad.budget_daily if ad.budget_daily is not None else 0) for ad in ads if ad.status == "active"]),
        "overall_ctr": (total_clicks / total_views * 100) if total_views > 0 else 0,
    }


@router.get("/", response_model=Dict[str, Any])
async def get_all_ads(placement: Optional[str] = None, active_only: bool = Query(False)):
    query = {}
    if active_only:
        query["status"] = "active"
    ads = await storage.findAll(query)
    return {"ads": ads}


@router.post("/", response_model=Dict[str, Any])
async def create_ad(ad_data: dict, _: dict = Depends(require_super_admin)):
    new_ad = await storage.create(ad_data)
    return new_ad


@router.put("/{ad_id}", response_model=Dict[str, Any])
async def update_ad(ad_id: str, ad_data: dict, _: dict = Depends(require_super_admin)):
    updated = await storage.update(ad_id, ad_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Ad not found")
    return updated



@router.patch("/{ad_id}/status", response_model=Dict[str, Any])
async def update_ad_status(ad_id: str, payload: dict, _: dict = Depends(require_super_admin)):
    status = payload.get("status")
    if not status:
        raise HTTPException(status_code=400, detail="Status is required")
        
    updated = await storage.update(ad_id, {"status": status})
    if not updated:
        raise HTTPException(status_code=404, detail="Ad not found")
    return {"message": f"Ad status updated to {status}"}

@router.delete("/{ad_id}", response_model=MessageResponse)
async def delete_ad(ad_id: str, _: dict = Depends(require_super_admin)):
    success = await storage.delete(ad_id)
    if not success:
        raise HTTPException(status_code=404, detail="Ad not found")
    return {"message": "Ad deleted"}


@router.post("/{ad_id}/track", response_model=Dict[str, Any])
async def track_ad_event(ad_id: str, event: dict, current_user: Optional[dict] = Depends(get_optional_user)):
    event_type = event.get("type")
    if event_type not in ["view", "click"]:
        raise HTTPException(status_code=400, detail="Invalid event type")

    ad = await storage.findById(ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    stats = (ad.stats or {})
    if event_type == "view":
        stats["impressions"] = stats.get("impressions", 0) + 1
    elif event_type == "click":
        stats["clicks"] = stats.get("clicks", 0) + 1
        impressions = stats.get("impressions", 0)
        if impressions > 0:
            stats["ctr"] = (stats["clicks"] / impressions) * 100

    await storage.update(ad_id, {"stats": stats})

    event_data = {
        "source": "ad",
        "campaign": ad_id,
        "type": event_type,
        "userId": current_user["_id"] if current_user else None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    await events_storage.create(event_data)

    return {"message": f"Ad {event_type} tracked"}
