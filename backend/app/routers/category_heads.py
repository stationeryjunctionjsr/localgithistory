import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field

from app.models.base import CamelBaseModel

from app.models.category_head import (
    CategoryHeadBase,
    CategoryHeadCreate,
    CategoryHeadInternalCreate,
    CategoryHeadInternalUpdate,
    CategoryHeadResponse,
    CategoryHeadUpdate,
)
from app.models.schemas import MessageResponse
from app.models.user import User
from app.repositories.category_head_repository import category_head_repository
from app.repositories.category_tag_repository import category_tag_repository
from app.utils.auth import require_super_admin
from app.utils.cache import cache
from app.utils.logger import logger

router = APIRouter()


def _invalidate_category_head_caches():
    try:
        cache.invalidate(get_active_category_heads)
    except Exception as e:
        logging.warning("Could not invalidate get_active_category_heads: %s", e)
    try:
        from app.routers.category_tags import get_active_category_tags
        cache.invalidate(get_active_category_tags)
    except Exception as e:
        logging.warning("Could not invalidate get_active_category_tags: %s", e)


@router.get("", response_model=List[CategoryHeadResponse])
@router.get("/")
async def get_category_heads(current_user: User = Depends(require_super_admin)):
    """Get all category heads with their associated category tags (Super Admin only)"""
    try:
        heads = await category_head_repository.findAll()
        return heads
    except Exception as e:
        logger.error("Unexpected error in get_category_heads: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/active", response_model=List[CategoryHeadResponse])
@cache.ttl_cache(ttl=300.0)
async def get_active_category_heads():
    """Get active category heads (public endpoint)"""
    try:
        heads = await category_head_repository.findAll(is_active=True)
        active_heads = [h for h in heads if h.is_active is not False]
        return active_heads
    except Exception as e:
        logger.error("Unexpected error in get_active_category_heads: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/{head_id}", response_model=CategoryHeadResponse)
async def get_category_head(
    head_id: str, current_user: User = Depends(require_super_admin)
):
    """Get a category head by ID (Super Admin only)"""
    try:
        head = await category_head_repository.findById(head_id)
        if not head:
            raise HTTPException(status_code=404, detail="Category head not found")
        return head
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in get_category_head: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/{head_id}/tags", response_model=List[Dict[str, Any]])
async def get_category_tags_for_head(head_id: str):
    """Get all category tags under this category head"""
    try:
        head = await category_head_repository.findById(head_id)
        if not head:
            # Try by name
            head = await category_head_repository.findByName(head_id)
            if not head:
                raise HTTPException(status_code=404, detail="Category head not found")

        hid = int(head.id) if str(head.id).isdigit() else None
        if hid is not None:
            tags = await category_tag_repository.findByCategoryHead(hid)
            return [
                {
                    "id": str(t.id),
                    "_id": str(t.id),
                    "externalId": t.external_id,
                    "name": t.name,
                    "description": t.description,
                    "isActive": bool(t.is_active),
                    "categoryHeadId": t.category_head_id,
                    "categoryHeadName": head.name,
                    "categoryCount": t.category_count or 0,
                }
                for t in tags
            ]
        return head.category_tags or []
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in get_category_tags_for_head: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.post("", response_model=CategoryHeadResponse, status_code=201)
@router.post("/", response_model=CategoryHeadResponse, status_code=201)
async def create_category_head(
    head: CategoryHeadCreate, current_user: User = Depends(require_super_admin)
):
    """Create a new category head (Super Admin only)"""
    try:
        existing = await category_head_repository.findByName(head.name)
        if existing:
            raise HTTPException(
                status_code=400, detail="Category head with this name already exists"
            )

        head_data = CategoryHeadInternalCreate(
            name=head.name.strip(),
            description=head.description,
            image_url=head.image_url,
            display_order=head.display_order,
            is_active=head.is_active,
            category_tag_ids=head.category_tag_ids or [],
        )
        new_head = await category_head_repository.create(head_data)
        _invalidate_category_head_caches()
        return new_head
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in create_category_head: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.put("/{head_id}", response_model=CategoryHeadResponse)
async def update_category_head(
    head_id: str,
    head_update: CategoryHeadUpdate,
    current_user: User = Depends(require_super_admin),
):
    """Update a category head (Super Admin only)"""
    try:
        head = await category_head_repository.findById(head_id)
        if not head:
            raise HTTPException(status_code=404, detail="Category head not found")

        update_data = CategoryHeadInternalUpdate()
        has_updates = False

        if head_update.name is not None:
            existing = await category_head_repository.findByName(head_update.name)
            existing_id = existing.id if existing else None
            if existing and str(existing_id) != str(head_id):
                raise HTTPException(
                    status_code=400, detail="Category head with this name already exists"
                )
            update_data.name = head_update.name.strip()
            has_updates = True

        if head_update.description is not None:
            update_data.description = head_update.description
            has_updates = True

        if head_update.image_url is not None:
            update_data.image_url = head_update.image_url
            has_updates = True

        if head_update.display_order is not None:
            update_data.display_order = head_update.display_order
            has_updates = True

        if head_update.is_active is not None:
            update_data.is_active = head_update.is_active
            has_updates = True

        if head_update.category_tag_ids is not None:
            update_data.category_tag_ids = head_update.category_tag_ids
            has_updates = True

        if not has_updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updated_head = await category_head_repository.update(head_id, update_data)
        _invalidate_category_head_caches()
        return updated_head
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in update_category_head: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.delete("/{head_id}", response_model=MessageResponse)
async def delete_category_head(
    head_id: str, current_user: User = Depends(require_super_admin)
):
    """Delete a category head (Super Admin only)"""
    try:
        head = await category_head_repository.findById(head_id)
        if not head:
            raise HTTPException(status_code=404, detail="Category head not found")

        await category_head_repository.hardDelete(head_id)
        _invalidate_category_head_caches()
        return {"message": "Category head deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in delete_category_head: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


class AssignTagsRequest(CamelBaseModel):
    category_tag_ids: List[int] = Field(default_factory=list)


@router.post("/{head_id}/tags", response_model=CategoryHeadResponse)
async def assign_tags_to_category_head(
    head_id: str,
    payload: AssignTagsRequest,
    current_user: User = Depends(require_super_admin),
):
    """Assign category tags to a category head (Super Admin only)"""
    try:
        head = await category_head_repository.findById(head_id)
        if not head:
            raise HTTPException(status_code=404, detail="Category head not found")

        update_data = CategoryHeadInternalUpdate(
            category_tag_ids=payload.category_tag_ids
        )
        updated = await category_head_repository.update(head_id, update_data)
        _invalidate_category_head_caches()
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in assign_tags_to_category_head: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")
