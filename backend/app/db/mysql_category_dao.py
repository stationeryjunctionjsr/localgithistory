"""
MySQL DAO for sj_categories. Fully relational with child tables for images, sub_categories, and category_tags.
"""

from typing import Dict, List, Optional, Tuple, Union
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc
from app.models.category import Category
from app.models.daos import CategoryInternalCreate, CategoryInternalUpdate, CategoryChildrenData


class MySQLCategoryDAO:
    @property
    def TABLE(self):
        return "sj_categories"

    def _factory(self):
        return get_async_session_factory()

    def _map_to_schema(
        self,
        r,
        images_rows=None,
        sub_rows=None,
        tags_rows=None,
    ) -> Category:
        images = [str(ir.image_url) for ir in images_rows if ir.category_id == r.id] if images_rows else []
        sub_categories = [str(sr.sub_category) for sr in sub_rows if sr.category_id == r.id] if sub_rows else []
        category_tags = [str(tr.tag) for tr in tags_rows if tr.category_id == r.id] if tags_rows else []
        return Category(
            id=str(r.id),
            name=r.name,
            description=r.description,
            is_active=bool(r.is_active) if r.is_active is not None else True,
            show_in_mobile_homepage=bool(r.show_in_mobile_homepage) if r.show_in_mobile_homepage is not None else False,
            category_tag=r.category_tag,
            category_tag_id=r.category_tag_id,
            minimum_quantity=r.minimum_quantity,
            gst=float(r.gst) if r.gst is not None else None,
            is_returnable=bool(r.is_returnable) if r.is_returnable is not None else True,
            images=images,
            sub_categories=sub_categories,
            category_tags=category_tags,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )

    async def _fetch_children(self, session, ids: List[int]):
        if not ids:
            return [], [], []

        chunks = [ids[i : i + 999] for i in range(0, len(ids), 999)]
        img_rows = []
        sub_rows = []
        tag_rows = []
        for chunk in chunks:
            chunk_params = {f"id_{i}": cid for i, cid in enumerate(chunk)}
            placeholders = ", ".join([f":{k}" for k in chunk_params.keys()])

            res_img = await session.execute(
                text(f"SELECT category_id, image_url FROM sj_category_images WHERE category_id IN ({placeholders})"),
                chunk_params,
            )
            img_rows.extend(res_img.fetchall())

            res_sub = await session.execute(
                text(
                    f"SELECT category_id, sub_category FROM sj_category_sub_categories WHERE category_id IN ({placeholders})"
                ),
                chunk_params,
            )
            sub_rows.extend(res_sub.fetchall())

            res_tag = await session.execute(
                text(f"SELECT category_id, tag FROM sj_category_category_tags WHERE category_id IN ({placeholders})"),
                chunk_params,
            )
            tag_rows.extend(res_tag.fetchall())

        return img_rows, sub_rows, tag_rows

    async def _replace_children(self, session, cid: int, data: Union[CategoryInternalCreate, CategoryInternalUpdate, CategoryChildrenData]):
        await session.execute(text("DELETE FROM sj_category_images WHERE category_id = :cid"), {"cid": cid})
        await session.execute(text("DELETE FROM sj_category_sub_categories WHERE category_id = :cid"), {"cid": cid})
        await session.execute(text("DELETE FROM sj_category_category_tags WHERE category_id = :cid"), {"cid": cid})

        images = data.images if data.images is not None else []
        for img in images:
            await session.execute(
                text("INSERT INTO sj_category_images (category_id, image_url) VALUES (:cid, :img)"),
                {"cid": cid, "img": str(img)},
            )

        sub_categories = data.sub_categories if data.sub_categories is not None else []
        for sub in sub_categories:
            await session.execute(
                text("INSERT INTO sj_category_sub_categories (category_id, sub_category) VALUES (:cid, :sub)"),
                {"cid": cid, "sub": str(sub)},
            )

        category_tags = data.category_tags if data.category_tags is not None else []
        for tag in category_tags:
            tag_id_res = await session.execute(
                text("SELECT id FROM sj_category_tags WHERE name = :tname LIMIT 1"),
                {"tname": str(tag).strip()},
            )
            tag_id = tag_id_res.scalar()
            await session.execute(
                text("INSERT INTO sj_category_category_tags (category_id, tag, category_tag_id) VALUES (:cid, :tag, :tid)"),
                {"cid": cid, "tag": str(tag), "tid": tag_id},
            )

    async def findAll(
        self,
        name: Optional[str] = None,
        category_tag: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_returnable: Optional[bool] = None,
    ) -> List[Category]:
        factory = self._factory()
        if not factory:
            return []

        where_clauses = []
        params = {}
        if name is not None:
            where_clauses.append("name = :name")
            params["name"] = name
        if category_tag is not None:
            where_clauses.append("category_tag = :category_tag")
            params["category_tag"] = category_tag
        if is_active is not None:
            where_clauses.append("is_active = :is_active")
            params["is_active"] = 1 if is_active else 0
        if is_returnable is not None:
            where_clauses.append("is_returnable = :is_returnable")
            params["is_returnable"] = 1 if is_returnable else 0

        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        async with factory() as session:
            result = await session.execute(
                text(f"SELECT * FROM {self.TABLE}{where_sql} ORDER BY id ASC"), params
            )
            rows = result.fetchall()
            if not rows:
                return []
            img_rows, sub_rows, tag_rows = await self._fetch_children(session, [int(r.id) for r in rows])
            return [self._map_to_schema(r, img_rows, sub_rows, tag_rows) for r in rows]

    async def findOne(
        self,
        id: Optional[int] = None,
        name: Optional[str] = None,
        category_tag: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[Category]:
        if id:
            return await self.findById(id)
        records = await self.findAll(name=name, category_tag=category_tag, is_active=is_active)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[Category]:
        if not id:
            return None
        factory = self._factory()
        if not factory:
            return None
        async with factory() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE id = :id LIMIT 1")
            params = {"id": id}
            result = await session.execute(q, params)
            row = result.fetchone()
            if not row:
                return None
            img_rows, sub_rows, tag_rows = await self._fetch_children(session, [row.id])
            return self._map_to_schema(row, img_rows, sub_rows, tag_rows)

    async def create(self, data: CategoryInternalCreate) -> Category:
        factory = self._factory()
        now = now_utc()
        async with factory() as session:
            tag_id = data.category_tag_id
            if tag_id is None and data.category_tag:
                res_tid = await session.execute(
                    text("SELECT id FROM sj_category_tags WHERE name = :tname LIMIT 1"),
                    {"tname": str(data.category_tag).strip()},
                )
                tag_id = res_tid.scalar()

            result = await session.execute(
                text(
                    f"""
                    INSERT INTO {self.TABLE} (
                        name, description, is_active, category_tag, category_tag_id,
                        minimum_quantity, gst, is_returnable, show_in_mobile_homepage,
                        created_at, updated_at
                    ) VALUES (
                        :name, :description, :is_active, :category_tag, :category_tag_id,
                        :minimum_quantity, :gst, :is_returnable, :show_in_mobile_homepage,
                        :created_at, :updated_at
                    )
                    """
                ),
                {
                    "name": data.name,
                    "description": data.description,
                    "is_active": 1 if data.is_active else 0,
                    "category_tag": data.category_tag,
                    "category_tag_id": tag_id,
                    "minimum_quantity": data.minimum_quantity,
                    "gst": data.gst,
                    "is_returnable": 1 if data.is_returnable else 0,
                    "show_in_mobile_homepage": 1 if data.show_in_mobile_homepage else 0,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            new_id = result.lastrowid
            await self._replace_children(session, new_id, data)
            await session.commit()
        return await self.findById(new_id)

    async def update(self, id: int, update_data: CategoryInternalUpdate) -> Optional[Category]:
        existing = await self.findById(id)
        if not existing:
            return None
        factory = self._factory()
        now = now_utc()
        cid = id
        async with factory() as session:
            new_tag_id = update_data.category_tag_id
            if new_tag_id is None and update_data.category_tag is not None:
                res_tid = await session.execute(
                    text("SELECT id FROM sj_category_tags WHERE name = :tname LIMIT 1"),
                    {"tname": str(update_data.category_tag).strip()},
                )
                new_tag_id = res_tid.scalar()
            elif new_tag_id is None:
                new_tag_id = existing.category_tag_id

            await session.execute(
                text(
                    f"""
                    UPDATE {self.TABLE} SET
                        name = :name,
                        description = :description,
                        is_active = :is_active,
                        category_tag = :category_tag,
                        category_tag_id = :category_tag_id,
                        minimum_quantity = :minimum_quantity,
                        gst = :gst,
                        is_returnable = :is_returnable,
                        show_in_mobile_homepage = :show_in_mobile_homepage,
                        updated_at = :updated_at
                    WHERE id = :id
                    """
                ),
                {
                    "id": cid,
                    "name": update_data.name if update_data.name is not None else existing.name,
                    "description": update_data.description if update_data.description is not None else existing.description,
                    "is_active": 1 if (update_data.is_active if update_data.is_active is not None else existing.is_active) else 0,
                    "category_tag": update_data.category_tag if update_data.category_tag is not None else existing.category_tag,
                    "category_tag_id": new_tag_id,
                    "minimum_quantity": update_data.minimum_quantity if update_data.minimum_quantity is not None else existing.minimum_quantity,
                    "gst": update_data.gst if update_data.gst is not None else existing.gst,
                    "is_returnable": 1 if (update_data.is_returnable if update_data.is_returnable is not None else existing.is_returnable) else 0,
                    "show_in_mobile_homepage": 1 if (update_data.show_in_mobile_homepage if update_data.show_in_mobile_homepage is not None else existing.show_in_mobile_homepage) else 0,
                    "updated_at": now,
                },
            )
            dummy_merged = CategoryChildrenData(
                images=update_data.images if update_data.images is not None else existing.images,
                subCategories=update_data.sub_categories if update_data.sub_categories is not None else existing.sub_categories,
                categoryTags=update_data.category_tags if update_data.category_tags is not None else existing.category_tags,
            )
            await self._replace_children(session, cid, dummy_merged)
            await session.commit()
        return await self.findById(cid)

    async def delete(self, id: int) -> bool:
        factory = self._factory()
        if not factory or not id:
            return False
        async with factory() as session:
            pk = id
            await session.execute(text("DELETE FROM sj_category_images WHERE category_id = :cid"), {"cid": pk})
            await session.execute(text("DELETE FROM sj_category_sub_categories WHERE category_id = :cid"), {"cid": pk})
            await session.execute(text("DELETE FROM sj_category_category_tags WHERE category_id = :cid"), {"cid": pk})
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"), {"id": pk}
            )
            await session.commit()
            return result.rowcount > 0
