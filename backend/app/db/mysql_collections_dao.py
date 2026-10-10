from typing import Optional, Dict, List, Any, Union
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
        
    async def findById(self, id: Union[int, str]) -> Optional['CollectionInternal']:
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
        name: Optional[str] = None,
    ) -> Optional['CollectionInternal']:
        if query:
            if "_id" in query or "id" in query:
                return await self.findById(query.get("_id") or query.get("id"))
            if "externalId" in query and query["externalId"]:
                return await self.findById(query["externalId"])
        results = await self.findAll(query=query, is_active=is_active, name=name)
        return results[0] if results else None

    async def findAll(
        self,
        query: Optional[dict] = None,
        is_active: Optional[bool] = None,
        name: Optional[str] = None,
    ) -> List['CollectionInternal']:
        if query:
            if is_active is None and "is_active" in query:
                is_active = query["is_active"]
            if name is None and "name" in query:
                name = query["name"]

        clauses = []
        params = {}
        if is_active is not None:
            clauses.append("is_active = :act")
            params["act"] = 1 if is_active else 0
        if name is not None:
            clauses.append("name = :name")
            params["name"] = name

        where_sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT * FROM {self.TABLE}{where_sql} ORDER BY display_order ASC, id ASC"

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

            await session.execute(text("DELETE FROM sj_collection_pages WHERE parent_id = :id"), {"id": pk})
            await session.execute(text("DELETE FROM sj_collection_segments WHERE parent_id = :id"), {"id": pk})
            await session.execute(text("DELETE FROM sj_collection_rules WHERE parent_id = :id"), {"id": pk})
            await session.execute(text("DELETE FROM sj_collection_products WHERE parent_id = :id"), {"id": pk})

            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pk},
            )
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(self, r, children: Dict) -> 'CollectionInternal':
        from app.models.daos_flat import CollectionInternal
        return CollectionInternal(
            id=str(r.id),
            external_id=r.external_id,
            name=r.name,
            description=r.description,
            image_url=r.image_url,
            is_active=bool(r.is_active) if r.is_active is not None else None,
            display_order=r.display_order,
            visible_pages=children.get("visible_pages", []),
            user_segments=children.get("user_segments", []),
            visibility_rules=children.get("visibility_rules", []),
            product_ids=children.get("product_ids", []),
            created_at=r.created_at,
            updated_at=r.updated_at,
        )

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
