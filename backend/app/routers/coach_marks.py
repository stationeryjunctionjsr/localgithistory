from app.models.user import User
from app.models.schemas import MessageResponse
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.models.daos_flat import CoachMarkInternalCreate, CoachMarkInternalUpdate
from app.models.schemas import CoachMarkCreate, CoachMarkResponse, CoachMarkUpdate
from app.repositories.coach_mark_repository import coach_mark_repository
from app.utils.auth import require_super_admin
from app.utils.cache import cache

router = APIRouter()


@router.get("", response_model=List[CoachMarkResponse])
@router.get("/", response_model=List[CoachMarkResponse])
@cache.ttl_cache(ttl=3600.0)
async def get_all_coach_marks():
    return await coach_mark_repository.findAll()


@router.get("/{id}", response_model=CoachMarkResponse)
@cache.ttl_cache(ttl=3600.0)
async def get_coach_mark(id: str):
    mark = await coach_mark_repository.findById(id)
    if not mark:
        raise HTTPException(status_code=404, detail="Coach mark not found")
    return mark


@router.post("", response_model=CoachMarkResponse)
@router.post("/", response_model=CoachMarkResponse)
async def create_coach_mark(mark: CoachMarkCreate, current_user: User = Depends(require_super_admin)):
    internal_data = CoachMarkInternalCreate(**mark.model_dump())
    return await coach_mark_repository.create(internal_data)


@router.put("/{id}", response_model=CoachMarkResponse)
async def update_coach_mark(id: str, mark_update: CoachMarkUpdate, current_user: User = Depends(require_super_admin)):
    mark = await coach_mark_repository.findById(id)
    if not mark:
        raise HTTPException(status_code=404, detail="Coach mark not found")
    internal_update = CoachMarkInternalUpdate(**mark_update.model_dump(exclude_unset=True))
    return await coach_mark_repository.update(id, internal_update)


@router.delete("/{id}", response_model=MessageResponse)
async def delete_coach_mark(id: str, current_user: User = Depends(require_super_admin)):
    await coach_mark_repository.delete(id)
    return {"message": "Coach mark deleted"}
