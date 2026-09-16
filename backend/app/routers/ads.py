from app.models.user import User
from typing import Dict, Any, List, Optional
from app.models.schemas import MessageResponse, AdCreate, AdUpdate, AdStatusUpdate, AdSummaryResponse, AdStats
from app.models.ad import Ad
import uuid
from datetime import datetime
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, Query

from app.db.storage_factory import get_storage
from app.utils.auth import get_optional_user, require_super_admin
from app.utils.logger import logger

router = APIRouter(prefix="/ads", tags=["Ads"])
storage = get_storage("ads")
events_storage = get_storage("tracking")

class AdEventPayload(BaseModel):
    type: str


@router.get("/summary", response_model=AdSummaryResponse)
async def get_ads_summary(_: User = Depends(require_super_admin)):
    ads = await storage.findAll({})
    
    total_views = sum([ad.stats.impressions if ad.stats and ad.stats.impressions else 0 for ad in ads])
    total_clicks = sum([ad.stats.clicks if ad.stats and ad.stats.clicks else 0 for ad in ads])
    active_campaigns = len([ad for ad in ads if ad.status == "active"])

    return {
        "total_ads": len(ads),
        "active": active_campaigns,
        "paused": len([ad for ad in ads if ad.status == "paused"]),
        "draft": len([ad for ad in ads if ad.status == "draft"]),
        "total_impressions": total_views,
        "total_clicks": total_clicks,
        "total_conversions": sum([ad.stats.conversions if ad.stats and ad.stats.conversions else 0 for ad in ads]),
        "total_spend_estimate": sum([(ad.budget_daily if ad.budget_daily is not None else 0) for ad in ads if ad.status == "active"]),
        "overall_ctr": (total_clicks / total_views * 100) if total_views > 0 else 0,
    }


@router.get("/", response_model=List[Ad])
async def get_all_ads(placement: Optional[str] = None, active_only: bool = Query(False)):
    query = {}
    if active_only:
        query["status"] = "active"
    ads = await storage.findAll(query)
    return ads


@router.post("/", response_model=Ad)
async def create_ad(ad_data: AdCreate, _: User = Depends(require_super_admin)):
    new_ad = await storage.create(ad_data)
    return new_ad


@router.put("/{ad_id}", response_model=Ad)
async def update_ad(ad_id: str, ad_data: AdUpdate, _: User = Depends(require_super_admin)):
    updated = await storage.update(ad_id, ad_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Ad not found")
    return updated


@router.patch("/{ad_id}/status", response_model=MessageResponse)
async def update_ad_status(ad_id: str, payload: AdStatusUpdate, _: User = Depends(require_super_admin)):
    status = payload.status
    if not status:
        raise HTTPException(status_code=400, detail="Status is required")
        
    updated = await storage.update(ad_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Ad not found")
    return {"message": f"Ad status updated to {status}"}


@router.delete("/{ad_id}", response_model=MessageResponse)
async def delete_ad(ad_id: str, _: User = Depends(require_super_admin)):
    success = await storage.delete(ad_id)
    if not success:
        raise HTTPException(status_code=404, detail="Ad not found")
    return {"message": "Ad deleted"}


@router.post("/{ad_id}/track", response_model=MessageResponse)
async def track_ad_event(ad_id: str, event: AdEventPayload, current_user: Optional[User] = Depends(get_optional_user)):
    event_type = event.type
    if event_type not in ["view", "click"]:
        raise HTTPException(status_code=400, detail="Invalid event type")

    ad = await storage.findById(ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    stats = ad.stats if ad.stats else AdStats()
    if event_type == "view":
        stats.impressions = (stats.impressions if stats.impressions else 0) + 1
    elif event_type == "click":
        stats.clicks = (stats.clicks if stats.clicks else 0) + 1
        impressions = stats.impressions if stats.impressions else 0
        if impressions > 0:
            stats.ctr = (stats.clicks / impressions) * 100

    await storage.update(ad_id, AdUpdate(stats=stats))

    event_data = {
        "source": "ad",
        "campaign": ad_id,
        "type": event_type,
        "userId": current_user.id if current_user else None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    await events_storage.create(event_data)

    return {"message": f"Ad {event_type} tracked"}
