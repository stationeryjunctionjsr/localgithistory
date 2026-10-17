from typing import List, Optional
from app.models.ad import Ad
from app.models.schemas import AdCreate, AdUpdate, AdSummaryResponse

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc

class MySQLAdDAO:
    TABLE = "sj_ads"

    def _map_to_schema(self, row) -> Ad:
        return Ad.model_validate(row)

    async def getSummary(self) -> AdSummaryResponse:
        async_session = get_async_session_factory()
        if not async_session:
            return AdSummaryResponse()
        async with async_session() as session:
            sql = f"""
                SELECT
                    COUNT(*) as total_ads,
                    COALESCE(SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END), 0) as active_count,
                    COALESCE(SUM(CASE WHEN status = 'paused' THEN 1 ELSE 0 END), 0) as paused_count,
                    COALESCE(SUM(CASE WHEN status = 'draft' THEN 1 ELSE 0 END), 0) as draft_count,
                    COALESCE(SUM(stat_impressions), 0) as total_impressions,
                    COALESCE(SUM(stat_clicks), 0) as total_clicks,
                    COALESCE(SUM(stat_conversions), 0) as total_conversions,
                    COALESCE(SUM(CASE WHEN status = 'active' THEN COALESCE(budget_daily, 0) ELSE 0 END), 0) as total_spend_estimate
                FROM {self.TABLE}
            """
            res = await session.execute(text(sql))
            row = res.fetchone()
            if not row:
                return AdSummaryResponse()

            total_clicks = int(row.total_clicks)
            total_impressions = int(row.total_impressions)
            overall_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0.0

            return AdSummaryResponse(
                total_ads=int(row.total_ads),
                active=int(row.active_count),
                paused=int(row.paused_count),
                draft=int(row.draft_count),
                total_impressions=total_impressions,
                total_clicks=total_clicks,
                total_conversions=int(row.total_conversions),
                total_spend_estimate=float(row.total_spend_estimate),
                total_views=total_impressions,
                active_campaigns=int(row.active_count),
                overall_ctr=overall_ctr,
                ctr=overall_ctr,
            )

    async def findAll(
        self,
        status: Optional[str] = None,
        platform: Optional[str] = None,
        name: Optional[str] = None,
        id: Optional[int] = None,
    ) -> List[Ad]:
        async_session = get_async_session_factory()
        if not async_session:
            return []
            
        where_clauses = []
        params = {}
        if id is not None:
            where_clauses.append("id = :id")
            params["id"] = id
        if status is not None:
            where_clauses.append("status = :status")
            params["status"] = status
        if platform is not None:
            where_clauses.append("platform = :platform")
            params["platform"] = platform
        if name is not None:
            where_clauses.append("name = :name")
            params["name"] = name
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        async with async_session() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id AS _id, name, platform, objective, status, budget_daily, budget_total, currency, start_date, end_date, target_url, headline, description, image_url, google_campaign_id, google_ad_group_id, meta_campaign_id, meta_ad_set_id, utm_source, utm_medium, utm_campaign, google_conversion_id, google_conversion_label, meta_pixel_id, notes, stat_impressions, stat_clicks, stat_leads, stat_purchases, stat_add_to_cart, stat_conversions, stat_conversion_value, stat_ctr, stat_cvr, created_at, updated_at, launched_at
                    FROM {self.TABLE}
                    WHERE {where_sql}
                    """
                ),
                params
            )
            rows = result.fetchall()
            
        return [Ad.model_validate(r) for r in rows]

    async def findOne(
        self,
        id: Optional[int] = None,
        name: Optional[str] = None,
        status: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> Optional[Ad]:
        if id is not None:
            return await self.findById(id)
        records = await self.findAll(status=status, platform=platform, name=name)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[Ad]:
        async_session = get_async_session_factory()
        if not async_session or not id:
            return None
        async with async_session() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": id},
                )
            ).fetchone()
        return self._map_to_schema(row) if row else None

    async def create(self, data: AdCreate) -> Ad:
        async_session = get_async_session_factory()
        if not async_session:
            raise RuntimeError("Database not available")
        now = now_utc()
        
        cols = ["created_at", "updated_at"]
        vals = [":c", ":u"]
        params = {"c": now, "u": now}

        scalar_map = {
            "name": "name", "platform": "platform", "objective": "objective", "status": "status",
            "budget_daily": "budget_daily", "budget_total": "budget_total", "currency": "currency",
            "start_date": "start_date", "end_date": "end_date", "target_url": "target_url",
            "headline": "headline", "description": "description", "image_url": "image_url",
            "google_campaign_id": "google_campaign_id", "google_ad_group_id": "google_ad_group_id",
            "meta_campaign_id": "meta_campaign_id", "meta_ad_set_id": "meta_ad_set_id",
            "utm_source": "utm_source", "utm_medium": "utm_medium", "utm_campaign": "utm_campaign",
            "google_conversion_id": "google_conversion_id", "google_conversion_label": "google_conversion_label",
            "meta_pixel_id": "meta_pixel_id", "notes": "notes", "launched_at": "launched_at"
        }
        for api_k, db_k in scalar_map.items():
            val = None
            match api_k:
                case "name": val = data.name if data.name is not None else None
                case "platform": val = data.platform if data.platform is not None else None
                case "objective": val = data.objective if data.objective is not None else None
                case "status": val = data.status if data.status is not None else None
                case "budget_daily": val = data.budget_daily if data.budget_daily is not None else None
                case "budget_total": val = data.budget_total if data.budget_total is not None else None
                case "currency": val = data.currency if data.currency is not None else None
                case "start_date": val = data.start_date if data.start_date is not None else None
                case "end_date": val = data.end_date if data.end_date is not None else None
                case "target_url": val = data.target_url if data.target_url is not None else None
                case "headline": val = data.headline if data.headline is not None else None
                case "description": val = data.description if data.description is not None else None
                case "image_url": val = data.image_url if data.image_url is not None else None
                case "google_campaign_id": val = data.google_campaign_id if data.google_campaign_id is not None else None
                case "google_ad_group_id": val = data.google_ad_group_id if data.google_ad_group_id is not None else None
                case "meta_campaign_id": val = data.meta_campaign_id if data.meta_campaign_id is not None else None
                case "meta_ad_set_id": val = data.meta_ad_set_id if data.meta_ad_set_id is not None else None
                case "utm_source": val = data.utm_source if data.utm_source is not None else None
                case "utm_medium": val = data.utm_medium if data.utm_medium is not None else None
                case "utm_campaign": val = data.utm_campaign if data.utm_campaign is not None else None
                case "google_conversion_id": val = data.google_conversion_id if data.google_conversion_id is not None else None
                case "google_conversion_label": val = data.google_conversion_label if data.google_conversion_label is not None else None
                case "meta_pixel_id": val = data.meta_pixel_id if data.meta_pixel_id is not None else None
                case "notes": val = data.notes if data.notes is not None else None
                case "launched_at": val = data.launched_at if data.launched_at is not None else None
            if val is not None:
                cols.append(db_k)
                vals.append(f":{api_k}")
                params[api_k] = val
        
        # Handle flat stats
        if data.stat_impressions is not None: cols.append("stat_impressions"); vals.append(":st_impressions"); params["st_impressions"] = data.stat_impressions
        if data.stat_clicks is not None: cols.append("stat_clicks"); vals.append(":st_clicks"); params["st_clicks"] = data.stat_clicks
        if data.stat_leads is not None: cols.append("stat_leads"); vals.append(":st_leads"); params["st_leads"] = data.stat_leads
        if data.stat_purchases is not None: cols.append("stat_purchases"); vals.append(":st_purchases"); params["st_purchases"] = data.stat_purchases
        if data.stat_add_to_cart is not None: cols.append("stat_add_to_cart"); vals.append(":st_add_to_cart"); params["st_add_to_cart"] = data.stat_add_to_cart
        if data.stat_conversions is not None: cols.append("stat_conversions"); vals.append(":st_conversions"); params["st_conversions"] = data.stat_conversions
        if data.stat_conversion_value is not None: cols.append("stat_conversion_value"); vals.append(":st_conversion_value"); params["st_conversion_value"] = data.stat_conversion_value
        if data.stat_ctr is not None: cols.append("stat_ctr"); vals.append(":st_ctr"); params["st_ctr"] = data.stat_ctr
        if data.stat_cvr is not None: cols.append("stat_cvr"); vals.append(":st_cvr"); params["st_cvr"] = data.stat_cvr

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        async with async_session() as session:
            result = await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = result.lastrowid
            await session.commit()
        return await self.findById(new_id)

    async def update(self, id: int, update_data: AdUpdate) -> Optional[Ad]:
        if not id:
            return None
        async_session = get_async_session_factory()
        if not async_session:
            return None

        now = now_utc()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now}

        if "name" in update_data.model_fields_set: updates.append("name = :name"); params["name"] = update_data.name
        if "platform" in update_data.model_fields_set: updates.append("platform = :platform"); params["platform"] = update_data.platform
        if "objective" in update_data.model_fields_set: updates.append("objective = :objective"); params["objective"] = update_data.objective
        if "status" in update_data.model_fields_set: updates.append("status = :status"); params["status"] = update_data.status
        if "budget_daily" in update_data.model_fields_set: updates.append("budget_daily = :budget_daily"); params["budget_daily"] = update_data.budget_daily
        if "budget_total" in update_data.model_fields_set: updates.append("budget_total = :budget_total"); params["budget_total"] = update_data.budget_total
        if "currency" in update_data.model_fields_set: updates.append("currency = :currency"); params["currency"] = update_data.currency
        if "start_date" in update_data.model_fields_set: updates.append("start_date = :start_date"); params["start_date"] = update_data.start_date
        if "end_date" in update_data.model_fields_set: updates.append("end_date = :end_date"); params["end_date"] = update_data.end_date
        if "target_url" in update_data.model_fields_set: updates.append("target_url = :target_url"); params["target_url"] = update_data.target_url
        if "headline" in update_data.model_fields_set: updates.append("headline = :headline"); params["headline"] = update_data.headline
        if "description" in update_data.model_fields_set: updates.append("description = :description"); params["description"] = update_data.description
        if "image_url" in update_data.model_fields_set: updates.append("image_url = :image_url"); params["image_url"] = update_data.image_url
        if "google_campaign_id" in update_data.model_fields_set: updates.append("google_campaign_id = :google_campaign_id"); params["google_campaign_id"] = update_data.google_campaign_id
        if "google_ad_group_id" in update_data.model_fields_set: updates.append("google_ad_group_id = :google_ad_group_id"); params["google_ad_group_id"] = update_data.google_ad_group_id
        if "meta_campaign_id" in update_data.model_fields_set: updates.append("meta_campaign_id = :meta_campaign_id"); params["meta_campaign_id"] = update_data.meta_campaign_id
        if "meta_ad_set_id" in update_data.model_fields_set: updates.append("meta_ad_set_id = :meta_ad_set_id"); params["meta_ad_set_id"] = update_data.meta_ad_set_id
        if "utm_source" in update_data.model_fields_set: updates.append("utm_source = :utm_source"); params["utm_source"] = update_data.utm_source
        if "utm_medium" in update_data.model_fields_set: updates.append("utm_medium = :utm_medium"); params["utm_medium"] = update_data.utm_medium
        if "utm_campaign" in update_data.model_fields_set: updates.append("utm_campaign = :utm_campaign"); params["utm_campaign"] = update_data.utm_campaign
        if "google_conversion_id" in update_data.model_fields_set: updates.append("google_conversion_id = :google_conversion_id"); params["google_conversion_id"] = update_data.google_conversion_id
        if "google_conversion_label" in update_data.model_fields_set: updates.append("google_conversion_label = :google_conversion_label"); params["google_conversion_label"] = update_data.google_conversion_label
        if "meta_pixel_id" in update_data.model_fields_set: updates.append("meta_pixel_id = :meta_pixel_id"); params["meta_pixel_id"] = update_data.meta_pixel_id
        if "notes" in update_data.model_fields_set: updates.append("notes = :notes"); params["notes"] = update_data.notes
        if "launched_at" in update_data.model_fields_set: updates.append("launched_at = :launched_at"); params["launched_at"] = update_data.launched_at

        # Stats
        if "stat_impressions" in update_data.model_fields_set: updates.append("stat_impressions = :st_impressions"); params["st_impressions"] = update_data.stat_impressions
        if "stat_clicks" in update_data.model_fields_set: updates.append("stat_clicks = :st_clicks"); params["st_clicks"] = update_data.stat_clicks
        if "stat_leads" in update_data.model_fields_set: updates.append("stat_leads = :st_leads"); params["st_leads"] = update_data.stat_leads
        if "stat_purchases" in update_data.model_fields_set: updates.append("stat_purchases = :st_purchases"); params["st_purchases"] = update_data.stat_purchases
        if "stat_add_to_cart" in update_data.model_fields_set: updates.append("stat_add_to_cart = :st_add_to_cart"); params["st_add_to_cart"] = update_data.stat_add_to_cart
        if "stat_conversions" in update_data.model_fields_set: updates.append("stat_conversions = :st_conversions"); params["st_conversions"] = update_data.stat_conversions
        if "stat_conversion_value" in update_data.model_fields_set: updates.append("stat_conversion_value = :st_conversion_value"); params["st_conversion_value"] = update_data.stat_conversion_value
        if "stat_ctr" in update_data.model_fields_set: updates.append("stat_ctr = :st_ctr"); params["st_ctr"] = update_data.stat_ctr
        if "stat_cvr" in update_data.model_fields_set: updates.append("stat_cvr = :st_cvr"); params["st_cvr"] = update_data.stat_cvr

        upd_sql = ", ".join(updates)
        async with async_session() as session:
            result = await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE id = :id"), params)
            await session.commit()
            if result.rowcount == 0:
                existing = await self.findById(id)
                if not existing:
                    return None
                
        return await self.findById(id)

    async def delete(self, id: int) -> bool:
        async_session = get_async_session_factory()
        if not async_session or not id:
            return False
        async with async_session() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": id},
            )
            await session.commit()
            return result.rowcount > 0


