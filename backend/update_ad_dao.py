import os
import re

filepath = 'app/db/mysql_ad_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# Remove _map_to_schema
text = re.sub(r'\s*def _map_to_schema\(self, r\).*?(?=\s*async def findAll)', '', text, flags=re.DOTALL)

# Update findAll
find_all_new = '''    async def findAll(self, query: Optional[Dict] = None) -> List[Any]:
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
            
        return [Ad.model_validate(r._mapping) for r in rows]'''
text = re.sub(r'\s*async def findAll\(self, query: Optional\[Dict\] = None\) -> List\[Dict\]:.*?(?=\s*async def findOne)', '\n' + find_all_new + '\n', text, flags=re.DOTALL)

# Update findById
find_by_id_new = '''    async def findById(self, id: str) -> Optional[Any]:
        factory = self._factory()
        if not factory:
            return None
        aid = int(id) if str(id).isdigit() else None
        from app.models.ad import Ad
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id AS _id, external_id, name, platform, objective, status, budget_daily, budget_total, currency, start_date, end_date, target_url, headline, description, image_url, google_campaign_id, google_ad_group_id, meta_campaign_id, meta_ad_set_id, utm_source, utm_medium, utm_campaign, google_conversion_id, google_conversion_label, meta_pixel_id, notes, stat_impressions, stat_clicks, stat_leads, stat_purchases, stat_add_to_cart, stat_conversions, stat_conversion_value, stat_ctr, stat_cvr, created_at, updated_at, launched_at
                    FROM {self.TABLE} WHERE id = :id
                    """
                ),
                {"id": aid},
            )
            row = result.fetchone()
        return Ad.model_validate(row._mapping) if row else None'''
text = re.sub(r'\s*async def findById\(self, id: str\) -> Optional\[Any\]:.*?(?=\s*async def create)', '\n' + find_by_id_new + '\n', text, flags=re.DOTALL)

# Update create stats block
create_stats_old = '''        stats = data.stats
        stats_map = {
            "impressions": "impressions", "clicks": "clicks", "leads": "leads", "purchases": "purchases",
            "add_to_cart": "add_to_cart", "conversions": "conversions", "conversion_value": "conversion_value",
            "ctr": "ctr", "cvr": "cvr"
        }
        if stats:
            for api_k, db_k in stats_map.items():
                val = None
                match api_k:
                    case "impressions": val = stats.impressions if stats.impressions is not None else None
                    case "clicks": val = stats.clicks if stats.clicks is not None else None
                    case "leads": val = stats.leads if stats.leads is not None else None
                    case "purchases": val = stats.purchases if stats.purchases is not None else None
                    case "add_to_cart": val = stats.add_to_cart if stats.add_to_cart is not None else None
                    case "conversions": val = stats.conversions if stats.conversions is not None else None
                    case "conversion_value": val = stats.conversion_value if stats.conversion_value is not None else None
                    case "ctr": val = stats.ctr if stats.ctr is not None else None
                    case "cvr": val = stats.cvr if stats.cvr is not None else None
                if val is not None:
                    cols.append(db_k)
                    vals.append(f":s_{api_k}")
                    params[f"s_{api_k}"] = val'''

create_stats_new = '''        # Handle flat stats
        stats_map = {
            "stat_impressions": "stat_impressions", "stat_clicks": "stat_clicks", "stat_leads": "stat_leads", "stat_purchases": "stat_purchases",
            "stat_add_to_cart": "stat_add_to_cart", "stat_conversions": "stat_conversions", "stat_conversion_value": "stat_conversion_value",
            "stat_ctr": "stat_ctr", "stat_cvr": "stat_cvr"
        }
        for api_k, db_k in stats_map.items():
            val = getattr(data, api_k, None) # Wait, getattr is banned? Let's use direct access if it's a Pydantic model
            # Actually, since data is AdCreate, we can access it directly
            pass
        
        if getattr(data, "stat_impressions", None) is not None: cols.append("stat_impressions"); vals.append(":st_impressions"); params["st_impressions"] = data.stat_impressions
        if getattr(data, "stat_clicks", None) is not None: cols.append("stat_clicks"); vals.append(":st_clicks"); params["st_clicks"] = data.stat_clicks
        if getattr(data, "stat_leads", None) is not None: cols.append("stat_leads"); vals.append(":st_leads"); params["st_leads"] = data.stat_leads
        if getattr(data, "stat_purchases", None) is not None: cols.append("stat_purchases"); vals.append(":st_purchases"); params["st_purchases"] = data.stat_purchases
        if getattr(data, "stat_add_to_cart", None) is not None: cols.append("stat_add_to_cart"); vals.append(":st_add_to_cart"); params["st_add_to_cart"] = data.stat_add_to_cart
        if getattr(data, "stat_conversions", None) is not None: cols.append("stat_conversions"); vals.append(":st_conversions"); params["st_conversions"] = data.stat_conversions
        if getattr(data, "stat_conversion_value", None) is not None: cols.append("stat_conversion_value"); vals.append(":st_conversion_value"); params["st_conversion_value"] = data.stat_conversion_value
        if getattr(data, "stat_ctr", None) is not None: cols.append("stat_ctr"); vals.append(":st_ctr"); params["st_ctr"] = data.stat_ctr
        if getattr(data, "stat_cvr", None) is not None: cols.append("stat_cvr"); vals.append(":st_cvr"); params["st_cvr"] = data.stat_cvr'''

# Wait, the rule is no getattr!
create_stats_new_no_getattr = '''        # Handle flat stats
        if data.stat_impressions is not None: cols.append("stat_impressions"); vals.append(":st_impressions"); params["st_impressions"] = data.stat_impressions
        if data.stat_clicks is not None: cols.append("stat_clicks"); vals.append(":st_clicks"); params["st_clicks"] = data.stat_clicks
        if data.stat_leads is not None: cols.append("stat_leads"); vals.append(":st_leads"); params["st_leads"] = data.stat_leads
        if data.stat_purchases is not None: cols.append("stat_purchases"); vals.append(":st_purchases"); params["st_purchases"] = data.stat_purchases
        if data.stat_add_to_cart is not None: cols.append("stat_add_to_cart"); vals.append(":st_add_to_cart"); params["st_add_to_cart"] = data.stat_add_to_cart
        if data.stat_conversions is not None: cols.append("stat_conversions"); vals.append(":st_conversions"); params["st_conversions"] = data.stat_conversions
        if data.stat_conversion_value is not None: cols.append("stat_conversion_value"); vals.append(":st_conversion_value"); params["st_conversion_value"] = data.stat_conversion_value
        if data.stat_ctr is not None: cols.append("stat_ctr"); vals.append(":st_ctr"); params["st_ctr"] = data.stat_ctr
        if data.stat_cvr is not None: cols.append("stat_cvr"); vals.append(":st_cvr"); params["st_cvr"] = data.stat_cvr'''

text = text.replace(create_stats_old, create_stats_new_no_getattr)

# Update update stats block
update_stats_old = '''        if data.stats is not None:
            if data.stats.impressions is not None: updates.append("stat_impressions = :st_impressions"); params["st_impressions"] = data.stats.impressions
            if data.stats.clicks is not None: updates.append("stat_clicks = :st_clicks"); params["st_clicks"] = data.stats.clicks
            if data.stats.leads is not None: updates.append("stat_leads = :st_leads"); params["st_leads"] = data.stats.leads
            if data.stats.purchases is not None: updates.append("stat_purchases = :st_purchases"); params["st_purchases"] = data.stats.purchases
            if data.stats.add_to_cart is not None: updates.append("stat_add_to_cart = :st_add_to_cart"); params["st_add_to_cart"] = data.stats.add_to_cart
            if data.stats.conversions is not None: updates.append("stat_conversions = :st_conversions"); params["st_conversions"] = data.stats.conversions
            if data.stats.conversion_value is not None: updates.append("stat_conversion_value = :st_conversion_value"); params["st_conversion_value"] = data.stats.conversion_value
            if data.stats.ctr is not None: updates.append("stat_ctr = :st_ctr"); params["st_ctr"] = data.stats.ctr
            if data.stats.cvr is not None: updates.append("stat_cvr = :st_cvr"); params["st_cvr"] = data.stats.cvr'''

update_stats_new = '''        # Handle flat stats
        if data.stat_impressions is not None: updates.append("stat_impressions = :st_impressions"); params["st_impressions"] = data.stat_impressions
        if data.stat_clicks is not None: updates.append("stat_clicks = :st_clicks"); params["st_clicks"] = data.stat_clicks
        if data.stat_leads is not None: updates.append("stat_leads = :st_leads"); params["st_leads"] = data.stat_leads
        if data.stat_purchases is not None: updates.append("stat_purchases = :st_purchases"); params["st_purchases"] = data.stat_purchases
        if data.stat_add_to_cart is not None: updates.append("stat_add_to_cart = :st_add_to_cart"); params["st_add_to_cart"] = data.stat_add_to_cart
        if data.stat_conversions is not None: updates.append("stat_conversions = :st_conversions"); params["st_conversions"] = data.stat_conversions
        if data.stat_conversion_value is not None: updates.append("stat_conversion_value = :st_conversion_value"); params["st_conversion_value"] = data.stat_conversion_value
        if data.stat_ctr is not None: updates.append("stat_ctr = :st_ctr"); params["st_ctr"] = data.stat_ctr
        if data.stat_cvr is not None: updates.append("stat_cvr = :st_cvr"); params["st_cvr"] = data.stat_cvr'''

text = text.replace(update_stats_old, update_stats_new)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
