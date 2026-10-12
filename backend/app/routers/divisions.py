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
    division_id: str, current_user: User = Depends(require_super_admin)
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


@router.get("/{division_id}/tags", response_model=List[Dict[str, Any]])
async def get_category_tags_for_division(division_id: str):
    """Get all category tags under this division"""
    try:
        division = await division_repository.findById(division_id)
        if not division:
            division = await division_repository.findByName(division_id)
            if not division:
                raise HTTPException(status_code=404, detail="Division not found")

        did = int(division.id) if str(division.id).isdigit() else None
        if did is not None:
            tags = await category_tag_repository.findByDivision(did)
            return [
                {
                    "id": str(t.id),
                    "_id": str(t.id),
                    "name": t.name,
                    "description": t.description,
                    "isActive": bool(t.is_active),
                    "divisionId": t.division_id or did,
                    "divisionName": division.name,
                    "categoryHeadId": t.division_id or did,
                    "categoryHeadName": division.name,
                    "categoryCount": t.category_count or 0,
                }
                for t in tags
            ]
        return division.category_tags or []
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
    division_id: str,
    division_update: DivisionUpdate,
    current_user: User = Depends(require_super_admin),
):
    """Update a division (Super Admin only)"""
    try:
        division = await division_repository.findById(division_id)
        if not division:
            raise HTTPException(status_code=404, detail="Division not found")

        update_data = DivisionInternalUpdate()
        has_updates = False

        if division_update.name is not None:
            existing = await division_repository.findByName(division_update.name)
            existing_id = existing.id if existing else None
            if existing and str(existing_id) != str(division_id):
                raise HTTPException(
                    status_code=400, detail="Division with this name already exists"
                )
            update_data.name = division_update.name.strip()
            has_updates = True

        if division_update.description is not None:
            update_data.description = division_update.description
            has_updates = True

        if division_update.image_url is not None:
            update_data.image_url = division_update.image_url
            has_updates = True

        if division_update.display_order is not None:
            update_data.display_order = division_update.display_order
            has_updates = True

        if division_update.is_active is not None:
            update_data.is_active = division_update.is_active
            has_updates = True

        if division_update.category_tag_ids is not None:
            update_data.category_tag_ids = division_update.category_tag_ids
            has_updates = True

        if not has_updates:
            raise HTTPException(status_code=400, detail="No fields to update")

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
    division_id: str, current_user: User = Depends(require_super_admin)
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
    division_id: str,
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
