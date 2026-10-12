"""
MySQL DAO for sj_category_tags.
Supports division_id / category_head_id relationships and category counts.
"""

from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple, Union

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc
from app.models.category import Category
from app.models.daos_flat import (
    CategoryTagInternal,
    CategoryTagInternalCreate,
    CategoryTagInternalUpdate,
)


class MySQLCategoryTagsDAO:
    def __init__(self):
        self.table_name = "sj_category_tags"

    @property
    def TABLE(self):
        return self.table_name

    def _factory(self):
        return get_async_session_factory()

    def _map_to_schema(
        self,
        r,
        div_rows=None,
        count_rows=None,
        cat_col_rows=None,
    ) -> CategoryTagInternal:
        div_id = r.division_id if r.division_id is not None else r.category_head_id
        division_name = None
        if div_id is not None and div_rows:
            for d in div_rows:
                if int(d.id) == int(div_id):
                    division_name = d.name
                    break
        category_count = 0
        if r.name:
            if count_rows:
                for c in count_rows:
                    if c.tag == r.name:
                        category_count = int(c.cnt)
                        break
            if cat_col_rows:
                for c in cat_col_rows:
                    if c.category_tag == r.name and int(c.cnt) > category_count:
                        category_count = int(c.cnt)
                        break
        return CategoryTagInternal(
            id=str(r.id),
            name=r.name,
            description=r.description,
            is_active=bool(r.is_active) if r.is_active is not None else True,
            division_id=div_id,
            division_name=division_name,
            category_head_id=div_id,
            category_head_name=division_name,
            category_count=category_count,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )

    async def _fetch_extra_info(self, session, rows: List[Any]):
        if not rows:
            return [], [], []

        div_rows = []
        count_rows = []
        cat_col_rows = []

        # 1. Fetch division / head names
        div_ids = list({
            int(r.division_id or r.category_head_id)
            for r in rows
            if (r.division_id is not None or r.category_head_id is not None)
        })
        if div_ids:
            d_placeholders = ", ".join([f":d_{i}" for i in range(len(div_ids))])
            d_params = {f"d_{i}": did for i, did in enumerate(div_ids)}
            try:
                res_divs = await session.execute(
                    text(f"SELECT id, name FROM sj_divisions WHERE id IN ({d_placeholders})"),
                    d_params,
                )
                div_rows = res_divs.fetchall()
            except Exception:
                try:
                    res_heads = await session.execute(
                        text(f"SELECT id, name FROM sj_category_heads WHERE id IN ({d_placeholders})"),
                        d_params,
                    )
                    div_rows = res_heads.fetchall()
                except Exception:
                    pass

        # 2. Count categories under each tag name
        tag_names = list({r.name for r in rows if r.name})
        if tag_names:
            t_placeholders = ", ".join([f":t_{i}" for i in range(len(tag_names))])
            t_params = {f"t_{i}": tn for i, tn in enumerate(tag_names)}
            res_counts = await session.execute(
                text(f"""
                    SELECT tag, COUNT(DISTINCT category_id) as cnt
                    FROM sj_category_category_tags
                    WHERE tag IN ({t_placeholders})
                    GROUP BY tag
                """),
                t_params,
            )
            count_rows = res_counts.fetchall()

            res_cat_col = await session.execute(
                text(f"""
                    SELECT category_tag, COUNT(*) as cnt
                    FROM sj_categories
                    WHERE category_tag IN ({t_placeholders})
                    GROUP BY category_tag
                """),
                t_params,
            )
            cat_col_rows = res_cat_col.fetchall()

        return div_rows, count_rows, cat_col_rows

    async def findById(self, id: Union[int, str]) -> Optional[CategoryTagInternal]:
        factory = self._factory()
        if not factory or not id:
            return None
        async with factory() as session:
            if not str(id).isdigit():
                return None
            q = text(f"SELECT * FROM {self.TABLE} WHERE id = :id LIMIT 1")
            params = {"id": int(id)}
            result = await session.execute(q, params)
            row = result.fetchone()
            if not row:
                return None
            div_rows, count_rows, cat_col_rows = await self._fetch_extra_info(session, [row])
            return self._map_to_schema(row, div_rows, count_rows, cat_col_rows)

    async def findOne(
        self,
        id: Optional[Union[int, str]] = None,
        name: Optional[str] = None,
        is_active: Optional[bool] = None,
        division_id: Optional[int] = None,
        category_head_id: Optional[int] = None,
    ) -> Optional[CategoryTagInternal]:
        if id:
            return await self.findById(id)
        target_did = division_id if division_id is not None else category_head_id
        results = await self.findAll(is_active=is_active, name=name, division_id=target_did)
        return results[0] if results else None

    async def findAll(
        self,
        is_active: Optional[bool] = None,
        name: Optional[str] = None,
        division_id: Optional[int] = None,
        category_head_id: Optional[int] = None,
    ) -> List[CategoryTagInternal]:
        clauses = []
        params = {}
        if is_active is not None:
            clauses.append("is_active = :act")
            params["act"] = 1 if is_active else 0
        if name is not None:
            clauses.append("LOWER(name) = LOWER(:name)")
            params["name"] = name.strip()
        target_did = division_id if division_id is not None else category_head_id
        if target_did is not None:
            clauses.append("(division_id = :did OR category_head_id = :did)")
            params["did"] = int(target_did)

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
            div_rows, count_rows, cat_col_rows = await self._fetch_extra_info(session, rows)
            return [self._map_to_schema(r, div_rows, count_rows, cat_col_rows) for r in rows]

    async def create(self, data: CategoryTagInternalCreate) -> CategoryTagInternal:
        factory = self._factory()
        now = now_utc()

        cols = ["created_at", "updated_at"]
        params = {"c": now, "u": now}

        if data.name is not None:
            cols.append("name")
            params["name"] = data.name.strip()

        if data.description is not None:
            cols.append("description")
            params["desc"] = data.description

        if data.is_active is not None:
            cols.append("is_active")
            params["act"] = 1 if data.is_active else 0

        target_did = data.division_id if data.division_id is not None else data.category_head_id
        if target_did is not None:
            cols.append("division_id")
            cols.append("category_head_id")
            params["did"] = int(target_did)

        col_sql = ", ".join(cols)
        val_parts = [":c", ":u"]
        if "name" in params: val_parts.append(":name")
        if "desc" in params: val_parts.append(":desc")
        if "act" in params: val_parts.append(":act")
        if "did" in params:
            val_parts.append(":did")
            val_parts.append(":did")

        val_sql = ", ".join(val_parts)

        async with factory() as session:
            result = await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = result.lastrowid

            # Sync junction tables
            if target_did is not None:
                try:
                    await session.execute(
                        text("INSERT IGNORE INTO sj_division_category_tags (division_id, category_tag_id, created_at) VALUES (:did, :tid, :now)"),
                        {"did": int(target_did), "tid": int(new_id), "now": now},
                    )
                except Exception:
                    pass
                try:
                    await session.execute(
                        text("INSERT IGNORE INTO sj_category_head_category_tags (category_head_id, category_tag_id, created_at) VALUES (:did, :tid, :now)"),
                        {"did": int(target_did), "tid": int(new_id), "now": now},
                    )
                except Exception:
                    pass
                await session.commit()

        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: CategoryTagInternalUpdate) -> Optional[CategoryTagInternal]:
        existing = await self.findById(id)
        if not existing:
            return None

        factory = self._factory()
        now = now_utc()
        tag_id = int(existing.id)

        updates = ["updated_at = :u"]
        params = {"id": tag_id, "u": now}

        if update_data.name is not None:
            updates.append("name = :name")
            params["name"] = update_data.name.strip()

        if update_data.description is not None:
            updates.append("description = :desc")
            params["desc"] = update_data.description

        if update_data.is_active is not None:
            updates.append("is_active = :act")
            params["act"] = 1 if update_data.is_active else 0

        target_did = update_data.division_id if update_data.division_id is not None else update_data.category_head_id
        if target_did is not None:
            div_val = int(target_did) if target_did != 0 else None
            updates.append("division_id = :did")
            updates.append("category_head_id = :did")
            params["did"] = div_val

        upd_sql = ", ".join(updates)
        async with factory() as session:
            await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE id = :id"), params)

            # Sync junction tables
            if target_did is not None:
                await session.execute(
                    text("DELETE FROM sj_division_category_tags WHERE category_tag_id = :tid"),
                    {"tid": tag_id},
                )
                await session.execute(
                    text("DELETE FROM sj_category_head_category_tags WHERE category_tag_id = :tid"),
                    {"tid": tag_id},
                )
                if target_did != 0:
                    try:
                        await session.execute(
                            text("INSERT INTO sj_division_category_tags (division_id, category_tag_id, created_at) VALUES (:did, :tid, :now)"),
                            {"did": int(target_did), "tid": tag_id, "now": now},
                        )
                    except Exception:
                        pass
                    try:
                        await session.execute(
                            text("INSERT INTO sj_category_head_category_tags (category_head_id, category_tag_id, created_at) VALUES (:did, :tid, :now)"),
                            {"did": int(target_did), "tid": tag_id, "now": now},
                        )
                    except Exception:
                        pass

            await session.commit()

        return await self.findById(str(tag_id))

    async def delete(self, id: Union[int, str]) -> bool:
        factory = self._factory()
        if not factory or not id:
            return False
        async with factory() as session:
            pk = int(id) if str(id).isdigit() else None
            if not pk:
                return False

            # Delete junction records
            await session.execute(
                text("DELETE FROM sj_division_category_tags WHERE category_tag_id = :tid"),
                {"tid": pk},
            )
            await session.execute(
                text("DELETE FROM sj_category_head_category_tags WHERE category_tag_id = :tid"),
                {"tid": pk},
            )
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pk},
            )
            await session.commit()
            return result.rowcount > 0

    async def findCategoriesByTag(self, tag_id_or_name: Union[int, str]) -> List[Category]:
        """Get all categories belonging to this category tag"""
        factory = self._factory()
        if not factory or not tag_id_or_name:
            return []

        async with factory() as session:
            tag_name = None
            tag_id = None
            if str(tag_id_or_name).isdigit():
                tag_id = int(tag_id_or_name)
                r = (await session.execute(text("SELECT name FROM sj_category_tags WHERE id = :id"), {"id": tag_id})).fetchone()
                if r:
                    tag_name = r.name
            else:
                tag_name = str(tag_id_or_name)
                r = (await session.execute(text("SELECT id FROM sj_category_tags WHERE name = :name"), {"name": tag_name})).fetchone()
                if r:
                    tag_id = int(r.id)

            where_parts = []
            params = {}
            if tag_id is not None:
                where_parts.append("c.category_tag_id = :tid")
                params["tid"] = tag_id
            if tag_name:
                where_parts.append("c.category_tag = :tname")
                where_parts.append("cct.tag = :tname")
                params["tname"] = tag_name

            where_sql = " OR ".join(where_parts) if where_parts else "1=0"
            sql = f"""
                SELECT DISTINCT c.id, c.name, c.description, c.is_active, c.category_tag, c.category_tag_id
                FROM sj_categories c
                LEFT JOIN sj_category_category_tags cct ON c.id = cct.category_id
                WHERE {where_sql}
                ORDER BY c.name ASC
            """
            result = await session.execute(text(sql), params)
            rows = result.fetchall()
            return [
                Category(
                    id=str(r.id),
                    name=r.name,
                    description=r.description,
                    is_active=bool(r.is_active),
                    category_tag=r.category_tag,
                    category_tag_id=r.category_tag_id,
                )
                for r in rows
            ]
