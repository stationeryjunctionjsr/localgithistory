"""
MySQL DAO for sj_brands. Implements FileStorage-like interface for 'brands'.
"""

from app.models.schemas import BrandResponse
from app.models.daos import BrandInternalCreate, BrandInternalUpdate
import secrets
from typing import Dict, List, Optional, Any

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc


class MySQLBrandDAO:
    @property
    def TABLE(self):
        return "sj_brands"

    def _factory(self):
        return get_async_session_factory()
    async def findAll(self, query: Optional[Dict] = None) -> List[BrandResponse]:
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
                elif k == "slug":
                    where_clauses.append("slug = :slug")
                    params["slug"] = v
                elif k == "is_active":
                    where_clauses.append("is_active = :is_active")
                    params["is_active"] = 1 if v else 0
                elif k == "name":
                    where_clauses.append("name = :name")
                    params["name"] = v
                elif k == "show_in_mobile_homepage":
                    where_clauses.append("show_in_mobile_homepage = :show_in_mobile_homepage")
                    params["show_in_mobile_homepage"] = 1 if v else 0
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id AS _id, external_id, name, slug, image_url AS logo_url, show_in_mobile_homepage, is_active, created_at, updated_at
                    FROM {self.TABLE}
                    WHERE {where_sql}
                    """
                ),
                params
            )
            rows = result.fetchall()
            
        return [BrandResponse.model_validate(r) for r in rows]


    async def findOne(self, query: Dict) -> Optional[BrandResponse]:
        docs = await self.findAll(query)
        return docs[0] if docs else None
    async def findById(self, id: str) -> Optional[BrandResponse]:
        factory = self._factory()
        if not factory:
            return None
        bid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id AS _id, external_id, name, slug, image_url AS logo_url, show_in_mobile_homepage, is_active, created_at, updated_at
                    FROM {self.TABLE} WHERE id = :id
                    """
                ),
                {"id": bid},
            )
            row = result.fetchone()
        return BrandResponse.model_validate(row) if row else None


    async def create(self, data: 'BrandInternalCreate') -> BrandResponse:
        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        now = now_utc()
        external_id = secrets.token_hex(16)
        async with factory() as session:
            await session.execute(
                text(
                    """
                    INSERT INTO sj_brands (external_id, name, slug, image_url, show_in_mobile_homepage, is_active, created_at, updated_at)
                    VALUES (:external_id, :name, :slug, :image_url, :show_in_mobile_homepage, :is_active, :created_at, :updated_at)
                    """
                ),
                {
                    "external_id": external_id,
                    "name": data.name,
                    "slug": data.name.lower().replace(" ", "-") if data.name else "",
                    "image_url": data.logoUrl,
                    "show_in_mobile_homepage": 1 if data.showInMobileHomepage else 0,
                    "is_active": 1 if (data.isActive if data.isActive is not None else True) else 0,
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

    async def update(self, id: str, update_data: 'BrandInternalUpdate') -> Optional[BrandResponse]:
        existing = await self.findById(id)
        if not existing:
            return None

        factory = self._factory()
        if not factory:
            return None
        now = now_utc()
        bid = int(id) if str(id).isdigit() else None
        
        updates = ["updated_at = :updated_at"]
        params = {"id": bid, "updated_at": now}

        if update_data.name is not None:
            updates.append("name = :name")
            params["name"] = update_data.name
            
            if update_data.slug is None:
                updates.append("slug = :slug")
                params["slug"] = update_data.name.lower().replace(" ", "-")

        if update_data.slug is not None:
            updates.append("slug = :slug")
            params["slug"] = update_data.slug
            
        if update_data.logoUrl is not None:
            updates.append("image_url = :image_url")
            params["image_url"] = update_data.logoUrl
            
        if update_data.showInMobileHomepage is not None:
            updates.append("show_in_mobile_homepage = :show_in_mobile_homepage")
            params["show_in_mobile_homepage"] = 1 if update_data.showInMobileHomepage else 0
            
        if update_data.isActive is not None:
            updates.append("is_active = :is_active")
            params["is_active"] = 1 if update_data.isActive else 0

        set_sql = ", ".join(updates)

        async with factory() as session:
            await session.execute(
                text(f"UPDATE sj_brands SET {set_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        bid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": bid},
            )
            await session.commit()
            return result.rowcount > 0

    async def deleteMany(self, query: Dict) -> BrandResponse:
        docs = await self.findAll(query)
        deleted = 0
        for d in docs:
            if await self.delete(d.id):
                deleted += 1
        return {"deletedCount": deleted}

    async def count(self, query: Optional[Dict] = None) -> int:
        docs = await self.findAll(query)
        return len(docs)

    find_all = findAll
    find_by_id = findById
    find_one = findOne

