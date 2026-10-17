from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.models.base import CamelBaseModel

class CustomerSegmentFilters(CamelBaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid', populate_by_name=True)
    min_average_order_value: Optional[float] = None
    max_average_order_value: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    min_order_frequency: Optional[int] = None
    max_order_frequency: Optional[int] = None
    state: Optional[str] = None
    district: Optional[str] = None
    app_user: Optional[bool] = None
    behavior: Optional[str] = None
    role: Optional[str] = None
    min_order_count: Optional[int] = None
    max_order_count: Optional[int] = None
    min_order_value: Optional[float] = None
    max_order_value: Optional[float] = None
    city: Optional[str] = None

class CustomerSegmentInternalCreate(BaseModel):
    id: Optional[int] = None
    name: str
    type: str
    isActive: bool = True
    isSystem: bool = False
    userIds: List[str] = []
    filters: Optional[CustomerSegmentFilters] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class CustomerSegmentInternalUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    isActive: Optional[bool] = None
    isSystem: Optional[bool] = None
    userIds: Optional[List[str]] = None
    filters: Optional[CustomerSegmentFilters] = None
    updatedAt: Optional[str] = None
    lastRefreshedAt: Optional[str] = None

class CustomerSegmentResponse(BaseModel):
    id: Optional[int] = None
    name: str
    type: str
    userIds: List[str] = []
    filters: Optional[CustomerSegmentFilters] = None
    isActive: bool
    isSystem: bool = False
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    lastRefreshedAt: Optional[str] = None

CustomerSegment = CustomerSegmentResponse
