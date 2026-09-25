from typing import Any
import secrets
from typing import Dict
from app.models.ad import Ad, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc

class MySQLAdDAO:
    TABLE = "sj_ads"

    def _factory(self):
        return get_async_session_factory()

    def _map_to_schema(self, row) -> Ad:
        return Ad(**self._map_to_schema_raw(row))
    def _map_to_schema_raw(self, row) -> dict:
        return {
            "_id": str(row.id),
            "id": row.id,
            "external_id": row.external_id,
            "name": row.name,
            "platform": row.platform,
            "objective": row.objective,
            "status": row.status,
            "budget_daily": row.budget_daily,
            "budget_total": row.budget_total,
            "currency": row.currency,
            "start_date": row.start_date.isoformat() if row.start_date else None,
            "end_date": row.end_date.isoformat() if row.end_date else None,
            "target_url": row.target_url,
            "headline": row.headline,
            "description": row.description,
            "image_url": row.image_url,
            "google_campaign_id": row.google_campaign_id,
            "google_ad_group_id": row.google_ad_group_id,
            "meta_campaign_id": row.meta_campaign_id,
            "meta_ad_set_id": row.meta_ad_set_id,
            "utm_source": row.utm_source,
            "utm_medium": row.utm_medium,
            "utm_campaign": row.utm_campaign,
            "google_conversion_id": row.google_conversion_id,
            "google_conversion_label": row.google_conversion_label,
            "meta_pixel_id": row.meta_pixel_id,
            "notes": row.notes,
            "stats": {
                "impressions": row.impressions,
                "clicks": row.clicks,
                "leads": row.leads,
                "purchases": row.purchases,
                "add_to_cart": row.add_to_cart,
                "conversions": row.conversions,
                "conversion_value": row.conversion_value,
                "ctr": float(row.ctr) if row.ctr else 0.0,
                "cvr": float(row.cvr) if row.cvr else 0.0,
            },
            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
            "launchedAt": row.launched_at.isoformat() if row.launched_at else None,
        }
    async def findAll(self, query: Optional[Dict] = None) -> List[Any]:
        factory = self._factory()
        if not factory:
            return []
            
        where_clauses = []
        params = {}
        if query:
            for k, v in query.items():
                if k in ("_id", "id"):
                    where_clauses.append("id = :id")
                    params["id"] = int(v) if str(v).isdigit() else None
                elif k == "status":
                    where_clauses.append("status = :status")
                    params["status"] = v
                elif k == "platform":
                    where_clauses.append("platform = :platform")
                    params["platform"] = v
                elif k == "name":
                    where_clauses.append("name = :name")
                    params["name"] = v
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        from app.models.ad import Ad
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id AS _id, external_id, name, platform, objective, status, budget_daily, budget_total, currency, start_date, end_date, target_url, headline, description, image_url, google_campaign_id, google_ad_group_id, meta_campaign_id, meta_ad_set_id, utm_source, utm_medium, utm_campaign, google_conversion_id, google_conversion_label, meta_pixel_id, notes, stat_impressions, stat_clicks, stat_leads, stat_purchases, stat_add_to_cart, stat_conversions, stat_conversion_value, stat_ctr, stat_cvr, created_at, updated_at, launched_at
                    FROM {self.TABLE}
                    WHERE {where_sql}
                    """
                ),
                params
            )
            rows = result.fetchall()
            
        return [Ad.model_validate(r._mapping) for r in rows]


    async def findOne(self, query: Dict) -> Optional[Dict]:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        return Ad.model_validate(self._map_to_schema(row)) if row else None

    async def create(self, data: Dict) -> Dict:
        factory = self._factory()
        now = now_utc()
        ext_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        vals = [":eid", ":c", ":u"]
        params = {"eid": ext_id, "c": now, "u": now}

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
        async with factory() as session:
            await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = (await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": ext_id})).scalar()
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, data: Any) -> Optional[Any]:
        existing = await self.findById(id)
        if not existing:
            return None

        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}

        if data.name is not None: updates.append("name = :name"); params["name"] = data.name
        if data.platform is not None: updates.append("platform = :platform"); params["platform"] = data.platform
        if data.objective is not None: updates.append("objective = :objective"); params["objective"] = data.objective
        if data.status is not None: updates.append("status = :status"); params["status"] = data.status
        if data.budget_daily is not None: updates.append("budget_daily = :budget_daily"); params["budget_daily"] = data.budget_daily
        if data.budget_total is not None: updates.append("budget_total = :budget_total"); params["budget_total"] = data.budget_total
        if data.currency is not None: updates.append("currency = :currency"); params["currency"] = data.currency
        if data.start_date is not None: updates.append("start_date = :start_date"); params["start_date"] = data.start_date
        if data.end_date is not None: updates.append("end_date = :end_date"); params["end_date"] = data.end_date
        if data.target_url is not None: updates.append("target_url = :target_url"); params["target_url"] = data.target_url
        if data.headline is not None: updates.append("headline = :headline"); params["headline"] = data.headline
        if data.description is not None: updates.append("description = :description"); params["description"] = data.description
        if data.image_url is not None: updates.append("image_url = :image_url"); params["image_url"] = data.image_url
        if data.google_campaign_id is not None: updates.append("google_campaign_id = :google_campaign_id"); params["google_campaign_id"] = data.google_campaign_id
        if data.google_ad_group_id is not None: updates.append("google_ad_group_id = :google_ad_group_id"); params["google_ad_group_id"] = data.google_ad_group_id
        if data.meta_campaign_id is not None: updates.append("meta_campaign_id = :meta_campaign_id"); params["meta_campaign_id"] = data.meta_campaign_id
        if data.meta_ad_set_id is not None: updates.append("meta_ad_set_id = :meta_ad_set_id"); params["meta_ad_set_id"] = data.meta_ad_set_id
        if data.utm_source is not None: updates.append("utm_source = :utm_source"); params["utm_source"] = data.utm_source
        if data.utm_medium is not None: updates.append("utm_medium = :utm_medium"); params["utm_medium"] = data.utm_medium
        if data.utm_campaign is not None: updates.append("utm_campaign = :utm_campaign"); params["utm_campaign"] = data.utm_campaign
        if data.google_conversion_id is not None: updates.append("google_conversion_id = :google_conversion_id"); params["google_conversion_id"] = data.google_conversion_id
        if data.google_conversion_label is not None: updates.append("google_conversion_label = :google_conversion_label"); params["google_conversion_label"] = data.google_conversion_label
        if data.meta_pixel_id is not None: updates.append("meta_pixel_id = :meta_pixel_id"); params["meta_pixel_id"] = data.meta_pixel_id
        if data.notes is not None: updates.append("notes = :notes"); params["notes"] = data.notes
        if data.launched_at is not None: updates.append("launched_at = :launched_at"); params["launched_at"] = data.launched_at

        # Handle flat stats
        if data.stat_impressions is not None: updates.append("stat_impressions = :st_impressions"); params["st_impressions"] = data.stat_impressions
        if data.stat_clicks is not None: updates.append("stat_clicks = :st_clicks"); params["st_clicks"] = data.stat_clicks
        if data.stat_leads is not None: updates.append("stat_leads = :st_leads"); params["st_leads"] = data.stat_leads
        if data.stat_purchases is not None: updates.append("stat_purchases = :st_purchases"); params["st_purchases"] = data.stat_purchases
        if data.stat_add_to_cart is not None: updates.append("stat_add_to_cart = :st_add_to_cart"); params["st_add_to_cart"] = data.stat_add_to_cart
        if data.stat_conversions is not None: updates.append("stat_conversions = :st_conversions"); params["st_conversions"] = data.stat_conversions
        if data.stat_conversion_value is not None: updates.append("stat_conversion_value = :st_conversion_value"); params["st_conversion_value"] = data.stat_conversion_value
        if data.stat_ctr is not None: updates.append("stat_ctr = :st_ctr"); params["st_ctr"] = data.stat_ctr
        if data.stat_cvr is not None: updates.append("stat_cvr = :st_cvr"); params["st_cvr"] = data.stat_cvr

        if len(updates) > 1:
            upd_sql = ", ".join(updates)
            SessionLocal = self._factory()
            async with SessionLocal() as session:
                await session.execute(text(f"UPDATE sj_ads SET {upd_sql} WHERE id = :id"), params)
                await session.commit()
                
        return await self.findById(id)
