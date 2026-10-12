from datetime import datetime
from typing import Optional, List
from app.models.base import CamelBaseModel

class SellerRequestResponseItem(CamelBaseModel):
    admin_id: Optional[str] = None
    response: Optional[str] = None
    created_at: Optional[datetime] = None

class SellerRequest(CamelBaseModel):
    id: Optional[int] = None
    request_number: Optional[str] = None
    user: Optional[str] = None
    user_id: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    attachments: Optional[List[str]] = None
    responses: Optional[List[SellerRequestResponseItem]] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
