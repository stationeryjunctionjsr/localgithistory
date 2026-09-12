from typing import Dict, Any, List
from app.models.schemas import MessageResponse
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

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
    id: str = Field(alias="_id")
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
class CategoryTagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    isActive: Optional[bool] = None


@router.get("", response_model=Dict[str, Any])
@router.get("/")
async def get_category_tags(current_user: dict = Depends(require_super_admin)):
    """Get all category tags (Super Admin only)"""
    try:
        tags = await category_tag_repository.findAll()
        return tags
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/active", response_model=Dict[str, Any])
@cache.ttl_cache(ttl=300.0)
async def get_active_category_tags():
    """Get active category tags (public endpoint)"""
    try:
        tags = await category_tag_repository.findAll()
        active_tags = [tag for tag in tags if tag.get("isActive") is not False]
        return active_tags
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.post("", response_model=Dict[str, Any])
@router.post("/", response_model=Dict[str, Any])
async def create_category_tag(tag: CategoryTagBase, current_user: dict = Depends(require_super_admin)):
    """Create a new category tag (Super Admin only)"""
    try:
        # Check if tag with same name already exists
        existing_tag = await category_tag_repository.findByName(tag.name)
        if existing_tag:
            raise HTTPException(status_code=400, detail="Category tag with this name already exists")

        tag_data = {"name": tag.name.strip(), "description": tag.description, "isActive": tag.isActive}

        new_tag = await category_tag_repository.create(tag_data)
        cache.invalidate(get_active_category_tags)
        try:
            from app.routers.categories import get_public_categories, get_tag_categories, get_tag_brands

            cache.invalidate(get_public_categories)
            cache.invalidate(get_tag_categories)
            cache.invalidate(get_tag_brands)
        except Exception:
            pass
        return new_tag
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.put("/{tag_id}", response_model=Dict[str, Any])
async def update_category_tag(
    tag_id: str, tag_update: CategoryTagUpdate, current_user: dict = Depends(require_super_admin)
):
    """Update a category tag (Super Admin only)"""
    try:
        tag = await category_tag_repository.findById(tag_id)
        if not tag:
            raise HTTPException(status_code=404, detail="Category tag not found")

        update_data = {}
        if tag_update.name is not None:
            # Check if tag with same name already exists (excluding current tag)
            existing_tag = await category_tag_repository.findByName(tag_update.name)
            if existing_tag and existing_tag.get("_id") != tag_id:
                raise HTTPException(status_code=400, detail="Category tag with this name already exists")
            update_data.name = tag_update.name.strip()

        if tag_update.description is not None:
            update_data.description = tag_update.description

        if tag_update.isActive is not None:
            update_data.isActive = tag_update.isActive

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        updated_tag = await category_tag_repository.update(tag_id, update_data)
        cache.invalidate(get_active_category_tags)
        try:
            from app.routers.categories import get_public_categories, get_tag_categories, get_tag_brands

            cache.invalidate(get_public_categories)
            cache.invalidate(get_tag_categories)
            cache.invalidate(get_tag_brands)
        except Exception:
            pass
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
        except Exception:
            pass
        return {"message": "Category tag hidden successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")

