
from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import SearchTagCreate, SearchTagUpdate
from app.repositories.search_tag_repository import search_tag_repository
from app.utils.auth import require_super_admin
from app.utils.cache import cache
from app.utils.logger import logger

router = APIRouter()


@router.get("")
@router.get("/")
@cache.ttl_cache(ttl=300.0)
async def get_all_tags():
    return await search_tag_repository.findAll()


@router.post("")
@router.post("/")
async def create_tag(tag: SearchTagCreate, admin: dict = Depends(require_super_admin)):
    return await search_tag_repository.create(tag.model_dump())


@router.put("/{id}")
async def update_tag(id: str, tag_update: SearchTagUpdate, admin: dict = Depends(require_super_admin)):
    logger.info("Updating search tag id=%s", id)
    tag = await search_tag_repository.findById(id)
    if not tag:
        logger.warning("Search tag not found by _id=%s; trying tagId fallback", id)
        # Try finding by tagId as fallback
        all_tags = await search_tag_repository.findAll()
        tag = next((t for t in all_tags if t.get("tagId") == id), None)
        if not tag:
            raise HTTPException(status_code=404, detail="Search tag not found")
        id = str(tag.get("_id"))
        logger.info("Search tag resolved by tagId fallback, internal id=%s", id)

    logger.info("Search tag found for update id=%s", id)
    return await search_tag_repository.update(id, tag_update.model_dump(exclude_unset=True))


@router.delete("/{id}")
async def delete_tag(id: str, admin: dict = Depends(require_super_admin)):
    await search_tag_repository.delete(id)
    return {"message": "Tag deleted"}
