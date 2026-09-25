from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import secrets
import json
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import CollectionInternal
from app.models.daos_flat import CollectionInternalCreate, CollectionInternalUpdate

def now_utc():
    return datetime.now(timezone.utc)

class MySQLCollectionsDAO:
    def __init__(self):
        self.table_name = "sj_collections"
    
    @property
    def TABLE(self):
        from app.config.settings import settings
        return self.table_name

    def _factory(self):
        return get_async_session_factory()
        
    async def findById(self, id: str) -> Optional['CollectionInternal']:
        return await self.findOne({"_id": id})

    async def findOne(self, query=None, **kwargs) -> Optional['CollectionInternal']:
        if query:
            kwargs.update(query)
        if not kwargs:
            return None
        
        async with self._factory()() as session:
            conditions = []
            params = {}
            
            query_map = {'name': 'name', 'description': 'description', 'image_url': 'image_url', 'is_active': 'is_active', 'display_order': 'display_order'}
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
            
    async def findAll(self, query: Optional[Dict[str, Any]] = None) -> List['CollectionInternal']:
        query = query or {}
        async with self._factory()() as session:
            sql = f"SELECT * FROM {self.TABLE}"
            params = {}
            
            query_map = {'name': 'name', 'description': 'description', 'image_url': 'image_url', 'is_active': 'is_active', 'display_order': 'display_order'}
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

    async def create(self, data: 'CollectionsInternalCreate') -> 'CollectionInternal':
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        params = {"eid": external_id, "c": now, "u": now}

        if data.name is not None:
            cols.append("name")
            params["s_name"] = data.name

        if data.description is not None:
            cols.append("description")
            params["s_description"] = data.description

        if data.image_url is not None:
            cols.append("image_url")
            params["s_image_url"] = data.image_url

        if data.is_active is not None:
            cols.append("is_active")
            params["s_is_active"] = data.is_active

        if data.display_order is not None:
            cols.append("display_order")
            params["s_display_order"] = data.display_order

        col_sql = ", ".join(cols)
        val_sql = ", ".join([":eid", ":c", ":u"] + [f":s_{k}" for k in ['name', 'description', 'image_url', 'is_active', 'display_order'] if f"s_{k}" in params] + [f":c_{k}" for k in [] if f"c_{k}" in params])
        
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

    async def update(self, id: str, update_data: 'CollectionsInternalUpdate') -> 'CollectionInternal':
        factory = self._factory()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now_utc()}

        if data.name is not None:
            updates.append("name = :s_name")
            params["s_name"] = data.name

        if data.description is not None:
            updates.append("description = :s_description")
            params["s_description"] = data.description

        if data.image_url is not None:
            updates.append("image_url = :s_imageUrl")
            params["s_image_url"] = data.image_url

        if data.is_active is not None:
            updates.append("is_active = :s_isActive")
            params["s_is_active"] = data.is_active

        if data.display_order is not None:
            updates.append("display_order = :s_displayOrder")
            params["s_display_order"] = data.display_order

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

            await session.execute(text(f"DELETE FROM sj_collection_pages WHERE parent_id = :id"), {"id": pk})

            await session.execute(text(f"DELETE FROM sj_collection_segments WHERE parent_id = :id"), {"id": pk})

            await session.execute(text(f"DELETE FROM sj_collection_rules WHERE parent_id = :id"), {"id": pk})

            await session.execute(text(f"DELETE FROM sj_collection_products WHERE parent_id = :id"), {"id": pk})

            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pk},
            )
            await session.commit()
            return result.rowcount > 0

    async def deleteMany(self, query: Dict) -> 'CollectionInternal':
        docs = await self.findAll(query)
        deleted = 0
        for d in docs:
            # Depending on schema format, id might be _id or id
            d_id = d.id
            if d_id and await self.delete(d_id):
                deleted += 1
        return {"deletedCount": deleted}

    def _map_to_schema(self, r, children: Dict) -> 'CollectionInternal':
        obj = CollectionInternal.model_validate(r)
        for k, v in children.items():
            setattr(obj, k, v)
        return obj

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:
        c_map = {rid: {} for rid in ids}
        if not ids:
            return c_map
            
        id_list = ",".join(map(str, ids))

        q_visible_pages = text(f"SELECT parent_id, page FROM sj_collection_pages WHERE parent_id IN ({id_list})")
        res_visible_pages = await session.execute(q_visible_pages)
        rows_visible_pages = res_visible_pages.fetchall()

        for r in rows_visible_pages:
            if "visible_pages" not in c_map[r.parent_id]:
                c_map[r.parent_id]["visible_pages"] = []
            c_map[r.parent_id]["visible_pages"].append(r[1])

        q_user_segments = text(f"SELECT parent_id, segment FROM sj_collection_segments WHERE parent_id IN ({id_list})")
        res_user_segments = await session.execute(q_user_segments)
        rows_user_segments = res_user_segments.fetchall()

        for r in rows_user_segments:
            if "user_segments" not in c_map[r.parent_id]:
                c_map[r.parent_id]["user_segments"] = []
            c_map[r.parent_id]["user_segments"].append(r[1])

        q_visibility_rules = text(f"SELECT parent_id, rule FROM sj_collection_rules WHERE parent_id IN ({id_list})")
        res_visibility_rules = await session.execute(q_visibility_rules)
        rows_visibility_rules = res_visibility_rules.fetchall()

        for r in rows_visibility_rules:
            if "visibility_rules" not in c_map[r.parent_id]:
                c_map[r.parent_id]["visibility_rules"] = []
            c_map[r.parent_id]["visibility_rules"].append(r[1])

        q_product_ids = text(f"SELECT parent_id, product_id FROM sj_collection_products WHERE parent_id IN ({id_list})")
        res_product_ids = await session.execute(q_product_ids)
        rows_product_ids = res_product_ids.fetchall()

        for r in rows_product_ids:
            if "product_ids" not in c_map[r.parent_id]:
                c_map[r.parent_id]["product_ids"] = []
            c_map[r.parent_id]["product_ids"].append(r[1])

        return c_map

    async def _replace_children(self, session, row_id: int, data: 'CamelBaseModel'):

        if data.visible_pages is not None:
            await session.execute(text(f"DELETE FROM sj_collection_pages WHERE parent_id = :id"), {"id": row_id})
            child_list = data.visible_pages or []

            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_collection_pages (parent_id, page) VALUES (:id, :v)"), {"id": row_id, "v": item})

        if data.user_segments is not None:
            await session.execute(text(f"DELETE FROM sj_collection_segments WHERE parent_id = :id"), {"id": row_id})
            child_list = data.user_segments or []

            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_collection_segments (parent_id, segment) VALUES (:id, :v)"), {"id": row_id, "v": item})

        if data.visibility_rules is not None:
            await session.execute(text(f"DELETE FROM sj_collection_rules WHERE parent_id = :id"), {"id": row_id})
            child_list = data.visibility_rules or []

            if child_list:
                for item in child_list:
                    val = item.model_dump_json() if type(item) is not str else item
                    await session.execute(text(f"INSERT INTO sj_collection_rules (parent_id, rule) VALUES (:id, :v)"), {"id": row_id, "v": val})

        if data.product_ids is not None:
            await session.execute(text(f"DELETE FROM sj_collection_products WHERE parent_id = :id"), {"id": row_id})
            child_list = data.product_ids or []

            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_collection_products (parent_id, product_id) VALUES (:id, :v)"), {"id": row_id, "v": item})
