from datetime import datetime, timezone
from typing import Optional, List, Union
from app.models.daos import BannerInternalCreate, BannerInternalUpdate, BannerFilter
from app.models.schemas import BannerResponse, BannerCreate, BannerUpdate
from app.db.storage_factory import get_storage

HOMEPAGE_ALIASES = frozenset({
    "home",
    "homepage",
    "homepage_web",
    "homepage_mobile",
    "homeweb",
    "homemobile",
})


class BannerRepository:
    def __init__(self) -> None:
        self.storage = get_storage("banners")

    async def findAll(self, filters: Optional[BannerFilter] = None) -> List[BannerResponse]:
        is_active = filters.is_active if filters else None
        is_published = filters.is_published if filters else None
        banners = await self.storage.findAll(is_active=is_active, is_published=is_published)

        if not filters:
            return banners

        user_role = str(filters.user_role or "guest").lower()
        target_page_type = str(filters.page_type or filters.position or "").lower()
        target_page_id = filters.page_id

        if target_page_type:
            filtered = []
            for banner in banners:
                segments = [str(s).lower() for s in (banner.user_segments or ["all"])]

                if user_role != "super_admin" and "all" not in segments and user_role not in segments:
                    continue

                pos = str(banner.position or "").lower()
                rules = banner.visibility_rules or []
                match = False

                is_home_request = target_page_type in HOMEPAGE_ALIASES or "home" in target_page_type

                if (
                    pos == target_page_type
                    or pos == "all"
                    or (is_home_request and pos in HOMEPAGE_ALIASES)
                ):
                    match = True

                if not match and rules:
                    for rule in rules:
                        rule_pg = str(rule.page_type or "").lower()
                        if rule_pg == target_page_type or (is_home_request and rule_pg in HOMEPAGE_ALIASES):
                            page_ids = rule.page_ids or []
                            if not page_ids or target_page_id in page_ids:
                                match = True
                                break

                if match:
                    filtered.append(banner)
            banners = filtered

        return banners

    async def findById(self, id: int) -> Optional[BannerResponse]:
        return await self.storage.findById(id)

    async def findActive(self, filters: Optional[BannerFilter] = None, zone_id: Optional[str] = None) -> List[BannerResponse]:
        effective_filters = filters.model_copy(update={"is_active": True, "is_published": True}) if filters else BannerFilter(is_active=True, is_published=True)
        banners = await self.findAll(effective_filters)

        active_banners = []
        now = datetime.now(timezone.utc)
        for banner in banners:
            start_dt = banner.start_date
            end_dt = banner.end_date

            if start_dt and start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=timezone.utc)
            if end_dt and end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=timezone.utc)

            if start_dt and now < start_dt:
                continue

            if end_dt and now > end_dt:
                continue

            active_banners.append(banner)

        effective_zone_id = zone_id or (filters.zone_id if filters else None)
        if effective_zone_id:
            active_banners = [
                b for b in active_banners
                if not b.zone_ids or effective_zone_id in b.zone_ids
            ]

        return active_banners

    async def create(self, banner_data: BannerCreate) -> BannerResponse:
        user_segments = banner_data.user_segments or ["all"]
        visibility_rules = banner_data.visibility_rules or []
        start_date = banner_data.start_date or datetime.now(timezone.utc)
        target_audience = banner_data.target_audience or (user_segments[0] if user_segments else "all")
        position = banner_data.position or ((visibility_rules[0].page_type or "homepage") if visibility_rules else "homepage")

        internal_create = BannerInternalCreate(
            title=banner_data.title or "",
            description=banner_data.description or "",
            image_url=banner_data.image_url,
            link_url=banner_data.link_url or "",
            display_order=banner_data.display_order or 0,
            start_date=start_date,
            end_date=banner_data.end_date,
            is_active=banner_data.is_active,
            is_published=banner_data.is_published,
            target_audience=target_audience,
            user_segments=user_segments,
            visibility_rules=visibility_rules,
            position=position,
            zone_ids=banner_data.zone_ids,
        )
        return await self.storage.create(internal_create)

    async def update(self, id: int, update_data: BannerUpdate) -> Optional[BannerResponse]:
        internal_update = BannerInternalUpdate.model_validate(update_data.model_dump(exclude_unset=True))
        return await self.storage.update(id, internal_update)

    async def delete(self, id: int) -> bool:
        return await self.storage.delete(id)


banner_repository = BannerRepository()

