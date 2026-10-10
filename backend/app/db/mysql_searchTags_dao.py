from typing import Optional, Dict, List, Any, Union
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
        return self.table_name

    def _factory(self):
        return get_async_session_factory()
        
    async def findById(self, id: Union[int, str]) -> Optional['SearchTagInternal']:
        factory = self._factory()
        if not factory or not id:
            return None
        async with factory() as session:
            if str(id).isdigit():
                q = text(f"SELECT * FROM {self.TABLE} WHERE id = :id LIMIT 1")
                params = {"id": int(id)}
            else:
                q = text(f"SELECT * FROM {self.TABLE} WHERE external_id = :id LIMIT 1")
                params = {"id": str(id)}
            result = await session.execute(q, params)
            row = result.fetchone()
            if not row:
                return None
            children_map = await self._fetch_children(session, [int(row.id)])
            return self._map_to_schema(row, children_map.get(int(row.id), {}))

    async def findOne(
        self,
        query: Optional[dict] = None,
        is_active: Optional[bool] = None,
        tag_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Optional['SearchTagInternal']:
        if query:
            if "_id" in query or "id" in query:
                return await self.findById(query.get("_id") or query.get("id"))
            if "externalId" in query and query["externalId"]:
                return await self.findById(query["externalId"])
        results = await self.findAll(query=query, is_active=is_active, tag_id=tag_id, name=name)
        return results[0] if results else None

    async def findAll(
        self,
        query: Optional[dict] = None,
        is_active: Optional[bool] = None,
        tag_id: Optional[str] = None,
        name: Optional[str] = None,
        tag_type: Optional[str] = None,
    ) -> List['SearchTagInternal']:
        if query:
            if is_active is None and "is_active" in query:
                is_active = query["is_active"]
            if tag_id is None and "tag_id" in query:
                tag_id = query["tag_id"]
            if name is None and "name" in query:
                name = query["name"]
            if tag_type is None and "type" in query:
                tag_type = query["type"]

        clauses = []
        params = {}
        if is_active is not None:
            clauses.append("is_active = :act")
            params["act"] = 1 if is_active else 0
        if tag_id is not None:
            clauses.append("tag_id = :tid")
            params["tid"] = tag_id
        if name is not None:
            clauses.append("name = :name")
            params["name"] = name
        if tag_type is not None:
            clauses.append("type = :ttype")
            params["ttype"] = tag_type

        where_sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT * FROM {self.TABLE}{where_sql} ORDER BY id ASC"

        factory = self._factory()
        if not factory:
            return []
        async with factory() as session:
            result = await session.execute(text(sql), params)
            rows = result.fetchall()
            if not rows:
                return []
            children_map = await self._fetch_children(session, [int(r.id) for r in rows])
            return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]

    async def create(self, data: 'SearchTagInternalCreate') -> 'SearchTagInternal':
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        params = {"eid": external_id, "c": now, "u": now}

        if data.tag_id is not None:
            cols.append("tag_id")
            params["s_tag_id"] = data.tag_id

        if data.name is not None:
            cols.append("name")
            params["s_name"] = data.name

        if data.type is not None:
            cols.append("type")
            params["s_type"] = data.type

        if data.is_active is not None:
            cols.append("is_active")
            params["s_is_active"] = data.is_active

        col_sql = ", ".join(cols)
        val_sql = ", ".join([":eid", ":c", ":u"] + [f":s_{k}" for k in ['tag_id', 'name', 'type', 'is_active'] if f"s_{k}" in params] + [f":c_{k}" for k in [] if f"c_{k}" in params])
        
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

    async def update(self, id: str, update_data: 'SearchTagInternalUpdate') -> 'SearchTagInternal':
        factory = self._factory()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now_utc()}

        if data.tag_id is not None:
            updates.append("tag_id = :s_tagId")
            params["s_tag_id"] = data.tag_id

        if data.name is not None:
            updates.append("name = :s_name")
            params["s_name"] = data.name

        if data.type is not None:
            updates.append("type = :s_type")
            params["s_type"] = data.type

        if data.is_active is not None:
            updates.append("is_active = :s_isActive")
            params["s_is_active"] = data.is_active

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

    async def delete(self, id: Union[int, str]) -> bool:
        factory = self._factory()
        if not factory or not id:
            return False
        async with factory() as session:
            if str(id).isdigit():
                pk = int(id)
            else:
                res = await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": str(id)}
                )
                pk = res.scalar()
                if not pk:
                    return False

            await session.execute(text("DELETE FROM sj_search_tag_categories WHERE parent_id = :id"), {"id": pk})
            await session.execute(text("DELETE FROM sj_search_tag_subcats WHERE parent_id = :id"), {"id": pk})
            await session.execute(text("DELETE FROM sj_search_tag_brands WHERE parent_id = :id"), {"id": pk})
            await session.execute(text("DELETE FROM sj_search_tag_collections WHERE parent_id = :id"), {"id": pk})
            await session.execute(text("DELETE FROM sj_search_tag_products WHERE parent_id = :id"), {"id": pk})
            await session.execute(text("DELETE FROM sj_search_tag_ex_products WHERE parent_id = :id"), {"id": pk})

            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pk},
            )
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(self, r, children: Dict) -> 'SearchTagInternal':
        from app.models.daos_flat import SearchTagInternal
        return SearchTagInternal(
            id=str(r.id),
            external_id=r.external_id,
            tag_id=r.tag_id,
            name=r.name,
            type=r.type,
            is_active=bool(r.is_active) if r.is_active is not None else None,
            categories=children.get("categories", []),
            sub_categories=children.get("subCategories", []),
            brands=children.get("brands", []),
            collections=children.get("collections", []),
            product_ids=children.get("productIds", []),
            excluded_product_ids=children.get("excludedProductIds", []),
            created_at=r.created_at,
            updated_at=r.updated_at,
        )

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

    async def _replace_children(self, session, row_id: int, data: 'CamelBaseModel'):

        if data.categories is not None:
            await session.execute(text(f"DELETE FROM sj_search_tag_categories WHERE parent_id = :id"), {"id": row_id})
            child_list = data.categories or []

            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_search_tag_categories (parent_id, category) VALUES (:id, :v)"), {"id": row_id, "v": item})

        if data.sub_categories is not None:
            await session.execute(text(f"DELETE FROM sj_search_tag_subcats WHERE parent_id = :id"), {"id": row_id})
            child_list = data.sub_categories or []

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

        if data.product_ids is not None:
            await session.execute(text(f"DELETE FROM sj_search_tag_products WHERE parent_id = :id"), {"id": row_id})
            child_list = data.product_ids or []

            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_search_tag_products (parent_id, product_id) VALUES (:id, :v)"), {"id": row_id, "v": item})

        if data.excluded_product_ids is not None:
            await session.execute(text(f"DELETE FROM sj_search_tag_ex_products WHERE parent_id = :id"), {"id": row_id})
            child_list = data.excluded_product_ids or []

            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_search_tag_ex_products (parent_id, product_id) VALUES (:id, :v)"), {"id": row_id, "v": item})
