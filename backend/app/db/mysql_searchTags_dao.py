from typing import Optional, List, Union
from datetime import datetime, timezone
import secrets
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
            child_rows = await self._fetch_children(session, [int(row.id)])
            return self._map_to_schema(row, child_rows)

    async def findOne(
        self,
        id: Optional[Union[int, str]] = None,
        external_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        tag_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Optional['SearchTagInternal']:
        if id is not None:
            return await self.findById(id)
        if external_id is not None:
            return await self.findById(external_id)
        results = await self.findAll(is_active=is_active, tag_id=tag_id, name=name)
        return results[0] if results else None

    async def findAll(
        self,
        is_active: Optional[bool] = None,
        tag_id: Optional[str] = None,
        name: Optional[str] = None,
        tag_type: Optional[str] = None,
    ) -> List['SearchTagInternal']:
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
            child_rows = await self._fetch_children(session, [int(r.id) for r in rows])
            return [self._map_to_schema(r, child_rows) for r in rows]

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
        val_sql = ", ".join([":eid", ":c", ":u"] + [f":s_{k}" for k in ['tag_id', 'name', 'type', 'is_active'] if f"s_{k}" in params])
        
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

        if update_data.tag_id is not None:
            updates.append("tag_id = :s_tag_id")
            params["s_tag_id"] = update_data.tag_id

        if update_data.name is not None:
            updates.append("name = :s_name")
            params["s_name"] = update_data.name

        if update_data.type is not None:
            updates.append("type = :s_type")
            params["s_type"] = update_data.type

        if update_data.is_active is not None:
            updates.append("is_active = :s_is_active")
            params["s_is_active"] = update_data.is_active

        if len(updates) > 1:
            upd_sql = ", ".join(updates)
            async with factory() as session:
                await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE id = :id"), params)
                await self._replace_children(session, int(id), update_data)
                await session.commit()
        else:
            async with factory() as session:
                await self._replace_children(session, int(id), update_data)
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

    def _map_to_schema(self, r, child_rows=None) -> 'SearchTagInternal':
        if child_rows:
            rows_categories, rows_subcats, rows_brands, rows_collections, rows_products, rows_ex_products = child_rows
            categories = [cr[1] for cr in rows_categories if cr.parent_id == r.id]
            sub_categories = [cr[1] for cr in rows_subcats if cr.parent_id == r.id]
            brands = [cr[1] for cr in rows_brands if cr.parent_id == r.id]
            collections = [cr[1] for cr in rows_collections if cr.parent_id == r.id]
            product_ids = [cr[1] for cr in rows_products if cr.parent_id == r.id]
            excluded_product_ids = [cr[1] for cr in rows_ex_products if cr.parent_id == r.id]
        else:
            categories = []
            sub_categories = []
            brands = []
            collections = []
            product_ids = []
            excluded_product_ids = []
        return SearchTagInternal(
            id=str(r.id),
            external_id=r.external_id,
            tag_id=r.tag_id,
            name=r.name,
            type=r.type,
            is_active=bool(r.is_active) if r.is_active is not None else None,
            categories=categories,
            sub_categories=sub_categories,
            brands=brands,
            collections=collections,
            product_ids=product_ids,
            excluded_product_ids=excluded_product_ids,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )

    async def _fetch_children(self, session, ids: List[int]):
        if not ids:
            return ([], [], [], [], [], [])
            
        id_list = ",".join(map(str, ids))

        q_categories = text(f"SELECT parent_id, category FROM sj_search_tag_categories WHERE parent_id IN ({id_list})")
        rows_categories = (await session.execute(q_categories)).fetchall()

        q_subCategories = text(f"SELECT parent_id, sub_category FROM sj_search_tag_subcats WHERE parent_id IN ({id_list})")
        rows_subCategories = (await session.execute(q_subCategories)).fetchall()

        q_brands = text(f"SELECT parent_id, brand FROM sj_search_tag_brands WHERE parent_id IN ({id_list})")
        rows_brands = (await session.execute(q_brands)).fetchall()

        q_collections = text(f"SELECT parent_id, collection FROM sj_search_tag_collections WHERE parent_id IN ({id_list})")
        rows_collections = (await session.execute(q_collections)).fetchall()

        q_productIds = text(f"SELECT parent_id, product_id FROM sj_search_tag_products WHERE parent_id IN ({id_list})")
        rows_productIds = (await session.execute(q_productIds)).fetchall()

        q_excludedProductIds = text(f"SELECT parent_id, product_id FROM sj_search_tag_ex_products WHERE parent_id IN ({id_list})")
        rows_excludedProductIds = (await session.execute(q_excludedProductIds)).fetchall()

        return (
            rows_categories,
            rows_subCategories,
            rows_brands,
            rows_collections,
            rows_productIds,
            rows_excludedProductIds,
        )

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
