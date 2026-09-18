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
        suffix = (settings.table_suffix if settings.table_suffix is not None else "")
        return f"sj_banners{suffix}"

    def _factory(self):
        return get_async_session_factory()

    def _map_to_schema(self, r, children: Dict) -> BannerResponse:
        return BannerResponse(**{
            "_id": str(r.id),
            "title": r.title,
            "description": r.description,
            "imageUrl": r.image_url,
            "linkUrl": r.link_url,
            "displayOrder": r.display_order,
            "startDate": r.start_date,
            "endDate": r.end_date,
            "isActive": bool(r.is_active) if r.is_active is not None else True,
            "isPublished": bool(r.is_published) if r.is_published is not None else False,
            "targetAudience": r.target_audience,
            "position": r.position,
            "userSegments": children["userSegments"] if "userSegments" in children else [],
            "visibilityRules": children["visibilityRules"] if "visibilityRules" in children else [],
            "createdAt": r.created_at.isoformat() if r.created_at else None,
            "updatedAt": r.updated_at.isoformat() if r.updated_at else None,
        })

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:
        c_map = {rid: {"userSegments": [], "visibilityRules": []} for rid in ids}
        if not ids:
            return c_map
        chunks = [ids[i : i + 999] for i in range(0, len(ids), 999)]
        for chunk in chunks:
            chunk_params = {f"id_{i}": cid for i, cid in enumerate(chunk)}
            placeholders = ", ".join([f":{k}" for k in chunk_params.keys()])

            res_us = await session.execute(
                text(f"SELECT banner_id, segment FROM sj_banner_user_segments WHERE banner_id IN ({placeholders})"),
                chunk_params,
            )
            for r in res_us.fetchall():
                c_map[r.banner_id]["userSegments"].append(r.segment)

            res_vr = await session.execute(
                text(f"SELECT banner_id, rule FROM sj_banner_visibility_rules WHERE banner_id IN ({placeholders})"),
                chunk_params,
            )
            for r in res_vr.fetchall():
                try:
                    c_map[r.banner_id]["visibilityRules"].append(json.loads(r.rule))
                except (json.JSONDecodeError, TypeError):
                    c_map[r.banner_id]["visibilityRules"].append(r.rule)
        return c_map

    async def _replace_children(self, session, bid: int, data: Dict):
        await session.execute(text("DELETE FROM sj_banner_user_segments WHERE banner_id = :bid"), {"bid": bid})
        await session.execute(text("DELETE FROM sj_banner_visibility_rules WHERE banner_id = :bid"), {"bid": bid})

        for seg in (data.userSegments if data.userSegments is not None else []):
            await session.execute(
                text("INSERT INTO sj_banner_user_segments (banner_id, segment) VALUES (:bid, :seg)"),
                {"bid": bid, "seg": str(seg)},
            )

        for rule in (data.visibilityRules if data.visibilityRules is not None else []):
            await session.execute(
                text("INSERT INTO sj_banner_visibility_rules (banner_id, rule) VALUES (:bid, :rule)"),
                {"bid": bid, "rule": json.dumps(rule.model_dump(exclude_unset=True))},
            )

    async def findAll(self, query: Optional[Dict] = None) -> List[BannerResponse]:
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
                elif k == "isActive":
                    where_clauses.append("is_active = :is_active")
                    params["is_active"] = int(bool(v))
                elif k == "position":
                    where_clauses.append("position = :pos")
                    params["pos"] = str(v)
                elif k == "targetAudience":
                    where_clauses.append("target_audience = :ta")
                    params["ta"] = str(v)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        async with factory() as session:
            result = await session.execute(
                text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"), params
            )
            rows = result.fetchall()
            c_map = await self._fetch_children(session, [r.id for r in rows])
        return [self._map_to_schema(r, c_map[r.id]) for r in rows]

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
                        created_at, updated_at
                    ) VALUES (
                        :external_id, :title, :description, :image_url, :link_url,
                        :display_order, :start_date, :end_date,
                        :is_active, :is_published, :target_audience, :position,
                        :created_at, :updated_at
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
                    "is_active": int(bool((data.isActive if data.isActive is not None else True))),
                    "is_published": int(bool((data.isPublished if data.isPublished is not None else False))),
                    "target_audience": data.targetAudience,
                    "position": data.position,
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
        for k in ["title", "description", "imageUrl", "linkUrl", "displayOrder", "startDate", "endDate", "isActive", "isPublished", "targetAudience", "position"]:
            val = None
            match k:
                case "title": val = update_data.title if update_data.title is not None else existing.title
                case "description": val = update_data.description if update_data.description is not None else existing.description
                case "imageUrl": val = update_data.imageUrl if update_data.imageUrl is not None else existing.imageUrl
                case "linkUrl": val = update_data.linkUrl if update_data.linkUrl is not None else existing.linkUrl
                case "displayOrder": val = update_data.displayOrder if update_data.displayOrder is not None else existing.displayOrder
                case "startDate": val = update_data.startDate if update_data.startDate is not None else existing.startDate
                case "endDate": val = update_data.endDate if update_data.endDate is not None else existing.endDate
                case "isActive": val = update_data.isActive if update_data.isActive is not None else existing.isActive
                case "isPublished": val = update_data.isPublished if update_data.isPublished is not None else existing.isPublished
                case "targetAudience": val = update_data.targetAudience if update_data.targetAudience is not None else existing.targetAudience
                case "position": val = update_data.position if update_data.position is not None else existing.position
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
                    "updated_at": now,
                },
            )
            # Need to pass an object with userSegments and visibilityRules for _replace_children
            from app.models.daos import BannerChildrenData
            dummy_merged = BannerChildrenData(
                userSegments=update_data.userSegments if update_data.userSegments is not None else existing.userSegments,
                visibilityRules=update_data.visibilityRules if update_data.visibilityRules is not None else existing.visibilityRules
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

