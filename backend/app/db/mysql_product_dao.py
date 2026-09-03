"""
MySQL DAO for sj_products (Fully Relational).
"""

import secrets

from typing import Dict, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.oracle_utils import now_utc


class MySQLProductDAO:
    @property
    def TABLE(self):
        suffix = getattr(settings, "table_suffix", "")
        return f"sj_products{suffix}"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_doc(self, r, children: Dict) -> Dict:
        return {
            "_id": str(r.id),
            "productId": r.id,
            "productIdFormatted": f"PDT-{r.id}",
            "name": r.name,
            "description": r.description,
            "sku": r.sku,
            "category": r.category,
            "subCategory": r.sub_category,
            "brand": r.brand,
            "mrp": float(r.mrp) if r.mrp is not None else None,
            "mrpPerCase": float(r.mrp_per_case) if r.mrp_per_case is not None else None,
            "quantityPerCase": int(r.quantity_per_case) if r.quantity_per_case is not None else None,
            "stock": int(r.stock) if r.stock is not None else 0,
            "images": children.get("images", []),
            "videos": children.get("videos", []),
            "isActive": bool(r.is_active) if r.is_active is not None else True,
            "tags": children.get("tags", []),
            "variantAttributes": children.get("variantAttributes", []),
            "variants": children.get("variants", []),
            "details": children.get("details", {}),
            "createdAt": r.created_at.isoformat() if r.created_at else None,
            "updatedAt": r.updated_at.isoformat() if r.updated_at else None,
        }

    def _build_query_conditions(self, query: Dict) -> tuple[str, str, Dict]:
        where_clauses = []
        params = {}
        join_sql = ""

        if "seller_ids" in query:
            seller_ids = query["seller_ids"]
            if not seller_ids:
                where_clauses.append("1=0")
            else:
                join_sql = " JOIN sj_product_sellers ps ON ps.product_id = p.external_id "
                where_clauses.append("ps.is_active = 1")
                where_clauses.append("ps.request_status = 'approved'")
                s_placeholders = []
                for i, sid in enumerate(seller_ids):
                    p_name = f"sid_{i}"
                    s_placeholders.append(f":{p_name}")
                    params[p_name] = str(sid)
                where_clauses.append(f"ps.seller_id IN ({', '.join(s_placeholders)})")

        if "name" in query and query["name"]:
            where_clauses.append("p.name = :name")
            params["name"] = query["name"]

        if "productIdFormatted" in query and query["productIdFormatted"]:
            pf = str(query["productIdFormatted"]).strip()
            if pf.startswith("PDT-"):
                num_id = pf.replace("PDT-", "")
                if num_id.isdigit():
                    where_clauses.append("p.id = :productIdFormattedVal")
                    params["productIdFormattedVal"] = int(num_id)
            elif pf.isdigit():
                where_clauses.append("p.id = :productIdFormattedVal")
                params["productIdFormattedVal"] = int(pf)

        if "category" in query and query["category"]:
            where_clauses.append("p.category = :category")
            params["category"] = query["category"]

        if "sku" in query and query["sku"]:
            where_clauses.append("p.sku = :sku")
            params["sku"] = query["sku"]

        if "categories" in query and query["categories"]:
            cats = [c.strip() for c in query["categories"].split(",") if c.strip()]
            if cats:
                cat_params = {f"cat_{i}": c for i, c in enumerate(cats)}
                params.update(cat_params)
                cat_placeholders = ", ".join([f":{k}" for k in cat_params.keys()])
                where_clauses.append(f"p.category IN ({cat_placeholders})")

        if "subCategory" in query and query["subCategory"]:
            where_clauses.append("p.sub_category = :subCategory")
            params["subCategory"] = query["subCategory"]

        if "brand" in query and query["brand"]:
            brands = [b.strip().lower() for b in query["brand"].split(",") if b.strip()]
            if brands:
                brand_params = {f"brand_{i}": b for i, b in enumerate(brands)}
                params.update(brand_params)
                brand_placeholders = ", ".join([f":{k}" for k in brand_params.keys()])
                where_clauses.append(f"LOWER(p.brand) IN ({brand_placeholders})")

        if "search" in query and query["search"]:
            term = query["search"].strip()
            where_clauses.append("MATCH (name, brand, category) AGAINST (:search_term IN BOOLEAN MODE)")
            boolean_term = " ".join(f"+{t}*" for t in term.split() if t.strip())
            params["search_term"] = boolean_term

        if "allowed_ids" in query:
            allowed_ids = query["allowed_ids"]
            if not allowed_ids:
                where_clauses.append("1=0")
            else:
                id_list = [int(aid) for aid in allowed_ids]
                chunks = [id_list[i : i + 999] for i in range(0, len(id_list), 999)]
                chunk_sqls = []
                for chunk_idx, chunk in enumerate(chunks):
                    id_params = {f"aid_{chunk_idx}_{i}": aid for i, aid in enumerate(chunk)}
                    params.update(id_params)
                    id_placeholders = ", ".join([f":{k}" for k in id_params.keys()])
                    chunk_sqls.append(f"p.id IN ({id_placeholders})")

                if len(chunk_sqls) == 1:
                    where_clauses.append(chunk_sqls[0])
                else:
                    where_clauses.append("(" + " OR ".join(chunk_sqls) + ")")

        if "isActive" in query:
            is_active = 1 if query["isActive"] else 0
            where_clauses.append("p.is_active = :isActive")
            params["isActive"] = is_active
        elif query.get("includeInactive") is not True:
            where_clauses.append("p.is_active = 1")

        price_col = "COALESCE(p.mrp_per_case, p.mrp)" if query.get("role") == "wholesaler" else "p.mrp"
        if "minPrice" in query and query["minPrice"]:
            where_clauses.append(f"{price_col} >= :minPrice")
            params["minPrice"] = float(query["minPrice"])
        if "maxPrice" in query and query["maxPrice"]:
            where_clauses.append(f"{price_col} <= :maxPrice")
            params["maxPrice"] = float(query["maxPrice"])

        availability = (query.get("availability") or "").strip().lower()
        if availability == "available":
            where_clauses.append("p.stock > 0")
        elif availability == "stock_out":
            where_clauses.append("p.stock <= 0")

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        return join_sql, where_sql, params

    async def _fetch_children_for_products(self, session, pids: List[int]) -> Dict[int, Dict]:
        children_map = {
            pid: {"images": [], "videos": [], "tags": [], "variantAttributes": [], "variants": [], "details": {}}
            for pid in pids
        }
        if not pids:
            return children_map

        chunks = [pids[i : i + 999] for i in range(0, len(pids), 999)]
        for chunk in chunks:
            chunk_params = {f"pid_{i}": pid for i, pid in enumerate(chunk)}
            placeholders = ", ".join([f":{k}" for k in chunk_params.keys()])

            # Images
            res = await session.execute(
                text(
                    f"SELECT product_id, image_url FROM sj_product_images WHERE product_id IN ({placeholders}) ORDER BY order_index ASC"
                ),
                chunk_params,
            )
            for r in res.fetchall():
                children_map[r.product_id]["images"].append(r.image_url)

            # Videos
            res = await session.execute(
                text(
                    f"SELECT product_id, video_url FROM sj_product_videos WHERE product_id IN ({placeholders}) ORDER BY order_index ASC"
                ),
                chunk_params,
            )
            for r in res.fetchall():
                children_map[r.product_id]["videos"].append(r.video_url)

            # Tags
            res = await session.execute(
                text(f"SELECT product_id, tag FROM sj_product_tags WHERE product_id IN ({placeholders})"), chunk_params
            )
            for r in res.fetchall():
                children_map[r.product_id]["tags"].append(r.tag)


            # Variant Attributes
            res = await session.execute(
                text(f"SELECT product_id, attribute_name FROM sj_product_variant_attributes WHERE product_id IN ({placeholders})"),
                chunk_params
            )
            for r in res.fetchall():
                children_map[r.product_id]["variantAttributes"].append(r.attribute_name)

            # Variants
            res = await session.execute(
                text(f"SELECT id, product_id, sku, price, price_per_case, stock FROM sj_product_variants WHERE product_id IN ({placeholders}) ORDER BY id ASC"),
                chunk_params
            )
            variants_by_id = {}
            for r in res.fetchall():
                v = {"sku": r.sku, "price": float(r.price) if r.price is not None else None, "pricePerCase": float(r.price_per_case) if r.price_per_case is not None else None, "stock": int(r.stock) if r.stock is not None else 0, "attributes": {}}
                variants_by_id[r.id] = v
                children_map[r.product_id]["variants"].append(v)
            
            if variants_by_id:
                v_ids = list(variants_by_id.keys())
                v_chunks = [v_ids[i:i+999] for i in range(0, len(v_ids), 999)]
                for v_chunk in v_chunks:
                    v_params = {f"vid_{i}": vid for i, vid in enumerate(v_chunk)}
                    v_placeholders = ", ".join([f":{k}" for k in v_params.keys()])
                    attr_res = await session.execute(
                        text(f"SELECT variant_id, attr_name, attr_value FROM sj_product_variant_combo_attrs WHERE variant_id IN ({v_placeholders})"),
                        v_params
                    )
                    for ar in attr_res.fetchall():
                        variants_by_id[ar.variant_id]["attributes"][ar.attr_name] = ar.attr_value
            # Attributes
        # res = await session.execute(
        # text(f"SELECT product_id, attr_name FROM sj_product_attributes WHERE product_id IN ({placeholders})"),
        # chunk_params,
        # )
        # for r in res.fetchall():
        # children_map[r.product_id]["attributes"].append(r.attr_name)
        #             # Details
            res = await session.execute(
                text(
                    f"SELECT product_id, detail_key, detail_value FROM sj_product_details WHERE product_id IN ({placeholders})"
                ),
                chunk_params,
            )
            for r in res.fetchall():
                children_map[r.product_id]["details"][r.detail_key] = r.detail_value

            # Combinations (This is trickier without JSON)
            # Fetch base combinations
        # res = await session.execute(
        # text(
        # f"SELECT id, product_id, sku, price, stock FROM sj_product_variant_combinations WHERE product_id IN ({placeholders})"
        # ),
        # chunk_params,
        # )
        # combos = res.fetchall()
        # if combos:
        # combo_ids = [c.id for c in combos]
        # c_params = {f"cid_{i}": cid for i, cid in enumerate(combo_ids)}
        # c_placeholders = ", ".join([f":{k}" for k in c_params.keys()])
        # opt_res = await session.execute(
        # text(
        # f"SELECT combination_id, attr_name, attr_value FROM sj_product_variant_options WHERE combination_id IN ({c_placeholders})"
        # ),
        # c_params,
        # )
        # opts = opt_res.fetchall()
        # opt_map = {cid: {} for cid in combo_ids}
        # for o in opts:
        # opt_map[o.combination_id][o.attr_name] = o.attr_value
        #         # for c in combos:
        # children_map[c.product_id]["combinations"].append(
        # {
        # "sku": c.sku,
        # "price": float(c.price) if c.price is not None else 0.0,
        # "stock": c.stock,
        # "attributes": opt_map[c.id],
        # }
        # )
        return children_map

    async def find_paginated(self, query: Dict, skip: int = 0, limit: int = 50, sort: str = "newest"):
        factory = self._factory()
        if not factory:
            return [], 0
        join_sql, where_sql, params = self._build_query_conditions(query)
        sort_sql = "ORDER BY p.created_at DESC"
        
        price_col = "COALESCE(p.mrp_per_case, p.mrp)" if query.get("role") == "wholesaler" else "p.mrp"
        
        if sort == "price_asc":
            sort_sql = f"ORDER BY {price_col} ASC NULLS LAST"
        elif sort == "price_desc":
            sort_sql = f"ORDER BY {price_col} DESC NULLS LAST"
        elif sort == "name_asc":
            sort_sql = "ORDER BY p.name ASC"
        elif sort == "name_desc":
            sort_sql = "ORDER BY p.name DESC"
        params_with_pagination = {**params, "skip": skip, "limit": limit}

        count_sql = f"SELECT COUNT(*) FROM {self.TABLE} p {join_sql} WHERE {where_sql}"
        query_sql = f"""
            SELECT p.id, p.external_id, p.name, p.description, p.sku, p.category, p.sub_category, p.brand,
                   p.mrp, p.mrp_per_case, p.quantity_per_case, p.stock, p.is_active, p.created_at, p.updated_at
            FROM {self.TABLE} p
            {join_sql} WHERE {where_sql} {sort_sql} LIMIT :limit OFFSET :skip
        """
        async with factory() as session:
            total_count = (await session.execute(text(count_sql), params)).scalar() or 0
            if total_count == 0:
                return [], 0
            rows = (await session.execute(text(query_sql), params_with_pagination)).fetchall()
            children_map = await self._fetch_children_for_products(session, [int(r.id) for r in rows])

        return [self._row_to_doc(r, children_map[int(r.id)]) for r in rows], total_count

    async def get_facets(self, query: Dict) -> Dict[str, List[str]]:
        factory = self._factory()
        if not factory:
            return {"brands": [], "categories": [], "subCategories": []}
        join_sql, where_sql, params = self._build_query_conditions(query)
        facet_sql = f"""
            SELECT 'brand' AS facet_type, p.brand AS val FROM {self.TABLE} p {join_sql}
                WHERE {where_sql} AND p.brand IS NOT NULL GROUP BY p.brand
            UNION ALL
            SELECT 'category', p.category FROM {self.TABLE} p {join_sql}
                WHERE {where_sql} AND p.category IS NOT NULL GROUP BY p.category
            UNION ALL
            SELECT 'subCategory', p.sub_category FROM {self.TABLE} p {join_sql}
                WHERE {where_sql} AND p.sub_category IS NOT NULL GROUP BY p.sub_category
        """
        facets: Dict[str, List[str]] = {"brands": [], "categories": [], "subCategories": []}
        async with factory() as session:
            for row in (await session.execute(text(facet_sql), params)).fetchall():
                if row.facet_type == "brand":
                    facets["brands"].append(row.val)
                elif row.facet_type == "category":
                    facets["categories"].append(row.val)
                elif row.facet_type == "subCategory":
                    facets["subCategories"].append(row.val)
        facets["brands"].sort()
        facets["categories"].sort()
        facets["subCategories"].sort()
        return facets

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        factory = self._factory()
        if not factory:
            return []
        join_sql, where_sql, params = self._build_query_conditions(query or {})
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"""
                SELECT p.id, p.external_id, p.name, p.description, p.sku, p.category, p.sub_category, p.brand,
                       p.mrp, p.mrp_per_case, p.quantity_per_case, p.stock, p.is_active, p.created_at, p.updated_at
                FROM {self.TABLE} p {join_sql} WHERE {where_sql} ORDER BY p.id ASC
            """),
                    params,
                )
            ).fetchall()
            children_map = await self._fetch_children_for_products(session, [int(r.id) for r in rows])
        return [self._row_to_doc(r, children_map[int(r.id)]) for r in rows]

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
            row = (
                await session.execute(
                    text(f"""
                SELECT p.id, p.external_id, p.name, p.description, p.sku, p.category, p.sub_category, p.brand,
                       p.mrp, p.mrp_per_case, p.quantity_per_case, p.stock, p.is_active, p.created_at, p.updated_at
                FROM {self.TABLE} p WHERE p.id = :id
            """),
                    {"id": pid},
                )
            ).fetchone()
            if not row:
                return None
            children_map = await self._fetch_children_for_products(session, [pid])
        return self._row_to_doc(row, children_map[pid])

    async def _replace_children(self, session, pid: int, data: Dict):
        # Delete old
        await session.execute(text("DELETE FROM sj_product_images WHERE product_id = :pid"), {"pid": pid})
        await session.execute(text("DELETE FROM sj_product_videos WHERE product_id = :pid"), {"pid": pid})
        await session.execute(text("DELETE FROM sj_product_tags WHERE product_id = :pid"), {"pid": pid})
        # await session.execute(text("DELETE FROM sj_product_attributes WHERE product_id = :pid"), {"pid": pid})
        await session.execute(text("DELETE FROM sj_product_details WHERE product_id = :pid"), {"pid": pid})
        # cascades to options

        # Insert variants
        await session.execute(text("DELETE FROM sj_product_variant_attributes WHERE product_id = :pid"), {"pid": pid})
        for attr in data.get("variantAttributes") or []:
            await session.execute(
                text("INSERT INTO sj_product_variant_attributes (product_id, attribute_name) VALUES (:pid, :attr)"),
                {"pid": pid, "attr": str(attr)}
            )
            
        await session.execute(text("DELETE FROM sj_product_variants WHERE product_id = :pid"), {"pid": pid})
        for variant in data.get("variants") or []:
            await session.execute(
                text("INSERT INTO sj_product_variants (product_id, sku, price, price_per_case, stock) VALUES (:pid, :sku, :price, :price_per_case, :stock)"),
                {"pid": pid, "sku": variant.get("sku"), "price": variant.get("price"), "price_per_case": variant.get("pricePerCase"), "stock": variant.get("stock", 0)}
            )
            vid = (await session.execute(text("SELECT LAST_INSERT_ID()"))).scalar()
            attrs = variant.get("attributes") or {}
            for k, v in attrs.items():
                await session.execute(
                    text("INSERT INTO sj_product_variant_combo_attrs (variant_id, attr_name, attr_value) VALUES (:vid, :k, :v)"),
                    {"vid": vid, "k": str(k), "v": str(v)}
                )


        # Insert images
        images = data.get("images") or []
        for i, img in enumerate(images):
            await session.execute(
                text("INSERT INTO sj_product_images (product_id, image_url, order_index) VALUES (:pid, :img, :idx)"),
                {"pid": pid, "img": img, "idx": i},
            )

        # Insert videos
        videos = data.get("videos") or []
        for i, vid in enumerate(videos):
            await session.execute(
                text("INSERT INTO sj_product_videos (product_id, video_url, order_index) VALUES (:pid, :vid, :idx)"),
                {"pid": pid, "vid": vid, "idx": i},
            )

        # Insert tags
        for tag in data.get("tags") or []:
            await session.execute(
                text("INSERT INTO sj_product_tags (product_id, tag) VALUES (:pid, :tag)"), {"pid": pid, "tag": tag}
            )

        # Insert attributes
        # for attr in data.get("variantAttributes") or []:
        # await session.execute(
        # text("INSERT INTO sj_product_attributes (product_id, attr_name) VALUES (:pid, :attr)"),
        # {"pid": pid, "attr": attr},
        # )
        #         # Insert details
        for k, v in (data.get("details") or {}).items():
            await session.execute(
                text("INSERT INTO sj_product_details (product_id, detail_key, detail_value) VALUES (:pid, :k, :v)"),
                {"pid": pid, "k": k, "v": str(v)},
            )

        # Insert combinations
        # for combo in data.get("variantCombinations") or []:
        # res = await session.execute(
        # text(
        # "INSERT INTO sj_product_variant_combinations (product_id, sku, price, stock) VALUES (:pid, :sku, :price, :stock)"
        # ),
        # {"pid": pid, "sku": combo.get("sku"), "price": combo.get("price"), "stock": combo.get("stock")},
        # )
        # combo_id = res.lastrowid
        #         # for attr_name, attr_value in (combo.get("attributes") or {}).items():
        # await session.execute(
        # text(
        # "INSERT INTO sj_product_variant_options (combination_id, attr_name, attr_value) VALUES (:cid, :k, :v)"
        # ),
        # {"cid": combo_id, "k": attr_name, "v": attr_value},
        # )
    async def create(self, data: Dict) -> Dict:
        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        now = now_utc()
        external_id = secrets.token_hex(16)

        async with factory() as session:
            await session.execute(
                text(f"""
                    INSERT INTO {self.TABLE} (
                        external_id, name, description, sku, category, sub_category, brand,
                        mrp, mrp_per_case, quantity_per_case, stock, is_active, created_at, updated_at
                    ) VALUES (
                        :external_id, :name, :description, :sku, :category, :sub_category, :brand,
                        :mrp, :mrp_per_case, :quantity_per_case, :stock, :is_active, :created_at, :updated_at
                    )
                """),
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
                    "is_active": 1 if data.get("isActive", True) else 0,
                    
                    
                    "created_at": now,
                    "updated_at": now,
                },
            )
            pid = (
                await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": external_id}
                )
            ).scalar()
            await self._replace_children(session, pid, data)
            await session.commit()
        return await self.findById(str(pid))

    async def update(self, id: str, update_data: Dict) -> Optional[Dict]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = {**existing, **update_data}
        factory = self._factory()
        now = now_utc()
        pid = int(id) if str(id).isdigit() else 0

        async with factory() as session:
            await session.execute(
                text(f"""
                UPDATE {self.TABLE} SET name = :name, description = :description, sku = :sku, category = :category,
                    sub_category = :sub_category, brand = :brand, mrp = :mrp, mrp_per_case = :mrp_per_case,
                    quantity_per_case = :quantity_per_case, stock = :stock, is_active = :is_active, updated_at = :updated_at
                WHERE id = :id
            """),
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
                    "is_active": 1 if merged.get("isActive", True) else 0,
                    
                    
                    "updated_at": now,
                },
            )
            await self._replace_children(session, pid, merged)
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else 0
        async with factory() as session:
            result = await session.execute(text(f"DELETE FROM {self.TABLE} WHERE id = :id"), {"id": pid})
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
        return len(await self.findAll(query))

    find_all = findAll
    find_by_id = findById
    find_one = findOne
