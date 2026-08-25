"""
Oracle DAO for sj_categories. Implements FileStorage-like interface for 'categories'.
"""

from app.config.settings import settings
import secrets
from typing import Dict, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.oracle_utils import json_dumps, json_loads, now_utc


class OracleCategoryDAO:
    @property
    def TABLE(self):
        suffix = getattr(settings, "table_suffix", "")
        return f"sj_categories{suffix}"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_doc(self, r) -> Dict:
        return {
            "_id": str(r.id),
            "name": r.name,
            "description": r.description,
            "images": json_loads(r.images) or [],
            "subCategories": json_loads(r.sub_categories) or [],
            "isActive": bool(r.is_active) if r.is_active is not None else True,
            "categoryTag": r.category_tag,
            "categoryTags": json_loads(r.category_tags) or [],
            "minimumQuantity": int(r.minimum_quantity) if r.minimum_quantity is not None else 0,
            "showInMobileHomepage": bool(r.show_in_mobile_homepage) if r.show_in_mobile_homepage is not None else True,
            "gst": float(r.gst) if r.gst is not None else 0.0,
            "isReturnable": bool(r.is_returnable) if r.is_returnable is not None else False,
            "createdAt": r.created_at.isoformat() if r.created_at else None,
            "updatedAt": r.updated_at.isoformat() if r.updated_at else None,
        }

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        factory = self._factory()
        if not factory:
            return []

        column_map = {
            "name": "name",
            "categoryTag": "category_tag",
            "isActive": "is_active",
            "showInMobileHomepage": "show_in_mobile_homepage",
            "gst": "gst",
            "isReturnable": "is_returnable",
        }
        bool_keys = {"isActive", "showInMobileHomepage", "isReturnable"}

        where_clauses = []
        params = {}
        if query:
            for k, v in query.items():
                if k in ("_id", "id"):
                    where_clauses.append("id = :id")
                    params["id"] = int(v) if str(v).isdigit() else 0
                elif k == "name":
                    where_clauses.append("LOWER(name) = :lower_name")
                    params["lower_name"] = str(v).lower()
                elif k in column_map:
                    col = column_map[k]
                    where_clauses.append(f"{col} = :{col}")
                    if k in bool_keys:
                        params[col] = 1 if v else 0
                    else:
                        params[col] = v

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id, external_id, name, description, images, sub_categories, is_active,
                           category_tag, category_tags, minimum_quantity, show_in_mobile_homepage,
                           gst, is_returnable,
                           created_at, updated_at
                    FROM {self.TABLE}
                    WHERE {where_sql}
                    """
                ),
                params,
            )
            rows = result.fetchall()
        docs = [self._row_to_doc(r) for r in rows]
        if not query:
            return docs
        filtered: List[Dict] = []
        for d in docs:
            match = True
            for k, v in query.items():
                if k in ("_id", "id"):
                    if str(d.get("_id")) != str(v):
                        match = False
                        break
                elif k == "name":
                    if (d.get("name") or "").lower() != str(v).lower():
                        match = False
                        break
                elif k in column_map:
                    continue
                elif d.get(k) != v:
                    match = False
                    break
            if match:
                filtered.append(d)
        return filtered

    async def findOne(self, query: Dict) -> Optional[Dict]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        factory = self._factory()
        if not factory:
            return None
        cid = int(id) if str(id).isdigit() else 0
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id, external_id, name, description, images, sub_categories, is_active,
                           category_tag, category_tags, minimum_quantity, show_in_mobile_homepage,
                           gst, is_returnable,
                           created_at, updated_at
                    FROM {self.TABLE} WHERE id = :id
                    """
                ),
                {"id": cid},
            )
            row = result.fetchone()
        return self._row_to_doc(row) if row else None

    async def create(self, data: Dict) -> Dict:
        factory = self._factory()
        if not factory:
            raise RuntimeError("Oracle not configured")
        now = now_utc()
        external_id = secrets.token_hex(16)
        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    INSERT INTO {self.TABLE} (
                        external_id, name, description, images, sub_categories, is_active,
                        category_tag, category_tags, minimum_quantity, show_in_mobile_homepage,
                        gst, is_returnable,
                        created_at, updated_at
                    ) VALUES (
                        :external_id, :name, :description, :images, :sub_categories, :is_active,
                        :category_tag, :category_tags, :minimum_quantity, :show_in_mobile_homepage,
                        :gst, :is_returnable,
                        :created_at, :updated_at
                    )
                    """
                ),
                {
                    "external_id": external_id,
                    "name": data.get("name"),
                    "description": data.get("description"),
                    "images": json_dumps(data.get("images") or []),
                    "sub_categories": json_dumps(data.get("subCategories") or []),
                    "is_active": 1 if data.get("isActive", True) else 0,
                    "category_tag": data.get("categoryTag"),
                    "category_tags": json_dumps(data.get("categoryTags") or []),
                    "minimum_quantity": data.get("minimumQuantity", 0),
                    "show_in_mobile_homepage": 1 if data.get("showInMobileHomepage", True) else 0,
                    "gst": float(data.get("gst", 0)),
                    "is_returnable": 1 if data.get("isReturnable", False) else 0,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            await session.commit()
            r = await session.execute(
                text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"),
                {"eid": external_id},
            )
            new_id = r.scalar()
        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: Dict) -> Optional[Dict]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = {**existing, **update_data}
        factory = self._factory()
        if not factory:
            return None
        now = now_utc()
        cid = int(id) if str(id).isdigit() else 0
        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    UPDATE {self.TABLE} SET
                        name = :name,
                        description = :description,
                        images = :images,
                        sub_categories = :sub_categories,
                        is_active = :is_active,
                        category_tag = :category_tag,
                        category_tags = :category_tags,
                        minimum_quantity = :minimum_quantity,
                        show_in_mobile_homepage = :show_in_mobile_homepage,
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
                    "images": json_dumps(merged.get("images") or []),
                    "sub_categories": json_dumps(merged.get("subCategories") or []),
                    "is_active": 1 if merged.get("isActive", True) else 0,
                    "category_tag": merged.get("categoryTag"),
                    "category_tags": json_dumps(merged.get("categoryTags") or []),
                    "minimum_quantity": merged.get("minimumQuantity", 0),
                    "show_in_mobile_homepage": 1 if merged.get("showInMobileHomepage", True) else 0,
                    "gst": float(merged.get("gst", 0)),
                    "is_returnable": 1 if merged.get("isReturnable", False) else 0,
                    "updated_at": now,
                },
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        cid = int(id) if str(id).isdigit() else 0
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": cid},
            )
            await session.commit()
            return result.rowcount > 0

    async def deleteMany(self, query: Dict) -> Dict:
        docs = await self.findAll(query)
        deleted = 0
        for d in docs:
            if await self.delete(d.get("_id")):
                deleted += 1
        return {"deletedCount": deleted}

    async def count(self, query: Optional[Dict] = None) -> int:
        docs = await self.findAll(query)
        return len(docs)

    find_all = findAll
    find_by_id = findById
    find_one = findOne
