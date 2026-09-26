from datetime import datetime, timezone
from typing import TYPE_CHECKING, Dict, Optional, Any
from app.models.daos import BannerInternalCreate, BannerInternalUpdate

from app.db.storage_factory import get_storage

if TYPE_CHECKING:
    from app.models.daos import BannerInternalCreate, BannerInternalUpdate
    


class BannerRepository:
    def __init__(self):
        self.storage = get_storage("banners")

    async def findAll(self, query: Optional[Dict] = None):
        banners = await self.storage.findAll()

        # Consistent preprocessing for ALL banners
        for banner in banners:
            # 1. User Segments normalization
            if not banner.user_segments:
                legacy_aud = (banner.target_audience if banner.target_audience is not None else "all")
                banner.user_segments = [legacy_aud] if legacy_aud else ["all"]

            # 2. Rules normalization
            if not banner.visibility_rules:
                banner.visibility_rules = []

            # 3. Always derive legacy fields for UI consistency
            segments = banner.user_segments
            rules = banner.visibility_rules
            banner.target_audience = segments[0] if segments else "all"

            if rules and len(rules) > 0:
                banner.position = (rules[0].pageType if rules[0].pageType else "homepage")
            
            # 4. Ensure required date fields exist for Pydantic validation
            if not banner.start_date:
                banner.start_date = banner.created_at or datetime.now(timezone.utc).isoformat()
            elif not banner.position:
                banner.position = "homepage"

        query = query or {}
        user_role = str((query["userRole"] if "userRole" in query else None) or "guest").lower()
        target_page_type = str((query["pageType"] if "pageType" in query else None) or (query["position"] if "position" in query else None) or "").lower()
        target_page_id = query["pageId"] if "pageId" in query else None

        if "isActive" in query and query["isActive"] is not None:
            banners = [b for b in banners if b.is_active == query["isActive"]]

        if "isPublished" in query and query["isPublished"] is not None:
            banners = [b for b in banners if b.is_published == query["isPublished"]]

        if target_page_type:
            filtered = []
            for banner in banners:
                segments = [str(s).lower() for s in (banner.user_segments if banner.user_segments is not None else ["all"])]

                # Role Check (Super Admin bypasses, otherwise check 'all' or specific role)
                if user_role != "super_admin" and "all" not in segments and user_role not in segments:
                    continue

                # Position/Rule Check
                legacy_pos = str((banner.position if banner.position is not None else "")).lower()
                rules = (banner.visibility_rules if banner.visibility_rules is not None else [])
                match = False

                # Standard homepage mapping
                homepage_aliases = [
                    "home",
                    "homepage",
                    "homepage_web",
                    "homepage_mobile",
                    "homeweb",
                    "homemobile",
                    "homeweb",
                    "homemobile",
                ]
                is_home_request = target_page_type in homepage_aliases or "home" in target_page_type

                # Check legacy position
                if (
                    legacy_pos == target_page_type
                    or legacy_pos == "all"
                    or (is_home_request and legacy_pos in homepage_aliases)
                ):
                    match = True

                # Check new rules
                if not match and rules:
                    for rule in rules:
                        rule_pg = str(rule.pageType if rule.pageType else "").lower()
                        if rule_pg == target_page_type or (is_home_request and rule_pg in homepage_aliases):
                            page_ids = rule.pageIds if rule.pageIds else []
                            if not page_ids or target_page_id in page_ids:
                                match = True
                                break

                if match:
                    filtered.append(banner)
            banners = filtered

        # Sort by displayOrder
        banners.sort(key=lambda x: x.displayOrder if x.displayOrder is not None else 0)

        return banners

    async def findById(self, id: str):
        return await self.storage.findById(id)

    async def findActive(self, query: Optional[Dict] = None, zone_id: Optional[str] = None):
        now = datetime.now(timezone.utc).isoformat()
        banners = await self.findAll({**(query or {}), "isActive": True, "isPublished": True})

        # Filter by date range
        active_banners = []
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        for banner in banners:
            start_date = banner.start_date
            end_date = banner.end_date

            def parse_iso(dt_str):
                if isinstance(dt_str, datetime):
                    if dt_str.tzinfo is not None:
                        from datetime import timezone
                        return dt_str.astimezone(timezone.utc).replace(tzinfo=None)
                    return dt_str
                if not dt_str or not str(dt_str).strip():
                    return None
                try:
                    # Handle Z suffix for UTC
                    if isinstance(dt_str, str) and dt_str.endswith("Z"):
                        dt_str = dt_str[:-1] + "+00:00"
                    dt = datetime.fromisoformat(dt_str)
                    # If aware, convert to naive UTC for consistent comparison
                    if dt.tzinfo is not None:
                        from datetime import timezone

                        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
                    return dt
                except (ValueError, TypeError):
                    return None

            start = parse_iso(start_date)
            if start and now < start:
                continue

            end = parse_iso(end_date)
            if end and now > end:
                continue

            active_banners.append(banner)

        # Zone filtering: if zone_id given, keep banners that have no zone restriction
        # (zoneIds is None/empty = applies to all zones) OR explicitly include this zone.
        if zone_id:
            active_banners = [
                b for b in active_banners
                if not b.zone_ids or zone_id in b.zone_ids
            ]

        return active_banners

    async def create(self, banner_data: 'BannerInternalCreate'):
        # Derive legacy fields for backward compatibility and admin table visibility
        user_segments = banner_data.user_segments if banner_data.user_segments is not None else ["all"]
        visibility_rules = banner_data.visibility_rules if banner_data.visibility_rules is not None else []
        start_date = banner_data.start_date

        target_audience = user_segments[0] if user_segments else "all"
        position = (visibility_rules[0].pageType if visibility_rules[0].pageType else "homepage") if visibility_rules else "homepage"

        if not start_date or not str(start_date).strip():
            start_date = datetime.now(timezone.utc).isoformat()

        banner_dict = {
            "title": banner_data.title if banner_data.title is not None else "",
            "description": banner_data.description if banner_data.description is not None else "",
            "imageUrl": banner_data.image_url if banner_data.image_url is not None else "",
            "linkUrl": banner_data.link_url if banner_data.link_url is not None else "",
            "displayOrder": banner_data.displayOrder if banner_data.displayOrder is not None else 0,
            "startDate": start_date,
            "endDate": banner_data.end_date,
            "isActive": banner_data.is_active if banner_data.is_active is not None else True,
            "isPublished": banner_data.is_published if banner_data.is_published is not None else False,
            "targetAudience": target_audience,
            "userSegments": user_segments,
            "visibilityRules": visibility_rules,
            "position": position,
            "zoneIds": banner_data.zone_ids if banner_data.zone_ids is not None else None,
        }

        banner_model = BannerInternalCreate.model_validate(banner_dict)
        return await self.storage.create(banner_model)

    async def update(self, id: str, update_data: 'BannerInternalUpdate'):
        # Sync legacy fields if new ones are provided
        update_dict = {}
        for field in update_data.model_fields_set:
            match field:
                case "title": update_dict["title"] = update_data.title
                case "description": update_dict["description"] = update_data.description
                case "imageUrl": update_dict["imageUrl"] = update_data.image_url
                case "linkUrl": update_dict["linkUrl"] = update_data.link_url
                case "displayOrder": update_dict["displayOrder"] = update_data.displayOrder
                case "startDate": update_dict["startDate"] = update_data.start_date
                case "endDate": update_dict["endDate"] = update_data.end_date
                case "isActive": update_dict["isActive"] = update_data.is_active
                case "isPublished": update_dict["isPublished"] = update_data.is_published
                case "targetAudience": update_dict["targetAudience"] = update_data.target_audience
                case "userSegments": update_dict["userSegments"] = update_data.user_segments
                case "visibilityRules": update_dict["visibilityRules"] = update_data.visibility_rules
                case "position": update_dict["position"] = update_data.position
                case "zoneIds": update_dict["zoneIds"] = update_data.zone_ids
        
        if "userSegments" in update_dict:
            segments = update_dict["userSegments"]
            update_dict["targetAudience"] = segments[0] if segments else "all"

        if "visibilityRules" in update_dict:
            rules = update_dict["visibilityRules"]
            update_dict["position"] = (rules[0].pageType if rules[0].pageType else "homepage") if rules else "homepage"

        update_model = BannerInternalUpdate.model_validate(update_dict)
        return await self.storage.update(id, update_model)

    async def delete(self, id: str):
        return await self.storage.delete(id)


banner_repository = BannerRepository()

