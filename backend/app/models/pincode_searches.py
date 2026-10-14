from datetime import datetime
from typing import List, Optional
from pydantic import Field
from app.models.base import CamelBaseModel

class PincodeSearches(CamelBaseModel):
    id: Optional[int] = None
    pincode: Optional[str] = None
    query: Optional[str] = None
    is_serviceable: bool = False
    timestamp: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def searched_at(self) -> Optional[str]:
        return self.timestamp


class PincodeSearchFilter(CamelBaseModel):
    pincode: Optional[str] = None
    query: Optional[str] = None
    is_serviceable: Optional[bool] = None
    timestamp: Optional[str] = None


class PincodeStatItem(CamelBaseModel):
    pincode: str
    city: Optional[str] = None
    state: Optional[str] = None
    is_serviceable: Optional[bool] = None
    count: int = 0
    last_searched_at: Optional[str] = None


class PincodeSearchStatsResponse(CamelBaseModel):
    total_searches: int = 0
    unique_pincodes: int = 0
    unique_pincodes_count: int = 0
    serviceable_searches: int = 0
    unserviceable_searches: int = 0
    top_unserviceable_pincodes: List[PincodeStatItem] = []
    top_searched_pincodes: List[PincodeStatItem] = []
    top_pincodes: List[PincodeStatItem] = []


class PincodeSearchListResponse(CamelBaseModel):
    items: List[PincodeSearches] = []
    searches: List[PincodeSearches] = []
    total: int = 0
    total_count: int = 0
    page: int = 1
    limit: int = 50
    pages: int = 0
