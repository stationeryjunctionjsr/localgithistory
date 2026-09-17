from pydantic import ConfigDict
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel

class Tracking(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    type: Optional[str] = Field(default=None, alias='type')
    userId: Optional[str] = Field(default=None, alias='userId')
    sessionId: Optional[str] = Field(default=None, alias='sessionId')
    searchTerm: Optional[str] = Field(default=None, alias='searchTerm')
    resultsCount: Optional[int] = Field(default=None, alias='resultsCount')
    productName: Optional[str] = Field(default=None, alias='productName')
    segment: Optional[str] = Field(default=None, alias='segment')
    page: Optional[str] = Field(default=None, alias='page')
    reason: Optional[str] = Field(default=None, alias='reason')
    filterType: Optional[str] = Field(default=None, alias='filterType')
    filterValue: Optional[str] = Field(default=None, alias='filterValue')
    cartValue: Optional[float] = Field(default=None, alias='cartValue')
    isReturning: Optional[bool] = Field(default=None, alias='isReturning')
    source: Optional[str] = Field(default=None, alias='source')
    campaign: Optional[str] = Field(default=None, alias='campaign')
    os: Optional[str] = Field(default=None, alias='os')
    browser: Optional[str] = Field(default=None, alias='browser')
    ipAddress: Optional[str] = Field(default=None, alias='ipAddress')
    pageViews: Optional[int] = Field(default=None, alias='pageViews')
    cartItems: Optional[List['ItemSnippet']] = Field(default=None, alias='cartItems')
    orderId: Optional[str] = Field(default=None, alias='orderId')
    orderValue: Optional[float] = Field(default=None, alias='orderValue')
    price: Optional[float] = Field(default=None, alias='price')
    category: Optional[str] = Field(default=None, alias='category')
    filterName: Optional[str] = Field(default=None, alias='filterName')
    id: str = Field(default=None, alias='_id')
    external_id: Optional[str] = Field(default=None, alias='externalId')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    product_ids: List[str] = Field(default=[], alias='product_ids')
    productIds: Optional[List[str]] = Field(default=None, alias='productIds')
    payload: Optional[Dict] = Field(default=None, alias='payload')
    product_id: Optional[str] = Field(default=None, alias='productId')
    quantity: int = Field(default=0, alias='quantity')
    tid: Optional[str] = Field(default=None, alias='tid')
    pid: Optional[str] = Field(default=None, alias='pid')
    k: Optional[str] = Field(default=None, alias='k')
    v: Optional[str] = Field(default=None, alias='v')
    eid: Optional[str] = Field(default=None, alias='eid')
    c: Optional[str] = Field(default=None, alias='c')
    u: Optional[str] = Field(default=None, alias='u')
    timestamp: Optional[str] = Field(default=None, alias='timestamp')


from app.models.schemas import ItemSnippet
Tracking.model_rebuild()
