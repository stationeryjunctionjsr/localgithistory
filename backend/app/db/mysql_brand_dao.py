"""
MySQL DAO for sj_brands. Implements FileStorage-like interface for 'brands'.
"""

import secrets
from typing import Dict, List, Optional, Any

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc
from app.models.brand import Brand


class MySQLBrandDAO:
    @property
    def TABLE(self):
        suffix = (settings.table_suffix if settings.table_suffix is not None else "")
        return f"sj_brands{suffix}"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_dict(self, r) -> BrandResponse:
        return BrandResponse(**{
            "_id": str(r.id),
            "name": r.name,
            "slug": r.slug,
            "logoUrl": r.image_url,
            "showInMobileHomepage": bool((r.show_in_mobile_homepage if r.show_in_mobile_homepage is not None else False)),
            "isActive": bool(r.is_active) if r.is_active is not None else True,
            "createdAt": r.created_at.isoformat() if r.created_at else None,
            "updatedAt": r.updated_at.isoformat() if r.updated_at else None,
        })


    async def findAll(self, query: Optional[Dict] = None) -> List[BrandResponse]:
        factory = self._factory()
        if not factory:
            return []
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id, external_id, name, slug, image_url, is_active, created_at, updated_at
                    FROM {self.TABLE}
                    """
                )
            )
            rows = result.fetchall()
        docs = [Brand.model_validate(self._row_to_dict(r)) for r in rows]
        if not query:
            return docs
        filtered: List[Dict] = []
        for d in docs:
            match = True
            for k, v in query.items():
                if k in ("_id", "id"):
                    if str(d._id) != str(v):
                        match = False
                        break
                elif d.get(k) != v:
                    match = False
                    break
            if match:
                filtered.append(d)
        return filtered

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
                    SELECT id, external_id, name, slug, image_url, is_active, created_at, updated_at
                    FROM {self.TABLE} WHERE id = :id
                    """
                ),
                {"id": bid},
            )
            row = result.fetchone()
        return self._row_to_dict(row) if row else None

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
                    INSERT INTO sj_brands (external_id, name, slug, image_url, is_active, created_at, updated_at)
                    VALUES (:external_id, :name, :slug, :image_url, :is_active, :created_at, :updated_at)
                    """
                ),
                {
                    "external_id": external_id,
                    "name": data.name,
                    "slug": data.name.lower().replace(" ", "-") if data.name else "",
                    "image_url": data.logoUrl or data.imageUrl,
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
        from app.models.daos import BrandInternalUpdate
        existing_dict = existing.model_dump(exclude_unset=True)
        update_dict = update_data.model_dump(exclude_unset=True)
        merged_dict = {**existing_dict, **update_dict}
        merged = BrandInternalUpdate(**merged_dict)
        factory = self._factory()
        if not factory:
            return None
        now = now_utc()
        bid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            await session.execute(
                text(
                    """
                    UPDATE sj_brands SET
                        name = :name,
                        slug = :slug,
                        image_url = :image_url,
                        is_active = :is_active,
                        updated_at = :updated_at
                    WHERE id = :id
                    """
                ),
                {
                    "id": bid,
                    "name": merged.name,
                    "slug": merged.slug,
                    "image_url": merged.logoUrl or merged.imageUrl,
                    "is_active": 1 if (merged.isActive if merged.isActive is not None else True) else 0,
                    "updated_at": now,
                },
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
            if await self.delete(d._id):
                deleted += 1
        return {"deletedCount": deleted}

    async def count(self, query: Optional[Dict] = None) -> int:
        docs = await self.findAll(query)
        return len(docs)

    find_all = findAll
    find_by_id = findById
    find_one = findOne

