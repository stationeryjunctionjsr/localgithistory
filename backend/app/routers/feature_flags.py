from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.user import User
from app.models.schemas import MessageResponse
from app.models.feature_flag import FeatureFlag, FeatureFlagCreate, FeatureFlagUpdate
from app.repositories.feature_flag_repository import FeatureFlagRepository
from app.utils.auth import require_super_admin
from app.utils.cache import cache
from app.utils.logger import logger

router = APIRouter()
feature_flag_repository = FeatureFlagRepository()

FeatureFlagItem = FeatureFlag


@router.get("", response_model=List[FeatureFlag])
@router.get("/", response_model=List[FeatureFlag])
async def get_all_feature_flags(current_user: User = Depends(require_super_admin)):
    """Get all feature flags (Super Admin only)"""
    try:
        flags = await feature_flag_repository.find_all()
        return flags
    except Exception as e:
        logger.error("Error fetching feature flags: %s", str(e), exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred")


@router.get("/enabled", response_model=List[FeatureFlag])
@cache.ttl_cache(ttl=300.0)
async def get_enabled_feature_flags():
    """Get all enabled feature flags (Public for frontend)"""
    try:
        flags = await feature_flag_repository.get_all_enabled()
        return flags
    except Exception as e:
        logger.error("Error fetching enabled feature flags: %s", str(e), exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred")


@router.get("/{flag_id}", response_model=FeatureFlag)
async def get_feature_flag(flag_id: str, current_user: User = Depends(require_super_admin)):
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


@router.get("/check/{flag_id}", response_model=FeatureFlag)
@cache.ttl_cache(ttl=300.0)
async def check_feature_flag(flag_id: str):
    """Check if a feature is enabled (Public endpoint)"""
    try:
        is_enabled = await feature_flag_repository.is_enabled(flag_id)
        return FeatureFlag(id=flag_id, flag_id=flag_id, enabled=is_enabled)
    except Exception as e:
        logger.error("Error checking feature flag: %s", str(e), exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred")


@router.post("", response_model=FeatureFlag, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=FeatureFlag, status_code=status.HTTP_201_CREATED)
async def create_feature_flag(flag_data: FeatureFlagCreate, current_user: User = Depends(require_super_admin)):
    """Create new feature flag (Super Admin only)"""
    try:
        existing = await feature_flag_repository.find_by_flag_id(flag_data.id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Feature flag with this ID already exists"
            )

        new_flag = await feature_flag_repository.create(
            FeatureFlag(
                flag_id=flag_data.id,
                name=flag_data.name,
                description=flag_data.description,
                enabled=flag_data.enabled if flag_data.enabled is not None else False,
                category=flag_data.category,
            )
        )

        return new_flag
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating feature flag: %s", str(e), exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred")


@router.put("/{flag_id}", response_model=FeatureFlag)
async def update_feature_flag(
    flag_id: str, update_data: FeatureFlagUpdate, current_user: User = Depends(require_super_admin)
):
    """Update feature flag (Super Admin only)"""
    try:
        flag = await feature_flag_repository.find_by_flag_id(flag_id)
        if not flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feature flag not found")

        updated = await feature_flag_repository.update(
            flag.id,
            FeatureFlag(
                flag_id=flag_id,
                name=update_data.name,
                description=update_data.description,
                enabled=update_data.enabled,
                category=update_data.category,
            ),
        )
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating feature flag: %s", str(e), exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred")


@router.patch("/{flag_id}/toggle", response_model=FeatureFlag)
async def toggle_feature_flag(flag_id: str, current_user: User = Depends(require_super_admin)):
    """Toggle feature flag (Super Admin only)"""
    try:
        flag = await feature_flag_repository.find_by_flag_id(flag_id)
        if not flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feature flag not found")

        updated = await feature_flag_repository.update(
            flag.id,
            FeatureFlag(enabled=not flag.enabled),
        )
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error toggling feature flag: %s", str(e), exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred")


@router.delete("/{flag_id}", status_code=status.HTTP_200_OK, response_model=MessageResponse)
async def delete_feature_flag(flag_id: str, current_user: User = Depends(require_super_admin)):
    """Delete feature flag (Super Admin only)"""
    try:
        flag = await feature_flag_repository.find_by_flag_id(flag_id)
        if not flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feature flag not found")

        await feature_flag_repository.delete(flag.id)
        return MessageResponse(message="Feature flag deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting feature flag: %s", str(e), exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred")
