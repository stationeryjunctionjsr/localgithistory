from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.repositories.feature_flag_repository import FeatureFlagRepository
from app.utils.auth import require_super_admin
from app.utils.cache import cache
from app.utils.logger import logger

router = APIRouter()
feature_flag_repository = FeatureFlagRepository()


class FeatureFlagCreate(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    enabled: Optional[bool] = False
    category: Optional[str] = "features"


class FeatureFlagUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    category: Optional[str] = None


@router.get("", response_model=List[Dict])
@router.get("/", response_model=List[Dict])
async def get_all_feature_flags(current_user: dict = Depends(require_super_admin)):
    """Get all feature flags (Super Admin only)"""
    try:
        flags = await feature_flag_repository.find_all()
        return flags
    except Exception as e:
        logger.error("Error fetching feature flags: %s", str(e), exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred")


@router.get("/enabled", response_model=List[Dict])
@cache.ttl_cache(ttl=300.0)
async def get_enabled_feature_flags():
    """Get all enabled feature flags (Public for frontend)"""
    try:
        flags = await feature_flag_repository.get_all_enabled()
        return flags
    except Exception as e:
        logger.error("Error fetching enabled feature flags: %s", str(e), exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred")


@router.get("/{flag_id}", response_model=Dict)
async def get_feature_flag(flag_id: str, current_user: dict = Depends(require_super_admin)):
    """Get feature flag by ID (Super Admin only)"""
    try:
        flag = await feature_flag_repository.find_by_flag_id(flag_id)
        if not flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feature flag not found")
        return flag
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching feature flag: %s", str(e), exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred")


@router.get("/check/{flag_id}", response_model=Dict)
@cache.ttl_cache(ttl=300.0)
async def check_feature_flag(flag_id: str):
    """Check if a feature is enabled (Public endpoint)"""
    try:
        is_enabled = await feature_flag_repository.is_enabled(flag_id)
        return {"enabled": is_enabled}
    except Exception as e:
        logger.error("Error checking feature flag: %s", str(e), exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred")


@router.post("", response_model=Dict, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=Dict, status_code=status.HTTP_201_CREATED)
async def create_feature_flag(flag_data: FeatureFlagCreate, current_user: dict = Depends(require_super_admin)):
    """Create new feature flag (Super Admin only)"""
    try:
        # Check if flag with same ID already exists
        existing = await feature_flag_repository.find_by_flag_id(flag_data.id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Feature flag with this ID already exists"
            )

        new_flag = await feature_flag_repository.create(
            {
                "id": flag_data.id,
                "name": flag_data.name,
                "description": flag_data.description,
                "enabled": flag_data.enabled,
                "category": flag_data.category,
            }
        )

        return new_flag
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating feature flag: %s", str(e), exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred")


@router.put("/{flag_id}", response_model=Dict)
async def update_feature_flag(
    flag_id: str, update_data: FeatureFlagUpdate, current_user: dict = Depends(require_super_admin)
):
    """Update feature flag (Super Admin only)"""
    try:
        flag = await feature_flag_repository.find_by_flag_id(flag_id)
        if not flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feature flag not found")

        update_dict = update_data.model_dump(exclude_unset=True)
        updated = await feature_flag_repository.update(flag["_id"], update_dict)
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating feature flag: %s", str(e), exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred")


@router.patch("/{flag_id}/toggle", response_model=Dict)
async def toggle_feature_flag(flag_id: str, current_user: dict = Depends(require_super_admin)):
    """Toggle feature flag (Super Admin only)"""
    try:
        flag = await feature_flag_repository.find_by_flag_id(flag_id)
        if not flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feature flag not found")

        updated = await feature_flag_repository.update(flag["_id"], {"enabled": not flag.get("enabled", False)})
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error toggling feature flag: %s", str(e), exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred")


@router.delete("/{flag_id}", status_code=status.HTTP_200_OK, response_model=MessageResponse)
async def delete_feature_flag(flag_id: str, current_user: dict = Depends(require_super_admin)):
    """Delete feature flag (Super Admin only)"""
    try:
        flag = await feature_flag_repository.find_by_flag_id(flag_id)
        if not flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feature flag not found")

        await feature_flag_repository.delete(flag["_id"])
        return {"message": "Feature flag deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting feature flag: %s", str(e), exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred")
