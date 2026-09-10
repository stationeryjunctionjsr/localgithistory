"""
MySQL DAO for sj_categories. Fully relational with child tables for images, sub_categories, and category_tags.
"""

import secrets
from typing import Dict, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.oracle_utils import now_utc
from app.models.category import Category


class MySQLCategoryDAO:
    @property
    def TABLE(self):
        suffix = getattr(settings, "table_suffix", "")
        return f"sj_categories{suffix}"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_dict(self, r, children: Dict) -> Dict:
        return {
            "_id": str(r.id),
            "name": r.name,
            "description": r.description,
            "isActive": bool(r.is_active) if r.is_active is not None else True,
            "categoryTag": r.category_tag,
            "minimumQuantity": getattr(r, "minimum_quantity", None),
            "gst": float(r.gst) if getattr(r, "gst", None) is not None else None,
            "isReturnable": bool(r.is_returnable) if getattr(r, "is_returnable", None) is not None else True,
            "images": children.get("images", []),
            "subCategories": children.get("subCategories", []),
            "categoryTags": children.get("categoryTags", []),
            "createdAt": r.created_at.isoformat() if r.created_at else None,
            "updatedAt": r.updated_at.isoformat() if r.updated_at else None,
        }

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:
        c_map = {rid: {"images": [], "subCategories": [], "categoryTags": []} for rid in ids}
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
                c_map[r.category_id]["subCategories"].append(r.sub_category)

            res_tag = await session.execute(
                text(f"SELECT category_id, tag FROM sj_category_category_tags WHERE category_id IN ({placeholders})"),
                chunk_params,
            )
            for r in res_tag.fetchall():
                c_map[r.category_id]["categoryTags"].append(r.tag)
        return c_map

    async def _replace_children(self, session, cid: int, data: Dict):
        await session.execute(text("DELETE FROM sj_category_images WHERE category_id = :cid"), {"cid": cid})
        await session.execute(text("DELETE FROM sj_category_sub_categories WHERE category_id = :cid"), {"cid": cid})
        await session.execute(text("DELETE FROM sj_category_category_tags WHERE category_id = :cid"), {"cid": cid})

        for img in data.get("images", []):
            await session.execute(
                text("INSERT INTO sj_category_images (category_id, image_url) VALUES (:cid, :img)"),
                {"cid": cid, "img": str(img)},
            )

        for sub in data.get("subCategories", []):
            await session.execute(
                text("INSERT INTO sj_category_sub_categories (category_id, sub_category) VALUES (:cid, :sub)"),
                {"cid": cid, "sub": str(sub)},
            )

        for tag in data.get("categoryTags", []):
            await session.execute(
                text("INSERT INTO sj_category_category_tags (category_id, tag) VALUES (:cid, :tag)"),
                {"cid": cid, "tag": str(tag)},
            )

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        factory = self._factory()
        if not factory:
            return []

        where_clauses = []
        params = {}
        if query:
            for k, v in query.items():
                if k in ("_id", "id"):
                    where_clauses.append("id = :id")
                    params["id"] = int(v) if str(v).isdigit() else 0
                elif k == "isActive":
                    where_clauses.append("is_active = :is_active")
                    params["is_active"] = int(bool(v))
                elif k == "name":
                    where_clauses.append("name = :name")
                    params["name"] = str(v)
                elif k == "categoryTag":
                    where_clauses.append("category_tag = :tag")
                    params["tag"] = str(v)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        async with factory() as session:
            result = await session.execute(
                text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"), params
            )
            rows = result.fetchall()
            c_map = await self._fetch_children(session, [r.id for r in rows])
        return [Category.model_validate(self._row_to_dict(r, c_map[r.id])) for r in rows]

    async def findOne(self, query: Dict) -> Optional[Dict]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        return await self.findOne({"_id": id})

    async def create(self, data: Dict) -> Dict:
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    INSERT INTO {self.TABLE} (
                        external_id, name, description, is_active, category_tag,
                        minimum_quantity, gst, is_returnable,
                        created_at, updated_at
                    ) VALUES (
                        :external_id, :name, :description, :is_active, :category_tag,
                        :minimum_quantity, :gst, :is_returnable,
                        :created_at, :updated_at
                    )
                    """
                ),
                {
                    "external_id": external_id,
                    "name": data.get("name"),
                    "description": data.get("description"),
                    "is_active": int(bool(data.get("isActive", True))),
                    "category_tag": data.get("categoryTag"),
                    "minimum_quantity": data.get("minimumQuantity"),
                    "gst": data.get("gst"),
                    "is_returnable": int(bool(data.get("isReturnable", True))),
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

    async def update(self, id: str, update_data: Dict) -> Optional[Dict]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = {**existing, **update_data}

        factory = self._factory()
        now = now_utc()
        cid = int(id) if str(id).isdigit() else 0
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
                        updated_at = :updated_at
                    WHERE id = :id
                    """
                ),
                {
                    "id": cid,
                    "name": merged.get("name"),
                    "description": merged.get("description"),
                    "is_active": int(bool(merged.get("isActive", True))),
                    "category_tag": merged.get("categoryTag"),
                    "minimum_quantity": merged.get("minimumQuantity"),
                    "gst": merged.get("gst"),
                    "is_returnable": int(bool(merged.get("isReturnable", True))),
                    "updated_at": now,
                },
            )
            await self._replace_children(session, cid, merged)
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"), {"id": int(id) if str(id).isdigit() else 0}
            )
            await session.commit()
            return result.rowcount > 0
