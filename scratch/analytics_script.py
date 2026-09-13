import re

with open('backend/app/routers/analytics.py', 'r') as f:
    content = f.read()

models = '''
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional

class RecordEventResponse(BaseModel):
    status: str
    eventId: Optional[str] = None

class KPIMetricsResponse(BaseModel):
    gross_sales: float
    returning_customer_rate: float
    orders_fulfilled: int
    orders: int

class DashboardDataResponse(BaseModel):
    model_config = ConfigDict(extra='allow')

class BundlePerformanceResponse(BaseModel):
    model_config = ConfigDict(extra='allow')

class SalesOverTimeResponse(BaseModel):
    period: str
    sales: float
    orderCount: int
    aov: float

class SalesBreakdownResponse(BaseModel):
    gross_sales: float
    discounts: float
    returns: float
    net_sales: float
    shipping_charges: float
    return_fees: float
    taxes: float
    total_sales: float

class AverageOrderValueResponse(BaseModel):
    period: str
    average_order_value: float

class SalesByChannelResponse(BaseModel):
    channel: str
    sales: float

class SalesByProductResponse(BaseModel):
    product_id: str
    productId: str
    name: str
    productName: str
    quantity: int
    revenue: float

class FunnelStage(BaseModel):
    count: int
    percentage: float
    drop_percentage: float

class FunnelStageNoDrop(BaseModel):
    count: int
    percentage: float

class ConversionRateResponse(BaseModel):
    sessions: FunnelStageNoDrop
    added_to_cart: FunnelStage
    reached_checkout: FunnelStage
    completed: FunnelStage
    overall_conversion_rate: float

class CheckoutFunnelResponse(BaseModel):
    cart: FunnelStageNoDrop
    shipping: FunnelStage
    review: FunnelStage
    payment: FunnelStage
    completed: FunnelStage
    overall_checkout_conversion: float

class SessionsByDeviceResponse(BaseModel):
    device: str
    sessions: int

class SessionsByLocationResponse(BaseModel):
    location: str
    sessions: int

class DurationBucket(BaseModel):
    range: str
    count: int

class UserMetric(BaseModel):
    userId: str
    name: str
    email: str
    averageSessionTimeSeconds: float
    totalSessions: int

class AllUserEngagementResponse(BaseModel):
    duration_buckets: List[DurationBucket]
    user_metrics: List[UserMetric]

class ProductsSellThroughResponse(BaseModel):
    product_id: str
    name: str
    sold: int
    stock: int
    sell_through_rate: float

class CustomerCohortResponse(BaseModel):
    cohort: str
    months: List[int]

class SessionsByLandingPageResponse(BaseModel):
    landing_page: str
    sessions: int

class UserEngagementResponse(BaseModel):
    userId: Optional[str] = None
    registrationDate: Optional[str] = None
    totalSessions: Optional[int] = None
    averageSessionTimeSeconds: Optional[float] = None
    averageDaysBetweenSessions: Optional[float] = None
    averagePagesPerSession: Optional[float] = None
    sessionsWithOrder: Optional[int] = None
    sessionOrderRate: Optional[float] = None
    error: Optional[str] = None

class TopUsersReportResponse(BaseModel):
    userId: str
    name: str
    userName: str
    email: str
    userEmail: str
    role: str
    revenue: float

class GenericListResponse(BaseModel):
    model_config = ConfigDict(extra='allow')
    
class GenericDictResponse(BaseModel):
    model_config = ConfigDict(extra='allow')
'''

# Insert models before @router.post("/events"...
content = content.replace('@router.post("/events"', models + '\n@router.post("/events"')

# Replacements
content = content.replace('response_model=Dict[str, Any]])\nasync def record_event', 'response_model=RecordEventResponse)\nasync def record_event')
content = content.replace('response_model=Dict[str, Any])\nasync def record_event', 'response_model=RecordEventResponse)\nasync def record_event')

content = content.replace('response_model=Dict[str, Any])\nasync def get_kpi_metrics', 'response_model=KPIMetricsResponse)\nasync def get_kpi_metrics')
content = content.replace('response_model=Dict[str, Any])\nasync def get_dashboard_data', 'response_model=DashboardDataResponse)\nasync def get_dashboard_data')
content = content.replace('response_model=List[Dict[str, Any]])\nasync def get_bundle_performance', 'response_model=List[BundlePerformanceResponse])\nasync def get_bundle_performance')
content = content.replace('response_model=List[Dict[str, Any]])\nasync def get_sales_over_time', 'response_model=List[SalesOverTimeResponse])\nasync def get_sales_over_time')
content = content.replace('response_model=Dict[str, Any])\nasync def get_sales_breakdown', 'response_model=SalesBreakdownResponse)\nasync def get_sales_breakdown')
content = content.replace('response_model=List[Dict[str, Any]])\nasync def get_average_order_value', 'response_model=List[AverageOrderValueResponse])\nasync def get_average_order_value')
content = content.replace('response_model=List[Dict[str, Any]])\nasync def get_sales_by_channel', 'response_model=List[SalesByChannelResponse])\nasync def get_sales_by_channel')
content = content.replace('response_model=List[Dict[str, Any]])\nasync def get_sales_by_product', 'response_model=List[SalesByProductResponse])\nasync def get_sales_by_product')

content = content.replace('response_model=Dict[str, Any])\nasync def get_conversion_rate', 'response_model=ConversionRateResponse)\nasync def get_conversion_rate')
content = content.replace('response_model=Dict[str, Any])\nasync def get_conversion_breakdown', 'response_model=ConversionRateResponse)\nasync def get_conversion_breakdown')
content = content.replace('response_model=Dict[str, Any])\nasync def get_checkout_funnel', 'response_model=CheckoutFunnelResponse)\nasync def get_checkout_funnel')

content = content.replace('response_model=List[Dict[str, Any]])\nasync def get_sessions_by_device', 'response_model=List[SessionsByDeviceResponse])\nasync def get_sessions_by_device')
content = content.replace('response_model=List[Dict[str, Any]])\nasync def get_sessions_by_location', 'response_model=List[SessionsByLocationResponse])\nasync def get_sessions_by_location')
content = content.replace('response_model=Dict[str, Any])\nasync def get_all_user_engagement', 'response_model=AllUserEngagementResponse)\nasync def get_all_user_engagement')
content = content.replace('response_model=List[Dict[str, Any]])\nasync def get_products_sell_through', 'response_model=List[ProductsSellThroughResponse])\nasync def get_products_sell_through')
content = content.replace('response_model=List[Dict[str, Any]])\nasync def get_customer_cohort', 'response_model=List[CustomerCohortResponse])\nasync def get_customer_cohort')
content = content.replace('response_model=List[Dict[str, Any]])\nasync def get_sessions_by_landing_page', 'response_model=List[SessionsByLandingPageResponse])\nasync def get_sessions_by_landing_page')

content = content.replace('response_model=Dict[str, Any])\nasync def get_my_user_engagement', 'response_model=UserEngagementResponse)\nasync def get_my_user_engagement')
content = content.replace('response_model=Dict[str, Any])\nasync def get_user_engagement_by_id', 'response_model=UserEngagementResponse)\nasync def get_user_engagement_by_id')

content = content.replace('response_model=List[Dict[str, Any]])\nasync def get_top_users_report', 'response_model=List[TopUsersReportResponse])\nasync def get_top_users_report')

# Catch all remaining Dict[str, Any] and List[Dict[str, Any]]
content = content.replace('response_model=List[Dict[str, Any]]', 'response_model=List[GenericListResponse]')
content = content.replace('response_model=Dict[str, Any]', 'response_model=GenericDictResponse')

with open('backend/app/routers/analytics.py', 'w') as f:
    f.write(content)
