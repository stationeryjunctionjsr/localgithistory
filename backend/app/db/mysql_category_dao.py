"""
MySQL DAO for sj_categories. Fully relational with child tables for images, sub_categories, and category_tags.
"""

from app.models.daos import CategoryInternalCreate, CategoryInternalUpdate
import secrets
from typing import Dict, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc
from app.models.category import Category


class MySQLCategoryDAO:
    @property
    def TABLE(self):
        return "sj_categories"

    def _factory(self):
        return get_async_session_factory()

    def __map_to_schema(self, r, children: Dict) -> Category:
        return {
            "_id": str(r.id),
            "name": r.name,
            "description": r.description,
            "isActive": bool(r.is_active) if r.is_active is not None else True,
            "categoryTag": r.category_tag,
            "minimumQuantity": r.minimum_quantity,
            "gst": float(r.gst) if r.gst is not None else None,
            "isReturnable": bool(r.is_returnable) if r.is_returnable is not None else True,
            "showInMobileHomepage": bool(r.show_in_mobile_homepage) if r.show_in_mobile_homepage is not None else False,
            "images": (children["images"] if "images" in children else []),
            "subCategories": (children["sub_categories"] if "subCategories" in children else []),
            "categoryTags": (children["category_tags"] if "categoryTags" in children else []),
            "createdAt": r.created_at.isoformat() if r.created_at else None,
            "updatedAt": r.updated_at.isoformat() if r.updated_at else None,
        }

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:
        c_map = {rid: {"images": [], "sub_categories": [], "category_tags": []} for rid in ids}
        if not ids:
            return c_map
        chunks = [ids[i : i + 999] for i in range(0, len(ids), 999)]
        for chunk in chunks:
            chunk_params = {f"id_{i}": cid for i, cid in enumerate(chunk)}
            placeholders = ", ".join([f":{k}" for k in chunk_params.keys()])

            res_img = await session.execute(
                text(f"SELECT category_id, image_url FROM sj_category_images WHERE category_id IN ({placeholders})"),
                chunk_params,
            )
            for r in res_img.fetchall():
                c_map[r.category_id]["images"].append(r.image_url)

            res_sub = await session.execute(
                text(
                    f"SELECT category_id, sub_category FROM sj_category_sub_categories WHERE category_id IN ({placeholders})"
                ),
                chunk_params,
            )
            for r in res_sub.fetchall():
                c_map[r.category_id]["sub_categories"].append(r.sub_category)

            res_tag = await session.execute(
                text(f"SELECT category_id, tag FROM sj_category_category_tags WHERE category_id IN ({placeholders})"),
                chunk_params,
            )
            for r in res_tag.fetchall():
                c_map[r.category_id]["category_tags"].append(r.tag)
        return c_map

    async def _replace_children(self, session, cid: int, data: Dict):
        await session.execute(text("DELETE FROM sj_category_images WHERE category_id = :cid"), {"cid": cid})
        await session.execute(text("DELETE FROM sj_category_sub_categories WHERE category_id = :cid"), {"cid": cid})
        await session.execute(text("DELETE FROM sj_category_category_tags WHERE category_id = :cid"), {"cid": cid})

        for img in (data.images if data.images is not None else []):
            await session.execute(
                text("INSERT INTO sj_category_images (category_id, image_url) VALUES (:cid, :img)"),
                {"cid": cid, "img": str(img)},
            )

        for sub in (data.sub_categories if data.sub_categories is not None else []):
            await session.execute(
                text("INSERT INTO sj_category_sub_categories (category_id, sub_category) VALUES (:cid, :sub)"),
                {"cid": cid, "sub": str(sub)},
            )

        for tag in (data.category_tags if data.category_tags is not None else []):
            await session.execute(
                text("INSERT INTO sj_category_category_tags (category_id, tag) VALUES (:cid, :tag)"),
                {"cid": cid, "tag": str(tag)},
            )

    async def findAll(self, query: Optional[Dict] = None) -> List[Category]:
        factory = self._factory()
        if not factory:
            return []

        where_clauses = []
        params = {}
        if query:
            for k, v in query.items():
                if k in ("_id", "id"):
                    where_clauses.append("id = :id")
                    params["id"] = int(v) if str(v).isdigit() else None
                elif k == "is_active":
                    where_clauses.append("is_active = :is_active")
                    params["is_active"] = int(bool(v))
                elif k == "name":
                    where_clauses.append("name = :name")
                    params["name"] = str(v)
                elif k == "category_tag":
                    where_clauses.append("category_tag = :tag")
                    params["tag"] = str(v)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        async with factory() as session:
            result = await session.execute(
                text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"), params
            )
            rows = result.fetchall()
            c_map = await self._fetch_children(session, [r.id for r in rows])
        out = []
        for r in rows:
            cat = Category.model_validate(r)
            for k, v in c_map[r.id].items():
                setattr(cat, k, v)
            out.append(cat)
        return out

    async def findOne(self, query: Dict) -> Optional[Category]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Category]:
        return await self.findOne({"_id": id})

    async def create(self, data: 'CategoryInternalCreate') -> Category:
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
                    "is_active": int(bool(data.is_active)),
                    "category_tag": data.category_tag,
                    "minimum_quantity": data.minimum_quantity,
                    "gst": data.gst,
                    "is_returnable": int(bool(data.is_returnable)),
                    "show_in_mobile_homepage": int(bool(data.show_in_mobile_homepage)),
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
        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: 'CategoryInternalUpdate') -> Optional[Category]:
        existing = await self.findById(id)
        if not existing:
            return None
        factory = self._factory()
        now = now_utc()
        cid = int(id) if str(id).isdigit() else None
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
                    "is_active": int(bool(update_data.is_active if update_data.is_active is not None else existing.is_active)),
                    "category_tag": update_data.category_tag if update_data.category_tag is not None else existing.category_tag,
                    "minimum_quantity": update_data.minimum_quantity if update_data.minimum_quantity is not None else existing.minimum_quantity,
                    "gst": update_data.gst if update_data.gst is not None else existing.gst,
                    "is_returnable": int(bool(update_data.is_returnable if update_data.is_returnable is not None else existing.is_returnable)),
                    "show_in_mobile_homepage": int(bool(update_data.show_in_mobile_homepage if update_data.show_in_mobile_homepage is not None else existing.show_in_mobile_homepage)),
                    "updated_at": now,
                },
            )
            from app.models.daos import CategoryChildrenData
            dummy_merged = CategoryChildrenData(
                images=update_data.images if update_data.images is not None else existing.images,
                subCategories=update_data.sub_categories if update_data.sub_categories is not None else existing.sub_categories,
                categoryTags=update_data.category_tags if update_data.category_tags is not None else existing.category_tags
            )
            await self._replace_children(session, cid, dummy_merged)
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"), {"id": int(id) if str(id).isdigit() else None}
            )
            await session.commit()
            return result.rowcount > 0


