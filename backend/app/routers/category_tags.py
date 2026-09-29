import logging
from typing import List
from app.models.schemas import MessageResponse
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field


from app.models.daos_flat import CategoryTagInternalCreate, CategoryTagInternalUpdate
from app.repositories.category_tag_repository import category_tag_repository
from app.utils.auth import require_super_admin
from app.utils.cache import cache
from app.utils.logger import logger

router = APIRouter()


class CategoryTagBase(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    isActive: bool = True


class CategoryTagResponse(CategoryTagBase):
    model_config = ConfigDict(populate_by_name=True)
    id: Optional[str] = Field(None, alias="_id")
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class CategoryTagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    isActive: Optional[bool] = None


@router.get("", response_model=List[CategoryTagResponse])
@router.get("/")
async def get_category_tags(current_user: dict = Depends(require_super_admin)):
    """Get all category tags (Super Admin only)"""
    try:
        tags = await category_tag_repository.findAll()
        return tags
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/active", response_model=List[CategoryTagResponse])
@cache.ttl_cache(ttl=300.0)
async def get_active_category_tags():
    """Get active category tags (public endpoint)"""
    try:
        tags = await category_tag_repository.findAll()
        active_tags = [tag for tag in tags if tag.is_active is not False]
        return active_tags
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.post("", response_model=CategoryTagResponse)
@router.post("/", response_model=CategoryTagResponse)
async def create_category_tag(tag: CategoryTagBase, current_user: dict = Depends(require_super_admin)):
    """Create a new category tag (Super Admin only)"""
    try:
        # Check if tag with same name already exists
        existing_tag = await category_tag_repository.findByName(tag.name)
        if existing_tag:
            raise HTTPException(status_code=400, detail="Category tag with this name already exists")

        tag_data = CategoryTagInternalCreate(name=tag.name.strip(), description=tag.description, is_active=tag.is_active)
        new_tag = await category_tag_repository.create(tag_data)
        cache.invalidate(get_active_category_tags)
        try:
            from app.routers.categories import get_public_categories, get_tag_categories, get_tag_brands

            cache.invalidate(get_public_categories)
            cache.invalidate(get_tag_categories)
            cache.invalidate(get_tag_brands)
        except Exception as e:
            logging.warning("category_tags: could not invalidate category/brand caches after tag mutation: %s", e, exc_info=e)
        return new_tag
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.put("/{tag_id}", response_model=CategoryTagResponse)
async def update_category_tag(
    tag_id: str, tag_update: CategoryTagUpdate, current_user: dict = Depends(require_super_admin)
):
    """Update a category tag (Super Admin only)"""
    try:
        tag = await category_tag_repository.findById(tag_id)
        if not tag:
            raise HTTPException(status_code=404, detail="Category tag not found")

        update_data = CategoryTagInternalUpdate()
        has_updates = False
        if tag_update.name is not None:
            # Check if tag with same name already exists (excluding current tag)
            existing_tag = await category_tag_repository.findByName(tag_update.name)
            existing_id = existing_tag.id if existing_tag else None
            if existing_tag and str(existing_id) != str(tag_id):
                raise HTTPException(status_code=400, detail="Category tag with this name already exists")
            update_data.name = tag_update.name.strip()
            has_updates = True

        if tag_update.description is not None:
            update_data.description = tag_update.description
            has_updates = True

        if tag_update.is_active is not None:
            update_data.is_active = tag_update.is_active
            has_updates = True

        if not has_updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updated_tag = await category_tag_repository.update(tag_id, update_data)
        cache.invalidate(get_active_category_tags)
        try:
            from app.routers.categories import get_public_categories, get_tag_categories, get_tag_brands

            cache.invalidate(get_public_categories)
            cache.invalidate(get_tag_categories)
            cache.invalidate(get_tag_brands)
        except Exception as e:
            logging.warning("category_tags: could not invalidate category/brand caches after tag mutation: %s", e, exc_info=e)
        return updated_tag
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.delete("/{tag_id}", response_model=MessageResponse)
async def hide_category_tag(tag_id: str, current_user: dict = Depends(require_super_admin)):
    """Hide a category tag (soft delete) (Super Admin only)"""
    try:
        tag = await category_tag_repository.findById(tag_id)
        if not tag:
            raise HTTPException(status_code=404, detail="Category tag not found")

        await category_tag_repository.delete(tag_id)
        cache.invalidate(get_active_category_tags)
        try:
            from app.routers.categories import get_public_categories, get_tag_categories, get_tag_brands

            cache.invalidate(get_public_categories)
            cache.invalidate(get_tag_categories)
            cache.invalidate(get_tag_brands)
        except Exception as e:
            logging.warning("category_tags: could not invalidate category/brand caches after tag mutation: %s", e, exc_info=e)
        return {"message": "Category tag hidden successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")

