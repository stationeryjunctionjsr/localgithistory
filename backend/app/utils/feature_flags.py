"""
Feature Flag Utility Functions
Use these functions to check feature flags in your code
"""

from typing import Dict, List, Optional

from fastapi import HTTPException, status

from app.repositories.feature_flag_repository import FeatureFlagRepository
from app.utils.logger import logger

feature_flag_repository = FeatureFlagRepository()


async def is_feature_enabled(flag_id: str) -> bool:
    """
    Check if a feature flag is enabled
    Args:
        flag_id: The feature flag ID
    Returns:
        True if enabled, False otherwise
    """
    try:
        return await feature_flag_repository.is_enabled(flag_id)
    except Exception as e:
        logger.error("Error checking feature flag %s: %s", flag_id, str(e), exc_info=True)
        # Default to false if there's an error
        return False


async def get_enabled_features() -> List[Dict]:
    """
    Get all enabled feature flags
    Returns:
        List of enabled feature flags
    """
    try:
        return await feature_flag_repository.get_all_enabled()
    except Exception as e:
        logger.error("Error getting enabled features: %s", str(e), exc_info=True)
        return []


async def get_feature_flag(flag_id: str) -> Optional[Dict]:
    """
    Get feature flag by ID
    Args:
        flag_id: The feature flag ID
    Returns:
        Feature flag object or None
    """
    try:
        return await feature_flag_repository.find_by_flag_id(flag_id)
    except Exception as e:
        logger.error("Error getting feature flag %s: %s", flag_id, str(e), exc_info=True)
        return None


def require_feature(flag_id: str):
    """
    Dependency factory to check if a feature is enabled
    Usage: feature_enabled: bool = Depends(require_feature('enable_coupons'))
    """

    async def feature_checker():
        is_enabled = await is_feature_enabled(flag_id)
        if not is_enabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"Feature {flag_id} is currently disabled"
            )
        return True

    return feature_checker
