import logging
from app.models.user import User
from typing import Dict, Any, List
from app.models.schemas import MessageResponse
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.models.schemas import BrandCreate, BrandUpdate, BrandResponse
from app.repositories.brand_repository import brand_repository
from app.utils.auth import require_super_admin
from app.utils.cache import cache
from app.utils.logger import logger

router = APIRouter()


@router.get("/public", response_model=List[BrandResponse])
@cache.ttl_cache(ttl=300.0)
async def get_public_brands(forHomepage: bool = False):
    """Active brands with name and logo. If forHomepage=true, only brands with display-in-homepage enabled (web & mobile)."""
    brands = await brand_repository.findActive()
    if forHomepage:
        featured = [b for b in brands if b.showInMobileHomepage]
        if featured:
            brands = featured
    return [
        {
            "_id": b.id,
            "name": (b.name or ""),
            "logoUrl": (b.image_url or "") or "",
            "showInMobileHomepage": b.showInMobileHomepage,
        }
        for b in brands
    ]


@router.get("", response_model=List[BrandResponse])
@router.get("/", response_model=List[BrandResponse])
async def get_brands(current_user: User = Depends(require_super_admin)):
    """All brands (super_admin only)."""
    return await brand_repository.findAll()


@router.post("/upload-logo", status_code=status.HTTP_200_OK, response_model=Dict[str, str])
async def upload_brand_logo(image: UploadFile = File(...), current_user: User = Depends(require_super_admin)):
    """Upload brand logo (super_admin only). Uses OCI Object Storage when configured."""
    try:
        from app.services.oci_storage import upload_image_and_return_path

        if not image.content_type or not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File is not an image")
        logo_url = await upload_image_and_return_path(image, "brands", filename_prefix="brand")
        return {"logoUrl": logo_url}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("upload_brand_logo failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Server error")


def _invalidate_brand_caches():
    cache.invalidate(get_public_brands)
    try:
        from app.routers.categories import get_tag_brands

        cache.invalidate(get_tag_brands)
    except Exception as e:
        logging.warning("_invalidate_brand_caches: could not invalidate get_tag_brands cache: %s", e, exc_info=e)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=BrandResponse)
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=BrandResponse)
async def create_brand(data: BrandCreate, current_user: User = Depends(require_super_admin)):
    brand = await brand_repository.create(data)
    _invalidate_brand_caches()
    return brand


@router.put("/{brand_id}", response_model=BrandResponse)
async def update_brand(brand_id: str, data: BrandUpdate, current_user: User = Depends(require_super_admin)):
    brand = await brand_repository.update(brand_id, data)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    _invalidate_brand_caches()
    return brand


@router.delete("/{brand_id}", response_model=MessageResponse)
async def delete_brand(brand_id: str, current_user: User = Depends(require_super_admin)):
    ok = await brand_repository.delete(brand_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Brand not found")
    _invalidate_brand_caches()
    return {"message": "Brand deleted successfully"}
