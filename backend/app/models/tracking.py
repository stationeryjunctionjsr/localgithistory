from pydantic import ConfigDict
from datetime import datetime
from typing import Optional, List
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
    cart_items: Optional[List['ItemSnippet']] = None
    order_id: Optional[str] = None
    order_value: Optional[float] = None
    price: Optional[float] = None
    category: Optional[str] = None
    filter_name: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    product_ids: Optional[List[str]] = None
    payload: Optional['TrackingPayload'] = None
    product_id: Optional[str] = None
    quantity: int = Field(default=0)
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


class RecentlyViewedProductItem(CamelBaseModel):
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    display_image: Optional[str] = None
    price: Optional[float] = None


class TopProductItem(CamelBaseModel):
    product_id: str
    product_name: str
    views: int = 0


class DropOffPointItem(CamelBaseModel):
    page: str
    count: int = 0
    reasons: dict[str, int] = Field(default_factory=dict)


class MostAbandonedProductItem(CamelBaseModel):
    product_id: str
    product_name: str
    category: str
    abandon_count: int = Field(default=0, alias="abandonCount")
    quantity_abandoned: int = Field(default=0, alias="quantityAbandoned")
    value_lost: float = Field(default=0.0, alias="valueLost")


class MostSearchedItem(CamelBaseModel):
    term: str
    count: int = 0
    avg_products_found: float = Field(default=0.0, alias="avgProductsFound")


class ZeroResultSearchItem(CamelBaseModel):
    term: str
    count: int = 0


class MostViewedItem(CamelBaseModel):
    product_id: str
    product_name: str
    count: int = 0


class ReturningUserItem(CamelBaseModel):
    user_id: str
    name: str
    email: str
    last_seen: Optional[str] = Field(default=None, alias="lastSeen")


class ProductSearchCount(CamelBaseModel):
    product_id: str
    count: int = 0


Tracking.model_rebuild()
TrackingPayload.model_rebuild()


