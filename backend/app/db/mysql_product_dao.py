"""
MySQL DAO for sj_products (Fully Relational).
"""

import json
import secrets

from typing import Any, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc
from app.models.daos import Product, ProductInternalCreate, ProductInternalUpdate
from app.models.product import Product


class MySQLProductDAO:
    @property
    def TABLE(self):
        suffix = (settings.table_suffix if settings.table_suffix is not None else "")
        return f"sj_products{suffix}"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_product(self, r, children: Any) -> Product:
        return Product(
            id=str(r.id),
            product_id=r.id,
            product_id_formatted=f"PDT-{r.id}",
            name=r.name,
            description=r.description,
            sku=r.sku,
            category=r.category,
            sub_category=r.sub_category,
            brand=r.brand,
            mrp=float(r.mrp) if r.mrp is not None else None,
            mrp_per_case=float(r.mrp_per_case) if r.mrp_per_case is not None else None,
            quantity_per_case=int(r.quantity_per_case) if r.quantity_per_case is not None else None,
            stock=int(r.stock) if r.stock is not None else 0,
            rating=float(r.rating) if r.rating is not None else 0.0,
            reviews=int(r.reviews) if r.reviews is not None else 0,
            images=children["images"] if "images" in children else [],
            videos=children["videos"] if "videos" in children else [],
            is_active=bool(r.is_active) if r.is_active is not None else True,
            tags=children["tags"] if "tags" in children else [],
            variant_attributes=children["variantAttributes"] if "variantAttributes" in children else [],
            variants=children["variants"] if "variants" in children else [],
            details=children["details"] if "details" in children else {},
            sellers=children["sellers"] if "sellers" in children else [],
            created_at=r.created_at,
            updated_at=r.updated_at
        )

    def _build_query_conditions(self, query: Any) -> tuple[str, str, Dict]:
        where_clauses = []
        params = {}
        join_sql = ""

        if "my_seller_id" in query:
            my_seller_id = query["my_seller_id"]
            join_sql = " JOIN sj_product_sellers ps ON ps.product_id = p.external_id "
            where_clauses.append("ps.seller_id = :my_seller_id")
            params["my_seller_id"] = str(my_seller_id)
        elif "seller_ids" in query:
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
        elif (query["includeInactive"] if "includeInactive" in query else None) is not True:
            where_clauses.append("p.is_active = 1")

        price_col = "COALESCE(p.mrp_per_case, p.mrp)" if (query["role"] if "role" in query else None) == "wholesaler" else "p.mrp"
        if "minPrice" in query and query["minPrice"]:
            where_clauses.append(f"{price_col} >= :minPrice")
            params["minPrice"] = float(query["minPrice"])
        if "maxPrice" in query and query["maxPrice"]:
            where_clauses.append(f"{price_col} <= :maxPrice")
            params["maxPrice"] = float(query["maxPrice"])

        availability = ((query["availability"] if "availability" in query else None) or "").strip().lower()
        if availability == "available":
            where_clauses.append("p.stock > 0")
        elif availability == "stock_out":
            where_clauses.append("p.stock <= 0")

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        return join_sql, where_sql, params

    async def _fetch_children_for_products(self, session, pids: List[int]) -> Any:
        children_map = {
            pid: {"images": [], "videos": [], "tags": [], "variantAttributes": [], "variants": [], "details": {}, "sellers": []}
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
                v = VariantOption(sku=r.sku, price=float(r.price) if r.price is not None else None, pricePerCase=float(r.price_per_case) if r.price_per_case is not None else None, stock=int(r.stock) if r.stock is not None else 0, attributes={})
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
                        variants_by_id[ar.variant_id].attributes[ar.attr_name] = ar.attr_value
                        # Sellers
            ext_placeholders = ", ".join([f"'PDT-{k}'" for k in chunk])
            res = await session.execute(
                text(f"SELECT product_id, seller_id, stock, is_active, request_status FROM sj_product_sellers WHERE product_id IN ({ext_placeholders})")
            )
            for r in res.fetchall():
                # Convert PDT-123 back to 123
                pid_int = int(r.product_id.replace("PDT-", ""))
                children_map[pid_int]["sellers"].append(
                    ProductSellerEntry(
                        sellerId=r.seller_id,
                        stock=int(r.stock) if r.stock is not None else 0,
                        isActive=bool(r.is_active),
                        requestStatus=r.request_status,
                        notes=None
                    )
                )

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
        
        price_col = "COALESCE(p.mrp_per_case, p.mrp)" if (query["role"] if "role" in query else None) == "wholesaler" else "p.mrp"
        
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
                   p.mrp, p.mrp_per_case, p.quantity_per_case, p.stock, p.is_active, p.rating, p.reviews, p.created_at, p.updated_at
            FROM {self.TABLE} p
            {join_sql} WHERE {where_sql} {sort_sql} LIMIT :limit OFFSET :skip
        """
        async with factory() as session:
            total_count = (await session.execute(text(count_sql), params)).scalar() or 0
            if total_count == 0:
                return [], 0
            rows = (await session.execute(text(query_sql), params_with_pagination)).fetchall()
            children_map = await self._fetch_children_for_products(session, [int(r.id) for r in rows])

        return [self._row_to_product(r, children_map[int(r.id)]) for r in rows], total_count

    async def get_facets(self, query: Any) -> Any:
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

    async def findAll(self, query: Optional[Any] = None) -> List[Product]:
        factory = self._factory()
        if not factory:
            return []
        join_sql, where_sql, params = self._build_query_conditions(query or {})
        async with factory() as session:
            rows = (
                await session.execute(
                    text(f"""
                SELECT p.id, p.external_id, p.name, p.description, p.sku, p.category, p.sub_category, p.brand,
                       p.mrp, p.mrp_per_case, p.quantity_per_case, p.stock, p.is_active, p.rating, p.reviews, p.created_at, p.updated_at
                FROM {self.TABLE} p {join_sql} WHERE {where_sql} ORDER BY p.id ASC
            """),
                    params,
                )
            ).fetchall()
            children_map = await self._fetch_children_for_products(session, [int(r.id) for r in rows])
        return [self._row_to_product(r, children_map[int(r.id)]) for r in rows]

    async def findOne(self, query: Any) -> Optional[Product]:
        if set(query.keys()) in ({"_id"}, {"id"}):
            return await self.findById((query["_id"] if "_id" in query else None) or (query["id"] if "id" in query else None))
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Product]:
        factory = self._factory()
        if not factory:
            return None
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            row = (
                await session.execute(
                    text(f"""
                SELECT p.id, p.external_id, p.name, p.description, p.sku, p.category, p.sub_category, p.brand,
                       p.mrp, p.mrp_per_case, p.quantity_per_case, p.stock, p.is_active, p.rating, p.reviews, p.created_at, p.updated_at
                FROM {self.TABLE} p WHERE p.id = :id
            """),
                    {"id": pid},
                )
            ).fetchone()
            if not row:
                return None
            children_map = await self._fetch_children_for_products(session, [pid])
        return self._row_to_product(row, children_map[pid])

    async def _replace_children(self, session, pid: int, data: Any):
        # Delete old
        await session.execute(text("DELETE FROM sj_product_images WHERE product_id = :pid"), {"pid": pid})
        await session.execute(text("DELETE FROM sj_product_videos WHERE product_id = :pid"), {"pid": pid})
        await session.execute(text("DELETE FROM sj_product_tags WHERE product_id = :pid"), {"pid": pid})
        # await session.execute(text("DELETE FROM sj_product_attributes WHERE product_id = :pid"), {"pid": pid})
        await session.execute(text("DELETE FROM sj_product_details WHERE product_id = :pid"), {"pid": pid})
        # cascades to options

        # Insert variants
        await session.execute(text("DELETE FROM sj_product_variant_attributes WHERE product_id = :pid"), {"pid": pid})
        for attr in (data.variantAttributes if data.variantAttributes is not None else []) or []:
            await session.execute(
                text("INSERT INTO sj_product_variant_attributes (product_id, attribute_name) VALUES (:pid, :attr)"),
                {"pid": pid, "attr": str(attr)}
            )
            
        await session.execute(text("DELETE FROM sj_product_variants WHERE product_id = :pid"), {"pid": pid})
        for variant in (data.variants if data.variants is not None else []) or []:
            await session.execute(
                text("INSERT INTO sj_product_variants (product_id, sku, price, price_per_case, stock) VALUES (:pid, :sku, :price, :price_per_case, :stock)"),
                {"pid": pid, "sku": (variant["sku"] if "sku" in variant else None), "price": (variant["price"] if "price" in variant else None), "price_per_case": (variant["pricePerCase"] if "pricePerCase" in variant else None), "stock": (variant["stock"] if "stock" in variant else 0)}
            )
            vid = (await session.execute(text("SELECT LAST_INSERT_ID()"))).scalar()
            attrs = (variant["attributes"] if "attributes" in variant else None) or {}
            for k, v in attrs.items():
                await session.execute(
                    text("INSERT INTO sj_product_variant_combo_attrs (variant_id, attr_name, attr_value) VALUES (:vid, :k, :v)"),
                    {"vid": vid, "k": str(k), "v": str(v)}
                )


        # Insert images
        images = (data.images if data.images is not None else []) or []
        for i, img in enumerate(images):
            await session.execute(
                text("INSERT INTO sj_product_images (product_id, image_url, order_index) VALUES (:pid, :img, :idx)"),
                {"pid": pid, "img": img, "idx": i},
            )

        # Insert videos
        videos = (data.videos if data.videos is not None else []) or []
        for i, vid in enumerate(videos):
            await session.execute(
                text("INSERT INTO sj_product_videos (product_id, video_url, order_index) VALUES (:pid, :vid, :idx)"),
                {"pid": pid, "vid": vid, "idx": i},
            )

        # Insert tags
        for tag in (data.tags if data.tags is not None else []) or []:
            await session.execute(
                text("INSERT INTO sj_product_tags (product_id, tag) VALUES (:pid, :tag)"), {"pid": pid, "tag": tag}
            )

        # Insert attributes
        # for attr in (data.variantAttributes if data.variantAttributes is not None else []) or []:
        # await session.execute(
        # text("INSERT INTO sj_product_attributes (product_id, attr_name) VALUES (:pid, :attr)"),
        # {"pid": pid, "attr": attr},
        # )
        # 
        # Insert details
        for k, v in (data.details or {}).items():
            await session.execute(
                text("INSERT INTO sj_product_details (product_id, detail_key, detail_value) VALUES (:pid, :k, :v)"),
                {"pid": pid, "k": k, "v": str(v)},
            )
            
        # Insert sellers
        await session.execute(text("DELETE FROM sj_product_sellers WHERE product_id = :pid_ext"), {"pid_ext": f"PDT-{pid}"})
        for seller in (data.sellers if data.sellers is not None else []):
            # seller might be a dict if it came from merged_dict or it might be ProductSellerEntry
            s_id = seller.sellerId
            s_stock = seller.stock
            s_active = seller.isActive
            s_status = seller.requestStatus
            
            await session.execute(
                text("INSERT INTO sj_product_sellers (product_id, seller_id, stock, is_active, request_status) VALUES (:pid_ext, :seller_id, :stock, :is_active, :request_status)"),
                {
                    "pid_ext": f"PDT-{pid}", 
                    "seller_id": str(s_id), 
                    "stock": int(s_stock) if s_stock is not None else 0, 
                    "is_active": 1 if s_active else 0, 
                    "request_status": str(s_status) if s_status else "pending"
                }
            )


        # Insert combinations
        # for combo in data.variantCombinations or []:
        # res = await session.execute(
        # text(
        # "INSERT INTO sj_product_variant_combinations (product_id, sku, price, stock) VALUES (:pid, :sku, :price, :stock)"
        # ),
        # {"pid": pid, "sku": (combo["sku"] if "sku" in combo else None), "price": (combo["price"] if "price" in combo else None), "stock": (combo["stock"] if "stock" in combo else None)},
        # )
        # combo_id = res.lastrowid
        #         # for attr_name, attr_value in ((combo["attributes"] if "attributes" in combo else None) or {}).items():
        # await session.execute(
        # text(
        # "INSERT INTO sj_product_variant_options (combination_id, attr_name, attr_value) VALUES (:cid, :k, :v)"
        # ),
        # {"cid": combo_id, "k": attr_name, "v": attr_value},
        # )
    async def create(self, data: 'ProductInternalCreate') -> Any:
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
                    "name": data.name,
                    "description": data.description,
                    "sku": data.sku,
                    "category": data.category,
                    "sub_category": data.subCategory,
                    "brand": data.brand,
                    "mrp": data.mrp,
                    "mrp_per_case": data.mrpPerCase,
                    "quantity_per_case": data.quantityPerCase,
                    "stock": data.stock if data.stock is not None else 0,
                    "is_active": 1 if data.isActive else 0,
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

    async def update(self, id: str, update_data: 'ProductInternalUpdate') -> Optional[Product]:
        existing = await self.findById(id)
        if not existing:
            return None
        from app.models.daos import ProductInternalUpdate
        existing = await self.findById(id)
        if not existing:
            return None
        from app.models.daos import ProductInternalUpdate
        merged = ProductInternalUpdate(
            name=update_data.name if update_data.name is not None else existing.name,
            description=update_data.description if update_data.description is not None else existing.description,
            sku=update_data.sku if update_data.sku is not None else existing.sku,
            category=update_data.category if update_data.category is not None else existing.category,
            subCategory=update_data.subCategory if update_data.subCategory is not None else existing.subCategory,
            brand=update_data.brand if update_data.brand is not None else existing.brand,
            mrp=update_data.mrp if update_data.mrp is not None else existing.mrp,
            mrpPerCase=update_data.mrpPerCase if update_data.mrpPerCase is not None else existing.mrpPerCase,
            quantityPerCase=update_data.quantityPerCase if update_data.quantityPerCase is not None else existing.quantityPerCase,
            stock=update_data.stock if update_data.stock is not None else existing.stock,
            isActive=update_data.isActive if update_data.isActive is not None else existing.isActive,
            rating=update_data.rating if update_data.rating is not None else existing.rating,
            reviews=update_data.reviews if update_data.reviews is not None else existing.reviews,
            images=update_data.images if update_data.images is not None else existing.images,
            tags=update_data.tags if update_data.tags is not None else existing.tags,
            videos=update_data.videos if update_data.videos is not None else existing.videos,
            sellers=update_data.sellers if update_data.sellers is not None else existing.sellers,
            details=update_data.details if update_data.details is not None else existing.details,
            variantAttributes=update_data.variantAttributes if update_data.variantAttributes is not None else existing.variantAttributes,
            variants=update_data.variants if update_data.variants is not None else existing.variants
        )
        factory = self._factory()
        now = now_utc()
        pid = int(id) if str(id).isdigit() else None

        async with factory() as session:
            await session.execute(
                text(f"""
                UPDATE {self.TABLE} SET name = :name, description = :description, sku = :sku, category = :category,
                    sub_category = :sub_category, brand = :brand, mrp = :mrp, mrp_per_case = :mrp_per_case,
                    quantity_per_case = :quantity_per_case, stock = :stock, is_active = :is_active, rating = :rating, reviews = :reviews, updated_at = :updated_at
                WHERE id = :id
            """),
                {
                    "id": pid,
                    "name": merged.name,
                    "description": merged.description,
                    "sku": merged.sku,
                    "category": merged.category,
                    "sub_category": merged.subCategory,
                    "brand": merged.brand,
                    "mrp": merged.mrp,
                    "mrp_per_case": merged.mrpPerCase,
                    "quantity_per_case": merged.quantityPerCase,
                    "stock": merged.stock,
                    "is_active": 1 if (merged.isActive if merged.isActive is not None else True) else None,
                    "rating": (merged.rating if merged.rating is not None else 0.0),
                    "reviews": (merged.reviews if merged.reviews is not None else 0),
                    "updated_at": now,
                },
            )
            await self._replace_children(session, pid, merged)
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            result = await session.execute(text(f"DELETE FROM {self.TABLE} WHERE id = :id"), {"id": pid})
            await session.commit()
            return result.rowcount > 0

    async def deleteMany(self, query: Any) -> Any:
        docs = await self.findAll(query)
        deleted = 0
        for d in docs:
            if await self.delete(d._id):
                deleted += 1
        return {"deletedCount": deleted}

    async def count(self, query: Optional[Any] = None) -> int:
        return len(await self.findAll(query))

    find_all = findAll
    find_by_id = findById
    find_one = findOne
