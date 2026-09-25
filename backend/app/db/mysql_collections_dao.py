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
            
            query_map = {'name': 'name', 'description': 'description', 'imageUrl': 'image_url', 'isActive': 'is_active', 'displayOrder': 'display_order'}
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
            
            query_map = {'name': 'name', 'description': 'description', 'imageUrl': 'image_url', 'isActive': 'is_active', 'displayOrder': 'display_order'}
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

        if data.name is not None:
            cols.append("name")
            params["s_name"] = data.name

        if data.description is not None:
            cols.append("description")
            params["s_description"] = data.description

        if data.imageUrl is not None:
            cols.append("image_url")
            params["s_imageUrl"] = data.imageUrl

        if data.isActive is not None:
            cols.append("is_active")
            params["s_isActive"] = data.isActive

        if data.displayOrder is not None:
            cols.append("display_order")
            params["s_displayOrder"] = data.displayOrder

        col_sql = ", ".join(cols)
        val_sql = ", ".join([":eid", ":c", ":u"] + [f":s_{k}" for k in ['name', 'description', 'imageUrl', 'isActive', 'displayOrder'] if f"s_{k}" in params] + [f":c_{k}" for k in [] if f"c_{k}" in params])
        
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

        if data.name is not None:
            updates.append("name = :s_name")
            params["s_name"] = data.name

        if data.description is not None:
            updates.append("description = :s_description")
            params["s_description"] = data.description

        if data.imageUrl is not None:
            updates.append("image_url = :s_imageUrl")
            params["s_imageUrl"] = data.imageUrl

        if data.isActive is not None:
            updates.append("is_active = :s_isActive")
            params["s_isActive"] = data.isActive

        if data.displayOrder is not None:
            updates.append("display_order = :s_displayOrder")
            params["s_displayOrder"] = data.displayOrder

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

        out["name"] = rm["name"]
        out["description"] = rm["description"]
        out["imageUrl"] = rm["image_url"]
        out["isActive"] = bool(rm["is_active"]) if rm["is_active"] is not None else None
        out["displayOrder"] = rm["display_order"]
        for k, v in children.items():
            out[k] = v
            
        return CollectionInternal(**out)

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:
        c_map = {rid: {} for rid in ids}
        if not ids:
            return c_map
            
        id_list = ",".join(map(str, ids))

        q_visiblePages = text(f"SELECT parent_id, page FROM sj_collection_pages WHERE parent_id IN ({id_list})")
        res_visiblePages = await session.execute(q_visiblePages)
        rows_visiblePages = res_visiblePages.fetchall()

        for r in rows_visiblePages:
            if "visiblePages" not in c_map[r.parent_id]:
                c_map[r.parent_id]["visiblePages"] = []
            c_map[r.parent_id]["visiblePages"].append(r[1])

        q_userSegments = text(f"SELECT parent_id, segment FROM sj_collection_segments WHERE parent_id IN ({id_list})")
        res_userSegments = await session.execute(q_userSegments)
        rows_userSegments = res_userSegments.fetchall()

        for r in rows_userSegments:
            if "userSegments" not in c_map[r.parent_id]:
                c_map[r.parent_id]["userSegments"] = []
            c_map[r.parent_id]["userSegments"].append(r[1])

        q_visibilityRules = text(f"SELECT parent_id, rule FROM sj_collection_rules WHERE parent_id IN ({id_list})")
        res_visibilityRules = await session.execute(q_visibilityRules)
        rows_visibilityRules = res_visibilityRules.fetchall()

        for r in rows_visibilityRules:
            if "visibilityRules" not in c_map[r.parent_id]:
                c_map[r.parent_id]["visibilityRules"] = []
            c_map[r.parent_id]["visibilityRules"].append(r[1])

        q_productIds = text(f"SELECT parent_id, product_id FROM sj_collection_products WHERE parent_id IN ({id_list})")
        res_productIds = await session.execute(q_productIds)
        rows_productIds = res_productIds.fetchall()

        for r in rows_productIds:
            if "productIds" not in c_map[r.parent_id]:
                c_map[r.parent_id]["productIds"] = []
            c_map[r.parent_id]["productIds"].append(r[1])

        return c_map

    async def _replace_children(self, session, row_id: int, data: Any):

        if data.visiblePages is not None:
            await session.execute(text(f"DELETE FROM sj_collection_pages WHERE parent_id = :id"), {"id": row_id})
            child_list = data.visiblePages or []

            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_collection_pages (parent_id, page) VALUES (:id, :v)"), {"id": row_id, "v": item})

        if data.userSegments is not None:
            await session.execute(text(f"DELETE FROM sj_collection_segments WHERE parent_id = :id"), {"id": row_id})
            child_list = data.userSegments or []

            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_collection_segments (parent_id, segment) VALUES (:id, :v)"), {"id": row_id, "v": item})

        if data.visibilityRules is not None:
            await session.execute(text(f"DELETE FROM sj_collection_rules WHERE parent_id = :id"), {"id": row_id})
            child_list = data.visibilityRules or []

            if child_list:
                for item in child_list:
                    val = item.model_dump_json() if type(item) is not str else item
                    await session.execute(text(f"INSERT INTO sj_collection_rules (parent_id, rule) VALUES (:id, :v)"), {"id": row_id, "v": val})

        if data.productIds is not None:
            await session.execute(text(f"DELETE FROM sj_collection_products WHERE parent_id = :id"), {"id": row_id})
            child_list = data.productIds or []

            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_collection_products (parent_id, product_id) VALUES (:id, :v)"), {"id": row_id, "v": item})
