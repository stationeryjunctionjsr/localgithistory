from app.models.user import User
from typing import List
from app.models.schemas import MessageResponse
from fastapi import APIRouter, Depends, HTTPException

from app.models.daos_flat import SearchTagInternalCreate, SearchTagInternalUpdate
from app.models.schemas import SearchTagCreate, SearchTagUpdate, SearchTagResponse
from app.repositories.search_tag_repository import search_tag_repository
from app.utils.auth import require_super_admin
from app.utils.cache import cache
from app.utils.logger import logger

router = APIRouter()


@router.get("", response_model=List[SearchTagResponse])
@router.get("/", response_model=List[SearchTagResponse])
@cache.ttl_cache(ttl=300.0)
async def get_all_tags():
    return await search_tag_repository.findAll()


@router.post("", response_model=SearchTagResponse)
@router.post("/", response_model=SearchTagResponse)
async def create_tag(tag: SearchTagCreate, admin: User = Depends(require_super_admin)):
    internal_data = SearchTagInternalCreate.model_validate(tag, from_attributes=True)
    return await search_tag_repository.create(internal_data)


@router.put("/{id}", response_model=SearchTagResponse)
async def update_tag(id: str, tag_update: SearchTagUpdate, admin: User = Depends(require_super_admin)):
    logger.info("Updating search tag id=%s", id)
    tag = await search_tag_repository.findById(id)
    if not tag:
        logger.warning("Search tag not found by _id=%s; trying tagId fallback", id)
        # Try finding by tagId as fallback
        all_tags = await search_tag_repository.findAll()
        tag = next((t for t in all_tags if t.tag_id == id), None)
        if not tag:
            raise HTTPException(status_code=404, detail="Search tag not found")
        id = str(tag.id)
        logger.info("Search tag resolved by tagId fallback, internal id=%s", id)

    logger.info("Search tag found for update id=%s", id)
    internal_update = SearchTagInternalUpdate.model_validate(tag_update, from_attributes=True)
    return await search_tag_repository.update(id, internal_update)


@router.delete("/{id}", response_model=MessageResponse)
async def delete_tag(id: str, admin: User = Depends(require_super_admin)):
    await search_tag_repository.delete(id)
    return {"message": "Tag deleted"}


