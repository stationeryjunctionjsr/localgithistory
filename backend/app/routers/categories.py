import logging
from app.models.user import User
from app.models.category import Category
from app.models.schemas import MessageResponse
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.repositories.category_repository import CategoryRepository
from app.utils.auth import require_super_admin, get_optional_user
from app.utils.cache import cache
from app.utils.logger import logger

router = APIRouter()
category_repository = CategoryRepository()


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    images: Optional[List[str]] = None
    subCategories: Optional[List[str]] = None
    minimumQuantity: int = Field(default=0, ge=0)  # Minimum quantity required for category
    categoryTag: Optional[str] = None
    isActive: bool = True
    showInMobileHomepage: bool = False
    gst: float = Field(default=0, ge=0, le=100)
    isReturnable: bool = False


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    images: Optional[List[str]] = None
    subCategories: Optional[List[str]] = None
    minimumQuantity: Optional[int] = Field(None, ge=0)
    categoryTag: Optional[str] = None
    isActive: Optional[bool] = None
    showInMobileHomepage: Optional[bool] = None
    gst: Optional[float] = Field(None, ge=0, le=100)
    isReturnable: Optional[bool] = None


@cache.ttl_cache(ttl=300.0)
async def _get_available_categories_cached(pincode: Optional[str], effective_role: str):
    if effective_role == "wholesaler":
        from app.repositories.zone_seller_cache import get_super_admin_seller_id
        sa_id = await get_super_admin_seller_id()
        if sa_id:
            seller_id_set = {sa_id}
        else:
            seller_id_set = set()
    else:
        if not pincode:
            return None

        from app.repositories.zone_seller_cache import get_seller_ids_for_pincode
        seller_id_set = await get_seller_ids_for_pincode(pincode)

        if seller_id_set is None:
            return None  # Pincode not in any zone -> fail open (show all)

    result = {
        "categoryNames": set(),
        "subCategories": {},  # dict[category_name, set[subcategory_name]]
        "brandNames": set(),
        "collectionNames": set(),
    }

    if not seller_id_set:
        # Zone found, but no sellers -> empty result
        return {"categoryNames": [], "subCategories": {}, "brandNames": [], "collectionNames": []}

    from app.repositories.product_repository import product_repository
    # We pass 'customer' to get the standard retail light catalog cache
    products = await product_repository._get_lightweight_search_catalog("customer", None)

    for p in products:
        p_seller_ids = p.catalog_seller_ids or []
        # Check if the product has any overlap with the zone's seller IDs
        if any(sid in seller_id_set for sid in p_seller_ids):
            cat = p.category
            if cat:
                result["categoryNames"].add(cat)
                if cat not in result["subCategories"]:
                    result["subCategories"][cat] = set()
                sub = p.sub_category
                if sub:
                    result["subCategories"][cat].add(sub)
            brand = p.brand
            if brand:
                result["brandNames"].add(brand)
            collections = p.resolved_collection_names or []
            for col in collections:
                result["collectionNames"].add(col)

    # Convert sets to lists for JSON serialization
    return {
        "categoryNames": list(result["categoryNames"]),
        "subCategories": {k: list(v) for k, v in result["subCategories"].items()},
        "brandNames": list(result["brandNames"]),
        "collectionNames": list(result["collectionNames"]),
    }


@router.get("/available", response_model=List[Category])
async def get_available_categories(
    pincode: Optional[str] = None, 
    role: Optional[str] = "customer",
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Returns the category names and subcategories that have at least one product
    available for the given pincode (based on zone -> seller mapping).
    Returns null if no pincode is provided or if the pincode is not in any zone (fail-open).
    """
    effective_role = role or "customer"
    if current_user and current_user.role:
        effective_role = current_user.role
        
    return await _get_available_categories_cached(pincode, effective_role)



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
                tag = tags[0] if isinstance(tags, list) and tags else ""
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
                tag = tags[0] if isinstance(tags, list) and tags else ""

            if (tag or "").lower() == target_tag:
                matching_cats.append(
                    {**cat, "categoryTag": tag or "", "categoryTags": [tag] if tag else [], "gst": (cat.gst if cat.gst is not None else 0)}
                )
        return matching_cats
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/public/tags/{tag_name}/brands", response_model=List[Any])
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
            cat["name"]
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
        logging.warning("Background task failed", exc_info=e)
    try:
        from app.repositories.coupon_repository import coupon_repository

        coupon_repository.invalidate_cache()
    except Exception as e:
        logging.warning("Background task failed", exc_info=e)


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
                tag = tags[0] if isinstance(tags, list) and tags else ""

            cat_with_tags = {
                **cat,
                "categoryTag": tag or "",
                "categoryTags": [tag] if tag else [],
                "gst": (cat.gst if cat.gst is not None else 0),
            }
            categories_with_tags.append(cat_with_tags)
        return categories_with_tags
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/{category_id}", response_model=Category)
async def get_category(category_id: str, current_user: User = Depends(require_super_admin)):
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


@router.post("/upload-images", response_model=Dict[str, List[str]])
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


@router.post("", response_model=Category)
@router.post("/", response_model=Category)
async def create_category(category: CategoryBase, current_user: User = Depends(require_super_admin)):
    """Create a new category (Super Admin only)"""
    try:
        # Check if category with same name already exists (case-insensitive)
        all_categories = await category_repository.findAll()
        name_lower = category.name.strip().lower()
        for cat in all_categories:
            if (cat.name or "").strip().lower() == name_lower:
                raise HTTPException(status_code=400, detail="Category with this name already exists")

        category_data = {
            "name": category.name.strip(),
            "description": category.description or "",
            "images": category.images or [],
            "subCategories": category.subCategories or [],
            "minimumQuantity": category.minimumQuantity or 0,
            "categoryTag": category.categoryTag or "",
            "isActive": category.isActive,
            "showInMobileHomepage": category.showInMobileHomepage,
            "gst": category.gst,
            "isReturnable": category.isReturnable,
        }

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
    category_id: str, category_update: CategoryUpdate, current_user: User = Depends(require_super_admin)
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

        updated_category = await category_repository.update(category_id, category_update)
        _invalidate_category_caches()
        return updated_category
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.delete("/{category_id}", response_model=MessageResponse)
async def delete_category(category_id: str, current_user: User = Depends(require_super_admin)):
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
