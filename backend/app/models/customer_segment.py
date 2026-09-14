from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field

class CustomerSegmentInternalCreate(BaseModel):
    id: str = Field(alias="_id", default="")
    name: str
    type: str
    isActive: bool = True
    isSystem: bool = False
    userIds: List[str] = []
    filters: Optional[Dict[str, Any]] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class CustomerSegmentInternalUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    isActive: Optional[bool] = None
    isSystem: Optional[bool] = None
    userIds: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    updatedAt: Optional[str] = None
    lastRefreshedAt: Optional[str] = None

class CustomerSegmentResponse(BaseModel):
    id: str = Field(alias="_id", default="")
    name: str
    type: str
    userIds: List[str] = []
    filters: Optional[Dict[str, Any]] = None
    isActive: bool
    isSystem: bool = False
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    lastRefreshedAt: Optional[str] = None

CustomerSegment = CustomerSegmentResponse
