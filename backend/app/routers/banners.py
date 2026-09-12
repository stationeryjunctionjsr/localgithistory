from app.models.user import User
from app.models.schemas import MessageResponse
from typing import Dict, Any, List, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.models.schemas import BannerCreate, BannerResponse, BannerUpdate
from app.repositories.banner_repository import banner_repository
from app.utils.auth import require_super_admin
from app.utils.cache import cache
from app.utils.logger import logger

router = APIRouter()


@router.get("/public", response_model=List[BannerResponse])
@cache.ttl_cache(ttl=300.0)
async def get_public_banners(
    position: Optional[str] = None,
    targetAudience: Optional[str] = None,
    pageType: Optional[str] = None,
    pageId: Optional[str] = None,
    userRole: Optional[str] = "guest",
):
    query = {
        "position": position,
        "targetAudience": targetAudience,
        "pageType": pageType,
        "pageId": pageId,
        "userRole": userRole,
    }
    banners = await banner_repository.findActive(query)

    # Enhanced position filtering to support sub-positions and legacy platform-agnostic ones
    if position:
        pos_lower = position.lower()
        target_positions = [pos_lower, "all"]

        # Homepage mapping
        homepage_variants = ["homepage", "home", "homepage_web", "homepage_mobile", "homeweb", "homemobile"]
        if pos_lower in homepage_variants or "home" in pos_lower:
            target_positions.extend(homepage_variants)

        # Sub-page mapping
        if "category" in pos_lower:
            target_positions.append("category")
        if "brand" in pos_lower:
            target_positions.append("brand")

        banners = [b for b in banners if str((b.position or "")).lower() in target_positions]

    if targetAudience:
        banners = [b for b in banners if b.target_audience == targetAudience or b.target_audience == "all"]

    return banners


@router.get("", response_model=List[BannerResponse])
@router.get("/", response_model=List[BannerResponse])
async def get_banners(
    isActive: Optional[bool] = None,
    isPublished: Optional[bool] = None,
    current_user: User = Depends(require_super_admin),
):
    query = {}
    if isActive is not None:
        query["isActive"] = isActive
    if isPublished is not None:
        query["isPublished"] = isPublished

    banners = await banner_repository.findAll(query)
    return banners


@router.post("/upload-image", status_code=status.HTTP_200_OK, response_model=Dict[str, str])
async def upload_banner_image(image: UploadFile = File(...), current_user: User = Depends(require_super_admin)):
    """Upload banner image (Super Admin only). Uses OCI Object Storage when configured."""
    try:
        from app.services.oci_storage import upload_image_and_return_path
        from PIL import Image
        import io

        if not image.content_type or not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"File {image.filename} is not an image")
            
        file_bytes = await image.read()
        if len(file_bytes) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image size exceeds the 5MB limit")
            
        try:
            img = Image.open(io.BytesIO(file_bytes))
            width, height = img.size
            if width > 4000 or height > 4000:
                raise HTTPException(status_code=400, detail=f"Image dimensions ({width}x{height}) exceed maximum allowed (4000x4000)")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image file format")
            
        await image.seek(0)
        
        image_url = await upload_image_and_return_path(image, "banners", filename_prefix="banner")
        return {"imageUrl": image_url, "image": image_url}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("upload_banner_image failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Server error")


@router.get("/{banner_id}", response_model=BannerResponse)
async def get_banner(banner_id: str, current_user: User = Depends(require_super_admin)):
    banner = await banner_repository.findById(banner_id)
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    return banner


@router.post("", response_model=BannerResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=BannerResponse, status_code=status.HTTP_201_CREATED)
async def create_banner(banner_data: BannerCreate, current_user: User = Depends(require_super_admin)):
    banner = await banner_repository.create(banner_data)
    cache.invalidate(get_public_banners)
    return banner


@router.put("/{banner_id}", response_model=BannerResponse)
async def update_banner(banner_id: str, banner_data: BannerUpdate, current_user: User = Depends(require_super_admin)):
    banner = await banner_repository.update(banner_id, banner_data)
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    cache.invalidate(get_public_banners)
    return banner


@router.delete("/{banner_id}", response_model=MessageResponse)
async def delete_banner(banner_id: str, current_user: User = Depends(require_super_admin)):
    result = await banner_repository.delete(banner_id)
    if not result:
        raise HTTPException(status_code=404, detail="Banner not found")
    cache.invalidate(get_public_banners)
    return {"message": "Banner deleted successfully"}

