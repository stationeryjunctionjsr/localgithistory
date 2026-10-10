"""
MySQL DAO for sj_categories. Fully relational with child tables for images, sub_categories, and category_tags.
"""

from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Union
import secrets
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
        images: List[str],
        sub_categories: List[str],
        category_tags: List[str],
    ) -> Category:
        return Category(
            id=str(r.id),
            name=r.name,
            description=r.description,
            is_active=bool(r.is_active) if r.is_active is not None else True,
            show_in_mobile_homepage=bool(r.show_in_mobile_homepage) if r.show_in_mobile_homepage is not None else False,
            category_tag=r.category_tag,
            minimum_quantity=r.minimum_quantity,
            gst=float(r.gst) if r.gst is not None else None,
            is_returnable=bool(r.is_returnable) if r.is_returnable is not None else True,
            images=images,
            sub_categories=sub_categories,
            category_tags=category_tags,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )

    async def _fetch_children(
        self, session, ids: List[int]
    ) -> Tuple[Dict[int, List[str]], Dict[int, List[str]], Dict[int, List[str]]]:
        images_by_cat: Dict[int, List[str]] = defaultdict(list)
        sub_cats_by_cat: Dict[int, List[str]] = defaultdict(list)
        tags_by_cat: Dict[int, List[str]] = defaultdict(list)
        if not ids:
            return images_by_cat, sub_cats_by_cat, tags_by_cat

        chunks = [ids[i : i + 999] for i in range(0, len(ids), 999)]
        for chunk in chunks:
            chunk_params = {f"id_{i}": cid for i, cid in enumerate(chunk)}
            placeholders = ", ".join([f":{k}" for k in chunk_params.keys()])

            res_img = await session.execute(
                text(f"SELECT category_id, image_url FROM sj_category_images WHERE category_id IN ({placeholders})"),
                chunk_params,
            )
            for r in res_img.fetchall():
                images_by_cat[int(r.category_id)].append(str(r.image_url))

            res_sub = await session.execute(
                text(
                    f"SELECT category_id, sub_category FROM sj_category_sub_categories WHERE category_id IN ({placeholders})"
                ),
                chunk_params,
            )
            for r in res_sub.fetchall():
                sub_cats_by_cat[int(r.category_id)].append(str(r.sub_category))

            res_tag = await session.execute(
                text(f"SELECT category_id, tag FROM sj_category_category_tags WHERE category_id IN ({placeholders})"),
                chunk_params,
            )
            for r in res_tag.fetchall():
                tags_by_cat[int(r.category_id)].append(str(r.tag))

        return images_by_cat, sub_cats_by_cat, tags_by_cat

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
            await session.execute(
                text("INSERT INTO sj_category_category_tags (category_id, tag) VALUES (:cid, :tag)"),
                {"cid": cid, "tag": str(tag)},
            )

    async def findAll(
        self,
        name: Optional[str] = None,
        category_tag: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_returnable: Optional[bool] = None,
        query: Optional[Dict] = None,
    ) -> List[Category]:
        factory = self._factory()
        if not factory:
            return []

        if query:
            if name is None and "name" in query:
                name = str(query["name"])
            if category_tag is None:
                if "category_tag" in query:
                    category_tag = str(query["category_tag"])
                elif "categoryTag" in query:
                    category_tag = str(query["categoryTag"])
            if is_active is None:
                if "is_active" in query:
                    is_active = bool(query["is_active"])
                elif "isActive" in query:
                    is_active = bool(query["isActive"])
            if is_returnable is None:
                if "is_returnable" in query:
                    is_returnable = bool(query["is_returnable"])
                elif "isReturnable" in query:
                    is_returnable = bool(query["isReturnable"])

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
            images_by_cat, subs_by_cat, tags_by_cat = await self._fetch_children(session, [int(r.id) for r in rows])
            return [
                self._map_to_schema(
                    r,
                    images=images_by_cat[int(r.id)],
                    sub_categories=subs_by_cat[int(r.id)],
                    category_tags=tags_by_cat[int(r.id)],
                )
                for r in rows
            ]

    async def findOne(
        self,
        id: Optional[Union[int, str]] = None,
        name: Optional[str] = None,
        category_tag: Optional[str] = None,
        is_active: Optional[bool] = None,
        query: Optional[Dict] = None,
    ) -> Optional[Category]:
        if id:
            return await self.findById(id)
        if query and ("_id" in query or "id" in query):
            q_id = query["_id"] if "_id" in query else query["id"]
            return await self.findById(q_id)
        docs = await self.findAll(name=name, category_tag=category_tag, is_active=is_active, query=query)
        return docs[0] if docs else None

    async def findById(self, id: Union[int, str]) -> Optional[Category]:
        if not id:
            return None
        factory = self._factory()
        if not factory:
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
            images_by_cat, subs_by_cat, tags_by_cat = await self._fetch_children(session, [int(row.id)])
            return self._map_to_schema(
                row,
                images=images_by_cat[int(row.id)],
                sub_categories=subs_by_cat[int(row.id)],
                category_tags=tags_by_cat[int(row.id)],
            )

    async def create(self, data: CategoryInternalCreate) -> Category:
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    INSERT INTO {self.TABLE} (
                        external_id, name, description, is_active, category_tag,
                        minimum_quantity, gst, is_returnable, show_in_mobile_homepage,
                        created_at, updated_at
                    ) VALUES (
                        :external_id, :name, :description, :is_active, :category_tag,
                        :minimum_quantity, :gst, :is_returnable, :show_in_mobile_homepage,
                        :created_at, :updated_at
                    )
                    """
                ),
                {
                    "external_id": external_id,
                    "name": data.name,
                    "description": data.description,
                    "is_active": 1 if data.is_active else 0,
                    "category_tag": data.category_tag,
                    "minimum_quantity": data.minimum_quantity,
                    "gst": data.gst,
                    "is_returnable": 1 if data.is_returnable else 0,
                    "show_in_mobile_homepage": 1 if data.show_in_mobile_homepage else 0,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            await session.commit()
            r = await session.execute(
                text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": external_id}
            )
            new_id = r.scalar()
            await self._replace_children(session, new_id, data)
            await session.commit()
        return await self.findById(int(new_id))

    async def update(self, id: Union[int, str], update_data: CategoryInternalUpdate) -> Optional[Category]:
        existing = await self.findById(id)
        if not existing:
            return None
        factory = self._factory()
        now = now_utc()
        cid = int(id) if str(id).isdigit() else int(existing.id)
        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    UPDATE {self.TABLE} SET
                        name = :name,
                        description = :description,
                        is_active = :is_active,
                        category_tag = :category_tag,
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
        return await self.findById(id)

    async def delete(self, id: Union[int, str]) -> bool:
        factory = self._factory()
        if not factory or not id:
            return False
        async with factory() as session:
            pk = int(id) if str(id).isdigit() else None
            if not pk:
                res = await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid LIMIT 1"), {"eid": str(id)}
                )
                pk = res.scalar()
                if not pk:
                    return False
            await session.execute(text("DELETE FROM sj_category_images WHERE category_id = :cid"), {"cid": pk})
            await session.execute(text("DELETE FROM sj_category_sub_categories WHERE category_id = :cid"), {"cid": pk})
            await session.execute(text("DELETE FROM sj_category_category_tags WHERE category_id = :cid"), {"cid": pk})
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"), {"id": pk}
            )
            await session.commit()
            return result.rowcount > 0
