"""
MySQL DAO for sj_brands. Implements FileStorage-like interface for 'brands'.
"""

from app.models.schemas import BrandResponse
from app.models.daos import BrandInternalCreate, BrandInternalUpdate
import secrets
from typing import List, Optional, Union, Any

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

    async def findAll(
        self,
        id: Optional[Union[int, str]] = None,
        slug: Optional[str] = None,
        is_active: Optional[bool] = None,
        name: Optional[str] = None,
        show_in_mobile_homepage: Optional[bool] = None,
    ) -> List[BrandResponse]:
        factory = self._factory()
        if not factory:
            return []
            
        where_clauses = []
        params = {}
        if id is not None:
            where_clauses.append("id = :id")
            params["id"] = int(id) if str(id).isdigit() else None
        if slug is not None:
            where_clauses.append("slug = :slug")
            params["slug"] = slug
        if is_active is not None:
            where_clauses.append("is_active = :is_active")
            params["is_active"] = 1 if is_active else 0
        if name is not None:
            where_clauses.append("name = :name")
            params["name"] = name
        if show_in_mobile_homepage is not None:
            where_clauses.append("show_in_mobile_homepage = :show_in_mobile_homepage")
            params["show_in_mobile_homepage"] = 1 if show_in_mobile_homepage else 0
        
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

    async def findOne(
        self,
        id: Optional[Union[int, str]] = None,
        slug: Optional[str] = None,
        is_active: Optional[bool] = None,
        name: Optional[str] = None,
    ) -> Optional[BrandResponse]:
        docs = await self.findAll(id=id, slug=slug, is_active=is_active, name=name)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[BrandResponse]:
        return await self.findOne(id=id)


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
                    "is_active": 1 if (data.is_active if data.is_active is not None else True) else 0,
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
            
        if update_data.is_active is not None:
            updates.append("is_active = :is_active")
            params["is_active"] = 1 if update_data.is_active else 0

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

    async def count(
        self,
        is_active: Optional[bool] = None,
        name: Optional[str] = None,
    ) -> int:
        docs = await self.findAll(is_active=is_active, name=name)
        return len(docs)

    find_all = findAll
    find_by_id = findById
    find_one = findOne

