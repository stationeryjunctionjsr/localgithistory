from app.models.user import User
from fastapi.responses import StreamingResponse
from app.models.schemas import MessageResponse
from typing import Dict, Any, List
import csv
import io
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.models.schemas import PaginatedProductResponse, ProductCreate, ProductResponse, ProductUpdate
from app.repositories.category_repository import category_repository
from app.repositories.product_repository import product_repository
from app.utils.auth import get_current_user, require_super_admin, get_optional_user
from app.utils.cache import cache
from app.utils.logger import logger


class BulkUpdateData(BaseModel):
    ids: List[str]
    isActive: Optional[bool] = None
    isExclusive: Optional[bool] = None


router = APIRouter()


async def _upload_product_image(image: UploadFile) -> str:
    """Upload one image; validated by magic bytes, size, and extension in oci_storage."""
    from app.services.oci_storage import upload_image_and_return_path

    return await upload_image_and_return_path(image, "products", filename_prefix="product")


@router.post("/upload-images", status_code=status.HTTP_200_OK, response_model=UploadImagesResponse)
async def upload_product_images(
    images: List[UploadFile] = File(...), current_user: User = Depends(require_super_admin)
):
    """Upload product images (Super Admin only). Uses OCI Object Storage when configured."""
    try:
        image_urls = []
        for image in images:
            path = await _upload_product_image(image)
            image_urls.append(path)
        return {"images": image_urls}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("upload_product_images failed: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while uploading images: {str(e)}",
        )


@router.post("/upload-csv", status_code=status.HTTP_200_OK, response_model=UploadCSVResponse)
async def upload_csv(file: UploadFile = File(...), current_user: User = Depends(require_super_admin)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    results = []
    errors = []
    row_number = 0

    try:
        contents = await file.read()
        if len(contents) > 5 * 1024 * 1024:  # 5 MB cap
            raise HTTPException(status_code=413, detail="CSV file exceeds the 5 MB size limit")
        csv_data = list(csv.DictReader(io.StringIO(contents.decode("utf-8"))))

        # Group rows by product name
        grouped_products = {}
        for idx, row in enumerate(csv_data):
            row_num = idx + 2
            name = (row.name or "").strip()

            if not name:
                errors.append({"row": row_num, "error": "Missing product name"})
                continue

            if name not in grouped_products:
                grouped_products[name] = []

            row["_row_number"] = row_num
            grouped_products[name].append(row)

        for name, rows in grouped_products.items():
            try:
                # The first row defines the main product details
                main_row = rows[0]
                row_number = main_row["_row_number"]

                if not main_row.category or not main_row.mrp:
                    errors.append(
                        {
                            "row": row_number,
                            "product": name,
                            "error": "Missing required fields on main row: category, mrp",
                        }
                    )
                    continue

                # Check if category exists, if not assign to "Others"
                category_name = main_row.category.strip()
                existing_category = await category_repository.findByName(category_name)
                if not existing_category:
                    category_name = "Others"

                mrp_per_case = None
                if main_row.mrp_per_case and str(main_row.get("mrpPerCase", "")).strip():
                    try:
                        mrp_per_case = float(main_row.mrp_per_case)
                    except (ValueError, TypeError) as e:
                        logger.warning("Invalid mrpPerCase in CSV row %s: %s", row_number, str(e))
                qty_per_case = None
                if main_row.get("quantityPerCase") and str(main_row.get("quantityPerCase", "")).strip():
                    try:
                        qty_per_case = int(float(main_row["quantityPerCase"]))
                    except (ValueError, TypeError) as e:
                        logger.warning("Invalid quantityPerCase in CSV row %s: %s", row_number, str(e))

                product_data = {
                    "name": name,
                    "productIdFormatted": main_row.get("productId", "").strip(),
                    "sku": main_row.get("sku", "").strip(),
                    "category": category_name,
                    "subCategory": main_row.get("subCategory", "").strip(),
                    "description": main_row.get("description", "").strip(),
                    "brand": main_row.get("brand", "").strip(),
                    "collection": main_row.get("collection", "").strip() or None,
                    "mrp": float(main_row.mrp),  # MRP per unit (required)
                    "mrpPerCase": mrp_per_case,
                    "quantityPerCase": qty_per_case,
                    "stock": 0,
                    "isActive": main_row.get("isActive", "true").lower() in ["true", "1", "yes"],
                    "images": [img.strip() for img in main_row.get("images", "").split(",") if img.strip()] if main_row.get("images") else [],
                    "videos": [vid.strip() for vid in main_row.get("videos", "").split(",") if vid.strip()] if main_row.get("videos") else [],
                    "variantAttributes": [],
                    "variants": [],
                }

                variant_attributes = set()
                variants_list = []

                for row in rows:
                    try:
                        row_price = (
                            float(row.mrp) if row.mrp and str(row.mrp).strip() else product_data.mrp
                        )
                    except ValueError:
                        row_price = product_data.mrp

                    try:
                        row_stock = int(row.stock) if row.stock and str(row.stock).strip() else 0
                    except ValueError:
                        row_stock = 0

                    row_sku = (row.sku or "").strip()

                    attributes = {}
                    # dynamically look for Attribute X and Variant X columns
                    for k, v in row.items():
                        if k and k.startswith("Attribute ") and v and str(v).strip():
                            num = k.replace("Attribute ", "")
                            val_key = f"Variant {num}"
                            variant_val = row.get(val_key, "").strip()
                            if variant_val:
                                attr_name = str(v).strip()
                                attributes[attr_name] = variant_val
                                variant_attributes.add(attr_name)

                    if attributes:
                        variants_list.append(
                            {"attributes": attributes, "price": row_price, "stock": row_stock, "sku": row_sku}
                        )
                    elif len(rows) == 1:
                        # No attributes, just update base stock and sku if it's the only row
                        product_data.stock = row_stock
                        if not product_data.sku:
                            product_data.sku = row_sku

                product_data.variantAttributes = list(variant_attributes)
                product_data.variants = variants_list

                existing = None
                from app.db.storage_factory import get_storage

                products_col = get_storage("products")

                if getattr(product_data, "productIdFormatted", None):
                    existing = await products_col.findOne({"productIdFormatted": product_data.productIdFormatted})
                elif getattr(product_data, "sku", None):
                    existing = await products_col.findOne({"sku": product_data.sku})
                else:
                    # Also try matching by exact name to avoid duplicates if SKU isn't set either
                    existing = await products_col.findOne({"name": product_data.name})

                if existing:
                    await product_repository.update(existing.id, product_data)
                    product_id_to_show = getattr(product_data, "productIdFormatted", product_data.name)
                    results.append({"product": product_id_to_show, "action": "updated"})
                else:
                    await product_repository.create(product_data)
                    results.append({"product": product_data.name, "action": "created"})
            except (ValueError, TypeError, KeyError) as e:
                errors.append(
                    {"row": main_row.get("_row_number", "N/A"), "product": name, "error": f"Data error: {str(e)}"}
                )
            except Exception as e:
                logger.error("Unexpected error processing product %s in CSV: %s", name, str(e), exc_info=True)
                errors.append(
                    {"row": main_row.get("_row_number", "N/A"), "product": name, "error": f"Internal error: {str(e)}"}
                )

        _invalidate_product_caches()
        return {
            "message": "CSV upload completed",
            "successCount": len(results),
            "errorCount": len(errors),
            "results": results,
            "errors": errors if errors else [],
        }
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding. Please use UTF-8.")
    except Exception as e:
        logger.error("upload_csv failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing CSV file: {str(e)}")


@router.get("/export-csv", response_class=StreamingResponse)
async def export_csv(current_user: User = Depends(require_super_admin)):
    """
    Export all products from the Oracle database to a CSV file.
    If no products are present, only headers are returned.
    """
    products = await product_repository.findAll()

    headers = [
        "name",
        "category",
        "subCategory",
        "description",
        "brand",
        "mrp",
        "mrpPerCase",
        "quantityPerCase",
        "stock",
        "Attribute 1",
        "Variant 1",
        "Attribute 2",
        "Variant 2",
        "Attribute 3",
        "Variant 3",
        "Attribute 4",
        "Variant 4",
        "Attribute 5",
        "Variant 5",
        "images",
        "videos",
        "isActive",
        "productId",
    ]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)

    for p in products:
        name = (p.name or "")
        category = (p.category or "")
        sub_category = p.sub_category or ""
        description = p.description or ""
        brand = p.brand or ""
        mrp = (p.mrp or "")
        mrp_per_case = p.mrp_per_case if p.mrp_per_case is not None else ""
        quantity_per_case = p.quantity_per_case if p.quantity_per_case is not None else ""

        images_list = (p.images or [])
        images = ",".join(images_list) if isinstance(images_list, list) else (images_list or "")

        videos_list = (p.videos or [])
        videos = ",".join(videos_list) if isinstance(videos_list, list) else (videos_list or "")

        is_active = "true" if (p.is_active if p.is_active is not None else True) else "false"
        product_id = p.product_id_formatted or (
            f"PDT-{p.product_id}" if p.product_id is not None else ""
        )

        combinations = (p.variants or []) or []
        if combinations:
            for idx, combo in enumerate(combinations):
                combo_mrp = combo.price if combo.price is not None else mrp
                combo_stock = combo.stock if combo.stock is not None else 0

                combo_attrs = combo.get("attributes", {}) or {}
                attr_cols = [""] * 10
                for attr_idx, (attr_key, attr_val) in enumerate(list(combo_attrs.items())[:5]):
                    attr_cols[attr_idx * 2] = attr_key
                    attr_cols[attr_idx * 2 + 1] = attr_val

                if idx == 0:
                    row = [
                        name,
                        category,
                        sub_category,
                        description,
                        brand,
                        combo_mrp,
                        mrp_per_case,
                        quantity_per_case,
                        combo_stock,
                        *attr_cols,
                        images,
                        videos,
                        is_active,
                        product_id,
                    ]
                else:
                    row = [name, "", "", "", "", combo_mrp, "", "", combo_stock, *attr_cols, "", "", "", ""]
                writer.writerow(row)
        else:
            attr_cols = [""] * 10
            row = [
                name,
                category,
                sub_category,
                description,
                brand,
                mrp,
                mrp_per_case,
                quantity_per_case,
                (p.stock if p.stock is not None else 0),
                *attr_cols,
                images,
                videos,
                is_active,
                product_id,
            ]
            writer.writerow(row)

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=products.csv"},
    )


@router.get("/suggest", response_model=SearchSuggestResponse)
async def get_search_suggestions(q: str = "", limit: int = 8, pincode: str = None, role: str = "customer"):
    """Lightweight autocomplete endpoint returning matching product names, brands, and categories"""
    if len(q) < 2:
        return {"products": [], "brands": [], "categories": []}

    q_lower = q.lower()
    tokens = [t for t in q_lower.split() if t.strip()]
    if not tokens:
        return {"products": [], "brands": [], "categories": []}

    query = {"search": q, "isActive": True}
    
    serviceable_seller_ids = None
    if role == "wholesaler":
        from app.repositories.zone_seller_cache import get_super_admin_seller_id
        sa_id = await get_super_admin_seller_id()
        if sa_id:
            serviceable_seller_ids = {sa_id}
        else:
            serviceable_seller_ids = set()
    elif pincode:
        from app.repositories.zone_seller_cache import get_seller_ids_for_pincode
        serviceable_seller_ids = await get_seller_ids_for_pincode(pincode)

    if serviceable_seller_ids is not None:
        query["seller_ids"] = list(serviceable_seller_ids)

    active_products = await product_repository.storage.findAll(query)

    products = []
    brands = set()
    categories = set()

    for p in active_products:
        name = (p.name or "")
        name_lower = name.lower()
        if all(t in name_lower for t in tokens):
            if p.brand:
                brands.add(p.brand)
            if p.category:
                categories.add(p.category)
                
            if len(products) < limit:
                display_image = p.display_image or (p.images[0] if p.images else None)
                products.append({
                    "productId": str((p.id if p.id is not None else p.product_id)),
                    "name": name,
                    "productName": name,
                    "displayImage": display_image
                })
            
            if len(products) >= limit and len(brands) >= 3 and len(categories) >= 3:
                break

    return {
        "products": products,
        "suggestions": [p.name for p in products],
        "brands": list(brands)[:3],
        "categories": list(categories)[:3]
    }


async def populate_product_discounts(
    products_list: List[dict], role: str, user_id: Optional[str] = None, skinny: bool = False
):
    from app.repositories.coupon_repository import coupon_repository, get_coupon_description

    # Pre-fetch cache of active automatic product discounts
    active_discounts = await coupon_repository.get_active_automatic_product_discounts()

    # Pre-fetch all active coupons once to pass to bulk checks
    all_coupons = await coupon_repository.get_active_coupons()
    user_behavior_cache = {}

    # Filter applicable ones for the current role and user (behavior matched)
    applicable_discounts = []
    for c in active_discounts:
        if role not in (c.applicable_roles or []):
            continue
        applicable_user_ids = c.applicable_user_ids or []
        if applicable_user_ids:
            if not user_id or str(user_id) not in [str(x) for x in applicable_user_ids]:
                continue
        behavior = c.user_behavior
        if behavior and behavior != "none":
            if not user_id or not await coupon_repository._user_matches_behavior(
                user_id, behavior, user_behavior_cache=user_behavior_cache
            ):
                continue
        applicable_discounts.append(c)

    for p in products_list:
        if p.mrp is None:
            raise ValueError(f"Data Integrity Error: Product {p.id} is missing MRP")
        mrp = float(p.mrp)
        p.originalPrice = mrp

        # Check automatic product discounts
        auto_discount_pct = 0.0
        auto_discount_value = 0.0
        auto_discount_type = "percentage"
        default_coupon = None

        pid = str((p.id or ""))
        for c in applicable_discounts:
            affected = c._affected_product_ids or set()
            if pid in affected:
                pct = 0.0
                val = float(c.discount_value or 0)
                if c.discount_type == "percentage":
                    pct = val
                elif c.discount_type == "fixed":
                    if mrp > 0:
                        pct = (val / mrp) * 100
                if pct > auto_discount_pct:
                    auto_discount_pct = pct
                    auto_discount_value = val
                    auto_discount_type = c.discount_type
                    default_coupon = c

        # Apply default discount to price
        final_price = product_repository.getPriceForRole(p, role, 1, user_id=user_id)
        p.price = final_price

        if default_coupon:
            p.defaultDiscountPercentage = round(auto_discount_pct, 2)

        if mrp > 0 and final_price < mrp:
            p.discountPercentage = round(((mrp - final_price) / mrp) * 100)

        # Fast path for list endpoints
        if skinny:
            p.applicableDiscounts = []
            continue

        # Get all other applicable discounts
        other_coupons = await coupon_repository.get_applicable_discounts_for_product(
            p, role, user_id, all_coupons=all_coupons, user_behavior_cache=user_behavior_cache
        )

        # Find active quantity-based coupon if any
        qty_coupon = None
        if default_coupon and default_coupon.get("minRequirementType") == "quantity_based":
            qty_coupon = default_coupon
        else:
            for oc in other_coupons:
                if oc.get("minRequirementType") == "quantity_based":
                    qty_coupon = oc
                    break

        if qty_coupon:
            p.quantityTiers = qty_coupon.get("quantityTiers") or []
            p.quantityItemType = qty_coupon.get("applicableItemType") or "units"

        app_discs = []
        if default_coupon and default_coupon.get("minRequirementType") == "quantity_based":
            app_discs.append(
                {
                    "type": default_coupon.get("typeOfDiscount"),
                    "code": default_coupon.get("code"),
                    "description": get_coupon_description(default_coupon),
                }
            )

        for oc in other_coupons:
            app_discs.append(
                {
                    "type": oc.get("typeOfDiscount"),
                    "code": oc.get("code"),
                    "description": get_coupon_description(oc),
                }
            )

        p.applicableDiscounts = app_discs


def _invalidate_product_caches():
    cache.invalidate(get_public_products)
    cache.invalidate(get_public_product)
    cache.invalidate(get_products)
    cache.invalidate(get_product)
    try:
        from app.routers.categories import get_tag_brands

        cache.invalidate(get_tag_brands)
    except Exception:
        pass
    try:
        from app.repositories.coupon_repository import coupon_repository

        coupon_repository.invalidate_cache()
    except Exception:
        pass


@router.get("/public", response_model=PaginatedProductResponse)
@cache.ttl_cache(ttl=300.0)
async def get_public_products(
    response: Response,
    category: Optional[str] = None,
    categories: Optional[str] = None,
    subCategory: Optional[str] = None,
    search: Optional[str] = None,
    brand: Optional[str] = None,
    collection: Optional[str] = None,
    popularity: Optional[str] = None,
    minDiscount: Optional[str] = None,
    minPrice: Optional[float] = None,
    maxPrice: Optional[float] = None,
    availability: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    role: str = "customer",
    categoryTag: Optional[str] = None,
    sort: Optional[str] = None,
    includeFacets: bool = True,
    skinny: bool = False,
    pincode: Optional[str] = None,
):
    """Get all products (public endpoint - no auth required)"""
    role = "customer" # Force role to customer for public endpoint
    query = {}
    if category:
        query.category = category
    if categories:
        query["categories"] = categories  # Comma-separated list of categories
    if subCategory:
        query["subCategory"] = subCategory
    if search:
        query["search"] = search
    if brand:
        query.brand = brand
    if collection:
        query["collection"] = collection
    if categoryTag:
        query["categoryTag"] = categoryTag
    if popularity:
        query["popularity"] = popularity
    if minDiscount:
        query["minDiscount"] = minDiscount
    if minPrice is not None:
        query["minPrice"] = minPrice
    if maxPrice is not None:
        query["maxPrice"] = maxPrice
    if availability:
        query["availability"] = availability
    if sort:
        query["sort"] = sort
    query.role = role

    # Zone-based seller filter: resolve pincode → zone → seller set so only
    # products serviceable in the user's zone are returned.
    # None means pincode was not supplied or not found → fail-open (show all).
    if pincode:
        from app.repositories.zone_seller_cache import get_seller_ids_for_pincode
        seller_id_set = await get_seller_ids_for_pincode(pincode)
        if seller_id_set is not None:
            query["allowed_seller_ids"] = list(seller_id_set)

    if role == "wholesaler":
        from app.repositories.zone_seller_cache import get_super_admin_seller_id
        sa_id = await get_super_admin_seller_id()
        if sa_id:
            query["allowed_seller_ids"] = [sa_id]

    if page > 1:
        includeFacets = False

    start_index = (page - 1) * limit
    products, total_count, facets, used_fuzzy, suggested_query = await product_repository.get_catalog(
        query, skip=start_index, limit=limit, sort=sort, include_facets=includeFacets
    )

    await populate_product_discounts(products, role, skinny=skinny)

    if skinny:
        for p in products:
            p.displayImage = p.display_image or (p.images[0] if p.images else None)
            p.pop("description", None)
            p.pop("variants", None)
            p.pop("videos", None)
            p.pop("images", None)
            p.pop("applicableDiscounts", None)
            p.pop("variations", None)
            p.pop("variantAttributes", None)

    products_with_pricing = []
    for product in products:
        # Ensure tags and variations arrays exist
        if "tags" not in product or product.tags is None:
            product.tags = []
        if "variations" not in product or product.variations is None:
            product.variations = []

        products_with_pricing.append(ProductResponse(**(product if hasattr(product, 'model_dump') else product)))

    # Tell browsers and CDNs to cache public product lists for 5 minutes
    # (matches the server-side TTL cache). stale-while-revalidate allows serving
    # stale content for up to 60s more while a fresh fetch happens in the background.
    response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=60"

    return {
        "products": products_with_pricing,
        "totalCount": total_count,
        "brands": facets.get("brands", []),
        "categories": facets.get("categories", []),
        "subCategories": facets.get("subCategories", []),
        "collections": facets.get("collections", []),
        "usedFuzzy": used_fuzzy,
        "suggestedQuery": suggested_query,
    }


@router.get("/public/{product_id}", response_model=ProductResponse)
@cache.ttl_cache(ttl=900.0)
async def get_public_product(product_id: str, role: str = "customer", response: Response = None):
    """Get a single product by ID (public endpoint - no auth required)"""
    role = "customer" # Force role to customer for public endpoint
    product = await product_repository.findById(product_id)

    if not product or not (product.is_active if product.is_active is not None else True):
        raise HTTPException(status_code=404, detail="Product not found")

    # Add dynamic tags for guest users and resolve search tags
    products_list = await product_repository.add_dynamic_tags([product], role, None)
    products_list = await product_repository.resolve_search_tags(products_list)
    product = products_list[0]

    await populate_product_discounts([product], role)
    # Ensure tags and variations arrays exist
    if "tags" not in product or product.tags is None:
        product.tags = []
    if "variations" not in product or product.variations is None:
        product.variations = []

    if response:
        # 15-minute browser/CDN cache for individual product pages
        response.headers["Cache-Control"] = "public, max-age=900, stale-while-revalidate=60"

    return ProductResponse(**(product if hasattr(product, 'model_dump') else product))


@router.get("", response_model=PaginatedProductResponse)
@router.get("/", response_model=PaginatedProductResponse)
@cache.ttl_cache(ttl=60.0)
async def get_products(
    category: Optional[str] = None,
    categories: Optional[str] = None,
    subCategory: Optional[str] = None,
    search: Optional[str] = None,
    brand: Optional[str] = None,
    collection: Optional[str] = None,
    popularity: Optional[str] = None,
    minDiscount: Optional[str] = None,
    minPrice: Optional[float] = None,
    maxPrice: Optional[float] = None,
    availability: Optional[str] = None,
    categoryTag: Optional[str] = None,
    sort: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    includeFacets: bool = True,
    skinny: bool = False,
    pincode: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    # Use effectiveRole if user is deactivated
    effective_role = current_user.effective_role or (current_user.role if current_user.role is not None else "customer")
    user_id = current_user.id

    query = {}
    if category:
        query.category = category
    if categories:
        query["categories"] = categories  # Comma-separated list of categories
    if subCategory:
        query["subCategory"] = subCategory
    if search:
        query["search"] = search
    if brand:
        query.brand = brand
    if collection:
        query["collection"] = collection
    if categoryTag:
        query["categoryTag"] = categoryTag
    if popularity:
        query["popularity"] = popularity
    if minDiscount:
        query["minDiscount"] = minDiscount
    if minPrice is not None:
        query["minPrice"] = minPrice
    if maxPrice is not None:
        query["maxPrice"] = maxPrice
    if availability:
        query["availability"] = availability
    if sort:
        query["sort"] = sort
    if status == "active":
        query.is_active = True
    elif status == "inactive":
        query.is_active = False
    elif status == "all":
        query["includeInactive"] = True

    query.role = effective_role
    query["user_id"] = user_id

    if effective_role == "wholesaler":
        from app.repositories.zone_seller_cache import get_super_admin_seller_id
        sa_id = await get_super_admin_seller_id()
        if sa_id:
            query["allowed_seller_ids"] = [sa_id]
    elif pincode:
        # Zone-based seller filter for retail customers: only show products
        # serviceable in their zone. None = pincode not in any zone → fail-open.
        from app.repositories.zone_seller_cache import get_seller_ids_for_pincode
        seller_id_set = await get_seller_ids_for_pincode(pincode)
        if seller_id_set is not None:
            query["allowed_seller_ids"] = list(seller_id_set)

    if page > 1:
        includeFacets = False

    start_index = (page - 1) * limit
    products, total_count, facets, used_fuzzy, suggested_query = await product_repository.get_catalog(
        query, skip=start_index, limit=limit, sort=sort, include_facets=includeFacets
    )

    await populate_product_discounts(products, effective_role, user_id=user_id, skinny=skinny)

    if skinny:
        for p in products:
            p.displayImage = p.display_image or (p.images[0] if p.images else None)
            p.pop("description", None)
            p.pop("variants", None)
            p.pop("videos", None)
            p.pop("images", None)
            p.pop("applicableDiscounts", None)
            p.pop("variations", None)
            p.pop("variantAttributes", None)

    products_with_pricing = []
    for product in products:
        # Ensure tags and variations arrays exist
        if "tags" not in product or product.tags is None:
            product.tags = []
        if "variations" not in product or product.variations is None:
            product.variations = []

        products_with_pricing.append(ProductResponse(**(product if hasattr(product, 'model_dump') else product)))

    return {
        "products": products_with_pricing,
        "totalCount": total_count,
        "brands": facets.get("brands", []),
        "categories": facets.get("categories", []),
        "subCategories": facets.get("subCategories", []),
        "collections": facets.get("collections", []),
        "usedFuzzy": used_fuzzy,
        "suggestedQuery": suggested_query,
    }


@router.get("/{product_id}", response_model=ProductResponse)
@cache.ttl_cache(ttl=900.0)
async def get_product(product_id: str, current_user: User = Depends(get_current_user)):
    product = await product_repository.findById(product_id)

    if not product or not (product.is_active if product.is_active is not None else True):
        raise HTTPException(status_code=404, detail="Product not found")

    # Use effectiveRole if user is deactivated
    effective_role = current_user.effective_role or (current_user.role if current_user.role is not None else "customer")
    user_id = current_user.id

    # Add dynamic tags for a single product too
    products_list = await product_repository.add_dynamic_tags([product], effective_role, user_id)
    products_list = await product_repository.resolve_search_tags(products_list)
    product = products_list[0]

    await populate_product_discounts([product], effective_role, user_id=user_id)

    # Legacy - min order quantity removed but kept for backward compatibility
    if effective_role == "wholesaler":
        product.minOrderQuantity = (product.b2b_min_order_quantity if product.b2b_min_order_quantity is not None else 10)
    else:
        product.minOrderQuantity = (product.min_order_quantity if product.min_order_quantity is not None else 1)

    # Ensure tags and variations arrays exist
    if "tags" not in product or product.tags is None:
        product.tags = []
    if "variations" not in product or product.variations is None:
        product.variations = []

    return ProductResponse(**(product if hasattr(product, 'model_dump') else product))


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product_data: ProductCreate, current_user: User = Depends(require_super_admin)):
    try:
        # Check for duplicate name or SKU
        existing_products = await product_repository.findAll()
        name_lower = product_data.name.strip().lower()
        sku_lower = (product_data.sku or "").strip().lower()
        
        for p in existing_products:
            if (p.name or "").strip().lower() == name_lower:
                raise HTTPException(status_code=400, detail=f"Product with name '{product_data.name}' already exists")
            if (p.sku or "").strip().lower() == sku_lower:
                raise HTTPException(status_code=400, detail=f"Product with SKU '{product_data.sku}' already exists")
                
        product = await product_repository.create(product_data)
        _invalidate_product_caches()
        return ProductResponse(**(product if hasattr(product, 'model_dump') else product))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str, product_data: ProductUpdate, current_user: User = Depends(require_super_admin)
):
    try:
        product = await product_repository.update(product_id, product_data)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        _invalidate_product_caches()
        return ProductResponse(**(product if hasattr(product, 'model_dump') else product))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{product_id}", response_model=MessageResponse)
async def delete_product(product_id: str, current_user: User = Depends(require_super_admin)):
    product = await product_repository.delete(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    _invalidate_product_caches()
    return {"message": "Product deleted successfully"}


@router.post("/bulk-update", response_model=MessageResponse)
async def bulk_update_products(update_data: BulkUpdateData, current_user: User = Depends(require_super_admin)):
    results = []
    for product_id in update_data.ids:
        data = {}
        if update_data.isActive is not None:
            data.is_active = update_data.isActive
        if update_data.isExclusive is not None:
            data.isExclusive = update_data.isExclusive

        if data:
            await product_repository.update(product_id, data)
            results.append(product_id)

    if results:
        _invalidate_product_caches()

    return {"message": f"Successfully updated {len(results)} products", "updatedIds": results}



class UploadImagesResponse(BaseModel):
    urls: List[str]

class UploadCSVResponse(BaseModel):
    success: bool
    imported: int
    failed: int

class UploadVideosResponse(BaseModel):
    urls: List[str]

class SearchSuggestResponse(BaseModel):
    products: List[Dict[str, Any]]
    brands: List[Dict[str, Any]]
    categories: List[Dict[str, Any]]

class ProductTagAction(BaseModel):
    searchTagId: str


@router.post("/{product_id}/search-tags", response_model=Dict[str, Any])
async def add_search_tag_to_product(
    product_id: str, action: ProductTagAction, current_user: User = Depends(require_super_admin)
):
    """Add a search tag to a specific product (adds to productIds, removes from excludedProductIds)"""
    product = await product_repository.findById(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    from app.repositories.search_tag_repository import search_tag_repository

    result = await search_tag_repository.addProductId(action.searchTagId, product_id)
    if not result:
        raise HTTPException(status_code=404, detail="Search tag not found")

    return {"message": "Search tag added to product"}


@router.delete("/{product_id}/search-tags/{search_tag_id}", response_model=MessageResponse)
async def remove_search_tag_from_product(
    product_id: str, search_tag_id: str, current_user: User = Depends(require_super_admin)
):
    """Remove a search tag from a specific product (adds to excludedProductIds, removes from productIds)"""
    product = await product_repository.findById(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    from app.repositories.search_tag_repository import search_tag_repository

    result = await search_tag_repository.excludeProductId(search_tag_id, product_id)
    if not result:
        raise HTTPException(status_code=404, detail="Search tag not found")

    return {"message": "Search tag removed from product"}


@router.get("/{product_id}/search-tags", response_model=List[Dict[str, Any]])
async def get_product_search_tags(product_id: str, current_user: User = Depends(require_super_admin)):
    """Get all resolved search tags for a specific product"""
    product = await product_repository.findById(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    products_with_tags = await product_repository.resolve_search_tags([product])
    resolved = products_with_tags[0].get("searchTags", [])

    # Also return all available search tags for the add dropdown
    from app.repositories.search_tag_repository import search_tag_repository

    all_tags = await search_tag_repository.findAllActive()

    return {
        "resolvedTags": resolved,
        "allTags": [{"_id": t.id, "name": t.name, "type": getattr(t, "type", None)} for t in all_tags],
    }


class NotifyMeRequest(BaseModel):
    email: Optional[str] = None


@router.post("/{product_id}/notify-me", status_code=status.HTTP_200_OK, response_model=MessageResponse)
async def notify_me(
    product_id: str,
    data: NotifyMeRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """Register a user email for stock restock notification on a product."""
    email = None
    user_id = None
    if current_user:
        email = current_user.email
        user_id = current_user.id

    # If user is not logged in or has no email, check data.email
    if not email:
        email = data.email

    if not email or "@" not in email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="A valid email address is required for notification."
        )

    # Check if product exists
    product = await product_repository.findById(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    from app.repositories.product_notification_repository import product_notification_repository

    await product_notification_repository.create_notification(product_id, email, user_id)
    return {"message": "Notification registered successfully", "email": email}

@router.post("/upload-videos", response_model=UploadVideosResponse)
async def upload_videos(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(require_super_admin)
):
    from app.utils.oci_storage import upload_file_to_oci
    import uuid
    urls = []
    for file in files:
        ext = file.filename.split('.')[-1] if '.' in file.filename else 'mp4'
        obj_name = f"videos/{uuid.uuid4()}.{ext}"
        content = await file.read()
        url = await upload_file_to_oci(content, obj_name, file.content_type)
        if url:
            urls.append(url)
    return {"urls": urls}
