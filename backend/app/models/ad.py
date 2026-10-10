from datetime import datetime
from typing import Optional
from pydantic import Field
from app.models.schemas import AdStats
from app.models.base import CamelBaseModel

class Ad(CamelBaseModel):
    id: Optional[str] = None
    external_id: Optional[str] = None
    name: Optional[str] = None
    platform: Optional[str] = None
    objective: Optional[str] = None
    status: Optional[str] = None
    budget_daily: Optional[float] = None
    budget_total: Optional[float] = None
    currency: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
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
    notes: Optional[str] = None
    stat_impressions: Optional[int] = 0
    stat_clicks: Optional[int] = 0
    stat_leads: Optional[int] = 0
    stat_purchases: Optional[int] = 0
    stat_add_to_cart: Optional[int] = 0
    stat_conversions: Optional[int] = 0
    stat_conversion_value: Optional[float] = 0.0
    stat_ctr: Optional[float] = 0.0
    stat_cvr: Optional[float] = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    launched_at: Optional[datetime] = None

    @property
    def stats(self) -> AdStats:
        return AdStats(
            impressions=self.stat_impressions or 0,
            clicks=self.stat_clicks or 0,
            leads=self.stat_leads or 0,
            purchases=self.stat_purchases or 0,
            add_to_cart=self.stat_add_to_cart or 0,
            conversions=self.stat_conversions or 0,
            conversion_value=self.stat_conversion_value or 0.0,
            ctr=self.stat_ctr or 0.0,
            cvr=self.stat_cvr or 0.0,
        )
