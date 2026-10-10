from datetime import datetime
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field

from app.models.base import CamelBaseModel
from app.models.daos_flat import (
    CategoryTagInternal,
    CategoryTagInternalCreate,
    CategoryTagInternalUpdate,
)
from app.models.schemas import MessageResponse
from app.models.category import Category
from app.models.user import User
from app.repositories.category_tag_repository import category_tag_repository
from app.utils.auth import require_super_admin
from app.utils.cache import cache
from app.utils.logger import logger

router = APIRouter()


class CategoryTagBase(CamelBaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    is_active: bool = True
    division_id: Optional[int] = None
    category_head_id: Optional[int] = None


class CategoryTagCreate(CategoryTagBase):
    pass


class CategoryTagResponse(CamelBaseModel):
    id: Optional[str] = None
    external_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = True
    division_id: Optional[int] = None
    division_name: Optional[str] = None
    category_head_id: Optional[int] = None
    category_head_name: Optional[str] = None
    category_count: Optional[int] = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CategoryTagUpdate(CamelBaseModel):
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    division_id: Optional[int] = None
    category_head_id: Optional[int] = None


def _invalidate_category_tag_caches():
    try:
        cache.invalidate(get_active_category_tags)
    except Exception as e:
        logging.warning("Could not invalidate get_active_category_tags: %s", e)
    try:
        from app.routers.categories import (
            get_public_categories,
            get_tag_brands,
            get_tag_categories,
        )

        cache.invalidate(get_public_categories)
        cache.invalidate(get_tag_categories)
        cache.invalidate(get_tag_brands)
    except Exception as e:
        logging.warning(
            "category_tags: could not invalidate category/brand caches after tag mutation: %s",
            e,
            exc_info=e,
        )
    try:
        from app.routers.divisions import get_active_divisions
        cache.invalidate(get_active_divisions)
    except Exception as e:
        logging.warning("Could not invalidate get_active_divisions: %s", e)
    try:
        from app.routers.category_heads import get_active_category_heads
        cache.invalidate(get_active_category_heads)
    except Exception as e:
        pass


@router.get("", response_model=List[CategoryTagResponse])
@router.get("/")
async def get_category_tags(
    division_id: Optional[int] = Query(None, alias="divisionId"),
    category_head_id: Optional[int] = Query(None, alias="categoryHeadId"),
    current_user: User = Depends(require_super_admin),
):
    """Get all category tags (Super Admin only, optionally filtered by divisionId / categoryHeadId)"""
    try:
        target_did = division_id if division_id is not None else category_head_id
        tags = await category_tag_repository.findAll(division_id=target_did)
        return tags
    except Exception as e:
        logger.error("Unexpected error in get_category_tags: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/active", response_model=List[CategoryTagResponse])
@cache.ttl_cache(ttl=300.0)
async def get_active_category_tags(
    division_id: Optional[int] = Query(None, alias="divisionId"),
    category_head_id: Optional[int] = Query(None, alias="categoryHeadId"),
):
    """Get active category tags (public endpoint, optionally filtered by divisionId / categoryHeadId)"""
    try:
        target_did = division_id if division_id is not None else category_head_id
        tags = await category_tag_repository.findAll(is_active=True, division_id=target_did)
        active_tags = [tag for tag in tags if tag.is_active is not False]
        return active_tags
    except Exception as e:
        logger.error("Unexpected error in get_active_category_tags: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/{tag_id}/categories", response_model=List[Category])
async def get_categories_for_tag(tag_id: str):
    """Get all categories that belong to this category tag"""
    try:
        tag = await category_tag_repository.findById(tag_id)
        if not tag:
            tag = await category_tag_repository.findByName(tag_id)
            if not tag:
                raise HTTPException(status_code=404, detail="Category tag not found")

        categories = await category_tag_repository.findCategoriesByTag(tag.id or tag.name)
        return categories
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in get_categories_for_tag: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/{tag_id}", response_model=CategoryTagResponse)
async def get_category_tag(
    tag_id: str, current_user: User = Depends(require_super_admin)
):
    """Get a category tag by ID (Super Admin only)"""
    try:
        tag = await category_tag_repository.findById(tag_id)
        if not tag:
            raise HTTPException(status_code=404, detail="Category tag not found")
        return tag
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in get_category_tag: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.post("", response_model=CategoryTagResponse, status_code=201)
@router.post("/", response_model=CategoryTagResponse, status_code=201)
async def create_category_tag(
    tag: CategoryTagBase, current_user: User = Depends(require_super_admin)
):
    """Create a new category tag (Super Admin only)"""
    try:
        existing_tag = await category_tag_repository.findByName(tag.name)
        if existing_tag:
            raise HTTPException(
                status_code=400, detail="Category tag with this name already exists"
            )

        target_did = tag.division_id if tag.division_id is not None else tag.category_head_id
        tag_data = CategoryTagInternalCreate(
            name=tag.name.strip(),
            description=tag.description,
            is_active=tag.is_active,
            division_id=target_did,
            category_head_id=target_did,
        )
        new_tag = await category_tag_repository.create(tag_data)
        _invalidate_category_tag_caches()
        return new_tag
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in create_category_tag: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.put("/{tag_id}", response_model=CategoryTagResponse)
async def update_category_tag(
    tag_id: str,
    tag_update: CategoryTagUpdate,
    current_user: User = Depends(require_super_admin),
):
    """Update a category tag (Super Admin only)"""
    try:
        tag = await category_tag_repository.findById(tag_id)
        if not tag:
            raise HTTPException(status_code=404, detail="Category tag not found")

        update_data = CategoryTagInternalUpdate()
        has_updates = False
        if tag_update.name is not None:
            existing_tag = await category_tag_repository.findByName(tag_update.name)
            existing_id = existing_tag.id if existing_tag else None
            if existing_tag and str(existing_id) != str(tag_id):
                raise HTTPException(
                    status_code=400, detail="Category tag with this name already exists"
                )
            update_data.name = tag_update.name.strip()
            has_updates = True

        if tag_update.description is not None:
            update_data.description = tag_update.description
            has_updates = True

        if tag_update.is_active is not None:
            update_data.is_active = tag_update.is_active
            has_updates = True

        target_did = tag_update.division_id if tag_update.division_id is not None else tag_update.category_head_id
        if target_did is not None:
            update_data.division_id = target_did
            update_data.category_head_id = target_did
            has_updates = True

        if not has_updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updated_tag = await category_tag_repository.update(tag_id, update_data)
        _invalidate_category_tag_caches()
        return updated_tag
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in update_category_tag: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.delete("/{tag_id}", response_model=MessageResponse)
async def delete_category_tag(
    tag_id: str, current_user: User = Depends(require_super_admin)
):
    """Delete a category tag (Super Admin only)"""
    try:
        tag = await category_tag_repository.findById(tag_id)
        if not tag:
            raise HTTPException(status_code=404, detail="Category tag not found")

        await category_tag_repository.hardDelete(tag_id)
        _invalidate_category_tag_caches()
        return MessageResponse(message="Category tag deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in delete_category_tag: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")
