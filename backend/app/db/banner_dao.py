"""
Oracle DAO for sj_banners. Implements FileStorage-like interface for 'banners'.

Note: many banner fields are stored as CLOB JSON columns (visibility_rules, user_segments) to match
the existing API shape.
"""

from app.config.settings import settings
import secrets
from typing import Dict, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.oracle_utils import json_dumps, json_loads, now_utc


class OracleBannerDAO:

    @property
    def TABLE(self):
        suffix = getattr(settings, 'table_suffix', '')
        return f"sj_banners{suffix}"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_doc(self, r) -> Dict:
        return {
            "_id": str(r.id),
            "title": r.title,
            "description": r.description,
            "imageUrl": r.image_url,
            "linkUrl": r.link_url,
            "displayOrder": int(r.display_order) if r.display_order is not None else 0,
            "startDate": r.start_date,
            "endDate": r.end_date,
            "isActive": bool(r.is_active) if r.is_active is not None else True,
            "isPublished": bool(r.is_published) if r.is_published is not None else True,
            "targetAudience": r.target_audience,
            "position": r.position,
            "userSegments": json_loads(r.user_segments) or [],
            "visibilityRules": json_loads(r.visibility_rules) or [],
            "createdAt": r.created_at.isoformat() if r.created_at else None,
            "updatedAt": r.updated_at.isoformat() if r.updated_at else None,
        }

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        factory = self._factory()
        if not factory:
            return []
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id, external_id, title, description, image_url, link_url, display_order,
                           start_date, end_date, is_active, is_published, target_audience, position,
                           user_segments, visibility_rules, created_at, updated_at
                    FROM {self.TABLE}
                    """
                )
            )
            rows = result.fetchall()
        docs = [self._row_to_doc(r) for r in rows]
        if not query:
            return docs
        filtered: List[Dict] = []
        for d in docs:
            match = True
            for k, v in query.items():
                if k in ("_id", "id"):
                    if str(d.get("_id")) != str(v):
                        match = False
                        break
                elif d.get(k) != v:
                    match = False
                    break
            if match:
                filtered.append(d)
        return filtered

    async def findOne(self, query: Dict) -> Optional[Dict]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        factory = self._factory()
        if not factory:
            return None
        bid = int(id) if str(id).isdigit() else 0
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id, external_id, title, description, image_url, link_url, display_order,
                           start_date, end_date, is_active, is_published, target_audience, position,
                           user_segments, visibility_rules, created_at, updated_at
                    FROM {self.TABLE} WHERE id = :id
                    """
                ),
                {"id": bid},
            )
            row = result.fetchone()
        return self._row_to_doc(row) if row else None

    async def create(self, data: Dict) -> Dict:
        factory = self._factory()
        if not factory:
            raise RuntimeError("Oracle not configured")
        now = now_utc()
        external_id = secrets.token_hex(16)
        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    INSERT INTO {self.TABLE} (
                        external_id, title, description, image_url, link_url, display_order,
                        start_date, end_date, is_active, is_published, target_audience, position,
                        user_segments, visibility_rules, created_at, updated_at
                    ) VALUES (
                        :external_id, :title, :description, :image_url, :link_url, :display_order,
                        :start_date, :end_date, :is_active, :is_published, :target_audience, :position,
                        :user_segments, :visibility_rules, :created_at, :updated_at
                    )
                    """
                ),
                {
                    "external_id": external_id,
                    "title": data.get("title"),
                    "description": data.get("description"),
                    "image_url": data.get("imageUrl"),
                    "link_url": data.get("linkUrl"),
                    "display_order": data.get("displayOrder", 0),
                    "start_date": data.get("startDate"),
                    "end_date": data.get("endDate"),
                    "is_active": 1 if data.get("isActive", True) else 0,
                    "is_published": 1 if data.get("isPublished", True) else 0,
                    "target_audience": data.get("targetAudience"),
                    "position": data.get("position"),
                    "user_segments": json_dumps(data.get("userSegments") or []),
                    "visibility_rules": json_dumps(data.get("visibilityRules") or []),
                    "created_at": now,
                    "updated_at": now,
                },
            )
            await session.commit()
            r = await session.execute(
                text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"),
                {"eid": external_id},
            )
            new_id = r.scalar()
        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: Dict) -> Optional[Dict]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = {**existing, **update_data}
        factory = self._factory()
        if not factory:
            return None
        now = now_utc()
        bid = int(id) if str(id).isdigit() else 0
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
                        user_segments = :user_segments,
                        visibility_rules = :visibility_rules,
                        updated_at = :updated_at
                    WHERE id = :id
                    """
                ),
                {
                    "id": bid,
                    "title": merged.get("title"),
                    "description": merged.get("description"),
                    "image_url": merged.get("imageUrl"),
                    "link_url": merged.get("linkUrl"),
                    "display_order": merged.get("displayOrder", 0),
                    "start_date": merged.get("startDate"),
                    "end_date": merged.get("endDate"),
                    "is_active": 1 if merged.get("isActive", True) else 0,
                    "is_published": 1 if merged.get("isPublished", True) else 0,
                    "target_audience": merged.get("targetAudience"),
                    "position": merged.get("position"),
                    "user_segments": json_dumps(merged.get("userSegments") or []),
                    "visibility_rules": json_dumps(merged.get("visibilityRules") or []),
                    "updated_at": now,
                },
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        bid = int(id) if str(id).isdigit() else 0
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": bid},
            )
            await session.commit()
            return result.rowcount > 0

    async def deleteMany(self, query: Dict) -> Dict:
        docs = await self.findAll(query)
        deleted = 0
        for d in docs:
            if await self.delete(d.get("_id")):
                deleted += 1
        return {"deletedCount": deleted}

    async def count(self, query: Optional[Dict] = None) -> int:
        docs = await self.findAll(query)
        return len(docs)

    find_all = findAll
    find_by_id = findById
    find_one = findOne
