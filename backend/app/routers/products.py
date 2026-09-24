from app.models.daos import ProductInternalUpdate
import logging
from app.models.user import User
from fastapi.responses import StreamingResponse
from app.models.schemas import MessageResponse
from typing import Dict, Any, List
import csv
import io
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

class SellerEntryUpdate(BaseModel):
    stock: Optional[int] = None
    isActive: Optional[bool] = None

class SellerRequestApprove(BaseModel):
    status: Optional[str] = "approved"
    notes: Optional[str] = None


from app.models.schemas import PaginatedProductResponse, ProductCreate, ProductResponse, ProductUpdate, UploadImagesResponse, UploadCSVResponse, SearchSuggestResponse, SellerProductRequestCreate, SellerProductApprove, ProductSellerEntry, VariantOption
from app.repositories.category_repository import category_repository
from app.repositories.product_repository import product_repository
from app.utils.auth import get_current_user, require_super_admin, get_optional_user, require_super_admin_or_seller
from app.utils.cache import cache
from app.utils.logger import logger


class BulkUpdateData(BaseModel):
    ids: List[str]
    isActive: Optional[bool] = None
    isExclusive: Optional[bool] = None


class CSVProductRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Optional[str] = None
    category: Optional[str] = None
    mrp: Optional[str] = None
    mrpPerCase: Optional[str] = None
    mrp_per_case: Optional[str] = None
    quantityPerCase: Optional[str] = None
    productId: Optional[str] = None
    sku: Optional[str] = None
    subCategory: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    collection: Optional[str] = None
    isActive: Optional[str] = "true"
    images: Optional[str] = None
    videos: Optional[str] = None
    stock: Optional[str] = "0"
    row_number: Optional[int] = None


class CSVProductPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    productIdFormatted: Optional[str] = None
    sku: Optional[str] = None
    category: str
    subCategory: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    collection: Optional[str] = None
    mrp: float
    mrpPerCase: Optional[float] = None
    quantityPerCase: Optional[int] = None
    stock: int = 0
    isActive: bool = True
    images: List[str] = Field(default_factory=list)
    videos: List[str] = Field(default_factory=list)
    variantAttributes: List[str] = Field(default_factory=list)
    variants: List[VariantOption] = Field(default_factory=list)


class ProductFacets(BaseModel):
    brands: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    subCategories: List[str] = Field(default_factory=list)
    collections: List[str] = Field(default_factory=list)


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
        for idx, r in enumerate(csv_data):
            row_num = idx + 2
            row_obj = CSVProductRow(**r, row_number=row_num)
            name = (row_obj.name or "").strip()

            if not name:
                errors.append({"row": row_num, "error": "Missing product name"})
                continue

            if name not in grouped_products:
                grouped_products[name] = []

            grouped_products[name].append(row_obj)

        for name, rows in grouped_products.items():
            try:
                # The first row defines the main product details
                main_row = rows[0]
                row_number = main_row.row_number if main_row.row_number is not None else 0

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
                category_name = (main_row.category or "").strip()
                existing_category = await category_repository.findByName(category_name)
                if not existing_category:
                    category_name = "Others"

                mrp_per_case = None
                mrp_pc = main_row.mrp_per_case or main_row.mrpPerCase
                if mrp_pc and str(mrp_pc).strip():
                    try:
                        mrp_per_case = float(mrp_pc)
                    except (ValueError, TypeError) as e:
                        logger.warning("Invalid mrpPerCase in CSV row %s: %s", row_number, str(e))
                qty_per_case = None
                qty_pc = main_row.quantity_per_case or main_row.quantityPerCase
                if qty_pc and str(qty_pc).strip():
                    try:
                        qty_per_case = int(float(qty_pc))
                    except (ValueError, TypeError) as e:
                        logger.warning("Invalid quantityPerCase in CSV row %s: %s", row_number, str(e))

                product_data = CSVProductPayload(
                    name=name,
                    productIdFormatted=(main_row.productId or "").strip(),
                    sku=(main_row.sku or "").strip(),
                    category=category_name,
                    subCategory=(main_row.subCategory or "").strip(),
                    description=(main_row.description or "").strip(),
                    brand=(main_row.brand or "").strip(),
                    collection=(main_row.collection or "").strip() or None,
                    mrp=float(main_row.mrp),  # MRP per unit (required)
                    mrpPerCase=mrp_per_case,
                    quantityPerCase=qty_per_case,
                    stock=0,
                    isActive=(main_row.isActive or "true").lower() in ["true", "1", "yes"],
                    images=[img.strip() for img in (main_row.images or "").split(",") if img.strip()] if main_row.images else [],
                    videos=[vid.strip() for vid in (main_row.videos or "").split(",") if vid.strip()] if main_row.videos else [],
                    variantAttributes=[],
                    variants=[],
                )

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
                    row_extra = row.model_extra or {}
                    for k, v in row_extra.items():
                        if k and k.startswith("Attribute ") and v and str(v).strip():
                            num = k.replace("Attribute ", "")
                            val_key = f"Variant {num}"
                            variant_val = str(row_extra[val_key] if val_key in row_extra else "").strip()
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

                if product_data.productIdFormatted:
                    existing = await products_col.findOne({"productIdFormatted": product_data.productIdFormatted})
                elif product_data.sku:
                    existing = await products_col.findOne({"sku": product_data.sku})
                else:
                    # Also try matching by exact name to avoid duplicates if SKU isn't set either
                    existing = await products_col.findOne({"name": product_data.name})

                if existing:
                    internal_data = ProductInternalUpdate(
                        name=product_data.name,
                        sku=product_data.sku,
                        category=product_data.category,
                        subCategory=product_data.subCategory,
                        description=product_data.description,
                        brand=product_data.brand,
                        collection=product_data.collection,
                        mrp=product_data.mrp,
                        mrpPerCase=product_data.mrpPerCase,
                        quantityPerCase=product_data.quantityPerCase,
                        stock=product_data.stock,
                        images=product_data.images,
                        videos=product_data.videos,
                        isActive=product_data.isActive,
                        isExclusive=product_data.isExclusive,
                        tags=product_data.tags,
                        variations=product_data.variations,
                        variantAttributes=product_data.variantAttributes,
                        variants=product_data.variants
                    )
                    await product_repository.update(existing.id, internal_data)
                    product_id_to_show = (product_data.productIdFormatted if product_data.productIdFormatted is not None else product_data.name)
                    results.append({"product": product_id_to_show, "action": "updated"})
                else:
                    await product_repository.create(product_data)
                    results.append({"product": product_data.name, "action": "created"})
            except (ValueError, TypeError, KeyError) as e:
                errors.append(
                    {"row": main_row.row_number if main_row.row_number is not None else "N/A", "product": name, "error": f"Data error: {str(e)}"}
                )
            except Exception as e:
                logger.error("Unexpected error processing product %s in CSV: %s", name, str(e), exc_info=True)
                errors.append(
                    {"row": main_row.row_number if main_row.row_number is not None else "N/A", "product": name, "error": f"Internal error: {str(e)}"}
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
        images = ",".join(images_list) if images_list else ""

        videos_list = (p.videos or [])
        videos = ",".join(videos_list) if videos_list else ""

        is_active = "true" if (p.is_active if p.is_active is not None else True) else "false"
        product_id = p.product_id_formatted or (
            f"PDT-{p.product_id}" if p.product_id is not None else ""
        )

        combinations = (p.variants or []) or []
        if combinations:
            for idx, combo in enumerate(combinations):
                combo_mrp = combo.price if combo.price is not None else mrp
                combo_stock = combo.stock if combo.stock is not None else 0

                combo_attrs = combo.attributes or {}
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
    """Lightweight autocomplete served from in-memory zone-filtered product catalog. Zero DB hits."""
    if len(q) < 2:
        return {"products": [], "brands": [], "categories": [], "suggestions": []}

    q_lower = q.lower()
    tokens = [t for t in q_lower.split() if t.strip()]
    if not tokens:
        return {"products": [], "brands": [], "categories": [], "suggestions": []}

    effective_role = "wholesaler" if role == "wholesaler" else "customer"

    # Determine zone-based serviceable seller set
    serviceable_seller_ids: Optional[set] = None
    if effective_role == "wholesaler":
        from app.repositories.zone_seller_cache import get_super_admin_seller_id
        sa_id = await get_super_admin_seller_id()
        serviceable_seller_ids = {sa_id} if sa_id else set()
    elif pincode:
        from app.repositories.zone_seller_cache import get_zone_id_and_seller_ids_for_pincode
        _zone_id, serviceable_seller_ids = await get_zone_id_and_seller_ids_for_pincode(pincode)

    # Pull from the in-memory lightweight catalog (300 s cache, rebuilt only on expiry)
    catalog = await product_repository._get_lightweight_search_catalog(effective_role, None)

    matched_products = []
    brands: set = set()
    categories: set = set()

    for p in catalog:
        # Zone filter: p is a dict produced by _get_lightweight_search_catalog
        if serviceable_seller_ids is not None:
            p_seller_ids = p["sellerIds"] if "sellerIds" in p else []
            if not any(sid in serviceable_seller_ids for sid in p_seller_ids):
                continue

        name = (p["name"] if "name" in p else "") or ""
        name_lower = name.lower()
        if not all(t in name_lower for t in tokens):
            continue

        p_brand = p["brand"] if "brand" in p else None
        p_category = p["category"] if "category" in p else None
        if p_brand:
            brands.add(p_brand)
        if p_category:
            categories.add(p_category)

        if len(matched_products) < limit:
            matched_products.append({
                "productId": str(p["_id"] if "_id" in p else ""),
                "name": name,
                "productName": name,
                "displayImage": p["displayImage"] if "displayImage" in p else None,
            })

        if len(matched_products) >= limit and len(brands) >= 3 and len(categories) >= 3:
            break

    return {
        "products": matched_products,
        "suggestions": [p["name"] for p in matched_products],
        "brands": list(brands)[:3],
        "categories": list(categories)[:3],
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
        if role not in (c.applicableRoles or []):
            continue
        applicable_user_ids = c.applicableUserIds or []
        if applicable_user_ids:
            if not user_id or str(user_id) not in [str(x) for x in applicable_user_ids]:
                continue
        behavior = c.userBehavior
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
                val = float(c.discountValue or 0)
                if c.discountType == "percentage":
                    pct = val
                elif c.discountType == "fixed":
                    if mrp > 0:
                        if not mrp:
                            raise ValueError("Cannot calculate discount: MRP is zero or None")
                        pct = (val / mrp) * 100
                if pct > auto_discount_pct:
                    auto_discount_pct = pct
                    auto_discount_value = val
                    auto_discount_type = c.discountType
                    default_coupon = c

        # Apply default discount to price
        final_price = product_repository.getPriceForRole(p, role, 1, user_id=user_id)
        p.price = final_price

        if default_coupon:
            p.defaultDiscountPercentage = round(auto_discount_pct, 2)

        if mrp > 0 and final_price < mrp:
            if not mrp:
                raise ValueError("Cannot calculate discount percentage: MRP is zero or None")
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
        default_min_req = default_coupon.minRequirementType
        if default_coupon and default_min_req == "quantity_based":
            qty_coupon = default_coupon
        else:
            for oc in other_coupons:
                oc_min_req = oc.minRequirementType
                if oc_min_req == "quantity_based":
                    qty_coupon = oc
                    break

        if qty_coupon:
            p.quantityTiers = qty_coupon.quantityTiers or []
            p.quantityItemType = qty_coupon.applicableItemType or "units"

        app_discs = []
        if default_coupon and default_min_req == "quantity_based":
            app_discs.append(
                {
                    "type": default_coupon.typeOfDiscount,
                    "code": default_coupon.code,
                    "description": get_coupon_description(default_coupon),
                }
            )

        for oc in other_coupons:
            app_discs.append(
                {
                    "type": oc.typeOfDiscount,
                    "code": oc.code,
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
    except Exception as e:
        logging.warning("Background task failed", exc_info=e)
    try:
        from app.repositories.coupon_repository import coupon_repository

        coupon_repository.invalidate_cache()
    except Exception as e:
        logging.warning("Background task failed", exc_info=e)



@cache.ttl_cache(ttl=300.0)
async def _get_public_products_cached(
    response: Response,
    category: Optional[str],
    categories: Optional[str],
    subCategory: Optional[str],
    search: Optional[str],
    brand: Optional[str],
    collection: Optional[str],
    popularity: Optional[str],
    minDiscount: Optional[str],
    minPrice: Optional[float],
    maxPrice: Optional[float],
    availability: Optional[str],
    page: int,
    limit: int,
    categoryTag: Optional[str],
    sort: Optional[str],
    includeFacets: bool,
    skinny: bool,
    zone_id: Optional[str],  # None for wholesaler (super-admin products) or no-pincode guest
):
    """Internal cached function. Cache key is zone_id — all pincodes in same zone share one entry."""
    role = "customer"  # public endpoint is always customer role
    query: dict = {}
    if category:
        query["category"] = category
    if categories:
        query["categories"] = categories
    if subCategory:
        query["subCategory"] = subCategory
    if search:
        query["search"] = search
    if brand:
        query["brand"] = brand
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
    query["role"] = role

    # Zone-based seller filter: zone_id already resolved by the route handler.
    if zone_id:
        from app.repositories.zone_seller_cache import get_seller_ids_for_zone_id
        seller_id_set = await get_seller_ids_for_zone_id(zone_id)
        if seller_id_set is not None:
            query["allowed_seller_ids"] = list(seller_id_set)

    if page > 1:
        includeFacets = False

    start_index = (page - 1) * limit
    products, total_count, facets, used_fuzzy, suggested_query = await product_repository.get_catalog(
        query, skip=start_index, limit=limit, sort=sort, include_facets=includeFacets
    )

    await populate_product_discounts(products, role, skinny=skinny)

    if skinny:
        for p in products:
            p.displayImage = p.displayImage or (p.images[0] if p.images else None)
            p.description = None
            p.variants = []
            p.videos = []
            p.images = []
            p.applicableDiscounts = None
            p.variant_attributes = []

    products_with_pricing = []
    for product in products:
        if product.tags is None:
            product.tags = []
        products_with_pricing.append(product)

    response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=60"

    if facets:
        f = ProductFacets(
            brands=facets["brands"],
            categories=facets["categories"],
            subCategories=facets["subCategories"],
            collections=facets["collections"]
        )
    else:
        f = ProductFacets()

    return {
        "products": products_with_pricing,
        "totalCount": total_count,
        "brands": f.brands,
        "categories": f.categories,
        "subCategories": f.subCategories,
        "collections": f.collections,
        "usedFuzzy": used_fuzzy,
        "suggestedQuery": suggested_query,
    }


@router.get("/public", response_model=PaginatedProductResponse)
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
    categoryTag: Optional[str] = None,
    sort: Optional[str] = None,
    includeFacets: bool = True,
    skinny: bool = False,
    myProducts: bool = False,
    pincode: Optional[str] = None,
):
    """Get products filtered by zone. Requires pincode for retail guests. Wholesalers use super-admin catalog."""
    # Guests without a pincode get an empty result set (zone is required for product visibility)
    if not pincode:
        return {
            "products": [],
            "totalCount": 0,
            "brands": [],
            "categories": [],
            "subCategories": {},
            "collections": [],
            "usedFuzzy": False,
            "suggestedQuery": None,
        }

    # Resolve pincode → zone_id. zone_id is the cache discriminator.
    from app.repositories.zone_seller_cache import get_zone_id_and_seller_ids_for_pincode
    zone_id, _ = await get_zone_id_and_seller_ids_for_pincode(pincode)

    return await _get_public_products_cached(
        response, category, categories, subCategory, search, brand, collection,
        popularity, minDiscount, minPrice, maxPrice, availability,
        page, limit, categoryTag, sort, includeFacets, skinny, zone_id,
    )


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

    return product


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
    myProducts: bool = False,
    pincode: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    # Use effectiveRole if user is deactivated
    effective_role = current_user.effective_role or (current_user.role if current_user.role is not None else "customer")
    user_id = current_user.id

    query = {}
    if category:
        query["category"] = category
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

    query["role"] = effective_role
    query["user_id"] = user_id

    if effective_role == "wholesaler":
        from app.repositories.zone_seller_cache import get_super_admin_seller_id
        sa_id = await get_super_admin_seller_id()
        if sa_id:
            query["allowed_seller_ids"] = [sa_id]
    elif effective_role == "seller" and myProducts:
        query["my_seller_id"] = user_id
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

        products_with_pricing.append(product)

    if facets:
        f = ProductFacets(
            brands=facets["brands"],
            categories=facets["categories"],
            subCategories=facets["subCategories"],
            collections=facets["collections"]
        )
    else:
        f = ProductFacets()

    return {
        "products": products_with_pricing,
        "totalCount": total_count,
        "brands": f.brands,
        "categories": f.categories,
        "subCategories": f.subCategories,
        "collections": f.collections,
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

    return product


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
        return product
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str, product_data: ProductUpdate, current_user: User = Depends(require_super_admin)
):
    try:
        internal_data = ProductInternalUpdate(
            name=product_data.name,
            sku=product_data.sku,
            category=product_data.category,
            subCategory=product_data.subCategory,
            description=product_data.description,
            brand=product_data.brand,
            collection=product_data.collection,
            mrp=product_data.mrp,
            mrpPerCase=product_data.mrpPerCase,
            quantityPerCase=product_data.quantityPerCase,
            stock=product_data.stock,
            images=product_data.images,
            videos=product_data.videos,
            isActive=product_data.isActive,
            isExclusive=product_data.isExclusive,
            tags=product_data.tags,
            variations=product_data.variations,
            variantAttributes=product_data.variantAttributes,
            variants=product_data.variants
        )
        product = await product_repository.update(product_id, internal_data)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        _invalidate_product_caches()
        return product
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
        data = ProductInternalUpdate()
        has_updates = False
        if update_data.isActive is not None:
            data.isActive = update_data.isActive
            has_updates = True
        if update_data.isExclusive is not None:
            data.isExclusive = update_data.isExclusive
            has_updates = True

        if has_updates:
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

class SearchSuggestProduct(BaseModel):
    productId: str
    name: str
    productName: str
    displayImage: Optional[str] = None

class SearchSuggestResponse(BaseModel):
    products: List[SearchSuggestProduct]
    suggestions: Optional[List[str]] = None
    brands: List[str]
    categories: List[str]

class ProductTagAction(BaseModel):
    searchTagId: str


@router.post("/{product_id}/search-tags", response_model=MessageResponse)
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


@router.get("/{product_id}/search-tags", response_model=List[str])
async def get_product_search_tags(product_id: str, current_user: User = Depends(require_super_admin)):
    """Get all resolved search tags for a specific product"""
    products_with_tags = await product_repository.find_with_resolved_search_tags({"_id": product_id})
    if not products_with_tags:
        raise HTTPException(status_code=404, detail="Product not found")

    first_product = products_with_tags[0]
    resolved = first_product.searchTags or []

    # Also return all available search tags for the add dropdown
    from app.repositories.search_tag_repository import search_tag_repository

    all_tags = await search_tag_repository.findAllActive()

    return {
        "resolvedTags": resolved,
        "allTags": [{"_id": t.id, "name": t.name, "type": t.type} for t in all_tags],
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
    # Import from the correct module path: app.services.oci_storage (not app.utils.oci_storage)
    import asyncio
    from app.services.oci_storage import build_key, key_to_media_path, upload_object, use_oci_storage

    ALLOWED_VIDEO_MIME = {"video/mp4", "video/quicktime", "video/x-msvideo", "video/webm", "video/x-matroska"}
    MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100 MB

    urls = []
    for file in files:
        content = await file.read()
        if len(content) > MAX_VIDEO_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File '{file.filename}' exceeds the 100 MB size limit",
            )
        mime = file.content_type or "video/mp4"
        if mime not in ALLOWED_VIDEO_MIME:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported video type '{mime}'. Allowed: {', '.join(sorted(ALLOWED_VIDEO_MIME))}",
            )
        ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "mp4"
        safe_filename = f"video-{__import__('uuid').uuid4().hex}.{ext}"
        if use_oci_storage():
            key = build_key("videos", safe_filename)
            await asyncio.to_thread(upload_object, key, content, mime)
            urls.append(key_to_media_path(key))
        else:
            # Local fallback
            from pathlib import Path
            from app.config.settings import settings
            env = settings.environment.lower()
            env_folder = "SJ_PROD" if env == "production" else ("SJ_UAT" if env == "uat" else "SJ_LOCAL")
            upload_dir = Path(__file__).resolve().parents[2] / "uploads" / env_folder / "videos"
            upload_dir.mkdir(parents=True, exist_ok=True)
            (upload_dir / safe_filename).write_bytes(content)
            urls.append(f"/uploads/{env_folder}/videos/{safe_filename}")
    return {"urls": urls}


@router.post("/{product_id}/seller-requests", response_model=ProductResponse)
async def create_seller_request(
    product_id: str,
    data: SellerProductRequestCreate,
    current_user: User = Depends(require_super_admin_or_seller)
):
    """Seller requests to sell a product."""
    if current_user.role not in ["seller", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only sellers can request to sell products")
        
    product = await product_repository.findById(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    seller_id = str(current_user.id)
    
    # Initialize sellers list if None
    sellers_list = product.sellers or []
    
    # Check if seller already has an entry
    existing_entry = next((s for s in sellers_list if str(s.sellerId) == seller_id), None)
    if existing_entry:
        if existing_entry.requestStatus == "pending":
            raise HTTPException(status_code=400, detail="Request already pending")
        if existing_entry.requestStatus == "approved":
            raise HTTPException(status_code=400, detail="Already approved to sell this product")
        # If rejected, they can re-request
        existing_entry.requestStatus = "pending"
        existing_entry.stock = data.stock or 0
        existing_entry.notes = data.notes
    else:
        # Create new entry
        new_entry = ProductSellerEntry(
            sellerId=seller_id,
            stock=data.stock or 0,
            isActive=False,
            requestStatus="pending",
            notes=data.notes
        )
        sellers_list.append(new_entry)
        
    # Save product
    update_data = ProductInternalUpdate(sellers=sellers_list)
    updated = await product_repository.update(product_id, update_data)
    return updated


@router.put("/{product_id}/sellers/me", response_model=ProductResponse)
async def update_my_seller_entry(
    product_id: str,
    data: SellerEntryUpdate,
    current_user: User = Depends(require_super_admin_or_seller)
):
    """Seller updates their stock or isActive status for a product."""
    if current_user.role not in ["seller", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only sellers can update their entries")
        
    product = await product_repository.findById(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    seller_id = str(current_user.id)
    sellers_list = product.sellers or []
    
    existing_entry = next((s for s in sellers_list if str(s.sellerId) == seller_id), None)
    if not existing_entry:
        raise HTTPException(status_code=404, detail="You are not a seller for this product")
        
    if existing_entry.requestStatus != "approved":
        raise HTTPException(status_code=400, detail="Your request to sell this product is not approved yet")
        
    if data.stock is not None:
        existing_entry.stock = data.stock
    if data.isActive is not None:
        existing_entry.isActive = data.isActive
        
    update_data = ProductInternalUpdate(sellers=sellers_list)
    updated = await product_repository.update(product_id, update_data)
    return updated


@router.put("/{product_id}/sellers/{seller_id}/approve", response_model=ProductResponse)
async def approve_seller_request(
    product_id: str,
    seller_id: str,
    data: SellerRequestApprove = None,
    current_user: User = Depends(require_super_admin)
):
    """Admin approves or rejects a seller's request to sell a product."""
    from app.repositories.user_repository import user_repository
    
    product = await product_repository.findById(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    sellers_list = product.sellers or []
    target_entry = next((s for s in sellers_list if str(s.sellerId) == seller_id), None)
    
    if not target_entry:
        raise HTTPException(status_code=404, detail="Seller request not found for this product")
        
    new_status = data.status if data and data.status else "approved"
    
    if new_status == "approved":
        # ZONE EXCLUSIVITY CHECK
        target_user = await user_repository.findById(seller_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="Seller user not found")
            
        target_zones = target_user.service_area_zones or []
        target_zones_set = set(target_zones)
        
        # Check all other approved sellers
        for s in sellers_list:
            if str(s.sellerId) != seller_id and s.requestStatus == "approved":
                other_user = await user_repository.findById(str(s.sellerId))
                if other_user:
                    other_zones = other_user.service_area_zones or []
                    overlap = target_zones_set.intersection(set(other_zones))
                    if overlap:
                        overlap_zones = ", ".join(overlap)
                        raise HTTPException(
                            status_code=400, 
                            detail=f"Zone overlap detected. Seller '{other_user.company_name or other_user.name}' is already selling this product in zone(s): {overlap_zones}. You must remove or deactivate the 1st seller before approving the 2nd seller."
                        )
                        
        target_entry.isActive = True
        
    target_entry.requestStatus = new_status
    if data and data.notes:
        target_entry.notes = data.notes
        
    update_data = ProductInternalUpdate(sellers=sellers_list)
    updated = await product_repository.update(product_id, update_data)
    return updated
