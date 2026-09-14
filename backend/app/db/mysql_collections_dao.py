"""
MySQL DAO for sj_collections.
"""

import secrets
from typing import Dict, List, Optional, Any
from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc
from app.models.schemas import CollectionResponse

class MySQLCollectionsDAO:
    @property
    def TABLE(self):
        suffix = (settings.table_suffix if settings.table_suffix is not None else "")
        return f"sj_collections{suffix}"
        
    @property
    def PRODUCTS_TABLE(self):
        suffix = (settings.table_suffix if settings.table_suffix is not None else "")
        return f"sj_collection_products{suffix}"

    def _factory(self):
        return get_async_session_factory()

    async def findAll(self, query: Optional[Dict] = None) -> List[CollectionResponse]:
        factory = self._factory()
        if not factory:
            return []
            
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id, external_id, name, description, slug, is_active, banner_image, thumbnail_image, display_order, created_at, updated_at
                    FROM {self.TABLE}
                    """
                )
            )
            rows = result.fetchall()
            
            prod_result = await session.execute(
                text(f"SELECT collection_id, product_id FROM {self.PRODUCTS_TABLE}")
            )
            prod_rows = prod_result.fetchall()
            
        prod_map = {}
        for pr in prod_rows:
            cid = str(pr.collection_id)
            if cid not in prod_map:
                prod_map[cid] = []
            prod_map[cid].append(str(pr.product_id))
            
        docs = []
        for r in rows:
            c_id = str(r.id)
            p_ids = prod_map.get(c_id, [])
            docs.append(CollectionResponse(**{
                "_id": c_id,
                "name": r.name,
                "description": r.description,
                "slug": r.slug,
                "isActive": bool(r.is_active) if r.is_active is not None else True,
                "bannerImage": r.banner_image,
                "thumbnailImage": r.thumbnail_image,
                "displayOrder": r.display_order,
                "productIds": p_ids,
                "createdAt": r.created_at.isoformat() if r.created_at else None,
                "updatedAt": r.updated_at.isoformat() if r.updated_at else None,
            }))
            
        if not query:
            return docs
            
        filtered: List[CollectionResponse] = []
        for d in docs:
            match = True
            for k, v in query.items():
                if k in ("_id", "id"):
                    if str(d.id) != str(v):
                        match = False
                        break
                elif k == "name" and d.name != v:
                    match = False
                    break
                elif k == "slug" and d.slug != v:
                    match = False
                    break
                elif k == "isActive" and d.isActive != v:
                    match = False
                    break
                elif k == "displayOrder" and d.displayOrder != v:
                    match = False
                    break
            if match:
                filtered.append(d)
        return filtered

    async def findOne(self, query: Dict) -> Optional[CollectionResponse]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[CollectionResponse]:
        factory = self._factory()
        if not factory:
            return None
        cid = int(id) if str(id).isdigit() else None
        
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id, external_id, name, description, slug, is_active, banner_image, thumbnail_image, display_order, created_at, updated_at
                    FROM {self.TABLE} WHERE id = :id
                    """
                ),
                {"id": cid},
            )
            row = result.fetchone()
            if not row:
                return None
                
            prod_result = await session.execute(
                text(f"SELECT product_id FROM {self.PRODUCTS_TABLE} WHERE collection_id = :cid"),
                {"cid": cid}
            )
            prod_rows = prod_result.fetchall()
            p_ids = [str(pr.product_id) for pr in prod_rows]
            
        return CollectionResponse(**{
            "_id": str(row.id),
            "name": row.name,
            "description": row.description,
            "slug": row.slug,
            "isActive": bool(row.is_active) if row.is_active is not None else True,
            "bannerImage": row.banner_image,
            "thumbnailImage": row.thumbnail_image,
            "displayOrder": row.display_order,
            "productIds": p_ids,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        })

    async def create(self, data: Any) -> CollectionResponse:
        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    INSERT INTO {self.TABLE} (
                        external_id, name, description, slug, is_active, banner_image, thumbnail_image, display_order, created_at, updated_at
                    ) VALUES (
                        :external_id, :name, :description, :slug, :is_active, :banner_image, :thumbnail_image, :display_order, :created_at, :updated_at
                    )
                    """
                ),
                {
                    "external_id": external_id,
                    "name": data.name,
                    "description": data.description,
                    "slug": data.slug,
                    "is_active": 1 if data.isActive else 0,
                    "banner_image": data.bannerImage,
                    "thumbnail_image": data.thumbnailImage,
                    "display_order": data.displayOrder,
                    "created_at": now,
                    "updated_at": now,
                }
            )
            await session.commit()
            
            r = await session.execute(
                text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"),
                {"eid": external_id},
            )
            new_id = r.scalar()
            
            productIds = data.productIds
            if productIds:
                for pid in productIds:
                    await session.execute(
                        text(f"INSERT INTO {self.PRODUCTS_TABLE} (collection_id, product_id) VALUES (:cid, :pid)"),
                        {"cid": new_id, "pid": pid}
                    )
                await session.commit()
                
        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: Any) -> Optional[CollectionResponse]:
        existing = await self.findById(id)
        if not existing:
            return None
            
        factory = self._factory()
        if not factory:
            return None
        now = now_utc()
        cid = int(id) if str(id).isdigit() else None
        
        upd_name = update_data.name if update_data.name is not None else existing.name
        upd_description = update_data.description if update_data.description is not None else existing.description
        upd_slug = update_data.slug if update_data.slug is not None else existing.slug
        upd_isActive = update_data.isActive if update_data.isActive is not None else existing.isActive
        upd_bannerImage = update_data.bannerImage if update_data.bannerImage is not None else existing.bannerImage
        upd_thumbnailImage = update_data.thumbnailImage if update_data.thumbnailImage is not None else existing.thumbnailImage
        upd_displayOrder = update_data.displayOrder if update_data.displayOrder is not None else existing.displayOrder
        
        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    UPDATE {self.TABLE} SET
                        name = :name,
                        description = :description,
                        slug = :slug,
                        is_active = :is_active,
                        banner_image = :banner_image,
                        thumbnail_image = :thumbnail_image,
                        display_order = :display_order,
                        updated_at = :updated_at
                    WHERE id = :id
                    """
                ),
                {
                    "id": cid,
                    "name": upd_name,
                    "description": upd_description,
                    "slug": upd_slug,
                    "is_active": 1 if upd_isActive else 0,
                    "banner_image": upd_bannerImage,
                    "thumbnail_image": upd_thumbnailImage,
                    "display_order": upd_displayOrder,
                    "updated_at": now,
                }
            )
            
            if update_data.productIds is not None:
                await session.execute(
                    text(f"DELETE FROM {self.PRODUCTS_TABLE} WHERE collection_id = :cid"),
                    {"cid": cid}
                )
                for pid in update_data.productIds:
                    await session.execute(
                        text(f"INSERT INTO {self.PRODUCTS_TABLE} (collection_id, product_id) VALUES (:cid, :pid)"),
                        {"cid": cid, "pid": pid}
                    )
                    
            await session.commit()
            
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        cid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            await session.execute(
                text(f"DELETE FROM {self.PRODUCTS_TABLE} WHERE collection_id = :cid"),
                {"cid": cid}
            )
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": cid},
            )
            await session.commit()
            return result.rowcount > 0

    async def deleteMany(self, query: Dict) -> Dict:
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
