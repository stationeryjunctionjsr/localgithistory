from pydantic import BaseModel, ConfigDict, Field
from typing import List, Dict, Any, Optional
from app.models.order import Order
from app.models.sub_order import SubOrder

class PaginatedOrdersResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    orders: List[Order]
    totalCount: int = Field(alias="totalCount")
    page: int
    limit: int

class PaginatedSubOrdersResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    subOrders: List[SubOrder] = Field(alias="subOrders")
    totalCount: int = Field(alias="totalCount")
    page: int
    limit: int

class DeliveryChargeUpdateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    message: str
    order: Order
    difference: float
    oldDeliveryCharge: float = Field(alias="oldDeliveryCharge")
    newDeliveryCharge: float = Field(alias="newDeliveryCharge")


# heavily nests User and Product objects inside the base Order fields.

