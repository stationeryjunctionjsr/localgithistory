from app.models.user import User
from typing import Dict, Any, List
from app.models.schemas import ProductResponse, MessageResponse, CollectionResponse
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.models.schemas import ProductResponse, MessageResponse, CollectionResponse, CollectionResponse, CollectionUpdate
from app.repositories.collection_repository import collection_repository
from app.utils.auth import require_super_admin
from app.utils.cache import cache
from app.utils.logger import logger

router = APIRouter()


@router.get("/public", response_model=List[CollectionResponse])
@cache.ttl_cache(ttl=300.0)
async def get_public_collections(
    visiblePage: Optional[str] = None,
    pageType: Optional[str] = None,
    pageId: Optional[str] = None,
    userRole: Optional[str] = "guest",
):
    """Active collections for landing page/consumer view."""
    query = {"isActive": True, "visiblePage": visiblePage, "pageType": pageType, "pageId": pageId, "userRole": userRole}
    return await collection_repository.findAll(query)


@router.get("", response_model=List[CollectionResponse])
@router.get("/", response_model=List[CollectionResponse])
async def get_collections(current_user: User = Depends(require_super_admin)):
    """All collections (super_admin only)."""
    return await collection_repository.findAll()


@router.get("/{collection_id}/products", response_model=List[ProductResponse])
@cache.ttl_cache(ttl=600.0)
async def get_collection_products(collection_id: str):
    """Get products belonging to a collection (public endpoint)."""
    from app.repositories.product_repository import product_repository

    collection = await collection_repository.findById(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    products = await product_repository.findByCollection(collection_id)
    return products


@router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(collection_id: str, current_user: User = Depends(require_super_admin)):
    """Get single collection by ID."""
    collection = await collection_repository.findById(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


@router.post("/upload-image", status_code=status.HTTP_200_OK, response_model=Dict[str, str])
async def upload_collection_image(image: UploadFile = File(...), current_user: User = Depends(require_super_admin)):
    """Upload collection cover image (super_admin only). Uses OCI Object Storage when configured."""
    try:
        from app.services.oci_storage import upload_image_and_return_path

        if not image.content_type or not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File is not an image")
        image_url = await upload_image_and_return_path(image, "collections", filename_prefix="collection")
        return {"imageUrl": image_url}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("upload_collection_image failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Server error")


def _invalidate_collection_caches():
    cache.invalidate(get_public_collections)
    cache.invalidate(get_collection_products)
    try:
        from app.routers.products import get_public_products

        cache.invalidate(get_public_products)
    except Exception:
        pass


@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(data: CollectionCreate, current_user: User = Depends(require_super_admin)):
    collection = await collection_repository.create(data)
    _invalidate_collection_caches()
    return collection


@router.put("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: str, data: CollectionUpdate, current_user: User = Depends(require_super_admin)
):
    collection = await collection_repository.update(collection_id, data)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    _invalidate_collection_caches()
    return collection


@router.delete("/{collection_id}", response_model=MessageResponse)
async def delete_collection(collection_id: str, current_user: User = Depends(require_super_admin)):
    ok = await collection_repository.delete(collection_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Collection not found")
    _invalidate_collection_caches()
    return {"message": "Collection deleted successfully"}


