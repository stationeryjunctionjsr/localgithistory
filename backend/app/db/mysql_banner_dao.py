"""
MySQL DAO for sj_banners. Implements FileStorage-like interface for 'banners'.
Fully relational with child tables for user_segments and visibility_rules.
"""

from app.models.schemas import BannerResponse
from app.models.daos import BannerInternalCreate, BannerInternalUpdate, BannerChildrenData
import secrets
from typing import List, Optional, Union
from pydantic import BaseModel
from app.models.banner import Banner

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
import json
from app.db.db_utils import now_utc, json_loads


class MySQLBannerDAO:
    @property
    def TABLE(self):
        return "sj_banners"

    def _factory(self):
        return get_async_session_factory()

    async def _hydrate_banner_rows(self, session, rows) -> List[BannerResponse]:
        if not rows:
            return []

        bids = [int(r._mapping["_id"]) for r in rows]
        bids_csv = ", ".join(str(b) for b in bids)

        seg_res = await session.execute(
            text(f"SELECT banner_id, segment FROM sj_banner_user_segments WHERE banner_id IN ({bids_csv})")
        )
        seg_map = {}
        for s_row in seg_res.fetchall():
            seg_map.setdefault(int(s_row.banner_id), []).append(s_row.segment)

        rules_res = await session.execute(
            text(f"SELECT banner_id, rule FROM sj_banner_visibility_rules WHERE banner_id IN ({bids_csv})")
        )
        rules_map = {}
        for r_row in rules_res.fetchall():
            try:
                rule_obj = json_loads(r_row.rule)
            except Exception:
                rule_obj = {"pageType": r_row.rule}
            rules_map.setdefault(int(r_row.banner_id), []).append(rule_obj)

        banners = []
        for r in rows:
            mapping = dict(r._mapping)
            bid = int(mapping["_id"])
            if mapping.get("zone_ids"):
                try:
                    mapping["zone_ids"] = json_loads(mapping["zone_ids"])
                except Exception:
                    mapping["zone_ids"] = None
            else:
                mapping["zone_ids"] = None

            mapping["user_segments"] = seg_map.get(bid) or ([mapping.get("target_audience")] if mapping.get("target_audience") else ["all"])
            mapping["visibility_rules"] = rules_map.get(bid) or []
            banners.append(BannerResponse.model_validate(mapping))
        return banners

    async def findAll(
        self,
        id: Optional[Union[int, str]] = None,
        is_active: Optional[bool] = None,
        is_published: Optional[bool] = None,
        title: Optional[str] = None,
    ) -> List[BannerResponse]:
        factory = self._factory()
        if not factory:
            return []
        where_clauses = []
        params = {}
        if id is not None:
            where_clauses.append("id = :id")
            params["id"] = int(id) if str(id).isdigit() else None
        if is_active is not None:
            where_clauses.append("is_active = :is_active")
            params["is_active"] = 1 if is_active else 0
        if is_published is not None:
            where_clauses.append("is_published = :is_published")
            params["is_published"] = 1 if is_published else 0
        if title is not None:
            where_clauses.append("title = :title")
            params["title"] = title
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        async with factory() as session:
            result = await session.execute(
                text(
                    f"SELECT id AS _id, external_id, title, description, image_url, link_url, "
                    f"display_order, start_date, end_date, is_active, is_published, "
                    f"target_audience, position, created_at, updated_at, zone_ids "
                    f"FROM {self.TABLE} WHERE {where_sql} ORDER BY display_order ASC, id ASC"
                ),
                params,
            )
            rows = result.fetchall()
            return await self._hydrate_banner_rows(session, rows)

    async def find_active_banners(
        self,
        current_time: Optional[datetime] = None,
        position: Optional[str] = None,
        target_audience: Optional[str] = None,
    ) -> List[BannerResponse]:
        factory = self._factory()
        if not factory:
            return []
        now_dt = current_time or now_utc()
        now_str = now_dt.isoformat()
        where_clauses = [
            "is_active = 1",
            "is_published = 1",
            "(start_date IS NULL OR start_date <= :now_str)",
            "(end_date IS NULL OR end_date >= :now_str)",
        ]
        params = {"now_str": now_str}
        if position:
            where_clauses.append("position = :position")
            params["position"] = position
        if target_audience and target_audience != "all":
            where_clauses.append("(target_audience = :target_audience OR target_audience = 'all' OR target_audience IS NULL)")
            params["target_audience"] = target_audience

        where_sql = " AND ".join(where_clauses)
        async with factory() as session:
            result = await session.execute(
                text(
                    f"SELECT id AS _id, external_id, title, description, image_url, link_url, "
                    f"display_order, start_date, end_date, is_active, is_published, "
                    f"target_audience, position, created_at, updated_at, zone_ids "
                    f"FROM {self.TABLE} WHERE {where_sql} ORDER BY display_order ASC, id ASC"
                ),
                params,
            )
            rows = result.fetchall()
            return await self._hydrate_banner_rows(session, rows)

    async def findOne(
        self,
        id: Optional[Union[int, str]] = None,
        is_active: Optional[bool] = None,
        is_published: Optional[bool] = None,
        title: Optional[str] = None,
    ) -> Optional[BannerResponse]:
        docs = await self.findAll(id=id, is_active=is_active, is_published=is_published, title=title)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[BannerResponse]:
        return await self.findOne(id=id)

    async def create(self, data: BannerInternalCreate) -> BannerResponse:
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    INSERT INTO {self.TABLE} (
                        external_id, title, description, image_url, link_url,
                        display_order, start_date, end_date,
                        is_active, is_published, target_audience, position,
                        zone_ids, created_at, updated_at
                    ) VALUES (
                        :external_id, :title, :description, :image_url, :link_url,
                        :display_order, :start_date, :end_date,
                        :is_active, :is_published, :target_audience, :position,
                        :zone_ids, :created_at, :updated_at
                    )
                    """
                ),
                {
                    "external_id": external_id,
                    "title": data.title,
                    "description": data.description,
                    "image_url": data.imageUrl,
                    "link_url": data.linkUrl,
                    "display_order": (data.displayOrder if data.displayOrder is not None else 0),
                    "start_date": data.startDate,
                    "end_date": data.endDate,
                    "is_active": int(bool((data.is_active if data.is_active is not None else True))),
                    "is_published": int(bool((data.isPublished if data.isPublished is not None else False))),
                    "target_audience": data.targetAudience,
                    "position": data.position,
                    "zone_ids": json.dumps(data.zoneIds) if data.zoneIds else None,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            await session.commit()
            r = await session.execute(
                text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": external_id}
            )
            new_id = r.scalar()
            await self._replace_children(session, new_id, data)
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: BannerInternalUpdate) -> Optional[BannerResponse]:
        existing = await self.findById(id)
        if not existing:
            return None
            
        merged = {}
        for k in ["title", "description", "imageUrl", "linkUrl", "displayOrder", "startDate", "endDate", "isActive", "isPublished", "targetAudience", "position", "zoneIds"]:
            val = None
            match k:
                case "title": val = update_data.title if update_data.title is not None else existing.title
                case "description": val = update_data.description if update_data.description is not None else existing.description
                case "imageUrl": val = update_data.imageUrl if update_data.imageUrl is not None else existing.image_url
                case "linkUrl": val = update_data.linkUrl if update_data.linkUrl is not None else existing.link_url
                case "displayOrder": val = update_data.displayOrder if update_data.displayOrder is not None else existing.display_order
                case "startDate": val = update_data.startDate if update_data.startDate is not None else existing.start_date
                case "endDate": val = update_data.endDate if update_data.endDate is not None else existing.end_date
                case "isActive": val = update_data.is_active if update_data.is_active is not None else existing.is_active
                case "isPublished": val = update_data.isPublished if update_data.isPublished is not None else existing.is_published
                case "targetAudience": val = update_data.targetAudience if update_data.targetAudience is not None else existing.target_audience
                case "position": val = update_data.position if update_data.position is not None else existing.position
                case "zoneIds": val = update_data.zoneIds if update_data.zoneIds is not None else existing.zone_ids
            merged[k] = val

        factory = self._factory()
        now = now_utc()
        bid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    UPDATE {self.TABLE} SET
                        title = :title,
                        description = :description,
                        image_url = :image_url,
                        link_url = :link_url,
                        display_order = :display_order,
                        start_date = :start_date,
                        end_date = :end_date,
                        is_active = :is_active,
                        is_published = :is_published,
                        target_audience = :target_audience,
                        position = :position,
                        zone_ids = :zone_ids,
                        updated_at = :updated_at
                    WHERE id = :id
                    """
                ),
                {
                    "id": bid,
                    "title": merged["title"],
                    "description": merged["description"],
                    "image_url": merged["imageUrl"],
                    "link_url": merged["linkUrl"],
                    "display_order": (merged["displayOrder"] if ("displayOrder" in merged and merged["displayOrder"] is not None) else 0),
                    "start_date": merged["startDate"],
                    "end_date": merged["endDate"],
                    "is_active": int(bool(merged["isActive"] if "isActive" in merged else True)),
                    "is_published": int(bool(merged["isPublished"] if "isPublished" in merged else False)),
                    "target_audience": merged["targetAudience"],
                    "position": merged["position"],
                    "zone_ids": json.dumps(merged["zoneIds"]) if merged.get("zoneIds") else None,
                    "updated_at": now,
                },
            )
            # Need to pass an object with userSegments and visibilityRules for _replace_children
            from app.models.daos import BannerChildrenData
            dummy_merged = BannerChildrenData(
                user_segments=update_data.user_segments if update_data.user_segments is not None else existing.user_segments,
                visibility_rules=update_data.visibility_rules if update_data.visibility_rules is not None else existing.visibility_rules
            )
            await self._replace_children(session, bid, dummy_merged)
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"), {"id": int(id) if str(id).isdigit() else None}
            )
            await session.commit()
            return result.rowcount > 0



    async def _replace_children(self, session, bid: int, data: Union[BannerInternalCreate, BannerInternalUpdate, BannerChildrenData]):
        await session.execute(text("DELETE FROM sj_banner_user_segments WHERE banner_id = :bid"), {"bid": bid})
        await session.execute(text("DELETE FROM sj_banner_visibility_rules WHERE banner_id = :bid"), {"bid": bid})
        
        user_segments = data.user_segments if data.user_segments is not None else []
        for seg in user_segments:
            await session.execute(
                text("INSERT INTO sj_banner_user_segments (banner_id, segment) VALUES (:bid, :seg)"),
                {"bid": bid, "seg": seg}
            )
            
        visibility_rules = data.visibility_rules if data.visibility_rules is not None else []
        for rule in visibility_rules:
            rule_val = rule.model_dump_json() if isinstance(rule, BaseModel) else str(rule)
            await session.execute(
                text("INSERT INTO sj_banner_visibility_rules (banner_id, rule) VALUES (:bid, :rule)"),
                {"bid": bid, "rule": rule_val}
            )
