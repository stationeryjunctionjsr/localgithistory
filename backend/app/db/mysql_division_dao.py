"""
MySQL DAO for sj_divisions.
Fully relational with junction table sj_division_category_tags and foreign key to sj_category_tags.
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc
from app.models.division import (
    DivisionCategoryTag,
    DivisionInternal,
    DivisionInternalCreate,
    DivisionInternalUpdate,
)


class MySQLDivisionDAO:
    def __init__(self):
        self.table_name = "sj_divisions"

    @property
    def TABLE(self):
        return self.table_name

    def _map_to_schema(
        self,
        r,
        junc_rows=None,
        direct_rows=None,
        count_rows=None,
    ) -> DivisionInternal:
        did = int(r.id)
        seen_tag_ids = set()
        tag_list = []
        tag_ids = []
        tag_names = []
        for row in (junc_rows or []) + (direct_rows or []):
            if int(row.division_id) == did and int(row.id) not in seen_tag_ids:
                tid = int(row.id)
                seen_tag_ids.add(tid)
                tag_ids.append(tid)
                if row.name:
                    tag_names.append(row.name)
                tag_list.append(
                    DivisionCategoryTag(
                        id=tid,
                        name=row.name,
                        description=row.description,
                        is_active=bool(row.is_active) if row.is_active is not None else True,
                    )
                )
        category_count = 0
        if count_rows and tag_names:
            tag_names_set = set(tag_names)
            for crow in count_rows:
                if crow.tag in tag_names_set:
                    category_count += int(crow.cnt)
        return DivisionInternal(
            id=r.id,
            name=r.name,
            description=r.description,
            image_url=r.image_url,
            display_order=r.display_order if r.display_order is not None else 0,
            is_active=bool(r.is_active) if r.is_active is not None else True,
            category_tag_ids=tag_ids,
            category_tags=tag_list,
            category_tag_names=tag_names,
            category_count=category_count,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )

    async def _fetch_children(self, session, division_ids: List[int]):
        if not division_ids:
            return [], [], []

        placeholders = ", ".join([f":d_{i}" for i in range(len(division_ids))])
        params = {f"d_{i}": did for i, did in enumerate(division_ids)}

        # 1. Fetch tags from junction table sj_division_category_tags
        q_junction_tags = text(f"""
            SELECT 
                j.division_id,
                j.display_order,
                t.id,
                t.name,
                t.description,
                t.is_active
            FROM sj_division_category_tags j
            JOIN sj_category_tags t ON j.category_tag_id = t.id
            WHERE j.division_id IN ({placeholders})
            ORDER BY j.display_order ASC, t.name ASC
        """)
        junc_rows = (await session.execute(q_junction_tags, params)).fetchall()

        # 2. Also fetch tags that have division_id set on sj_category_tags directly
        q_direct_tags = text(f"""
            SELECT 
                t.division_id,
                t.id,
                t.name,
                t.description,
                t.is_active
            FROM sj_category_tags t
            WHERE t.division_id IN ({placeholders})
            ORDER BY t.name ASC
        """)
        direct_rows = (await session.execute(q_direct_tags, params)).fetchall()

        # 3. Count total categories under the tags for each division
        all_tag_names = list({row.name for row in junc_rows + direct_rows if row.name})
        count_rows = []
        if all_tag_names:
            tag_placeholders = ", ".join([f":t_{i}" for i in range(len(all_tag_names))])
            tag_params = {f"t_{i}": tn for i, tn in enumerate(all_tag_names)}
            q_cat_counts = text(f"""
                SELECT cct.tag, COUNT(DISTINCT c.id) as cnt
                FROM sj_categories c
                LEFT JOIN sj_category_category_tags cct ON c.id = cct.category_id
                WHERE (cct.tag IN ({tag_placeholders}) OR c.category_tag IN ({tag_placeholders}))
                  AND c.is_active = 1
                GROUP BY cct.tag
            """)
            try:
                count_rows = (await session.execute(q_cat_counts, tag_params)).fetchall()
            except Exception:
                pass

        return junc_rows, direct_rows, count_rows

    async def _sync_junction_tags(self, session, division_id: int, tag_ids: List[int]):
        # 1. Clear previous junction entries
        await session.execute(
            text("DELETE FROM sj_division_category_tags WHERE division_id = :did"),
            {"did": division_id},
        )

        # 2. Reset division_id on sj_category_tags previously belonging to this division
        await session.execute(
            text("UPDATE sj_category_tags SET division_id = NULL WHERE division_id = :did"),
            {"did": division_id},
        )

        # 3. Insert into junction table and update foreign key
        for order, tid in enumerate(tag_ids):
            if tid:
                await session.execute(
                    text("""
                        INSERT INTO sj_division_category_tags (division_id, category_tag_id, display_order, created_at)
                        VALUES (:did, :tid, :ord, :now)
                    """),
                    {"did": division_id, "tid": int(tid), "ord": order, "now": now_utc()},
                )
                await session.execute(
                    text("UPDATE sj_category_tags SET division_id = :did WHERE id = :tid"),
                    {"did": division_id, "tid": int(tid)},
                )

    async def findById(self, id: int) -> Optional[DivisionInternal]:
        async_session = get_async_session_factory()
        if not async_session or not id:
            return None
        async with async_session() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE id = :id LIMIT 1")
            result = await session.execute(q, {"id": id})
            row = result.fetchone()
            if not row:
                return None
            junc_rows, direct_rows, count_rows = await self._fetch_children(session, [row.id])
            return self._map_to_schema(row, junc_rows, direct_rows, count_rows)

    async def findByName(self, name: str) -> Optional[DivisionInternal]:
        async_session = get_async_session_factory()
        if not async_session or not name:
            return None
        async with async_session() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE LOWER(name) = LOWER(:name) LIMIT 1")
            result = await session.execute(q, {"name": name.strip()})
            row = result.fetchone()
            if not row:
                return None
            junc_rows, direct_rows, count_rows = await self._fetch_children(session, [int(row.id)])
            return self._map_to_schema(row, junc_rows, direct_rows, count_rows)

    async def findOne(
        self,
        is_active: Optional[bool] = None,
        name: Optional[str] = None,
    ) -> Optional[DivisionInternal]:
        results = await self.findAll(is_active=is_active, name=name)
        return results[0] if results else None

    async def findAll(
        self,
        is_active: Optional[bool] = None,
        name: Optional[str] = None,
    ) -> List[DivisionInternal]:

        clauses = []
        params = {}
        if is_active is not None:
            clauses.append("is_active = :act")
            params["act"] = 1 if is_active else 0
        if name is not None:
            clauses.append("LOWER(name) = LOWER(:name)")
            params["name"] = name.strip()

        where_sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT * FROM {self.TABLE}{where_sql} ORDER BY display_order ASC, name ASC"

        async_session = get_async_session_factory()
        if not async_session:
            return []
        async with async_session() as session:
            result = await session.execute(text(sql), params)
            rows = result.fetchall()
            if not rows:
                return []
            division_ids = [int(r.id) for r in rows]
            junc_rows, direct_rows, count_rows = await self._fetch_children(session, division_ids)
            return [self._map_to_schema(r, junc_rows, direct_rows, count_rows) for r in rows]

    async def create(self, item: DivisionInternalCreate) -> DivisionInternal:
        async_session = get_async_session_factory()
        if not async_session:
            raise RuntimeError("Database not available")

        now = now_utc()
        async with async_session() as session:
            q = text(f"""
                INSERT INTO {self.TABLE} (
                    name, description, image_url, display_order, is_active, created_at, updated_at
                ) VALUES (
                    :name, :desc, :img, :ord, :act, :now, :now
                )
            """)
            result = await session.execute(
                q,
                {
                    "name": item.name.strip(),
                    "desc": item.description,
                    "img": item.image_url,
                    "ord": item.display_order if item.display_order is not None else 0,
                    "act": 1 if item.is_active else 0,
                    "now": now,
                },
            )
            division_id = result.lastrowid
            if item.category_tag_ids:
                await self._sync_junction_tags(session, division_id, item.category_tag_ids)
            await session.commit()

        created = await self.findById(division_id)
        if not created:
            raise RuntimeError(f"Failed to create division {item.name}")
        return created

    async def update(
        self, id: int, item: DivisionInternalUpdate
    ) -> Optional[DivisionInternal]:
        if not id:
            return None

        update_fields = ["updated_at = :now"]
        now = now_utc()
        params = {"id": id, "now": now}

        if "name" in item.model_fields_set:
            update_fields.append("name = :name")
            params["name"] = item.name.strip() if item.name else item.name
        if "description" in item.model_fields_set:
            update_fields.append("description = :desc")
            params["desc"] = item.description
        if "image_url" in item.model_fields_set:
            update_fields.append("image_url = :img")
            params["img"] = item.image_url
        if "display_order" in item.model_fields_set:
            update_fields.append("display_order = :ord")
            params["ord"] = item.display_order
        if "is_active" in item.model_fields_set:
            update_fields.append("is_active = :act")
            params["act"] = 1 if item.is_active else 0

        has_tags_update = "category_tag_ids" in item.model_fields_set
        async_session = get_async_session_factory()
        if not async_session:
            return None

        async with async_session() as session:
            q = text(f"UPDATE {self.TABLE} SET {', '.join(update_fields)} WHERE id = :id")
            result = await session.execute(q, params)

            if has_tags_update:
                await self._sync_junction_tags(session, id, item.category_tag_ids or [])

            await session.commit()
            if result.rowcount == 0 and not has_tags_update:
                existing = await self.findById(id)
                if not existing:
                    return None

        return await self.findById(id)

    async def delete(self, id: int) -> bool:
        if not id:
            return False
        async_session = get_async_session_factory()
        if not async_session:
            return False
        async with async_session() as session:
            # 1. Unlink tags
            await session.execute(
                text("UPDATE sj_category_tags SET division_id = NULL WHERE division_id = :did"),
                {"did": id},
            )
            # 2. Delete junction rows
            await session.execute(
                text("DELETE FROM sj_division_category_tags WHERE division_id = :did"),
                {"did": id},
            )
            # 3. Delete division
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": id},
            )
            await session.commit()
            return result.rowcount > 0
