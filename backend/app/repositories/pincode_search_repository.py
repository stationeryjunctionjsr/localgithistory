from datetime import datetime, timedelta, timezone
from typing import List, Optional

from app.db.storage_factory import get_storage
from app.models.pincode_searches import (
    PincodeSearches,
    PincodeSearchListResponse,
    PincodeSearchStatsResponse,
    PincodeStatItem,
)
from app.utils.logger import logger

IST = timezone(timedelta(hours=5, minutes=30))


class PincodeSearchRepository:
    def __init__(self) -> None:
        self._storage = None

    @property
    def storage(self):
        if self._storage is None:
            self._storage = get_storage("pincodeSearches")
        return self._storage

    async def log_search(
        self,
        pincode: str,
        is_serviceable: bool,
        seller_count: int = 0,
        serviceable_seller_ids: Optional[List[str]] = None,
        user_role: str = "customer",
        user_id: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
    ) -> Optional[PincodeSearches]:
        """Log a pincode search event into the database with timestamp and serviceability details."""
        try:
            now_ist = datetime.now(IST).isoformat()
            doc = {
                "pincode": str(pincode).strip(),
                "isServiceable": bool(is_serviceable),
                "status": "serviceable" if is_serviceable else "not_serviceable",
                "sellerCount": int(seller_count or 0),
                "serviceableSellerIds": serviceable_seller_ids or [],
                "userRole": str(user_role or "customer"),
                "userId": str(user_id) if user_id else None,
                "city": city or None,
                "state": state or None,
                "district": district or None,
                "searchedAt": now_ist,
                "date": now_ist,
            }
            return await self.storage.create(doc)
        except Exception as e:
            logger.error("Failed to log pincode search for %s: %s", pincode, str(e), exc_info=True)
            return None

    async def get_searches(
        self,
        page: int = 1,
        limit: int = 50,
        is_serviceable: Optional[bool] = None,
        search: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> PincodeSearchListResponse:
        """Fetch paginated pincode search logs with optional filters."""
        skip = max(0, (page - 1) * limit)
        try:
            items, total = await self.storage.find_paginated(
                is_serviceable=is_serviceable,
                search=search,
                start_date=start_date,
                end_date=end_date,
                skip=skip,
                limit=limit,
            )
            pages = (total + limit - 1) // limit if limit > 0 else 1
            return PincodeSearchListResponse(
                items=items,
                searches=items,
                total=total,
                total_count=total,
                page=page,
                limit=limit,
                pages=pages,
            )
        except Exception as e:
            logger.error("Failed to fetch pincode searches: %s", str(e), exc_info=True)
            return PincodeSearchListResponse(items=[], searches=[], total=0, total_count=0, page=page, limit=limit, pages=0)

    async def get_stats(self) -> PincodeSearchStatsResponse:
        """Get summary analytics on pincode searches for Super Admin via direct SQL pushdown."""
        return await self.storage.get_stats()


pincode_search_repository = PincodeSearchRepository()
