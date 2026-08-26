import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.utils.auth import require_super_admin, get_optional_user
from app.db.storage_factory import get_storage
from app.utils.logger import logger

router = APIRouter(prefix="/ads", tags=["Ads"])
storage = get_storage("ads")
events_storage = get_storage("adEvents")

@router.get("/summary")
async def get_ads_summary(_: dict = Depends(require_super_admin)):
    ads = await storage.findAll({})
    total_views = 0
    total_clicks = 0
    active_campaigns = 0
    for ad in ads:
        total_views += ad.get("views", 0)
        total_clicks += ad.get("clicks", 0)
        if ad.get("isActive", True):
            active_campaigns += 1
    return {
        "activeCampaigns": active_campaigns,
        "totalViews": total_views,
        "totalClicks": total_clicks,
        "conversionRate": round((total_clicks / total_views * 100) if total_views > 0 else 0, 2)
    }

@router.get("/")
async def get_all_ads(
    placement: Optional[str] = None,
    active_only: bool = Query(False)
):
    query = {}
    if placement:
        query["placement"] = placement
    if active_only:
        query["isActive"] = True
    ads = await storage.findAll(query)
    # Sort by displayOrder
    ads.sort(key=lambda x: x.get("displayOrder", 999))
    return ads

@router.post("/")
async def create_ad(ad_data: dict, _: dict = Depends(require_super_admin)):
    ad_data["views"] = 0
    ad_data["clicks"] = 0
    ad_data["createdAt"] = datetime.utcnow().isoformat() + "Z"
    ad_data["updatedAt"] = ad_data["createdAt"]
    if "displayOrder" not in ad_data:
        ad_data["displayOrder"] = 0
    created = await storage.create(ad_data)
    return created

@router.put("/{ad_id}")
async def update_ad(ad_id: str, ad_data: dict, _: dict = Depends(require_super_admin)):
    ad_data["updatedAt"] = datetime.utcnow().isoformat() + "Z"
    updated = await storage.update(ad_id, ad_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Ad not found")
    return updated

@router.delete("/{ad_id}")
async def delete_ad(ad_id: str, _: dict = Depends(require_super_admin)):
    deleted = await storage.delete(ad_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Ad not found")
    return {"message": "Ad deleted successfully"}

@router.post("/{ad_id}/track")
async def track_ad_event(
    ad_id: str,
    event: dict,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    event_type = event.get("type")
    if event_type not in ["view", "click"]:
        raise HTTPException(status_code=400, detail="Invalid event type")
    
    ad = await storage.findById(ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
        
    updated = await storage.update(ad_id, {
        event_type + "s": ad.get(event_type + "s", 0) + 1
    })
    
    # Log event
    event_data = {
        "adId": ad_id,
        "type": event_type,
        "userId": current_user["_id"] if current_user else None,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    await events_storage.create(event_data)
    return {"message": f"Ad {event_type} tracked"}
