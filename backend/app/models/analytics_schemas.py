from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime
from app.models.base import CamelBaseModel


class UserOrderStatsResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    userId: str
    name: str
    email: str
    totalOrders: int
    averageOrderValue: float
    daysSinceLastOrder: Optional[int] = None
    avgOrdersPerMonth: float


class ItemsByUserTypeResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    role: str
    views: int
    searches: int


class ReturnsReportResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    returnId: str
    orderId: int
    createdAt: datetime
    status: str
    refundValue: float
    userName: str
    userEmail: str
    itemCount: int
    paymentMethod: Optional[str] = None
    orderTotal: Optional[float] = None


class PaymentMethodsReportResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    paymentMethod: str
    orderCount: int
    revenue: float
    avgOrderValue: float


class RevenueByCategoryResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    category: str
    orderCount: int
    quantity: int
    revenue: float


class InventoryAlertResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    productId: int
    name: str
    sku: Optional[str] = None
    category: str
    stock: int
    status: str


class FulfillmentTimeReportResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    orderId: int
    orderNumber: str
    createdAt: datetime
    status: str
    orderTotal: float
    userName: str
    fulfillmentHours: Optional[float] = None
    fulfillmentDays: Optional[float] = None


class CouponUsageReportResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    couponCode: str
    discountType: str
    discountValue: float
    usageCount: int
    totalDiscountGiven: float
    totalRevenue: float


class SalesByLocationReportResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    location: str
    orderCount: int
    quantity: int
    revenue: float


class NewVsReturningCustomerSalesResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    customerType: str
    orderCount: int
    revenue: float


class ItemsBoughtTogetherResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    productAId: str
    productAName: str
    productBId: str
    productBName: str
    frequency: int


class SalesByDeviceReportResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    deviceType: str
    orderCount: int
    revenue: float


class TopReturnedProductsResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    productId: str
    productName: str
    category: str
    returnCount: int
    quantityReturned: int
    revenueLost: float


class InventoryValueByCategoryResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    category: str
    productCount: int
    totalStock: int
    inventoryValue: float


class SessionsOverTimeResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    period: str
    sessions: int
    visitors: int
    uniqueVisitors: int


class VisitorsNowResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    windowMinutes: int
    activeVisitors: int
    loggedInSessions: int
    guestSessions: int


class SearchesNoClicksResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    term: str
    searchCount: int
    totalResults: int
    avgResults: float


class SearchConversionResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    totalSearchSessions: int
    convertedSessions: int
    nonConvertedSessions: int
    conversionRate: float


class BounceRateResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    period: str
    totalSessions: int
    bouncedSessions: int
    bounceRate: float


class RFMSegmentsResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    userId: str
    name: str
    email: str
    segment: str
    orderCount: int
    totalSpend: float
    recencyDays: Optional[int] = None
    lastOrder: Optional[str] = None


class CustomerFrequencyResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    type: str
    customers: int
    customerPct: float
    orders: int
    avgOrders: float
    revenue: float


class NetSalesResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    orderId: str
    orderNumber: str
    createdAt: str
    customerName: str
    status: str
    grossSales: float
    discount: float
    tax: float
    shipping: float
    netSales: float


class SalesHeatmapResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    dayOfWeek: str
    hour: int
    orderCount: int
    revenue: float


class InventoryRunwayResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    productId: str
    name: str
    category: str
    currentStock: int
    unitsSold30d: int
    avgDailySales: float
    daysRemaining: Optional[float] = None


class DiscountsAuditResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    orderId: str
    orderNumber: str
    createdAt: str
    customerName: str
    grossSales: float
    discountApplied: float
    discountPct: float
    couponCode: Optional[str] = None
    discountType: Optional[str] = None
    discountValue: Optional[float] = None
    netAfterDiscount: float


class ProductsPctSoldResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    productId: str
    name: str
    sku: Optional[str] = None
    category: str
    openingStock: int
    currentStock: int
    unitsSold: int
    pctSold: float


class MonthlyRevenueItem(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    month: str
    revenue: float
    orders: Optional[int] = None


class BundlePerformanceReportResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    bundleId: Optional[str] = None
    name: Optional[str] = None
    status: Optional[str] = None
    isActive: Optional[bool] = None
    price: Optional[float] = None
    orderCount: Optional[int] = None
    revenue: Optional[float] = None
    copiesSold: Optional[int] = None
    monthlyRevenue: Optional[List[MonthlyRevenueItem]] = None


class SalesByChannelDetailedResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    channel: str
    channelLabel: str
    orderCount: int
    revenue: float
    revenuePct: float
    aov: float


class AllReportsSummaryResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    searched_products: int
    viewed_products: int
    drop_off_points: int
    cart_abandonments: int
    returning_users: int
    items_by_user_type: int
    highest_selling_products: int
    top_business_customers: int
    top_retail_customers: int
    user_engagement: int
    returns: int
    payment_methods: int
    revenue_by_category: int
    inventory_alerts: int
    fulfillment_time: int
    coupon_usage: int
    sales_by_location: int
    new_vs_returning: int
    items_bought_together: int
    zero_result_searches: int
    sales_by_device: int
    products_sell_through: int
    aov_over_time: int
    top_returned_products: int
    inventory_value: int
    most_abandoned_products: int


class SalesOverTimeResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    period: str
    sales: float
    orderCount: int
    aov: float


class SalesBreakdownResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    gross_sales: float
    discounts: float
    returns: float
    net_sales: float
    shipping_charges: float
    return_fees: float
    taxes: float
    total_sales: float


class AverageOrderValueResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    period: str
    average_order_value: float


class SalesByChannelResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    channel: str
    sales: float


class SalesByProductResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    product_id: int
    name: str
    quantity: int
    revenue: float



class TopUsersReportResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    userId: str
    name: str
    userName: str
    email: str
    userEmail: str
    role: str
    revenue: float
    orderCount: int = Field(default=0)


class ProductsSellThroughResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    product_id: str
    name: str
    sold: int
    stock: int
    sell_through_rate: float


class CustomerCohortResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    cohort: str
    months: List[int]


class ConversionOrderStats(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    total_orders: int = 0
    non_cancelled_orders: int = 0
    completed_sessions: int = 0


class FunnelStage(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    count: int
    percentage: float
    drop_percentage: float


class FunnelStageNoDrop(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    count: int
    percentage: float


class ConversionRateResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    sessions: FunnelStageNoDrop
    added_to_cart: FunnelStage
    reached_checkout: FunnelStage
    completed: FunnelStage
    overall_conversion_rate: float


class CheckoutFunnelResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    cart: FunnelStageNoDrop
    shipping: FunnelStage
    review: FunnelStage
    payment: FunnelStage
    completed: FunnelStage
    overall_checkout_conversion: float


class SessionsByDeviceResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    device: str
    sessions: int


class SessionsByLocationResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    location: str
    sessions: int


class SessionsByLandingPageResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    landing_page: str
    sessions: int


class DurationBucket(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    range: str
    count: int


class UserMetric(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    userId: str
    name: str
    email: str
    averageSessionTimeSeconds: float
    totalSessions: int


class AllUserEngagementResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    duration_buckets: List[DurationBucket]
    user_metrics: List[UserMetric]


class UserEngagementResponse(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    userId: Optional[str] = None
    registrationDate: Optional[str] = None
    totalSessions: Optional[int] = None
    averageSessionTimeSeconds: Optional[float] = None
    averageDaysBetweenSessions: Optional[float] = None
    averagePagesPerSession: Optional[float] = None
    sessionsWithOrder: Optional[int] = None
    sessionOrderRate: Optional[float] = None
    error: Optional[str] = None
