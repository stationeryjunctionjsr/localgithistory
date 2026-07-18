"""
Oracle DAO for sj_products. Implements the same interface as FileStorage for 'products'.
"""

from app.config.settings import settings
import secrets
from typing import Dict, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.oracle_utils import json_dumps, json_loads, now_utc


class OracleProductDAO:

    @property
    def TABLE(self):
        suffix = getattr(settings, 'table_suffix', '')
        return f"sj_products{suffix}"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_doc(self, r) -> Dict:
        return {
            "_id": str(r.id),
            "productId": r.id,
            "productIdFormatted": f"PDT-{r.id}",
            "name": r.name,
            "description": json_loads(r.description) if r.description else r.description,
            "sku": r.sku,
            "category": r.category,
            "subCategory": r.sub_category,
            "brand": r.brand,
            "mrp": float(r.mrp) if r.mrp is not None else None,
            "mrpPerCase": float(r.mrp_per_case) if r.mrp_per_case is not None else None,
            "quantityPerCase": int(r.quantity_per_case) if r.quantity_per_case is not None else None,
            "stock": int(r.stock) if r.stock is not None else 0,
            "images": json_loads(r.images) or [],
            "videos": json_loads(r.videos) or [],
            "isActive": bool(r.is_active) if r.is_active is not None else True,
            "tags": json_loads(r.tags) or [],
            "variantAttributes": json_loads(r.variant_attributes) or [],
            "variantCombinations": json_loads(r.variant_combinations) or [],
            "details": json_loads(r.details) or {},
            "createdAt": r.created_at.isoformat() if r.created_at else None,
            "updatedAt": r.updated_at.isoformat() if r.updated_at else None,
        }

    def _build_query_conditions(self, query: Dict) -> tuple[str, Dict]:
        where_clauses = []
        params = {}

        if "name" in query and query["name"]:
            where_clauses.append("name = :name")
            params["name"] = query["name"]

        if "productIdFormatted" in query and query["productIdFormatted"]:
            pf = str(query["productIdFormatted"]).strip()
            if pf.startswith("PDT-"):
                num_id = pf.replace("PDT-", "")
                if num_id.isdigit():
                    where_clauses.append("id = :productIdFormattedVal")
                    params["productIdFormattedVal"] = int(num_id)
            elif pf.isdigit():
                where_clauses.append("id = :productIdFormattedVal")
                params["productIdFormattedVal"] = int(pf)
        
        if "category" in query and query["category"]:
            where_clauses.append("category = :category")
            params["category"] = query["category"]
            
        if "sku" in query and query["sku"]:
            where_clauses.append("sku = :sku")
            params["sku"] = query["sku"]
            
        if "categories" in query and query["categories"]:
            cats = [c.strip() for c in query["categories"].split(",") if c.strip()]
            if cats:
                cat_params = {f"cat_{i}": c for i, c in enumerate(cats)}
                params.update(cat_params)
                cat_placeholders = ", ".join([f":{k}" for k in cat_params.keys()])
                where_clauses.append(f"category IN ({cat_placeholders})")
            
        if "subCategory" in query and query["subCategory"]:
            where_clauses.append("sub_category = :subCategory")
            params["subCategory"] = query["subCategory"]
            
        if "brand" in query and query["brand"]:
            brands = [b.strip().lower() for b in query["brand"].split(",") if b.strip()]
            if brands:
                brand_params = {f"brand_{i}": b for i, b in enumerate(brands)}
                params.update(brand_params)
                brand_placeholders = ", ".join([f":{k}" for k in brand_params.keys()])
                where_clauses.append(f"LOWER(brand) IN ({brand_placeholders})")
            
        if "search" in query and query["search"]:
            term = query["search"].strip().lower()
            tokens = [t for t in term.split() if t.strip()]
            if query.get("use_db_fuzzy"):
                for idx, token in enumerate(tokens):
                    clause = f"""(
                        UTL_MATCH.edit_distance_similarity(LOWER(name), :f_token_{idx}) >= 70 OR
                        UTL_MATCH.edit_distance_similarity(LOWER(brand), :f_token_{idx}) >= 70 OR
                        UTL_MATCH.edit_distance_similarity(LOWER(category), :f_token_{idx}) >= 70 OR
                        UTL_MATCH.edit_distance_similarity(LOWER(sku), :f_token_{idx}) >= 70
                    )"""
                    where_clauses.append(clause)
                    params[f"f_token_{idx}"] = token
            else:
                for idx, token in enumerate(tokens):
                    term_like = f"%{token}%"
                    where_clauses.append(
                        f"(LOWER(name) LIKE :search_{idx} OR LOWER(brand) LIKE :search_{idx} OR LOWER(category) LIKE :search_{idx} OR LOWER(sku) LIKE :search_{idx})"
                    )
                    params[f"search_{idx}"] = term_like
            
        if "allowed_ids" in query:
            allowed_ids = query["allowed_ids"]
            if not allowed_ids:
                where_clauses.append("1=0") # No match possible
            else:
                # Handle Oracle IN clause limit of 1000
                id_list = [int(aid) for aid in allowed_ids]
                chunks = [id_list[i:i + 999] for i in range(0, len(id_list), 999)]
                chunk_sqls = []
                for chunk_idx, chunk in enumerate(chunks):
                    id_params = {f"aid_{chunk_idx}_{i}": aid for i, aid in enumerate(chunk)}
                    params.update(id_params)
                    id_placeholders = ", ".join([f":{k}" for k in id_params.keys()])
                    chunk_sqls.append(f"id IN ({id_placeholders})")
                
                if len(chunk_sqls) == 1:
                    where_clauses.append(chunk_sqls[0])
                else:
                    where_clauses.append("(" + " OR ".join(chunk_sqls) + ")")
            
        if "isActive" in query:
            is_active = 1 if query["isActive"] else 0
            where_clauses.append("is_active = :isActive")
            params["isActive"] = is_active
        elif query.get("includeInactive") is not True:
            where_clauses.append("is_active = 1")
            
        if "minPrice" in query and query["minPrice"]:
            where_clauses.append("mrp >= :minPrice")
            params["minPrice"] = float(query["minPrice"])
        if "maxPrice" in query and query["maxPrice"]:
            where_clauses.append("mrp <= :maxPrice")
            params["maxPrice"] = float(query["maxPrice"])

        availability = (query.get("availability") or "").strip().lower()
        if availability == "available":
            where_clauses.append("stock > 0")
        elif availability == "stock_out":
            where_clauses.append("stock <= 0")

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        return where_sql, params

    async def find_paginated(self, query: Dict, skip: int = 0, limit: int = 50, sort: str = "newest"):
        factory = self._factory()
        if not factory:
            return [], 0
            
        where_sql, params = self._build_query_conditions(query)
        
        sort_sql = "ORDER BY created_at DESC"
        if sort == "price_asc":
            sort_sql = "ORDER BY mrp ASC NULLS LAST"
        elif sort == "price_desc":
            sort_sql = "ORDER BY mrp DESC NULLS LAST"
        elif sort == "name_asc":
            sort_sql = "ORDER BY name ASC"
        elif sort == "name_desc":
            sort_sql = "ORDER BY name DESC"
            
        params_with_pagination = {**params, "skip": skip, "limit": limit}
        
        # Single round-trip: COUNT via window function avoids a separate query.
        query_sql = f"""
            SELECT id, external_id, name, description, sku, category, sub_category, brand,
                   mrp, mrp_per_case, quantity_per_case,
                   stock, images, videos, is_active, tags,
                   variant_attributes, variant_combinations, details, created_at, updated_at,
                   COUNT(*) OVER () AS total_count
            FROM {self.TABLE}
            WHERE {where_sql}
            {sort_sql}
            OFFSET :skip ROWS FETCH NEXT :limit ROWS ONLY
        """
        async with factory() as session:
            result = await session.execute(text(query_sql), params_with_pagination)
            rows = result.fetchall()
            
        if not rows:
            return [], 0
        total_count = rows[0].total_count
        docs = [self._row_to_doc(r) for r in rows]
        return docs, total_count

    async def get_facets(self, query: Dict) -> Dict[str, List[str]]:
        factory = self._factory()
        if not factory:
            return {"brands": [], "categories": [], "subCategories": []}
            
        where_sql, params = self._build_query_conditions(query)
        
        # Single round-trip for all three facets via UNION ALL.
        facet_sql = f"""
            SELECT 'brand' AS facet_type, brand AS val FROM {self.TABLE}
                WHERE {where_sql} AND brand IS NOT NULL GROUP BY brand
            UNION ALL
            SELECT 'category', category FROM {self.TABLE}
                WHERE {where_sql} AND category IS NOT NULL GROUP BY category
            UNION ALL
            SELECT 'subCategory', sub_category FROM {self.TABLE}
                WHERE {where_sql} AND sub_category IS NOT NULL GROUP BY sub_category
        """
        facets: Dict[str, List[str]] = {"brands": [], "categories": [], "subCategories": []}
        async with factory() as session:
            result = await session.execute(text(facet_sql), params)
            for row in result.fetchall():
                ft, val = row.facet_type, row.val
                if ft == "brand":
                    facets["brands"].append(val)
                elif ft == "category":
                    facets["categories"].append(val)
                elif ft == "subCategory":
                    facets["subCategories"].append(val)
        facets["brands"].sort()
        facets["categories"].sort()
        facets["subCategories"].sort()
        return facets


    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        factory = self._factory()
        if not factory:
            return []
            
        where_sql, params = self._build_query_conditions(query or {})
        
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id, external_id, name, description, sku, category, sub_category, brand,
                           mrp, mrp_per_case, quantity_per_case,
                           stock, images, videos, is_active, tags,
                           variant_attributes, variant_combinations, details, created_at, updated_at
                    FROM {self.TABLE}
                    WHERE {where_sql}
                    ORDER BY id ASC
                    """
                ),
                params
            )
            rows = result.fetchall()
        return [self._row_to_doc(r) for r in rows]

    async def findOne(self, query: Dict) -> Optional[Dict]:
        if set(query.keys()) in ({"_id"}, {"id"}):
            return await self.findById(query.get("_id") or query.get("id"))
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        factory = self._factory()
        if not factory:
            return None
        pid = int(id) if str(id).isdigit() else 0
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id, external_id, name, description, sku, category, sub_category, brand,
                           mrp, mrp_per_case, quantity_per_case,
                           stock, images, videos, is_active, tags,
                           variant_attributes, variant_combinations, details, created_at, updated_at
                    FROM {self.TABLE} WHERE id = :id
                    """
                ),
                {"id": pid},
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
                        external_id, name, description, sku, category, sub_category, brand,
                        mrp, mrp_per_case, quantity_per_case,
                        stock, images, videos, is_active, tags,
                        variant_attributes, variant_combinations, details, created_at, updated_at
                    ) VALUES (
                        :external_id, :name, :description, :sku, :category, :sub_category, :brand,
                        :mrp, :mrp_per_case, :quantity_per_case,
                        :stock, :images, :videos, :is_active, :tags,
                        :variant_attributes, :variant_combinations, :details, :created_at, :updated_at
                    )
                    """
                ),
                {
                    "external_id": external_id,
                    "name": data.get("name"),
                    "description": data.get("description"),
                    "sku": data.get("sku"),
                    "category": data.get("category"),
                    "sub_category": data.get("subCategory"),
                    "brand": data.get("brand"),
                    "mrp": data.get("mrp"),
                    "mrp_per_case": data.get("mrpPerCase"),
                    "quantity_per_case": data.get("quantityPerCase"),
                    "stock": data.get("stock", 0),
                    "images": json_dumps(data.get("images") or []),
                    "videos": json_dumps(data.get("videos") or []),
                    "is_active": 1 if data.get("isActive", True) else 0,
                    "tags": json_dumps(data.get("tags") or []),
                    "variant_attributes": json_dumps(data.get("variantAttributes") or []),
                    "variant_combinations": json_dumps(data.get("variantCombinations") or []),
                    "details": json_dumps(data.get("details") or {}),
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
        pid = int(id) if str(id).isdigit() else 0

        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    UPDATE {self.TABLE} SET
                        name = :name,
                        description = :description,
                        sku = :sku,
                        category = :category,
                        sub_category = :sub_category,
                        brand = :brand,
                        mrp = :mrp,
                        mrp_per_case = :mrp_per_case,
                        quantity_per_case = :quantity_per_case,
                        stock = :stock,
                        images = :images,
                        videos = :videos,
                        is_active = :is_active,
                        tags = :tags,
                        variant_attributes = :variant_attributes,
                        variant_combinations = :variant_combinations,
                        details = :details,
                        updated_at = :updated_at
                    WHERE id = :id
                    """
                ),
                {
                    "id": pid,
                    "name": merged.get("name"),
                    "description": merged.get("description"),
                    "sku": merged.get("sku"),
                    "category": merged.get("category"),
                    "sub_category": merged.get("subCategory"),
                    "brand": merged.get("brand"),
                    "mrp": merged.get("mrp"),
                    "mrp_per_case": merged.get("mrpPerCase"),
                    "quantity_per_case": merged.get("quantityPerCase"),
                    "stock": merged.get("stock", 0),
                    "images": json_dumps(merged.get("images") or []),
                    "videos": json_dumps(merged.get("videos") or []),
                    "is_active": 1 if merged.get("isActive", True) else 0,
                    "tags": json_dumps(merged.get("tags") or []),
                    "variant_attributes": json_dumps(merged.get("variantAttributes") or []),
                    "variant_combinations": json_dumps(merged.get("variantCombinations") or []),
                    "details": json_dumps(merged.get("details") or {}),
                    "updated_at": now,
                },
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        pid = int(id) if str(id).isdigit() else 0
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pid},
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
