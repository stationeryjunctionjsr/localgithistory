from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import CollectionInternal, CollectionInternalCreate, CollectionInternalUpdate

def now_utc():
    return datetime.now(timezone.utc)

class MySQLCollectionsDAO:
    def __init__(self):
        self.table_name = "sj_collections"
    
    @property
    def TABLE(self):
        from app.config.settings import settings
        return self.table_name

    async def findById(self, id: int) -> Optional[CollectionInternal]:
        if not id:
            return None
        async_session = get_async_session_factory()
        if not async_session:
            return None
        async with async_session() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE id = :id LIMIT 1")
            params = {"id": id}
            result = await session.execute(q, params)
            row = result.fetchone()
            if not row:
                return None
            rows_visible_pages, rows_user_segments, rows_visibility_rules, rows_product_ids = await self._fetch_children(session, [row.id])
            return self._map_to_schema(row, rows_visible_pages, rows_user_segments, rows_visibility_rules, rows_product_ids)

    async def findOne(
        self,
        is_active: Optional[bool] = None,
        name: Optional[str] = None,
    ) -> Optional[CollectionInternal]:
        results = await self.findAll(is_active=is_active, name=name)
        return results[0] if results else None

    async def findAll(
        self,
        is_active: Optional[bool] = None,
        name: Optional[str] = None,
    ) -> List[CollectionInternal]:
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

        async_session = get_async_session_factory()
        if not async_session:
            return []
        async with async_session() as session:
            result = await session.execute(text(sql), params)
            rows = result.fetchall()
            if not rows:
                return []
            rows_visible_pages, rows_user_segments, rows_visibility_rules, rows_product_ids = await self._fetch_children(session, [int(r.id) for r in rows])
            return [self._map_to_schema(r, rows_visible_pages, rows_user_segments, rows_visibility_rules, rows_product_ids) for r in rows]

    async def create(self, data: CollectionInternalCreate) -> CollectionInternal:
        async_session = get_async_session_factory()
        if not async_session:
            raise RuntimeError("Database session factory unavailable")
        now = now_utc()
        
        cols = ["created_at", "updated_at"]
        params = {"c": now, "u": now}

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
            params["s_is_active"] = 1 if data.is_active else 0

        if data.display_order is not None:
            cols.append("display_order")
            params["s_display_order"] = data.display_order

        col_sql = ", ".join(cols)
        val_sql = ", ".join([":c", ":u"] + [f":s_{k}" for k in ['name', 'description', 'image_url', 'is_active', 'display_order'] if f"s_{k}" in params])
        
        async with async_session() as session:
            result = await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = result.lastrowid
            if data.visible_pages:
                await self._replace_visible_pages(session, new_id, data.visible_pages)
            if data.user_segments:
                await self._replace_user_segments(session, new_id, data.user_segments)
            if data.visibility_rules:
                await self._replace_visibility_rules(session, new_id, data.visibility_rules)
            if data.product_ids:
                await self._replace_products(session, new_id, data.product_ids)
            await session.commit()
            
        return await self.findById(new_id)

    async def update(self, id: int, update_data: CollectionInternalUpdate) -> Optional[CollectionInternal]:
        async_session = get_async_session_factory()
        if not async_session or not id:
            return None

        fields = update_data.model_fields_set
        if not fields:
            return await self.findById(id)

        updates = ["updated_at = :u"]
        params = {"id": id, "u": now_utc()}

        if "name" in fields:
            updates.append("name = :s_name")
            params["s_name"] = update_data.name

        if "description" in fields:
            updates.append("description = :s_description")
            params["s_description"] = update_data.description

        if "image_url" in fields:
            updates.append("image_url = :s_image_url")
            params["s_image_url"] = update_data.image_url

        if "is_active" in fields:
            updates.append("is_active = :s_is_active")
            params["s_is_active"] = 1 if update_data.is_active else 0

        if "display_order" in fields:
            updates.append("display_order = :s_display_order")
            params["s_display_order"] = update_data.display_order

        upd_sql = ", ".join(updates)
        async with async_session() as session:
            await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE id = :id"), params)
            if "visible_pages" in fields:
                await self._replace_visible_pages(session, id, update_data.visible_pages or [])
            if "user_segments" in fields:
                await self._replace_user_segments(session, id, update_data.user_segments or [])
            if "visibility_rules" in fields:
                await self._replace_visibility_rules(session, id, update_data.visibility_rules or [])
            if "product_ids" in fields:
                await self._replace_products(session, id, update_data.product_ids or [])
            await session.commit()
                
        return await self.findById(id)

    async def delete(self, id: int) -> bool:
        async_session = get_async_session_factory()
        if not async_session or not id:
            return False
        async with async_session() as session:
            pk = id

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

    def _map_to_schema(self, r, rows_visible_pages, rows_user_segments, rows_visibility_rules, rows_product_ids) -> CollectionInternal:
        row_id = r.id
        return CollectionInternal(
            id=str(r.id),
            name=r.name,
            description=r.description,
            image_url=r.image_url,
            is_active=bool(r.is_active) if r.is_active is not None else None,
            display_order=r.display_order,
            visible_pages=[rp.page for rp in rows_visible_pages if int(rp.parent_id) == row_id],
            user_segments=[rs.segment for rs in rows_user_segments if int(rs.parent_id) == row_id],
            visibility_rules=[rr.rule for rr in rows_visibility_rules if int(rr.parent_id) == row_id],
            product_ids=[rpr.product_id for rpr in rows_product_ids if int(rpr.parent_id) == row_id],
            created_at=r.created_at,
            updated_at=r.updated_at,
        )

    async def _fetch_children(self, session, ids: List[int]):
        if not ids:
            return [], [], [], []
            
        id_list = ",".join(map(str, ids))

        q_visible_pages = text(f"SELECT parent_id, page FROM sj_collection_pages WHERE parent_id IN ({id_list})")
        res_visible_pages = await session.execute(q_visible_pages)
        rows_visible_pages = res_visible_pages.fetchall()

        q_user_segments = text(f"SELECT parent_id, segment FROM sj_collection_segments WHERE parent_id IN ({id_list})")
        res_user_segments = await session.execute(q_user_segments)
        rows_user_segments = res_user_segments.fetchall()

        q_visibility_rules = text(f"SELECT parent_id, rule FROM sj_collection_rules WHERE parent_id IN ({id_list})")
        res_visibility_rules = await session.execute(q_visibility_rules)
        rows_visibility_rules = res_visibility_rules.fetchall()

        q_product_ids = text(f"SELECT parent_id, product_id FROM sj_collection_products WHERE parent_id IN ({id_list})")
        res_product_ids = await session.execute(q_product_ids)
        rows_product_ids = res_product_ids.fetchall()

        return rows_visible_pages, rows_user_segments, rows_visibility_rules, rows_product_ids

    async def _replace_children(self, session, row_id: int, data: Union[CollectionInternalCreate, CollectionInternalUpdate]):
        fields = data.model_fields_set
        if "visible_pages" in fields and data.visible_pages is not None:
            await session.execute(text(f"DELETE FROM sj_collection_pages WHERE parent_id = :id"), {"id": row_id})
            child_list = data.visible_pages or []
            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_collection_pages (parent_id, page) VALUES (:id, :v)"), {"id": row_id, "v": item})

        if "user_segments" in fields and data.user_segments is not None:
            await session.execute(text(f"DELETE FROM sj_collection_segments WHERE parent_id = :id"), {"id": row_id})
            child_list = data.user_segments or []
            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_collection_segments (parent_id, segment) VALUES (:id, :v)"), {"id": row_id, "v": item})

        if "visibility_rules" in fields and data.visibility_rules is not None:
            await session.execute(text(f"DELETE FROM sj_collection_rules WHERE parent_id = :id"), {"id": row_id})
            child_list = data.visibility_rules or []
            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_collection_rules (parent_id, rule) VALUES (:id, :v)"), {"id": row_id, "v": item})

        if "product_ids" in fields and data.product_ids is not None:
            await session.execute(text(f"DELETE FROM sj_collection_products WHERE parent_id = :id"), {"id": row_id})
            child_list = data.product_ids or []
            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_collection_products (parent_id, product_id) VALUES (:id, :v)"), {"id": row_id, "v": item})
