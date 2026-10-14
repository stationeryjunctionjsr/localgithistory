"""
MySQL DAO for sj_products (Fully Relational).
"""

from app.models.schemas import ProductSellerEntry, VariantOption
import json

from datetime import datetime
from typing import Any, List, Optional, Set

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc
from app.models.daos import ProductInternalCreate, ProductInternalUpdate
from app.models.product import Product, ProductFilter, ProductCatalogQuery, ProductFacets


class MySQLProductDAO:
    @property
    def TABLE(self):
        return "sj_products"

    def _row_to_product(self, r, children: dict) -> Product:
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
            weight_grams=int(r.weight_grams) if r.weight_grams is not None else 200,
            length_cm=float(r.length_cm) if r.length_cm is not None else None,
            width_cm=float(r.width_cm) if r.width_cm is not None else None,
            height_cm=float(r.height_cm) if r.height_cm is not None else None,
            hsn_code=str(r.hsn_code) if r.hsn_code is not None else None,
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

    def _build_query_conditions(self, filter: Optional[ProductFilter] = None):
        where_clauses: list[str] = []
        params = {}
        join_sql = ""

        if filter:
            if filter.my_seller_id:
                join_sql = " JOIN sj_product_sellers ps ON ps.product_id = CONCAT('PDT-', p.id) "
                where_clauses.append("ps.seller_id = :my_seller_id")
                params["my_seller_id"] = filter.my_seller_id
            elif filter.seller_ids:
                seller_ids = filter.seller_ids
                if not seller_ids:
                    where_clauses.append("1=0")
                else:
                    join_sql = " JOIN sj_product_sellers ps ON ps.product_id = CONCAT('PDT-', p.id) "
                    where_clauses.append("ps.is_active = 1")
                    where_clauses.append("ps.request_status = 'approved'")
                    s_placeholders = []
                    for i, sid in enumerate(seller_ids):
                        p_name = f"sid_{i}"
                        s_placeholders.append(f":{p_name}")
                        params[p_name] = sid
                    where_clauses.append(f"ps.seller_id IN ({', '.join(s_placeholders)})")

            if filter.id is not None:
                where_clauses.append("p.id = :id")
                params["id"] = filter.id

            if filter.name:
                where_clauses.append("p.name = :name")
                params["name"] = filter.name

            if filter.category:
                where_clauses.append("p.category = :category")
                params["category"] = filter.category

            if filter.sku:
                where_clauses.append("p.sku = :sku")
                params["sku"] = filter.sku

            if filter.categories:
                cats = [c.strip() for c in filter.categories.split(",") if c.strip()]
                if cats:
                    cat_params = {f"cat_{i}": c for i, c in enumerate(cats)}
                    params.update(cat_params)
                    cat_placeholders = ", ".join([f":{k}" for k in cat_params.keys()])
                    where_clauses.append(f"p.category IN ({cat_placeholders})")

            if filter.sub_category:
                where_clauses.append("p.sub_category = :subCategory")
                params["subCategory"] = filter.sub_category

            if filter.brand:
                brands = [b.strip().lower() for b in filter.brand.split(",") if b.strip()]
                if brands:
                    brand_params = {f"brand_{i}": b for i, b in enumerate(brands)}
                    params.update(brand_params)
                    brand_placeholders = ", ".join([f":{k}" for k in brand_params.keys()])
                    where_clauses.append(f"LOWER(p.brand) IN ({brand_placeholders})")

            if filter.search:
                term = filter.search.strip()
                where_clauses.append("MATCH (name, brand, category) AGAINST (:search_term IN BOOLEAN MODE)")
                boolean_term = " ".join(f"+{t}*" for t in term.split() if t.strip())
                params["search_term"] = boolean_term

            if filter.allowed_ids is not None:
                if not filter.allowed_ids:
                    where_clauses.append("1=0")
                else:
                    chunks = [filter.allowed_ids[i : i + 999] for i in range(0, len(filter.allowed_ids), 999)]
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

            if filter.is_active is not None:
                is_active = 1 if filter.is_active else 0
                where_clauses.append("p.is_active = :isActive")
                params["isActive"] = is_active
            elif not filter.include_inactive:
                where_clauses.append("p.is_active = 1")

            price_col = "COALESCE(p.mrp_per_case, p.mrp)" if filter.role == "wholesaler" else "p.mrp"
            if filter.min_price is not None:
                where_clauses.append(f"{price_col} >= :minPrice")
                params["minPrice"] = filter.min_price
            if filter.max_price is not None:
                where_clauses.append(f"{price_col} <= :maxPrice")
                params["maxPrice"] = filter.max_price

            availability = (filter.availability or "").strip().lower()
            if availability == "available":
                where_clauses.append("p.stock > 0")
            elif availability == "stock_out":
                where_clauses.append("p.stock <= 0")
        else:
            where_clauses.append("p.is_active = 1")

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        return join_sql, where_sql, params

    async def _fetch_children_for_products(self, session, pids: List[int]) -> dict[int, dict]:
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

    async def find_paginated(
        self, filter: ProductFilter, skip: int = 0, limit: int = 50, sort: str = "newest"
    ) -> tuple[List[Product], int]:
        join_sql, where_sql, params = self._build_query_conditions(filter)
        sort_sql = "ORDER BY p.created_at DESC"
        
        price_col = "COALESCE(p.mrp_per_case, p.mrp)" if filter.role == "wholesaler" else "p.mrp"
        
        if sort == "price_asc":
            sort_sql = f"ORDER BY ({price_col} IS NULL) ASC, {price_col} ASC"
        elif sort == "price_desc":
            sort_sql = f"ORDER BY ({price_col} IS NULL) ASC, {price_col} DESC"
        elif sort == "name_asc":
            sort_sql = "ORDER BY p.name ASC"
        elif sort == "name_desc":
            sort_sql = "ORDER BY p.name DESC"

        count_sql = f"SELECT COUNT(*) FROM {self.TABLE} p {join_sql} WHERE {where_sql}"
        query_sql = f"""
            SELECT p.id, p.name, p.description, p.sku, p.category, p.sub_category, p.brand,
                   p.mrp, p.mrp_per_case, p.quantity_per_case, p.stock, p.is_active, p.rating, p.reviews,
                   p.weight_grams, p.length_cm, p.width_cm, p.height_cm, p.hsn_code, p.created_at, p.updated_at
            FROM {self.TABLE} p
            {join_sql} WHERE {where_sql} {sort_sql} LIMIT :limit OFFSET :skip
        """
        async_session = get_async_session_factory()
        async with async_session() as session:
            total_count = (await session.execute(text(count_sql), params)).scalar() or 0
            if total_count == 0:
                return [], 0
            params["skip"] = skip
            params["limit"] = limit
            rows = (await session.execute(text(query_sql), params)).fetchall()
            children_map = await self._fetch_children_for_products(session, [r.id for r in rows])

        return [self._row_to_product(r, children_map[r.id]) for r in rows], total_count

    async def get_facets(self, filter: ProductFilter) -> ProductFacets:
        join_sql, where_sql, params = self._build_query_conditions(filter)
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
        brands = []
        categories = []
        sub_categories = []
        async_session = get_async_session_factory()
        async with async_session() as session:
            for row in (await session.execute(text(facet_sql), params)).fetchall():
                if row.facet_type == "brand":
                    brands.append(row.val)
                elif row.facet_type == "category":
                    categories.append(row.val)
                elif row.facet_type == "subCategory":
                    sub_categories.append(row.val)
        brands.sort()
        categories.sort()
        sub_categories.sort()
        return ProductFacets(brands=brands, categories=categories, sub_categories=sub_categories)

    async def get_active_products_count(self) -> int:
        """Returns count of active products directly via SQL pushdown without loading products."""
        async_session = get_async_session_factory()
        async with async_session() as session:
            q = text(f"SELECT COUNT(*) FROM {self.TABLE} WHERE is_active = 1")
            return (await session.execute(q)).scalar() or 0

    async def findAll(self, filter: Optional[ProductFilter] = None) -> List[Product]:
        join_sql, where_sql, params = self._build_query_conditions(filter)
        async_session = get_async_session_factory()
        async with async_session() as session:
            rows = (
                await session.execute(
                    text(f"""
                SELECT p.id, p.name, p.description, p.sku, p.category, p.sub_category, p.brand,
                       p.mrp, p.mrp_per_case, p.quantity_per_case, p.stock, p.is_active, p.rating, p.reviews,
                       p.weight_grams, p.length_cm, p.width_cm, p.height_cm, p.hsn_code, p.created_at, p.updated_at
                FROM {self.TABLE} p {join_sql} WHERE {where_sql} ORDER BY p.id ASC
            """),
                    params,
                )
            ).fetchall()
            children_map = await self._fetch_children_for_products(session, [r.id for r in rows])
        return [self._row_to_product(r, children_map[r.id]) for r in rows]

    async def findOne(self, filter: ProductFilter) -> Optional[Product]:
        records = await self.findAll(filter)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[Product]:
        if not id:
            return None
        async_session = get_async_session_factory()
        async with async_session() as session:
            row = (
                await session.execute(
                    text(f"""
                SELECT p.id, p.name, p.description, p.sku, p.category, p.sub_category, p.brand,
                       p.mrp, p.mrp_per_case, p.quantity_per_case, p.stock, p.is_active, p.rating, p.reviews, p.created_at, p.updated_at
                FROM {self.TABLE} p WHERE p.id = :id
            """),
                    {"id": id},
                )
            ).fetchone()
            if not row:
                return None
            children_map = await self._fetch_children_for_products(session, [id])
        return self._row_to_product(row, children_map[id])

    async def findByIds(self, ids: List[int]) -> List[Product]:
        if not ids:
            return []
        return await self.findAll(ProductFilter(allowed_ids=ids))

    async def _replace_children(self, session, pid: int, data: 'CamelBaseModel'):
        fields_set = data.model_fields_set

        # Images
        if "images" in fields_set:
            await session.execute(text("DELETE FROM sj_product_images WHERE product_id = :pid"), {"pid": pid})
            images = (data.images if data.images is not None else []) or []
            for i, img in enumerate(images):
                await session.execute(
                    text("INSERT INTO sj_product_images (product_id, image_url, order_index) VALUES (:pid, :img, :idx)"),
                    {"pid": pid, "img": img, "idx": i},
                )

        # Videos
        if "videos" in fields_set:
            await session.execute(text("DELETE FROM sj_product_videos WHERE product_id = :pid"), {"pid": pid})
            videos = (data.videos if data.videos is not None else []) or []
            for i, vid in enumerate(videos):
                await session.execute(
                    text("INSERT INTO sj_product_videos (product_id, video_url, order_index) VALUES (:pid, :vid, :idx)"),
                    {"pid": pid, "vid": vid, "idx": i},
                )

        # Tags
        if "tags" in fields_set:
            await session.execute(text("DELETE FROM sj_product_tags WHERE product_id = :pid"), {"pid": pid})
            for tag in (data.tags if data.tags is not None else []) or []:
                await session.execute(
                    text("INSERT INTO sj_product_tags (product_id, tag) VALUES (:pid, :tag)"), {"pid": pid, "tag": tag}
                )

        # Details
        if "details" in fields_set:
            await session.execute(text("DELETE FROM sj_product_details WHERE product_id = :pid"), {"pid": pid})
            details = data.details
            if details is not None:
                if details.material is not None:
                    await session.execute(text("INSERT INTO sj_product_details (product_id, detail_key, detail_value) VALUES (:pid, :k, :v)"), {"pid": pid, "k": "material", "v": str(details.material)})
                if details.weight is not None:
                    await session.execute(text("INSERT INTO sj_product_details (product_id, detail_key, detail_value) VALUES (:pid, :k, :v)"), {"pid": pid, "k": "weight", "v": str(details.weight)})
                if details.dimensions is not None:
                    await session.execute(text("INSERT INTO sj_product_details (product_id, detail_key, detail_value) VALUES (:pid, :k, :v)"), {"pid": pid, "k": "dimensions", "v": str(details.dimensions)})
                if details.manufacturer is not None:
                    await session.execute(text("INSERT INTO sj_product_details (product_id, detail_key, detail_value) VALUES (:pid, :k, :v)"), {"pid": pid, "k": "manufacturer", "v": str(details.manufacturer)})
                if details.origin is not None:
                    await session.execute(text("INSERT INTO sj_product_details (product_id, detail_key, detail_value) VALUES (:pid, :k, :v)"), {"pid": pid, "k": "origin", "v": str(details.origin)})
                if details.warranty is not None:
                    await session.execute(text("INSERT INTO sj_product_details (product_id, detail_key, detail_value) VALUES (:pid, :k, :v)"), {"pid": pid, "k": "warranty", "v": str(details.warranty)})

        # Variant Attributes
        if "variant_attributes" in fields_set:
            await session.execute(text("DELETE FROM sj_product_variant_attributes WHERE product_id = :pid"), {"pid": pid})
            for attr in (data.variant_attributes if data.variant_attributes is not None else []) or []:
                await session.execute(
                    text("INSERT INTO sj_product_variant_attributes (product_id, attribute_name) VALUES (:pid, :attr)"),
                    {"pid": pid, "attr": str(attr)}
                )

        # Variants
        if "variants" in fields_set:
            await session.execute(text("DELETE FROM sj_product_variants WHERE product_id = :pid"), {"pid": pid})
            for variant in (data.variants if data.variants is not None else []) or []:
                await session.execute(
                    text("INSERT INTO sj_product_variants (product_id, sku, price, price_per_case, stock) VALUES (:pid, :sku, :price, :price_per_case, :stock)"),
                    {"pid": pid, "sku": variant.sku, "price": variant.price, "price_per_case": variant.pricePerCase, "stock": variant.stock if variant.stock is not None else 0}
                )
                vid = (await session.execute(text("SELECT LAST_INSERT_ID()"))).scalar()
                attrs = variant.attributes
                if attrs is not None:
                    if attrs.size is not None:
                        await session.execute(text("INSERT INTO sj_product_variant_combo_attrs (variant_id, attr_name, attr_value) VALUES (:vid, :k, :v)"), {"vid": vid, "k": "size", "v": str(attrs.size)})
                    if attrs.color is not None:
                        await session.execute(text("INSERT INTO sj_product_variant_combo_attrs (variant_id, attr_name, attr_value) VALUES (:vid, :k, :v)"), {"vid": vid, "k": "color", "v": str(attrs.color)})
                    if attrs.material is not None:
                        await session.execute(text("INSERT INTO sj_product_variant_combo_attrs (variant_id, attr_name, attr_value) VALUES (:vid, :k, :v)"), {"vid": vid, "k": "material", "v": str(attrs.material)})
                    if attrs.style is not None:
                        await session.execute(text("INSERT INTO sj_product_variant_combo_attrs (variant_id, attr_name, attr_value) VALUES (:vid, :k, :v)"), {"vid": vid, "k": "style", "v": str(attrs.style)})
                    if attrs.weight is not None:
                        await session.execute(text("INSERT INTO sj_product_variant_combo_attrs (variant_id, attr_name, attr_value) VALUES (:vid, :k, :v)"), {"vid": vid, "k": "weight", "v": str(attrs.weight)})
                    if attrs.flavor is not None:
                        await session.execute(text("INSERT INTO sj_product_variant_combo_attrs (variant_id, attr_name, attr_value) VALUES (:vid, :k, :v)"), {"vid": vid, "k": "flavor", "v": str(attrs.flavor)})

        # Sellers
        if "sellers" in fields_set:
            await session.execute(text("DELETE FROM sj_product_sellers WHERE product_id = :pid_ext"), {"pid_ext": f"PDT-{pid}"})
            for seller in (data.sellers if data.sellers is not None else []):
                s_entry = ProductSellerEntry.model_validate(seller)
                await session.execute(
                    text("INSERT INTO sj_product_sellers (product_id, seller_id, stock, is_active, request_status) VALUES (:pid_ext, :seller_id, :stock, :is_active, :request_status)"),
                    {
                        "pid_ext": f"PDT-{pid}", 
                        "seller_id": s_entry.seller_id, 
                        "stock": s_entry.stock if s_entry.stock is not None else 0, 
                        "is_active": 1 if s_entry.is_active else 0, 
                        "request_status": s_entry.request_status or "pending"
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
    async def create(self, data: 'ProductInternalCreate') -> 'Product':
        async_session = get_async_session_factory()
        if not async_session:
            raise RuntimeError("MySQL not configured")
        now = now_utc()

        async with async_session() as session:
            result = await session.execute(
                text(f"""
                    INSERT INTO {self.TABLE} (
                        name, description, sku, category, sub_category, brand,
                        mrp, mrp_per_case, quantity_per_case, stock, is_active, rating, reviews,
                        weight_grams, length_cm, width_cm, height_cm, hsn_code, created_at, updated_at
                    ) VALUES (
                        :name, :description, :sku, :category, :sub_category, :brand,
                        :mrp, :mrp_per_case, :quantity_per_case, :stock, :is_active, :rating, :reviews,
                        :weight_grams, :length_cm, :width_cm, :height_cm, :hsn_code, :created_at, :updated_at
                    )
                """),
                {
                    "name": data.name,
                    "description": data.description,
                    "sku": data.sku,
                    "category": data.category,
                    "sub_category": data.sub_category,
                    "brand": data.brand,
                    "mrp": data.mrp,
                    "mrp_per_case": data.mrp_per_case,
                    "quantity_per_case": data.quantity_per_case,
                    "stock": data.stock if data.stock is not None else 0,
                    "is_active": 1 if data.is_active else 0,
                    "rating": data.rating if data.rating is not None else 0.0,
                    "reviews": data.reviews if data.reviews is not None else 0,
                    "weight_grams": data.weight_grams or 200,
                    "length_cm": data.length_cm,
                    "width_cm": data.width_cm,
                    "height_cm": data.height_cm,
                    "hsn_code": data.hsn_code,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            pid = result.lastrowid
            await self._replace_children(session, pid, data)
            await session.commit()
        return await self.findById(pid)

    async def update(self, id: int, update_data: 'ProductInternalUpdate') -> Optional[Product]:
        if not id:
            return None
        now = now_utc()
        fields_set = update_data.model_fields_set

        updates = ["updated_at = :updated_at"]
        params = {"id": id, "updated_at": now}

        if "name" in fields_set:
            updates.append("name = :name")
            params["name"] = update_data.name
        if "description" in fields_set:
            updates.append("description = :description")
            params["description"] = update_data.description
        if "sku" in fields_set:
            updates.append("sku = :sku")
            params["sku"] = update_data.sku
        if "category" in fields_set:
            updates.append("category = :category")
            params["category"] = update_data.category
        if "sub_category" in fields_set:
            updates.append("sub_category = :sub_category")
            params["sub_category"] = update_data.sub_category
        if "brand" in fields_set:
            updates.append("brand = :brand")
            params["brand"] = update_data.brand
        if "mrp" in fields_set:
            updates.append("mrp = :mrp")
            params["mrp"] = update_data.mrp
        if "mrp_per_case" in fields_set:
            updates.append("mrp_per_case = :mrp_per_case")
            params["mrp_per_case"] = update_data.mrp_per_case
        if "quantity_per_case" in fields_set:
            updates.append("quantity_per_case = :quantity_per_case")
            params["quantity_per_case"] = update_data.quantity_per_case
        if "stock" in fields_set:
            updates.append("stock = :stock")
            params["stock"] = update_data.stock
        if "rating" in fields_set:
            updates.append("rating = :rating")
            params["rating"] = update_data.rating
        if "reviews" in fields_set:
            updates.append("reviews = :reviews")
            params["reviews"] = update_data.reviews
        if "weight_grams" in fields_set:
            updates.append("weight_grams = :weight_grams")
            params["weight_grams"] = update_data.weight_grams
        if "length_cm" in fields_set:
            updates.append("length_cm = :length_cm")
            params["length_cm"] = update_data.length_cm
        if "width_cm" in fields_set:
            updates.append("width_cm = :width_cm")
            params["width_cm"] = update_data.width_cm
        if "height_cm" in fields_set:
            updates.append("height_cm = :height_cm")
            params["height_cm"] = update_data.height_cm
        if "hsn_code" in fields_set:
            updates.append("hsn_code = :hsn_code")
            params["hsn_code"] = update_data.hsn_code
        if "is_active" in fields_set:
            updates.append("is_active = :is_active")
            params["is_active"] = 1 if update_data.is_active else 0

        set_sql = ", ".join(updates)
        async_session = get_async_session_factory()
        if not async_session:
            return None

        async with async_session() as session:
            res = await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            if res.rowcount == 0:
                chk = await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE id = :id"), {"id": id})
                if not chk.fetchone():
                    return None
            await self._replace_children(session, id, update_data)
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: int) -> bool:
        if not id:
            return False
        async_session = get_async_session_factory()
        if not async_session:
            return False
        async with async_session() as session:
            result = await session.execute(text(f"DELETE FROM {self.TABLE} WHERE id = :id"), {"id": id})
            await session.commit()
            return result.rowcount > 0

    async def deleteMany(self, filter: Optional[ProductFilter] = None) -> int:
        records = await self.findAll(filter)
        deleted = 0
        for r in records:
            if await self.delete(r.id):
                deleted += 1
        return deleted

    async def count(self, filter: Optional[ProductFilter] = None) -> int:
        return len(await self.findAll(filter))

    find_all = findAll
    find_by_id = findById
    find_one = findOne

    async def get_new_arrival_ids(
        self, cutoff: datetime, exclude_product_ids: Optional[Set[str]] = None, limit: int = 10
    ) -> List[str]:
        """
        Fetch active products created on or after cutoff, ordered by created_at DESC.
        """
        async_session = get_async_session_factory()
        if not async_session:
            return []

        sql = f"""
            SELECT id FROM {self.TABLE}
            WHERE is_active = 1
              AND created_at >= :cutoff
            ORDER BY created_at DESC
        """
        params = {"cutoff": cutoff}
        exclude = exclude_product_ids or set()

        async with async_session() as session:
            result = await session.execute(text(sql), params)
            out: List[str] = []
            for row in result.fetchall():
                pid = str(row.id)
                if pid not in exclude:
                    out.append(pid)
                    if len(out) >= limit:
                        break
            return out
