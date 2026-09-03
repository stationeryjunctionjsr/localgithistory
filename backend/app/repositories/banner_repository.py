from datetime import datetime, timezone
from typing import Dict, Optional

from app.db.storage_factory import get_storage


class BannerRepository:
    def __init__(self):
        self.storage = get_storage("banners")

    async def findAll(self, query: Optional[Dict] = None):
        banners = await self.storage.findAll()

        # Consistent preprocessing for ALL banners
        for banner in banners:
            # 1. User Segments normalization
            if not banner.get("userSegments"):
                legacy_aud = banner.get("targetAudience", "all")
                banner["userSegments"] = [legacy_aud] if legacy_aud else ["all"]

            # 2. Rules normalization
            if not banner.get("visibilityRules"):
                banner["visibilityRules"] = []

            # 3. Always derive legacy fields for UI consistency
            segments = banner["userSegments"]
            rules = banner["visibilityRules"]
            banner["targetAudience"] = segments[0] if segments else "all"

            if rules and len(rules) > 0:
                banner["position"] = rules[0].get("pageType", "homepage")
            
            # 4. Ensure required date fields exist for Pydantic validation
            if not banner.get("startDate"):
                banner["startDate"] = banner.get("createdAt") or datetime.now(timezone.utc).isoformat()
            elif not banner.get("position"):
                banner["position"] = "homepage"

        query = query or {}
        user_role = str(query.get("userRole") or "guest").lower()
        target_page_type = str(query.get("pageType") or query.get("position") or "").lower()
        target_page_id = query.get("pageId")

        if query.get("isActive") is not None:
            banners = [b for b in banners if b.get("isActive") == query["isActive"]]

        if query.get("isPublished") is not None:
            banners = [b for b in banners if b.get("isPublished") == query["isPublished"]]

        if target_page_type:
            filtered = []
            for banner in banners:
                segments = [str(s).lower() for s in banner.get("userSegments", ["all"])]

                # Role Check (Super Admin bypasses, otherwise check 'all' or specific role)
                if user_role != "super_admin" and "all" not in segments and user_role not in segments:
                    continue

                # Position/Rule Check
                legacy_pos = str(banner.get("position", "")).lower()
                rules = banner.get("visibilityRules", [])
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
                        rule_pg = str(rule.get("pageType", "")).lower()
                        if rule_pg == target_page_type or (is_home_request and rule_pg in homepage_aliases):
                            page_ids = rule.get("pageIds", [])
                            if not page_ids or target_page_id in page_ids:
                                match = True
                                break

                if match:
                    filtered.append(banner)
            banners = filtered

        # Sort by displayOrder
        banners.sort(key=lambda x: x.get("displayOrder", 0))

        return banners

    async def findById(self, id: str):
        return await self.storage.findById(id)

    async def findActive(self, query: Optional[Dict] = None):
        now = datetime.now(timezone.utc).isoformat()
        banners = await self.findAll({**(query or {}), "isActive": True, "isPublished": True})

        # Filter by date range
        active_banners = []
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        for banner in banners:
            start_date = banner.get("startDate")
            end_date = banner.get("endDate")

            def parse_iso(dt_str):
                if not dt_str or not str(dt_str).strip():
                    return None
                try:
                    # Handle Z suffix for UTC
                    if dt_str.endswith("Z"):
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

        return active_banners

    async def create(self, banner_data: Dict):
        # Derive legacy fields for backward compatibility and admin table visibility
        user_segments = banner_data.get("userSegments", ["all"])
        visibility_rules = banner_data.get("visibilityRules", [])

        target_audience = user_segments[0] if user_segments else "all"
        position = visibility_rules[0].get("pageType", "homepage") if visibility_rules else "homepage"

        start_date = banner_data.get("startDate")
        if not start_date or not str(start_date).strip():
            start_date = datetime.now(timezone.utc).isoformat()

        banner = {
            "title": banner_data.get("title", ""),
            "description": banner_data.get("description", ""),
            "imageUrl": banner_data["imageUrl"],
            "linkUrl": banner_data.get("linkUrl", ""),
            "displayOrder": banner_data.get("displayOrder", 0),
            "startDate": start_date,
            "endDate": banner_data.get("endDate"),
            "isActive": banner_data.get("isActive", True),
            "isPublished": banner_data.get("isPublished", False),
            "targetAudience": target_audience,
            "userSegments": user_segments,
            "visibilityRules": visibility_rules,
            "position": position,
        }

        return await self.storage.create(banner)

    async def update(self, id: str, update_data: Dict):
        # Sync legacy fields if new ones are provided
        if "userSegments" in update_data:
            segments = update_data["userSegments"]
            update_data["targetAudience"] = segments[0] if segments else "all"

        if "visibilityRules" in update_data:
            rules = update_data["visibilityRules"]
            update_data["position"] = rules[0].get("pageType", "homepage") if rules else "homepage"

        return await self.storage.update(id, update_data)

    async def delete(self, id: str):
        return await self.storage.delete(id)


banner_repository = BannerRepository()
