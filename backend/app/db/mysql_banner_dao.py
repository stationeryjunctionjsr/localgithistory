"""
MySQL DAO for sj_banners. Implements FileStorage-like interface for 'banners'.
Fully relational with child tables for user_segments and visibility_rules.
"""

from app.models.schemas import BannerResponse
from app.models.daos import BannerInternalCreate, BannerInternalUpdate
import secrets
from typing import Dict
import json
from app.models.banner import Banner, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc


class MySQLBannerDAO:
    @property
    def TABLE(self):
        return "sj_banners"

    def _factory(self):
        return get_async_session_factory()
    async def findAll(self, query: Optional[Dict] = None) -> List[BannerResponse]:
        factory = self._factory()
        where_clauses = []
        params = {}
        if query:
            for k, v in query.items():
                if k in ("_id", "id"):
                    where_clauses.append("id = :id")
                    params["id"] = int(v) if str(v).isdigit() else None
                elif k == "is_active":
                    where_clauses.append("is_active = :is_active")
                    params["is_active"] = 1 if v else 0
                elif k == "is_published":
                    where_clauses.append("is_published = :is_published")
                    params["is_published"] = 1 if v else 0
                elif k == "title":
                    where_clauses.append("title = :title")
                    params["title"] = v
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        async with factory() as session:
            result = await session.execute(
                text(f"SELECT id AS _id, external_id, title, description, image_url, link_url, display_order, start_date, end_date, is_active, is_published, target_audience, position, zone_ids, created_at, updated_at FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"), params
            )
            rows = result.fetchall()
            
        import json
        out = []
        for r in rows:
            d = dict(r._mapping)
            if d.get("zone_ids"):
                d["zone_ids"] = json.loads(d["zone_ids"])
            out.append(BannerResponse.model_validate(d))
        return out


    async def findOne(self, query: Dict) -> Optional[BannerResponse]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[BannerResponse]:
        return await self.findOne({"_id": id})

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
                        zone_ids,
                        created_at, updated_at
                    ) VALUES (
                        :external_id, :title, :description, :image_url, :link_url,
                        :display_order, :start_date, :end_date,
                        :is_active, :is_published, :target_audience, :position,
                        :zone_ids,
                        :created_at, :updated_at
                    )
                    """
                ),
                {
                    "external_id": external_id,
                    "title": data.title,
                    "description": data.description,
                    "image_url": data.image_url,
                    "link_url": data.link_url,
                    "display_order": (data.displayOrder if data.displayOrder is not None else 0),
                    "start_date": data.start_date,
                    "end_date": data.end_date,
                    "is_active": int(bool((data.isActive if data.isActive is not None else True))),
                    "is_published": int(bool((data.is_published if data.is_published is not None else False))),
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
            
        merged = {}
        for k in ["title", "description", "imageUrl", "linkUrl", "displayOrder", "startDate", "endDate", "isActive", "isPublished", "targetAudience", "position", "zoneIds"]:
            val = None
            match k:
                case "title": val = update_data.title if update_data.title is not None else existing.title
                case "description": val = update_data.description if update_data.description is not None else existing.description
                case "imageUrl": val = update_data.image_url if update_data.image_url is not None else existing.image_url
                case "linkUrl": val = update_data.link_url if update_data.link_url is not None else existing.link_url
                case "displayOrder": val = update_data.displayOrder if update_data.displayOrder is not None else existing.display_order
                case "startDate": val = update_data.start_date if update_data.start_date is not None else existing.start_date
                case "endDate": val = update_data.end_date if update_data.end_date is not None else existing.end_date
                case "isActive": val = update_data.isActive if update_data.isActive is not None else existing.is_active
                case "isPublished": val = update_data.is_published if update_data.is_published is not None else existing.is_published
                case "targetAudience": val = update_data.target_audience if update_data.target_audience is not None else existing.target_audience
                case "position": val = update_data.position if update_data.position is not None else existing.position
                case "zoneIds": val = update_data.zone_ids if update_data.zone_ids is not None else existing.zone_ids
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
                    "zone_ids": json.dumps(merged["zoneIds"]) if merged["zoneIds"] else None,
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

