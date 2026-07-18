"""
Ad Campaign router — manages Google Ads & Meta (Facebook/Instagram) campaigns.
Stores campaign metadata, launch/pause/stop status, and records engagement/
conversion events fired by front-end pixels.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.utils.auth import get_optional_user, require_super_admin
# File-based ad storage is disabled — Oracle is the only supported backend.
# from app.utils.file_storage import DATA_DIR, ensure_data_dir

router = APIRouter()

# ADS_FILE = DATA_DIR / "ads.json"
# AD_EVENTS_FILE = DATA_DIR / "ad_events.json"


# ── helpers ──────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# File-based helpers are disabled — Oracle is the only supported backend.
# def _load(path: Path) -> List[Dict]:
#     ensure_data_dir()
#     if not path.exists():
#         path.write_text("[]", encoding="utf-8")
#     try:
#         return json.loads(path.read_text(encoding="utf-8")) or []
#     except Exception:
#         return []
#
# def _save(path: Path, data: List[Dict]) -> None:
#     ensure_data_dir()
#     path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def _find_ad(ads: List[Dict], ad_id: str) -> Optional[Dict]:
    return next((a for a in ads if a["id"] == ad_id), None)


# ── Pydantic models ──────────────────────────────────────────────────────────

class AdCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    platform: str = Field(..., pattern="^(google|meta|both|social|email|qr|whatsapp)$")
    objective: str = Field(
        "traffic",
        pattern="^(awareness|traffic|engagement|leads|conversions|catalog_sales|app_installs)$",
    )
    budget_daily: float = Field(0.0, ge=0)
    budget_total: float = Field(0.0, ge=0)
    currency: str = Field("INR", max_length=3)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    target_url: Optional[str] = None
    headline: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    # Platform-specific IDs (filled after launching in ad platform)
    google_campaign_id: Optional[str] = None
    google_ad_group_id: Optional[str] = None
    meta_campaign_id: Optional[str] = None
    meta_ad_set_id: Optional[str] = None
    # UTM params auto-generated if empty
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    # Pixel / conversion tracking
    google_conversion_id: Optional[str] = None
    google_conversion_label: Optional[str] = None
    meta_pixel_id: Optional[str] = None
    # Audience targeting
    target_audience: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class AdUpdate(BaseModel):
    name: Optional[str] = None
    platform: Optional[str] = Field(None, pattern="^(google|meta|both|social|email|qr|whatsapp)$")
    objective: Optional[str] = None
    budget_daily: Optional[float] = None
    budget_total: Optional[float] = None
    currency: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    target_url: Optional[str] = None
    headline: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    google_campaign_id: Optional[str] = None
    google_ad_group_id: Optional[str] = None
    meta_campaign_id: Optional[str] = None
    meta_ad_set_id: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    google_conversion_id: Optional[str] = None
    google_conversion_label: Optional[str] = None
    meta_pixel_id: Optional[str] = None
    target_audience: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class AdStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(draft|active|paused|completed|archived)$")


class AdEventRecord(BaseModel):
    ad_id: str
    event_type: str  # impression | click | lead | purchase | add_to_cart | page_view
    platform: str  # google | meta | organic
    value: float = 0.0
    currency: str = "INR"
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# ── Internal helper ───────────────────────────────────────────────────────────

def _compute_stats(ad_events: List[Dict]) -> Dict:
    impressions = sum(1 for e in ad_events if e.get("event_type") == "impression")
    clicks = sum(1 for e in ad_events if e.get("event_type") == "click")
    leads = sum(1 for e in ad_events if e.get("event_type") == "lead")
    purchases = sum(1 for e in ad_events if e.get("event_type") == "purchase")
    add_to_cart = sum(1 for e in ad_events if e.get("event_type") == "add_to_cart")
    conversion_value = sum(e.get("value", 0) for e in ad_events if e.get("event_type") == "purchase")
    ctr = round(clicks / impressions * 100, 2) if impressions else 0
    cvr = round((purchases + leads) / clicks * 100, 2) if clicks else 0
    return {
        "impressions": impressions,
        "clicks": clicks,
        "leads": leads,
        "purchases": purchases,
        "add_to_cart": add_to_cart,
        "conversions": purchases + leads,
        "conversion_value": conversion_value,
        "ctr": ctr,
        "cvr": cvr,
    }


# ── Admin CRUD ───────────────────────────────────────────────────────────────

@router.get("/summary")
async def get_ads_summary(_: dict = Depends(require_super_admin)):
    # File-based ad storage disabled. TODO: implement Oracle-backed ad storage.
    raise HTTPException(status_code=501, detail="Ad storage not yet implemented in Oracle. JSON file storage has been disabled.")
    # ads = _load(ADS_FILE)
    # events = _load(AD_EVENTS_FILE)
    # summary = {
    #     "total_ads": len(ads),
    #     "active": sum(1 for a in ads if a.get("status") == "active"),
    #     "paused": sum(1 for a in ads if a.get("status") == "paused"),
    #     "draft": sum(1 for a in ads if a.get("status") == "draft"),
    #     "total_impressions": sum(1 for e in events if e.get("event_type") == "impression"),
    #     "total_clicks": sum(1 for e in events if e.get("event_type") == "click"),
    #     "total_conversions": sum(
    #         1 for e in events if e.get("event_type") in ("purchase", "lead")
    #     ),
    #     "total_spend_estimate": sum(a.get("budget_daily", 0) for a in ads if a.get("status") == "active"),
    # }
    # total_impressions = summary["total_impressions"]
    # total_clicks = summary["total_clicks"]
    # summary["overall_ctr"] = round(total_clicks / total_impressions * 100, 2) if total_impressions else 0
    # return summary


@router.get("")
@router.get("/")
async def list_ads(
    platform: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    _: dict = Depends(require_super_admin),
):
    # File-based ad storage disabled. TODO: implement Oracle-backed ad storage.
    raise HTTPException(status_code=501, detail="Ad storage not yet implemented in Oracle. JSON file storage has been disabled.")
    # ads = _load(ADS_FILE)
    # if platform:
    #     ads = [a for a in ads if a.get("platform") == platform or a.get("platform") == "both"]
    # if status:
    #     ads = [a for a in ads if a.get("status") == status]
    # # Attach live stats
    # events = _load(AD_EVENTS_FILE)
    # for ad in ads:
    #     ad_events = [e for e in events if e.get("ad_id") == ad["id"]]
    #     ad["stats"] = _compute_stats(ad_events)
    # return {"ads": ads, "total": len(ads)}


@router.post("", status_code=201)

@router.post("/", status_code=201)
async def create_ad(payload: AdCreate, _: dict = Depends(require_super_admin)):
    # File-based ad storage disabled. TODO: implement Oracle-backed ad storage.
    raise HTTPException(status_code=501, detail="Ad storage not yet implemented in Oracle. JSON file storage has been disabled.")
    # ads = _load(ADS_FILE)
    # ad_id = str(uuid.uuid4())
    # now = _now()
    # ... (original ad creation logic)
    # _save(ADS_FILE, ads)
    # return ad


@router.get("/{ad_id}")
async def get_ad(ad_id: str, _: dict = Depends(require_super_admin)):
    # File-based ad storage disabled. TODO: implement Oracle-backed ad storage.
    raise HTTPException(status_code=501, detail="Ad storage not yet implemented in Oracle. JSON file storage has been disabled.")
    # ads = _load(ADS_FILE)
    # ad = _find_ad(ads, ad_id)
    # if not ad:
    #     raise HTTPException(status_code=404, detail="Ad not found")
    # events = _load(AD_EVENTS_FILE)
    # ad_events = [e for e in events if e.get("ad_id") == ad_id]
    # ad["stats"] = _compute_stats(ad_events)
    # ad["events"] = ad_events[-100:]
    # return ad


@router.put("/{ad_id}")
async def update_ad(ad_id: str, payload: AdUpdate, _: dict = Depends(require_super_admin)):
    # File-based ad storage disabled. TODO: implement Oracle-backed ad storage.
    raise HTTPException(status_code=501, detail="Ad storage not yet implemented in Oracle. JSON file storage has been disabled.")
    # ads = _load(ADS_FILE)
    # ad = _find_ad(ads, ad_id)
    # if not ad:
    #     raise HTTPException(status_code=404, detail="Ad not found")
    # updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    # ad.update(updates)
    # ad["updated_at"] = _now()
    # _save(ADS_FILE, ads)
    # return ad


@router.patch("/{ad_id}/status")
async def update_ad_status(ad_id: str, payload: AdStatusUpdate, _: dict = Depends(require_super_admin)):
    # File-based ad storage disabled. TODO: implement Oracle-backed ad storage.
    raise HTTPException(status_code=501, detail="Ad storage not yet implemented in Oracle. JSON file storage has been disabled.")
    # ads = _load(ADS_FILE)
    # ad = _find_ad(ads, ad_id)
    # if not ad:
    #     raise HTTPException(status_code=404, detail="Ad not found")
    # old_status = ad.get("status")
    # ad["status"] = payload.status
    # ad["updated_at"] = _now()
    # if payload.status == "active" and old_status != "active":
    #     ad["launched_at"] = _now()
    # if payload.status == "paused":
    #     ad["paused_at"] = _now()
    # _save(ADS_FILE, ads)
    # return ad


@router.delete("/{ad_id}", status_code=204)
async def delete_ad(ad_id: str, _: dict = Depends(require_super_admin)):
    # File-based ad storage disabled. TODO: implement Oracle-backed ad storage.
    raise HTTPException(status_code=501, detail="Ad storage not yet implemented in Oracle. JSON file storage has been disabled.")
    # ads = _load(ADS_FILE)
    # new_ads = [a for a in ads if a["id"] != ad_id]
    # if len(new_ads) == len(ads):
    #     raise HTTPException(status_code=404, detail="Ad not found")
    # _save(ADS_FILE, new_ads)
    # return None


# ── Engagement / Conversion events ──────────────────────────────────────────

@router.post("/events/record")
async def record_ad_event(
    payload: AdEventRecord,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """Record an ad engagement/conversion event fired by front-end tracking pixels."""
    # File-based ad event storage disabled. TODO: implement Oracle-backed ad storage.
    raise HTTPException(status_code=501, detail="Ad event storage not yet implemented in Oracle. JSON file storage has been disabled.")
    # events = _load(AD_EVENTS_FILE)
    # event = {
    #     "id": str(uuid.uuid4()),
    #     "ad_id": payload.ad_id,
    #     "event_type": payload.event_type,
    #     "platform": payload.platform,
    #     "value": payload.value,
    #     "currency": payload.currency,
    #     "session_id": payload.session_id,
    #     "user_id": payload.user_id or (current_user.get("_id") if current_user else None),
    #     "metadata": payload.metadata or {},
    #     "recorded_at": _now(),
    # }
    # events.append(event)
    # if len(events) > 10_000:
    #     events = events[-10_000:]
    # _save(AD_EVENTS_FILE, events)
    # return {"ok": True}


@router.get("/{ad_id}/stats")
async def get_ad_stats(ad_id: str, _: dict = Depends(require_super_admin)):
    # File-based ad event storage disabled. TODO: implement Oracle-backed ad storage.
    raise HTTPException(status_code=501, detail="Ad storage not yet implemented in Oracle. JSON file storage has been disabled.")
    # events = _load(AD_EVENTS_FILE)
    # ad_events = [e for e in events if e.get("ad_id") == ad_id]
    # return _compute_stats(ad_events)
