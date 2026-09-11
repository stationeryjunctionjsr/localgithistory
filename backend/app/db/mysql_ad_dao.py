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

    def _row_to_dict(self, row) -> Dict:
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

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        query = query or {}
        where_clauses = []
        params = {}
        if "status" in query:
            where_clauses.append("status = :status")
            params["status"] = query["status"]
        if "platform" in query:
            where_clauses.append("platform = :platform")
            params["platform"] = query["platform"]

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        factory = self._factory()
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"),
                    params,
                )
            ).fetchall()
        return [Ad.model_validate(self._row_to_dict(r) ) for r in rows]

    async def findOne(self, query: Dict) -> Optional[Dict]:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "id" in query:
            return await self.findById(query["id"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else 0
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": pid},
                )
            ).fetchone()
        return Ad.model_validate(self._row_to_dict(row)) if row else None

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
            if api_k in data:
                cols.append(db_k)
                vals.append(f":{api_k}")
                params[api_k] = data[api_k]
        
        stats = data.get("stats") or {}
        stats_map = {
            "impressions": "impressions", "clicks": "clicks", "leads": "leads", "purchases": "purchases",
            "add_to_cart": "add_to_cart", "conversions": "conversions", "conversion_value": "conversion_value",
            "ctr": "ctr", "cvr": "cvr"
        }
        for api_k, db_k in stats_map.items():
            if api_k in stats:
                cols.append(db_k)
                vals.append(f":s_{api_k}")
                params[f"s_{api_k}"] = stats[api_k]

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

    async def update(self, id: str, data: Dict) -> Optional[Dict]:
        existing = await self.findById(id)
        if not existing:
            return None
        
        merged = {**existing, **data}
        if "stats" in data:
            merged["stats"] = {**(existing.stats or {}), **data["stats"]}

        now = now_utc()
        pid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :u"]
        params = {"id": pid, "u": now}

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
            if api_k in merged:
                updates.append(f"{db_k} = :{api_k}")
                params[api_k] = merged[api_k]

        stats_map = {
            "impressions": "impressions", "clicks": "clicks", "leads": "leads", "purchases": "purchases",
            "add_to_cart": "add_to_cart", "conversions": "conversions", "conversion_value": "conversion_value",
            "ctr": "ctr", "cvr": "cvr"
        }
        stats = merged.get("stats", {})
        for api_k, db_k in stats_map.items():
            if api_k in stats:
                updates.append(f"{db_k} = :s_{api_k}")
                params[f"s_{api_k}"] = stats[api_k]

        set_sql = ", ".join(updates)
        factory = self._factory()
        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pid},
            )
            await session.commit()
            return res.rowcount > 0
