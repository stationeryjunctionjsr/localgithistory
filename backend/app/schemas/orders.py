from pydantic import BaseModel, ConfigDict, Field
from typing import List, Dict, Any, Optional
from app.models.order import Order
from app.models.sub_order import SubOrder

class PaginatedOrdersResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    orders: List[Order]
    totalCount: int = Field(alias="totalCount")
    page: int
    limit: int

class PaginatedSubOrdersResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    subOrders: List[SubOrder] = Field(alias="subOrders")
    totalCount: int = Field(alias="totalCount")
    page: int
    limit: int

class DeliveryChargeUpdateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    message: str
    order: Dict[str, Any]
    difference: float
    oldDeliveryCharge: float = Field(alias="oldDeliveryCharge")
    newDeliveryCharge: float = Field(alias="newDeliveryCharge")

# Notice we use Dict[str, Any] for the order because `populate_order` 
# heavily nests User and Product objects inside the base Order fields.
