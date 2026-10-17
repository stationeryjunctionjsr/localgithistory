import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field

from app.models.base import CamelBaseModel
from app.models.division import (
    DivisionBase,
    DivisionCreate,
    DivisionInternalCreate,
    DivisionInternalUpdate,
    DivisionResponse,
    DivisionUpdate,
)
from app.models.schemas import MessageResponse
from app.models.user import User
from app.repositories.division_repository import division_repository
from app.repositories.category_tag_repository import category_tag_repository
from app.routers.category_tags import CategoryTagResponse
from app.utils.auth import require_super_admin
from app.utils.cache import cache
from app.utils.logger import logger

router = APIRouter()


def _invalidate_division_caches():
    try:
        cache.invalidate(get_active_divisions)
    except Exception as e:
        logging.warning("Could not invalidate get_active_divisions: %s", e)
    try:
        from app.routers.category_tags import get_active_category_tags
        cache.invalidate(get_active_category_tags)
    except Exception as e:
        logging.warning("Could not invalidate get_active_category_tags: %s", e)


@router.get("", response_model=List[DivisionResponse])
@router.get("/")
async def get_divisions(current_user: User = Depends(require_super_admin)):
    """Get all divisions with their associated category tags (Super Admin only)"""
    try:
        divisions = await division_repository.findAll()
        return divisions
    except Exception as e:
        logger.error("Unexpected error in get_divisions: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/active", response_model=List[DivisionResponse])
@cache.ttl_cache(ttl=300.0)
async def get_active_divisions():
    """Get active divisions (public endpoint)"""
    try:
        divisions = await division_repository.findAll(is_active=True)
        active_divisions = [d for d in divisions if d.is_active is not False]
        return active_divisions
    except Exception as e:
        logger.error("Unexpected error in get_active_divisions: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/{division_id}", response_model=DivisionResponse)
async def get_division(
    division_id: int, current_user: User = Depends(require_super_admin)
):
    """Get a division by ID (Super Admin only)"""
    try:
        division = await division_repository.findById(division_id)
        if not division:
            raise HTTPException(status_code=404, detail="Division not found")
        return division
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in get_division: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/{division_id}/tags", response_model=List[CategoryTagResponse])
async def get_category_tags_for_division(division_id: int):
    """Get all category tags under this division"""
    try:
        division = await division_repository.findById(division_id)
        if not division:
            raise HTTPException(status_code=404, detail="Division not found")

        did = division.id
        if did is not None:
            tags = await category_tag_repository.findByDivision(did)
            return [
                CategoryTagResponse(
                    id=t.id,
                    name=t.name,
                    description=t.description,
                    is_active=bool(t.is_active),
                    division_id=t.division_id or did,
                    division_name=division.name,
                    category_head_id=t.division_id or did,
                    category_head_name=division.name,
                    category_count=t.category_count or 0,
                )
                for t in tags
            ]
        return [
            CategoryTagResponse(
                id=t.id,
                name=t.name,
                description=t.description,
                is_active=bool(t.is_active),
                division_id=did,
                division_name=division.name,
                category_head_id=did,
                category_head_name=division.name,
                category_count=0,
            )
            for t in (division.category_tags or [])
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in get_category_tags_for_division: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.post("", response_model=DivisionResponse, status_code=201)
@router.post("/", response_model=DivisionResponse, status_code=201)
async def create_division(
    division: DivisionCreate, current_user: User = Depends(require_super_admin)
):
    """Create a new division (Super Admin only)"""
    try:
        existing = await division_repository.findByName(division.name)
        if existing:
            raise HTTPException(
                status_code=400, detail="Division with this name already exists"
            )

        division_data = DivisionInternalCreate(
            name=division.name.strip(),
            description=division.description,
            image_url=division.image_url,
            display_order=division.display_order,
            is_active=division.is_active,
            category_tag_ids=division.category_tag_ids or [],
        )
        new_division = await division_repository.create(division_data)
        _invalidate_division_caches()
        return new_division
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in create_division: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.put("/{division_id}", response_model=DivisionResponse)
async def update_division(
    division_id: int,
    division_update: DivisionUpdate,
    current_user: User = Depends(require_super_admin),
):
    """Update a division (Super Admin only)"""
    try:
        division = await division_repository.findById(division_id)
        if not division:
            raise HTTPException(status_code=404, detail="Division not found")

        if not division_update.model_fields_set:
            raise HTTPException(status_code=400, detail="No fields to update")

        if division_update.name is not None:
            existing = await division_repository.findByName(division_update.name)
            existing_id = existing.id if existing else None
            if existing and existing_id != division_id:
                raise HTTPException(
                    status_code=400, detail="Division with this name already exists"
                )
            division_update.name = division_update.name.strip()

        update_data = DivisionInternalUpdate.model_validate(
            division_update.model_dump(exclude_unset=True)
        )
        updated_division = await division_repository.update(division_id, update_data)
        _invalidate_division_caches()
        return updated_division
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in update_division: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.delete("/{division_id}", response_model=MessageResponse)
async def delete_division(
    division_id: int, current_user: User = Depends(require_super_admin)
):
    """Delete a division (Super Admin only)"""
    try:
        division = await division_repository.findById(division_id)
        if not division:
            raise HTTPException(status_code=404, detail="Division not found")

        await division_repository.hardDelete(division_id)
        _invalidate_division_caches()
        return {"message": "Division deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in delete_division: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


class AssignTagsRequest(CamelBaseModel):
    category_tag_ids: List[int] = Field(default_factory=list)


@router.post("/{division_id}/tags", response_model=DivisionResponse)
async def assign_tags_to_division(
    division_id: int,
    payload: AssignTagsRequest,
    current_user: User = Depends(require_super_admin),
):
    """Assign category tags to a division (Super Admin only)"""
    try:
        division = await division_repository.findById(division_id)
        if not division:
            raise HTTPException(status_code=404, detail="Division not found")

        update_data = DivisionInternalUpdate(
            category_tag_ids=payload.category_tag_ids
        )
        updated = await division_repository.update(division_id, update_data)
        _invalidate_division_caches()
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in assign_tags_to_division: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")
