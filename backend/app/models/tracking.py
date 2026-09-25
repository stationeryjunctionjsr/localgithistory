from pydantic import ConfigDict
from datetime import datetime
from typing import Optional, List, Any
from pydantic import Field
from pydantic import BaseModel
from app.models.base import CamelBaseModel

class Tracking(CamelBaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    type: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    search_term: Optional[str] = None
    results_count: Optional[int] = None
    product_name: Optional[str] = None
    segment: Optional[str] = None
    page: Optional[str] = None
    reason: Optional[str] = None
    filter_type: Optional[str] = None
    filter_value: Optional[str] = None
    cart_value: Optional[float] = None
    is_returning: Optional[bool] = None
    source: Optional[str] = None
    campaign: Optional[str] = None
    os: Optional[str] = None
    browser: Optional[str] = None
    ip_address: Optional[str] = None
    page_views: Optional[int] = None
    cart_items: Optional[List['ItemSnippet']] = None
    order_id: Optional[str] = None
    order_value: Optional[float] = None
    price: Optional[float] = None
    category: Optional[str] = None
    filter_name: Optional[str] = None
    id: str = None
    external_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    product_ids: List[str] = Field(default=[])
    product_ids: Optional[List[str]] = None
    payload: Optional['TrackingPayload'] = None
    product_id: Optional[str] = None
    quantity: int = Field(default=0)
    tid: Optional[str] = None
    pid: Optional[str] = None
    k: Optional[str] = None
    v: Optional[str] = None
    eid: Optional[str] = None
    c: Optional[str] = None
    u: Optional[str] = None
    timestamp: Optional[str] = None


from app.models.schemas import ItemSnippet

class TrackingPayload(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    value: Optional[str] = None
    name: Optional[str] = None
    query: Optional[str] = None
    currency: Optional[str] = None
    amount: Optional[float] = None
    product_id: Optional[str] = None
    category_id: Optional[str] = None
    order_id: Optional[str] = None
    page: Optional[str] = None
    label: Optional[str] = None

Tracking.model_rebuild()
TrackingPayload.model_rebuild()
