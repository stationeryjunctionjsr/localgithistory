from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel
from app.models.base import CamelBaseModel

class SellerRequest(CamelBaseModel):
    id: str = None
    external_id: Optional[str] = None
    request_number: Optional[str] = None
    user: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    attachments: Optional[str] = None
    responses: Optional[str] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    admin_id: Optional[str] = None
    response: Optional[str] = None
    rid: Optional[str] = None
    url: Optional[str] = None
    admin: Optional[str] = None
    text: Optional[str] = None
    c: Optional[str] = None
    user_id: Optional[str] = None
    eid: Optional[str] = None
    deleted_count: int = Field(default=0)
