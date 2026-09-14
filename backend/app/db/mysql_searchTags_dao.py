import logging
import secrets
from typing import Dict, List, Optional
from datetime import datetime

from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc
from app.models.schemas import SearchTagResponse

logger = logging.getLogger(__name__)

class MySQLSearchtagsDAO:
    TABLE = "sj_search_tags"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_obj(self, row, child_map: dict) -> SearchTagResponse:
        data = {
            "id": row.tag_id,
            "_id": str(row.tag_id),
            "tagId": row.tag_id,
            "name": row.name,
            "type": row.type,
            "isActive": bool(row.is_active) if row.is_active is not None else False,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        }
        
        # Child tables
        data["categories"] = child_map.get("categories", [])
        data["subCategories"] = child_map.get("subCategories", [])
        data["brands"] = child_map.get("brands", [])
        data["collections"] = child_map.get("collections", [])
        data["productIds"] = child_map.get("productIds", [])
        data["excludedProductIds"] = child_map.get("excludedProductIds", [])
        
        return SearchTagResponse.model_validate(data)

    async def _fetch_children(self, session, tag_ids: List[str]) -> Dict[str, dict]:
        if not tag_ids:
            return {}
        
        children = {tid: {
            "categories": [], "subCategories": [], "brands": [], 
            "collections": [], "productIds": [], "excludedProductIds": []
        } for tid in tag_ids}
        
        params = {"tag_ids": tuple(tag_ids)}
        
        cat_rows = (await session.execute(text("SELECT tag_id, category FROM sj_search_tag_categories WHERE tag_id IN :tag_ids"), params)).fetchall()
        for r in cat_rows: children[str(r.tag_id)]["categories"].append(r.category)
            
        sub_rows = (await session.execute(text("SELECT tag_id, sub_category FROM sj_search_tag_subcats WHERE tag_id IN :tag_ids"), params)).fetchall()
        for r in sub_rows: children[str(r.tag_id)]["subCategories"].append(r.sub_category)
            
        brand_rows = (await session.execute(text("SELECT tag_id, brand FROM sj_search_tag_brands WHERE tag_id IN :tag_ids"), params)).fetchall()
        for r in brand_rows: children[str(r.tag_id)]["brands"].append(r.brand)
            
        col_rows = (await session.execute(text("SELECT tag_id, collection FROM sj_search_tag_collections WHERE tag_id IN :tag_ids"), params)).fetchall()
        for r in col_rows: children[str(r.tag_id)]["collections"].append(r.collection)
            
        prod_rows = (await session.execute(text("SELECT tag_id, product_id FROM sj_search_tag_products WHERE tag_id IN :tag_ids"), params)).fetchall()
        for r in prod_rows: children[str(r.tag_id)]["productIds"].append(r.product_id)
            
        ex_prod_rows = (await session.execute(text("SELECT tag_id, product_id FROM sj_search_tag_ex_products WHERE tag_id IN :tag_ids"), params)).fetchall()
        for r in ex_prod_rows: children[str(r.tag_id)]["excludedProductIds"].append(r.product_id)
            
        return children

    async def findAll(self, query: Optional[Dict] = None) -> List[SearchTagResponse]:
        query = query or {}
        where_clauses = []
        params = {}
        
        if "isActive" in query:
            where_clauses.append("is_active = :isActive")
            params["isActive"] = query["isActive"]
        if "type" in query:
            where_clauses.append("type = :type")
            params["type"] = query["type"]
            
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        factory = self._factory()
        async with factory() as session:
            rows = (await session.execute(text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY tag_id ASC"), params)).fetchall()
            if not rows:
                return []
                
            tag_ids = [str(r.tag_id) for r in rows]
            children_map = await self._fetch_children(session, tag_ids)
            
        return [self._row_to_obj(r, children_map.get(str(r.tag_id), {})) for r in rows]

    async def findOne(self, query: Dict) -> Optional[SearchTagResponse]:
        if "_id" in query:
            return await self.findById(query["_id"])
        if "tagId" in query:
            return await self.findById(query["tagId"])
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[SearchTagResponse]:
        factory = self._factory()
        async with factory() as session:
            row = (await session.execute(text(f"SELECT * FROM {self.TABLE} WHERE tag_id = :id"), {"id": id})).fetchone()
            if not row:
                return None
            children_map = await self._fetch_children(session, [str(row.tag_id)])
            
        return self._row_to_obj(row, children_map.get(str(row.tag_id), {}))

    async def create(self, data) -> SearchTagResponse:
        try:
            tag_id = data.tagId
            if not tag_id:
                tag_id = secrets.token_hex(12)
        except AttributeError:
            tag_id = secrets.token_hex(12)
            
        created_at = now_utc()
        
        factory = self._factory()
        async with factory() as session:
            await session.execute(
                text(
                    f"INSERT INTO {self.TABLE} (tag_id, name, type, is_active, created_at, updated_at) "
                    "VALUES (:tag_id, :name, :type, :is_active, :created_at, :updated_at)"
                ),
                {
                    "tag_id": tag_id,
                    "name": data.name,
                    "type": data.type,
                    "is_active": data.isActive,
                    "created_at": created_at,
                    "updated_at": created_at
                }
            )
            
            try:
                if data.categories is not None:
                    for item in data.categories:
                        await session.execute(text("INSERT INTO sj_search_tag_categories (tag_id, category) VALUES (:tag_id, :item)"), {"tag_id": tag_id, "item": item})
            except AttributeError: pass
                
            try:
                if data.subCategories is not None:
                    for item in data.subCategories:
                        await session.execute(text("INSERT INTO sj_search_tag_subcats (tag_id, sub_category) VALUES (:tag_id, :item)"), {"tag_id": tag_id, "item": item})
            except AttributeError: pass
            
            try:
                if data.brands is not None:
                    for item in data.brands:
                        await session.execute(text("INSERT INTO sj_search_tag_brands (tag_id, brand) VALUES (:tag_id, :item)"), {"tag_id": tag_id, "item": item})
            except AttributeError: pass
            
            try:
                if data.collections is not None:
                    for item in data.collections:
                        await session.execute(text("INSERT INTO sj_search_tag_collections (tag_id, collection) VALUES (:tag_id, :item)"), {"tag_id": tag_id, "item": item})
            except AttributeError: pass
            
            try:
                if data.productIds is not None:
                    for item in data.productIds:
                        await session.execute(text("INSERT INTO sj_search_tag_products (tag_id, product_id) VALUES (:tag_id, :item)"), {"tag_id": tag_id, "item": item})
            except AttributeError: pass
            
            try:
                if data.excludedProductIds is not None:
                    for item in data.excludedProductIds:
                        await session.execute(text("INSERT INTO sj_search_tag_ex_products (tag_id, product_id) VALUES (:tag_id, :item)"), {"tag_id": tag_id, "item": item})
            except AttributeError: pass
            
            await session.commit()
            
        return await self.findById(tag_id)

    async def update(self, id: str, data) -> Optional[SearchTagResponse]:
        factory = self._factory()
        updated_at = now_utc()
        
        async with factory() as session:
            row = (await session.execute(text(f"SELECT tag_id FROM {self.TABLE} WHERE tag_id = :id"), {"id": id})).fetchone()
            if not row:
                return None
                
            updates = []
            params = {"id": id, "updated_at": updated_at}
            
            try:
                if data.name is not None:
                    updates.append("name = :name")
                    params["name"] = data.name
            except AttributeError: pass
            
            try:
                if data.type is not None:
                    updates.append("type = :type")
                    params["type"] = data.type
            except AttributeError: pass
            
            try:
                if data.isActive is not None:
                    updates.append("is_active = :is_active")
                    params["is_active"] = data.isActive
            except AttributeError: pass
            
            if updates:
                updates.append("updated_at = :updated_at")
                set_clause = ", ".join(updates)
                await session.execute(
                    text(f"UPDATE {self.TABLE} SET {set_clause} WHERE tag_id = :id"),
                    params
                )
                
            try:
                if data.categories is not None:
                    await session.execute(text("DELETE FROM sj_search_tag_categories WHERE tag_id = :id"), {"id": id})
                    for item in data.categories:
                        await session.execute(text("INSERT INTO sj_search_tag_categories (tag_id, category) VALUES (:id, :item)"), {"id": id, "item": item})
            except AttributeError: pass
            
            try:
                if data.subCategories is not None:
                    await session.execute(text("DELETE FROM sj_search_tag_subcats WHERE tag_id = :id"), {"id": id})
                    for item in data.subCategories:
                        await session.execute(text("INSERT INTO sj_search_tag_subcats (tag_id, sub_category) VALUES (:id, :item)"), {"id": id, "item": item})
            except AttributeError: pass
            
            try:
                if data.brands is not None:
                    await session.execute(text("DELETE FROM sj_search_tag_brands WHERE tag_id = :id"), {"id": id})
                    for item in data.brands:
                        await session.execute(text("INSERT INTO sj_search_tag_brands (tag_id, brand) VALUES (:id, :item)"), {"id": id, "item": item})
            except AttributeError: pass
            
            try:
                if data.collections is not None:
                    await session.execute(text("DELETE FROM sj_search_tag_collections WHERE tag_id = :id"), {"id": id})
                    for item in data.collections:
                        await session.execute(text("INSERT INTO sj_search_tag_collections (tag_id, collection) VALUES (:id, :item)"), {"id": id, "item": item})
            except AttributeError: pass
            
            try:
                if data.productIds is not None:
                    await session.execute(text("DELETE FROM sj_search_tag_products WHERE tag_id = :id"), {"id": id})
                    for item in data.productIds:
                        await session.execute(text("INSERT INTO sj_search_tag_products (tag_id, product_id) VALUES (:id, :item)"), {"id": id, "item": item})
            except AttributeError: pass
            
            try:
                if data.excludedProductIds is not None:
                    await session.execute(text("DELETE FROM sj_search_tag_ex_products WHERE tag_id = :id"), {"id": id})
                    for item in data.excludedProductIds:
                        await session.execute(text("INSERT INTO sj_search_tag_ex_products (tag_id, product_id) VALUES (:id, :item)"), {"id": id, "item": item})
            except AttributeError: pass
            
            await session.commit()
            
        return await self.findById(id)
        
    async def delete(self, id: str) -> bool:
        factory = self._factory()
        async with factory() as session:
            await session.execute(text("DELETE FROM sj_search_tag_categories WHERE tag_id = :id"), {"id": id})
            await session.execute(text("DELETE FROM sj_search_tag_subcats WHERE tag_id = :id"), {"id": id})
            await session.execute(text("DELETE FROM sj_search_tag_brands WHERE tag_id = :id"), {"id": id})
            await session.execute(text("DELETE FROM sj_search_tag_collections WHERE tag_id = :id"), {"id": id})
            await session.execute(text("DELETE FROM sj_search_tag_products WHERE tag_id = :id"), {"id": id})
            await session.execute(text("DELETE FROM sj_search_tag_ex_products WHERE tag_id = :id"), {"id": id})
            
            res = await session.execute(text(f"DELETE FROM {self.TABLE} WHERE tag_id = :id"), {"id": id})
            await session.commit()
            return res.rowcount > 0
