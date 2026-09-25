from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import secrets
import json
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import SearchTagInternal
from app.models.daos_flat import SearchTagInternalCreate, SearchTagInternalUpdate

def now_utc():
    return datetime.now(timezone.utc)

class MySQLSearchTagsDAO:
    def __init__(self):
        self.table_name = "sj_search_tags"
    
    @property
    def TABLE(self):
        from app.config.settings import settings
        return "{self.table_name}"

    def _factory(self):
        return get_async_session_factory()
        
    async def findById(self, id: str) -> Optional[Any]:
        return await self.findOne({"_id": id})

    async def findOne(self, query=None, **kwargs) -> Optional[Any]:
        if query:
            kwargs.update(query)
        if not kwargs:
            return None
        
        async with self._factory()() as session:
            conditions = []
            params = {}
            
            query_map = {'tagId': 'tag_id', 'name': 'name', 'type': 'type', 'isActive': 'is_active'}
            query_map["_id"] = "id"
            query_map["externalId"] = "external_id"
            
            for k, v in kwargs.items():
                db_col = query_map[k] if k in query_map else k
                conditions.append(f"{db_col} = :{k}")
                params[k] = v
                
            where_clause = " AND ".join(conditions)
            q = text(f"SELECT * FROM {self.TABLE} WHERE {where_clause} LIMIT 1")
            result = await session.execute(q, params)
            row = result.fetchone()
            if not row:
                return None
                
            children_map = await self._fetch_children(session, [int(row.id)]) if True else {}
            return self._map_to_schema(row, children_map.get(int(row.id), {}))
            
    async def findAll(self, query: Optional[Dict[str, Any]] = None) -> List[Any]:
        query = query or {}
        async with self._factory()() as session:
            sql = f"SELECT * FROM {self.TABLE}"
            params = {}
            
            query_map = {'tagId': 'tag_id', 'name': 'name', 'type': 'type', 'isActive': 'is_active'}
            query_map["_id"] = "id"
            query_map["externalId"] = "external_id"
            
            if query:
                conditions = []
                for k, v in query.items():
                    db_col = query_map[k] if k in query_map else k
                    conditions.append(f"{db_col} = :{k}")
                    params[k] = v
                if conditions:
                    sql += " WHERE " + " AND ".join(conditions)
                    
            q = text(sql)
            result = await session.execute(q, params)
            rows = result.fetchall()
            
            if not rows:
                return []
                
            children_map = await self._fetch_children(session, [int(r.id) for r in rows]) if True else {}
            
            return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]

    async def create(self, data: Any) -> Any:
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        params = {"eid": external_id, "c": now, "u": now}

        if data.tagId is not None:
            cols.append("tag_id")
            params["s_tagId"] = data.tagId

        if data.name is not None:
            cols.append("name")
            params["s_name"] = data.name

        if data.type is not None:
            cols.append("type")
            params["s_type"] = data.type

        if data.isActive is not None:
            cols.append("is_active")
            params["s_isActive"] = data.isActive

        col_sql = ", ".join(cols)
        val_sql = ", ".join([":eid", ":c", ":u"] + [f":s_{k}" for k in ['tagId', 'name', 'type', 'isActive'] if f"s_{k}" in params] + [f":c_{k}" for k in [] if f"c_{k}" in params])
        
        async with factory() as session:
            await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = (
                await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": external_id}
                )
            ).scalar()
            await self._replace_children(session, new_id, data)
            await session.commit()
            
        return await self.findById(str(new_id))

    async def update(self, id: str, data: Any) -> Any:
        factory = self._factory()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now_utc()}

        if data.tagId is not None:
            updates.append("tag_id = :s_tagId")
            params["s_tagId"] = data.tagId

        if data.name is not None:
            updates.append("name = :s_name")
            params["s_name"] = data.name

        if data.type is not None:
            updates.append("type = :s_type")
            params["s_type"] = data.type

        if data.isActive is not None:
            updates.append("is_active = :s_isActive")
            params["s_isActive"] = data.isActive

        if len(updates) > 1:
            upd_sql = ", ".join(updates)
            async with factory() as session:
                await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE id = :id"), params)
                await self._replace_children(session, int(id), data)
                await session.commit()
        else:
            async with factory() as session:
                await self._replace_children(session, int(id), data)
                await session.commit()
                
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        pk = int(id) if str(id).isdigit() else None
        async with factory() as session:

            await session.execute(text(f"DELETE FROM sj_search_tag_categories WHERE parent_id = :id"), {"id": pk})

            await session.execute(text(f"DELETE FROM sj_search_tag_subcats WHERE parent_id = :id"), {"id": pk})

            await session.execute(text(f"DELETE FROM sj_search_tag_brands WHERE parent_id = :id"), {"id": pk})

            await session.execute(text(f"DELETE FROM sj_search_tag_collections WHERE parent_id = :id"), {"id": pk})

            await session.execute(text(f"DELETE FROM sj_search_tag_products WHERE parent_id = :id"), {"id": pk})

            await session.execute(text(f"DELETE FROM sj_search_tag_ex_products WHERE parent_id = :id"), {"id": pk})

            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pk},
            )
            await session.commit()
            return result.rowcount > 0

    async def deleteMany(self, query: Dict) -> Any:
        docs = await self.findAll(query)
        deleted = 0
        for d in docs:
            # Depending on schema format, id might be _id or id
            d_id = d.id
            if d_id and await self.delete(d_id):
                deleted += 1
        return {"deletedCount": deleted}

    def _map_to_schema(self, r, children: Dict) -> Any:
        rm = r._mapping
        out = {
            "_id": str(rm["id"]), 
            "externalId": rm["external_id"]
        }
        
        created_at = rm["created_at"]
        if created_at:
            out["createdAt"] = created_at.isoformat()
            
        updated_at = rm["updated_at"]
        if updated_at:
            out["updatedAt"] = updated_at.isoformat()

        out["tagId"] = rm["tag_id"]
        out["name"] = rm["name"]
        out["type"] = rm["type"]
        out["isActive"] = bool(rm["is_active"]) if rm["is_active"] is not None else None
        for k, v in children.items():
            out[k] = v
            
        return SearchTagInternal(**out)

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:
        c_map = {rid: {} for rid in ids}
        if not ids:
            return c_map
            
        id_list = ",".join(map(str, ids))

        q_categories = text(f"SELECT parent_id, category FROM sj_search_tag_categories WHERE parent_id IN ({id_list})")
        res_categories = await session.execute(q_categories)
        rows_categories = res_categories.fetchall()

        for r in rows_categories:
            if "categories" not in c_map[r.parent_id]:
                c_map[r.parent_id]["categories"] = []
            c_map[r.parent_id]["categories"].append(r[1])

        q_subCategories = text(f"SELECT parent_id, sub_category FROM sj_search_tag_subcats WHERE parent_id IN ({id_list})")
        res_subCategories = await session.execute(q_subCategories)
        rows_subCategories = res_subCategories.fetchall()

        for r in rows_subCategories:
            if "subCategories" not in c_map[r.parent_id]:
                c_map[r.parent_id]["subCategories"] = []
            c_map[r.parent_id]["subCategories"].append(r[1])

        q_brands = text(f"SELECT parent_id, brand FROM sj_search_tag_brands WHERE parent_id IN ({id_list})")
        res_brands = await session.execute(q_brands)
        rows_brands = res_brands.fetchall()

        for r in rows_brands:
            if "brands" not in c_map[r.parent_id]:
                c_map[r.parent_id]["brands"] = []
            c_map[r.parent_id]["brands"].append(r[1])

        q_collections = text(f"SELECT parent_id, collection FROM sj_search_tag_collections WHERE parent_id IN ({id_list})")
        res_collections = await session.execute(q_collections)
        rows_collections = res_collections.fetchall()

        for r in rows_collections:
            if "collections" not in c_map[r.parent_id]:
                c_map[r.parent_id]["collections"] = []
            c_map[r.parent_id]["collections"].append(r[1])

        q_productIds = text(f"SELECT parent_id, product_id FROM sj_search_tag_products WHERE parent_id IN ({id_list})")
        res_productIds = await session.execute(q_productIds)
        rows_productIds = res_productIds.fetchall()

        for r in rows_productIds:
            if "productIds" not in c_map[r.parent_id]:
                c_map[r.parent_id]["productIds"] = []
            c_map[r.parent_id]["productIds"].append(r[1])

        q_excludedProductIds = text(f"SELECT parent_id, product_id FROM sj_search_tag_ex_products WHERE parent_id IN ({id_list})")
        res_excludedProductIds = await session.execute(q_excludedProductIds)
        rows_excludedProductIds = res_excludedProductIds.fetchall()

        for r in rows_excludedProductIds:
            if "excludedProductIds" not in c_map[r.parent_id]:
                c_map[r.parent_id]["excludedProductIds"] = []
            c_map[r.parent_id]["excludedProductIds"].append(r[1])

        return c_map

    async def _replace_children(self, session, row_id: int, data: Any):

        if data.categories is not None:
            await session.execute(text(f"DELETE FROM sj_search_tag_categories WHERE parent_id = :id"), {"id": row_id})
            child_list = data.categories or []

            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_search_tag_categories (parent_id, category) VALUES (:id, :v)"), {"id": row_id, "v": item})

        if data.subCategories is not None:
            await session.execute(text(f"DELETE FROM sj_search_tag_subcats WHERE parent_id = :id"), {"id": row_id})
            child_list = data.subCategories or []

            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_search_tag_subcats (parent_id, sub_category) VALUES (:id, :v)"), {"id": row_id, "v": item})

        if data.brands is not None:
            await session.execute(text(f"DELETE FROM sj_search_tag_brands WHERE parent_id = :id"), {"id": row_id})
            child_list = data.brands or []

            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_search_tag_brands (parent_id, brand) VALUES (:id, :v)"), {"id": row_id, "v": item})

        if data.collections is not None:
            await session.execute(text(f"DELETE FROM sj_search_tag_collections WHERE parent_id = :id"), {"id": row_id})
            child_list = data.collections or []

            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_search_tag_collections (parent_id, collection) VALUES (:id, :v)"), {"id": row_id, "v": item})

        if data.productIds is not None:
            await session.execute(text(f"DELETE FROM sj_search_tag_products WHERE parent_id = :id"), {"id": row_id})
            child_list = data.productIds or []

            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_search_tag_products (parent_id, product_id) VALUES (:id, :v)"), {"id": row_id, "v": item})

        if data.excludedProductIds is not None:
            await session.execute(text(f"DELETE FROM sj_search_tag_ex_products WHERE parent_id = :id"), {"id": row_id})
            child_list = data.excludedProductIds or []

            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_search_tag_ex_products (parent_id, product_id) VALUES (:id, :v)"), {"id": row_id, "v": item})
