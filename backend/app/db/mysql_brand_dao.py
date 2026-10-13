"""
MySQL DAO for sj_brands. Implements FileStorage-like interface for 'brands'.
"""

from app.models.schemas import BrandResponse
from app.models.daos import BrandInternalCreate, BrandInternalUpdate
from typing import List, Optional, Any

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc


class MySQLBrandDAO:
    @property
    def TABLE(self):
        return "sj_brands"

    async def findAll(
        self,
        id: Optional[int] = None,
        slug: Optional[str] = None,
        is_active: Optional[bool] = None,
        name: Optional[str] = None,
        show_in_mobile_homepage: Optional[bool] = None,
    ) -> List[BrandResponse]:
        async_session = get_async_session_factory()
            
        where_clauses = []
        params = {}
        if id is not None:
            where_clauses.append("id = :id")
            params["id"] = id
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
        
        async with async_session() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id AS _id, name, slug, image_url AS logo_url, show_in_mobile_homepage, is_active, created_at, updated_at
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
        id: Optional[int] = None,
        slug: Optional[str] = None,
        is_active: Optional[bool] = None,
        name: Optional[str] = None,
    ) -> Optional[BrandResponse]:
        records = await self.findAll(id=id, slug=slug, is_active=is_active, name=name)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[BrandResponse]:
        return await self.findOne(id=id)


    async def create(self, data: 'BrandInternalCreate') -> BrandResponse:
        async_session = get_async_session_factory()
        now = now_utc()
        async with async_session() as session:
            result = await session.execute(
                text(
                    """
                    INSERT INTO sj_brands (name, slug, image_url, show_in_mobile_homepage, is_active, created_at, updated_at)
                    VALUES (:name, :slug, :image_url, :show_in_mobile_homepage, :is_active, :created_at, :updated_at)
                    """
                ),
                {
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
            new_id = result.lastrowid
        return await self.findById(new_id)

    async def update(self, id: int, update_data: 'BrandInternalUpdate') -> Optional[BrandResponse]:
        if not id:
            return None
        async_session = get_async_session_factory()
        now = now_utc()
        
        updates = ["updated_at = :updated_at"]
        params = {"id": id, "updated_at": now}

        if "name" in update_data.model_fields_set:
            updates.append("name = :name")
            params["name"] = update_data.name
            if "slug" not in update_data.model_fields_set and update_data.name is not None:
                updates.append("slug = :slug")
                params["slug"] = update_data.name.lower().replace(" ", "-")

        if "slug" in update_data.model_fields_set:
            updates.append("slug = :slug")
            params["slug"] = update_data.slug

        if "logo_url" in update_data.model_fields_set:
            updates.append("image_url = :image_url")
            params["image_url"] = update_data.logo_url

        if "show_in_mobile_homepage" in update_data.model_fields_set:
            updates.append("show_in_mobile_homepage = :show_in_mobile_homepage")
            params["show_in_mobile_homepage"] = 1 if update_data.show_in_mobile_homepage else 0

        if "is_active" in update_data.model_fields_set:
            updates.append("is_active = :is_active")
            params["is_active"] = 1 if update_data.is_active else 0

        set_sql = ", ".join(updates)

        async with async_session() as session:
            result = await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
            if result.rowcount == 0:
                existing = await self.findById(id)
                if not existing:
                    return None
        return await self.findById(id)

    async def delete(self, id: int) -> bool:
        if not id:
            return False
        async_session = get_async_session_factory()
        bid = id
        async with async_session() as session:
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
        records = await self.findAll(is_active=is_active, name=name)
        return len(records)

    find_all = findAll
    find_by_id = findById
    find_one = findOne

