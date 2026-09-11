from typing import Dict, Any, List
from app.models.schemas import MessageResponse
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.repositories.pincode_search_repository import pincode_search_repository
from app.utils.auth import require_super_admin

router = APIRouter(prefix="/admin/pincode-searches", tags=["admin-pincode-searches"])


@router.get("", response_model=Dict[str, Any])
@router.get("/", response_model=Dict[str, Any])
async def get_pincode_searches(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    isServiceable: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    current_user: dict = Depends(require_super_admin),
):
    """Super Admin: Get paginated list of searched pincodes with serviceability status and timestamps."""
    return await pincode_search_repository.get_searches(
        page=page,
        limit=limit,
        is_serviceable=isServiceable,
        search=search,
        start_date=startDate,
        end_date=endDate,
    )


@router.get("/stats", response_model=Dict[str, Any])
async def get_pincode_search_stats(
    current_user: dict = Depends(require_super_admin),
):
    """Super Admin: Get aggregated statistics on searched pincodes and top unserviceable demand areas."""
    return await pincode_search_repository.get_stats()
