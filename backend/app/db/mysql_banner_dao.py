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

    def _map_to_schema(self, r) -> BannerResponse:
        zone_ids = None
        if r.zone_ids:
            try:
                zone_ids = json_loads(r.zone_ids)
            except Exception:
                zone_ids = None

        user_segments_raw = json_loads(r.user_segments_json) if getattr(r, "user_segments_json", None) else []
        user_segments = [str(s) for s in user_segments_raw if s] if isinstance(user_segments_raw, list) else []
        if not user_segments and r.target_audience:
            user_segments = [r.target_audience]
        if not user_segments:
            user_segments = ["all"]

        rules_raw = json_loads(r.visibility_rules_json) if getattr(r, "visibility_rules_json", None) else []
        visibility_rules = []
        if isinstance(rules_raw, list):
            for rule in rules_raw:
                if not rule:
                    continue
                if isinstance(rule, str) and (rule.startswith("{") or rule.startswith("[")):
                    try:
                        visibility_rules.append(json_loads(rule))
                    except Exception:
                        visibility_rules.append({"pageType": rule})
                elif isinstance(rule, str):
                    visibility_rules.append({"pageType": rule})
                else:
                    visibility_rules.append(rule)

        return BannerResponse(
            id=str(r._id),
            external_id=r.external_id,
            title=r.title,
            description=r.description,
            image_url=r.image_url,
            link_url=r.link_url,
            display_order=r.display_order or 0,
            start_date=r.start_date,
            end_date=r.end_date,
            is_active=bool(r.is_active) if r.is_active is not None else True,
            is_published=bool(r.is_published) if r.is_published is not None else False,
            target_audience=r.target_audience,
            position=r.position,
            created_at=r.created_at,
            updated_at=r.updated_at,
            zone_ids=zone_ids,
            user_segments=user_segments,
            visibility_rules=visibility_rules,
        )

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
            where_clauses.append("b.id = :id")
            params["id"] = int(id) if str(id).isdigit() else None
        if is_active is not None:
            where_clauses.append("b.is_active = :is_active")
            params["is_active"] = 1 if is_active else 0
        if is_published is not None:
            where_clauses.append("b.is_published = :is_published")
            params["is_published"] = 1 if is_published else 0
        if title is not None:
            where_clauses.append("b.title = :title")
            params["title"] = title
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        async with factory() as session:
            result = await session.execute(
                text(
                    f"SELECT b.id AS _id, b.external_id, b.title, b.description, b.image_url, b.link_url, "
                    f"b.display_order, b.start_date, b.end_date, b.is_active, b.is_published, "
                    f"b.target_audience, b.position, b.created_at, b.updated_at, b.zone_ids, "
                    f"COALESCE((SELECT JSON_ARRAYAGG(s.segment) FROM sj_banner_user_segments s WHERE s.banner_id = b.id), JSON_ARRAY()) AS user_segments_json, "
                    f"COALESCE((SELECT JSON_ARRAYAGG(r.rule) FROM sj_banner_visibility_rules r WHERE r.banner_id = b.id), JSON_ARRAY()) AS visibility_rules_json "
                    f"FROM {self.TABLE} b WHERE {where_sql} ORDER BY b.display_order ASC, b.id ASC"
                ),
                params,
            )
            rows = result.fetchall()
            return [self._map_to_schema(r) for r in rows]

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
            "b.is_active = 1",
            "b.is_published = 1",
            "(b.start_date IS NULL OR b.start_date <= :now_str)",
            "(b.end_date IS NULL OR b.end_date >= :now_str)",
        ]
        params = {"now_str": now_str}
        if position:
            where_clauses.append("b.position = :position")
            params["position"] = position
        if target_audience and target_audience != "all":
            where_clauses.append("(b.target_audience = :target_audience OR b.target_audience = 'all' OR b.target_audience IS NULL)")
            params["target_audience"] = target_audience

        where_sql = " AND ".join(where_clauses)
        async with factory() as session:
            result = await session.execute(
                text(
                    f"SELECT b.id AS _id, b.external_id, b.title, b.description, b.image_url, b.link_url, "
                    f"b.display_order, b.start_date, b.end_date, b.is_active, b.is_published, "
                    f"b.target_audience, b.position, b.created_at, b.updated_at, b.zone_ids, "
                    f"COALESCE((SELECT JSON_ARRAYAGG(s.segment) FROM sj_banner_user_segments s WHERE s.banner_id = b.id), JSON_ARRAY()) AS user_segments_json, "
                    f"COALESCE((SELECT JSON_ARRAYAGG(r.rule) FROM sj_banner_visibility_rules r WHERE r.banner_id = b.id), JSON_ARRAY()) AS visibility_rules_json "
                    f"FROM {self.TABLE} b WHERE {where_sql} ORDER BY b.display_order ASC, b.id ASC"
                ),
                params,
            )
            rows = result.fetchall()
            return [self._map_to_schema(r) for r in rows]

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
                    "image_url": data.image_url,
                    "link_url": data.link_url,
                    "display_order": (data.display_order if data.display_order is not None else 0),
                    "start_date": data.start_date,
                    "end_date": data.end_date,
                    "is_active": 1 if (data.is_active if data.is_active is not None else True) else 0,
                    "is_published": 1 if (data.is_published if data.is_published is not None else False) else 0,
                    "target_audience": data.target_audience,
                    "position": data.position,
                    "zone_ids": json.dumps(data.zone_ids) if data.zone_ids else None,
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

        title = update_data.title if update_data.title is not None else existing.title
        description = update_data.description if update_data.description is not None else existing.description
        image_url = update_data.image_url if update_data.image_url is not None else existing.image_url
        link_url = update_data.link_url if update_data.link_url is not None else existing.link_url
        display_order = update_data.display_order if update_data.display_order is not None else (existing.display_order or 0)
        start_date = update_data.start_date if update_data.start_date is not None else existing.start_date
        end_date = update_data.end_date if update_data.end_date is not None else existing.end_date
        is_active = update_data.is_active if update_data.is_active is not None else existing.is_active
        is_published = update_data.is_published if update_data.is_published is not None else existing.is_published
        target_audience = update_data.target_audience if update_data.target_audience is not None else existing.target_audience
        position = update_data.position if update_data.position is not None else existing.position
        zone_ids = update_data.zone_ids if update_data.zone_ids is not None else existing.zone_ids

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
                    "title": title,
                    "description": description,
                    "image_url": image_url,
                    "link_url": link_url,
                    "display_order": display_order,
                    "start_date": start_date,
                    "end_date": end_date,
                    "is_active": 1 if is_active else 0,
                    "is_published": 1 if is_published else 0,
                    "target_audience": target_audience,
                    "position": position,
                    "zone_ids": json.dumps(zone_ids) if zone_ids else None,
                    "updated_at": now,
                },
            )
            dummy_merged = BannerChildrenData(
                user_segments=update_data.user_segments if update_data.user_segments is not None else existing.user_segments,
                visibility_rules=update_data.visibility_rules if update_data.visibility_rules is not None else existing.visibility_rules,
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
