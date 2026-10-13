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
        try:
            all_records = await self.storage.findAll() or []
        except Exception as e:
            logger.error("Failed to fetch pincode searches: %s", str(e), exc_info=True)
            return PincodeSearchListResponse(items=[], searches=[], total=0, total_count=0, page=page, limit=limit, pages=0)

        # Sort newest first
        all_records.sort(key=lambda r: r.searched_at or r.created_at or "", reverse=True)

        filtered = []
        for r in all_records:
            if is_serviceable is not None:
                if bool(r.is_serviceable) != is_serviceable:
                    continue

            if search:
                term = search.strip().lower()
                pin = str((r.pincode if r.pincode is not None else "")).lower()
                c = str((r.city if r.city is not None else "") or "").lower()
                s = str((r.state if r.state is not None else "") or "").lower()
                d = str((r.district if r.district is not None else "") or "").lower()
                if term not in pin and term not in c and term not in s and term not in d:
                    continue

            if start_date:
                dt_str = r.searched_at or r.created_at or ""
                if dt_str and dt_str < start_date:
                    continue

            if end_date:
                dt_str = r.searched_at or r.created_at or ""
                if dt_str and dt_str > end_date:
                    continue

            filtered.append(r)

        total = len(filtered)
        start_idx = max(0, (page - 1) * limit)
        end_idx = start_idx + limit
        paginated = filtered[start_idx:end_idx]

        pages = (total + limit - 1) // limit if limit > 0 else 1

        return PincodeSearchListResponse(
            items=paginated,
            searches=paginated,
            total=total,
            total_count=total,
            page=page,
            limit=limit,
            pages=pages,
        )

    async def get_stats(self) -> PincodeSearchStatsResponse:
        """Get summary analytics on pincode searches for Super Admin."""
        try:
            all_records = await self.storage.findAll() or []
        except Exception as e:
            logger.error("Failed to fetch pincode search stats: %s", str(e), exc_info=True)
            return PincodeSearchStatsResponse()

        total_searches = len(all_records)
        unique_pins = set()
        serviceable_count = 0
        unserviceable_count = 0
        unserviceable_freq: dict[str, dict] = {}
        overall_freq: dict[str, dict] = {}

        for r in all_records:
            pin = str((r.pincode if r.pincode is not None else "")).strip()
            if not pin:
                continue
            unique_pins.add(pin)
            is_serv = bool(r.is_serviceable)
            if is_serv:
                serviceable_count += 1
            else:
                unserviceable_count += 1
                if pin not in unserviceable_freq:
                    unserviceable_freq[pin] = {
                        "pincode": pin,
                        "city": r.city,
                        "state": r.state,
                        "count": 0,
                        "last_searched_at": r.searched_at,
                    }
                unserviceable_freq[pin]["count"] += 1
                unserviceable_freq[pin]["last_searched_at"] = max(
                    unserviceable_freq[pin]["last_searched_at"] or "", r.searched_at or ""
                )

            if pin not in overall_freq:
                overall_freq[pin] = {
                    "pincode": pin,
                    "city": r.city,
                    "state": r.state,
                    "is_serviceable": is_serv,
                    "count": 0,
                    "last_searched_at": r.searched_at,
                }
            overall_freq[pin]["count"] += 1
            overall_freq[pin]["last_searched_at"] = max(
                overall_freq[pin]["last_searched_at"] or "", r.searched_at or ""
            )

        top_unserviceable = [
            PincodeStatItem(
                pincode=x["pincode"],
                city=x["city"],
                state=x["state"],
                count=x["count"],
                last_searched_at=x["last_searched_at"],
            )
            for x in sorted(unserviceable_freq.values(), key=lambda x: x["count"], reverse=True)[:10]
        ]
        top_searched = [
            PincodeStatItem(
                pincode=x["pincode"],
                city=x["city"],
                state=x["state"],
                is_serviceable=x["is_serviceable"],
                count=x["count"],
                last_searched_at=x["last_searched_at"],
            )
            for x in sorted(overall_freq.values(), key=lambda x: x["count"], reverse=True)[:10]
        ]

        return PincodeSearchStatsResponse(
            total_searches=total_searches,
            unique_pincodes=len(unique_pins),
            unique_pincodes_count=len(unique_pins),
            serviceable_searches=serviceable_count,
            unserviceable_searches=unserviceable_count,
            top_unserviceable_pincodes=top_unserviceable,
            top_searched_pincodes=top_searched,
            top_pincodes=top_searched,
        )


pincode_search_repository = PincodeSearchRepository()
