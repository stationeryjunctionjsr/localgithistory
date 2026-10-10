from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query

from app.models.user import User
from app.models.schemas import (
    MessageResponse,
    AdCreate,
    AdUpdate,
    AdStatusUpdate,
    AdSummaryResponse,
    AnalyticsEventCreate,
    AnalyticsEventPayload,
)
from app.models.ad import Ad
from app.models.base import CamelBaseModel
from app.db.storage_factory import get_storage
from app.utils.auth import get_optional_user, require_super_admin

router = APIRouter(prefix="/ads", tags=["Ads"])
storage = get_storage("ads")
events_storage = get_storage("tracking")

class AdEventPayload(CamelBaseModel):
    type: str


@router.get("/summary", response_model=AdSummaryResponse)
async def get_ads_summary(_: User = Depends(require_super_admin)) -> AdSummaryResponse:
    return await storage.getSummary()


@router.get("/", response_model=List[Ad])
async def get_all_ads(placement: Optional[str] = None, active_only: bool = Query(False)) -> List[Ad]:
    ads = await storage.findAll(status="active" if active_only else None)
    return ads


@router.post("/", response_model=Ad)
async def create_ad(ad_data: AdCreate, _: User = Depends(require_super_admin)) -> Ad:
    new_ad = await storage.create(ad_data)
    return new_ad


@router.put("/{ad_id}", response_model=Ad)
async def update_ad(ad_id: str, ad_data: AdUpdate, _: User = Depends(require_super_admin)) -> Ad:
    updated = await storage.update(ad_id, ad_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Ad not found")
    return updated


@router.patch("/{ad_id}/status", response_model=MessageResponse)
async def update_ad_status(ad_id: str, payload: AdStatusUpdate, _: User = Depends(require_super_admin)) -> MessageResponse:
    status = payload.status
    if not status:
        raise HTTPException(status_code=400, detail="Status is required")
        
    updated = await storage.update(ad_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Ad not found")
    return MessageResponse(message=f"Ad status updated to {status}")


@router.delete("/{ad_id}", response_model=MessageResponse)
async def delete_ad(ad_id: str, _: User = Depends(require_super_admin)) -> MessageResponse:
    success = await storage.delete(ad_id)
    if not success:
        raise HTTPException(status_code=404, detail="Ad not found")
    return MessageResponse(message="Ad deleted")


@router.post("/{ad_id}/track", response_model=MessageResponse)
async def track_ad_event(
    ad_id: str,
    event: AdEventPayload,
    current_user: Optional[User] = Depends(get_optional_user),
) -> MessageResponse:
    event_type = event.type
    if event_type not in ["view", "click"]:
        raise HTTPException(status_code=400, detail="Invalid event type")

    ad = await storage.findById(ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    if event_type == "view":
        new_impressions = (ad.stat_impressions or 0) + 1
        new_ctr = ((ad.stat_clicks or 0) / new_impressions * 100) if new_impressions > 0 else 0.0
        await storage.update(ad_id, AdUpdate(stat_impressions=new_impressions, stat_ctr=new_ctr))
    elif event_type == "click":
        new_clicks = (ad.stat_clicks or 0) + 1
        impressions = ad.stat_impressions or 0
        new_ctr = (new_clicks / impressions * 100) if impressions > 0 else 0.0
        await storage.update(ad_id, AdUpdate(stat_clicks=new_clicks, stat_ctr=new_ctr))

    event_payload = AnalyticsEventCreate(
        source="ad",
        type=event_type,
        user_id=current_user.id if current_user else None,
        filter_name="campaign",
        filter_value=ad_id,
        payload=AnalyticsEventPayload(source="ad"),
    )
    await events_storage.create(event_payload)

    return MessageResponse(message=f"Ad {event_type} tracked")
