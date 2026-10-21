import logging
from app.models.user import User
from app.models.category import Category
from app.models.schemas import MessageResponse, MultipleImageUploadResponse
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.models.base import CamelBaseModel
from app.repositories.category_repository import CategoryRepository
from app.utils.auth import require_super_admin, get_optional_user
from app.utils.cache import cache
from app.utils.logger import logger

router = APIRouter()
category_repository = CategoryRepository()


class AvailableCategoriesResponse(CamelBaseModel):
    """Response schema for GET /available — zone/scope-scoped category/brand/collection lists.

    Replaces the incorrect List[Category] response_model that raised a 500
    ResponseValidationError because the endpoint returns a structured dict, not a
    flat list of Category objects.
    """
    category_names: List[str] = []
    sub_categories: Dict[str, List[str]] = {}
    brand_names: List[str] = []
    collection_names: List[str] = []


class CategoryBase(CamelBaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    images: Optional[List[str]] = None
    sub_categories: Optional[List[str]] = None
    minimum_quantity: int = Field(default=0, ge=0)  # Minimum quantity required for category
    category_tag: Optional[str] = None
    category_tag_id: Optional[int] = None
    is_active: bool = True
    show_in_mobile_homepage: bool = False
    gst: float = Field(default=0, ge=0, le=100)
    is_returnable: bool = False


class CategoryUpdate(CamelBaseModel):
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    images: Optional[List[str]] = None
    sub_categories: Optional[List[str]] = None
    minimum_quantity: Optional[int] = Field(None, ge=0)
    category_tag: Optional[str] = None
    category_tag_id: Optional[int] = None
    is_active: Optional[bool] = None
    show_in_mobile_homepage: Optional[bool] = None
    gst: Optional[float] = Field(None, ge=0, le=100)
    is_returnable: Optional[bool] = None


@cache.ttl_cache(ttl=300.0)
async def _get_available_categories_cached(
    effective_role: str,
    fulfillment_type: str,   # "hyperlocal" | "pan_india"
    zone_id: Optional[int],  # int zone ID for hyperlocal, None for pan-india / unzoned
) -> AvailableCategoriesResponse:
    """Zone/scope-scoped category + brand + collection lists for the navigation menu.

    Seller resolution matches the product-listing persona rules exactly:
      wholesaler   → Super Admin (SA) seller set
      hyperlocal   → sellers declared for zone_id
      pan_india    → Super Admin (SA) seller set  (includes no-pincode guests)
    """
    from app.repositories.zone_seller_cache import (
        get_super_admin_seller_id,
        get_seller_ids_for_zone_id,
    )

    _empty = AvailableCategoriesResponse()

    if effective_role == "wholesaler":
        sa_id = await get_super_admin_seller_id()
        seller_id_set: set = {sa_id} if sa_id else set()
    elif fulfillment_type == "hyperlocal" and zone_id is not None:
        seller_id_set = await get_seller_ids_for_zone_id(zone_id) or set()
    else:
        # pan_india (pincode not in any zone) or no pincode → SA catalog
        sa_id = await get_super_admin_seller_id()
        seller_id_set = {sa_id} if sa_id else set()

    if not seller_id_set:
        # Zone exists but no sellers declared — return empty (not a 500)
        return _empty

    allowed_seller_ids = {int(s) for s in seller_id_set if str(s).isdigit()}

    from app.repositories.product_repository import product_repository
    from app.models.product import ProductFilter
    products = await product_repository.findAll(ProductFilter(is_active=True))

    cat_names: set = set()
    sub_cats: dict = {}
    brand_names: set = set()
    collection_names: set = set()

    for p in products:
        p_seller_ids = p.catalog_seller_ids or []
        if not any(sid in allowed_seller_ids for sid in p_seller_ids):
            continue
        cat = p.category
        if cat:
            cat_names.add(cat)
            if cat not in sub_cats:
                sub_cats[cat] = set()
            sub = p.sub_category
            if sub:
                sub_cats[cat].add(sub)
        brand = p.brand
        if brand:
            brand_names.add(brand)
        for col in (p.resolved_collection_names or []):
            collection_names.add(col)

    return AvailableCategoriesResponse(
        category_names=sorted(cat_names),
        sub_categories={k: sorted(v) for k, v in sub_cats.items()},
        brand_names=sorted(brand_names),
        collection_names=sorted(collection_names),
    )


@router.get("/available", response_model=AvailableCategoriesResponse)
async def get_available_categories(
    pincode: Optional[str] = None,
    role: Optional[str] = "customer",
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Return category/brand/collection names scoped to the customer's zone or scope.

    Persona rules (mirrors product-listing visibility exactly):
      No pincode            → SA catalog  [add-to-cart disabled by FE]
      Hyperlocal pincode    → zone sellers' categories
      Pan-India pincode     → SA catalog
      Wholesaler            → SA catalog (B2B tier)
    """
    effective_role = role or "customer"
    if current_user and current_user.role:
        effective_role = current_user.role

    if effective_role == "wholesaler":
        return await _get_available_categories_cached("wholesaler", "pan_india", None)

    # Retail / guest — resolve pincode → fulfillment_type + zone_id via the same
    # helper used by products and recommendations, so all three endpoints stay in sync.
    from app.repositories.zone_seller_cache import get_retail_seller_set
    _, fulfillment_type, zone_id = await get_retail_seller_set(pincode, subtract_unavailable=False)
    return await _get_available_categories_cached(effective_role, fulfillment_type, zone_id)



@router.get("/public", response_model=List[Category])
@cache.ttl_cache(ttl=300.0)
async def get_public_categories(forHomepage: bool = False):
    """Get active categories (public endpoint). If forHomepage=true, only categories with display-in-homepage enabled (web & mobile)."""
    try:
        categories = await category_repository.findAll()
        active_categories = []
        for cat in categories:
            if cat.is_active is False:
                continue
            if forHomepage and not cat.show_in_mobile_homepage:
                continue
            tag = cat.category_tag
            tags = (cat.category_tags or [])
            if not tag and tags:
                tag = tags[0] if tags else ""
            cat.category_tag = tag or ""
            cat.category_tags = [tag] if tag else []
            cat.gst = cat.gst if cat.gst is not None else 0
            active_categories.append(cat)
        return active_categories
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/public/tags/{tag_name}/categories", response_model=List[Category])
@cache.ttl_cache(ttl=300.0)
async def get_tag_categories(tag_name: str):
    """Get active categories associated with a specific tag"""
    try:
        categories = await category_repository.findAll()
        target_tag = tag_name.lower()
        matching_cats = []
        for cat in categories:
            if cat.is_active is False:
                continue

            tag = cat.category_tag
            tags = (cat.category_tags or [])
            if not tag and tags:
                tag = tags[0] if tags else ""

            if (tag or "").lower() == target_tag:
                cat.category_tag = tag or ""
                cat.category_tags = [tag] if tag else []
                cat.gst = (cat.gst if cat.gst is not None else 0)
                matching_cats.append(cat)
        return matching_cats
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/public/tags/{tag_name}/brands", response_model=List[str])
@cache.ttl_cache(ttl=300.0)
async def get_tag_brands(tag_name: str):
    """Get brands associated with a specific tag via categories and products"""
    try:
        from app.repositories.brand_repository import brand_repository
        from app.repositories.product_repository import product_repository

        # 1. Get matching categories
        categories = await category_repository.findAll()
        target_tag = tag_name.lower()
        matching_cat_names = [
            cat.name
            for cat in categories
            if cat.is_active is not False and (cat.category_tag or "").lower() == target_tag
        ]

        # 2. Get all products in these categories
        products = await product_repository.findAll()
        associated_brands = set()
        for p in products:
            if (p.is_active if p.is_active is not None else True) and p.category in matching_cat_names:
                brand_name = p.brand
                if brand_name:
                    associated_brands.add(brand_name.lower())

        # 3. Get brand details for matching brand names
        all_brands = await brand_repository.findAll()
        matching_brands = [
            b for b in all_brands if (b.is_active if b.is_active is not None else True) and (b.name or "").lower() in associated_brands
        ]

        return matching_brands
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


def _invalidate_category_caches():
    cache.invalidate(get_public_categories)
    cache.invalidate(get_tag_categories)
    cache.invalidate(get_tag_brands)
    try:
        from app.routers.category_tags import get_active_category_tags

        cache.invalidate(get_active_category_tags)
    except Exception as e:
        logging.warning("_invalidate_category_caches: could not invalidate category_tags cache: %s", e, exc_info=e)
    try:
        from app.repositories.coupon_repository import coupon_repository

        coupon_repository.invalidate_cache()
    except Exception as e:
        logging.warning("_invalidate_category_caches: could not invalidate coupon cache: %s", e, exc_info=e)


@router.get("", response_model=List[Category])
@router.get("/", response_model=List[Category])
async def get_categories(current_user: User = Depends(require_super_admin)):
    """Get all categories (Super Admin only)"""
    try:
        categories = await category_repository.findAll()
        # Ensure all categories have categoryTags field (for backward compatibility)
        categories_with_tags = []
        for cat in categories:
            # Migration logic for response
            tag = cat.category_tag
            tags = (cat.category_tags or [])

            if not tag and tags:
                tag = tags[0] if tags else ""

            cat.category_tag = tag or ""
            cat.category_tags = [tag] if tag else []
            cat.gst = (cat.gst if cat.gst is not None else 0)

            categories_with_tags.append(cat)
        return categories_with_tags
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/{category_id}", response_model=Category)
async def get_category(category_id: int, current_user: User = Depends(require_super_admin)):
    """Get category by ID (Super Admin only)"""
    try:
        category = await category_repository.findById(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        category.gst = (category.gst if category.gst is not None else 0)
        return category
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.post("/upload-images", response_model=MultipleImageUploadResponse)
async def upload_category_images(
    images: List[UploadFile] = File(...), current_user: User = Depends(require_super_admin)
):
    """Upload category images (Super Admin only). Uses OCI Object Storage when configured."""
    try:
        from app.services.oci_storage import upload_image_and_return_path

        image_urls = []
        for image in images:
            if not image.content_type or not image.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail=f"File {image.filename} is not an image")
            path = await upload_image_and_return_path(image, "categories", filename_prefix="category")
            image_urls.append(path)
        return {"images": image_urls}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("upload_category_images failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Server error")


@router.post("", response_model=Category, status_code=201)
@router.post("/", response_model=Category, status_code=201)
async def create_category(category: CategoryBase, current_user: User = Depends(require_super_admin)):
    """Create a new category (Super Admin only)"""
    try:
        # Check if category with same name already exists (case-insensitive)
        all_categories = await category_repository.findAll()
        name_lower = category.name.strip().lower()
        for cat in all_categories:
            if (cat.name or "").strip().lower() == name_lower:
                raise HTTPException(status_code=400, detail="Category with this name already exists")

        from app.models.daos import CategoryInternalCreate
        category_data = CategoryInternalCreate(
            name=category.name.strip(),
            description=category.description or "",
            images=category.images or [],
            sub_categories=category.sub_categories or [],
            minimum_quantity=category.minimum_quantity or 0,
            category_tag=category.category_tag or "",
            category_tag_id=category.category_tag_id,
            is_active=category.is_active,
            show_in_mobile_homepage=category.show_in_mobile_homepage,
            gst=category.gst,
            is_returnable=category.is_returnable,
        )

        new_category = await category_repository.create(category_data)
        _invalidate_category_caches()
        return new_category
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.put("/{category_id}", response_model=Category)
async def update_category(
    category_id: int, category_update: CategoryUpdate, current_user: User = Depends(require_super_admin)
):
    """Update a category (Super Admin only)"""
    try:
        category = await category_repository.findById(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        if category_update.name is not None:
            # Check if category with same name already exists (excluding current category) (case-insensitive)
            all_categories = await category_repository.findAll()
            name_lower = category_update.name.strip().lower()
            for cat in all_categories:
                if (cat.name or "").strip().lower() == name_lower and str(cat.id) != str(category_id):
                    raise HTTPException(status_code=400, detail=f"Category with name '{category_update.name}' already exists")
            category_update.name = category_update.name.strip()

        # Ensure we have at least one field to update
        if not category_update.model_fields_set:
            raise HTTPException(status_code=400, detail="No fields to update")

        from app.models.daos import CategoryInternalUpdate
        internal_update = CategoryInternalUpdate.model_validate(
            category_update.model_dump(exclude_unset=True)
        )
        updated_category = await category_repository.update(category_id, internal_update)
        _invalidate_category_caches()
        return updated_category
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.delete("/{category_id}", response_model=MessageResponse)
async def delete_category(category_id: int, current_user: User = Depends(require_super_admin)):
    """Delete a category (soft delete) (Super Admin only)"""
    try:
        category = await category_repository.findById(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        await category_repository.delete(category_id)
        _invalidate_category_caches()
        return {"message": "Category deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")
