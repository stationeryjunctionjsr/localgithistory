from datetime import datetime
from typing import Any, List, Optional, Tuple
from pydantic import Field
from app.models.base import CamelBaseModel


class EngagementWeights(CamelBaseModel):
    product_view: float = 1.0
    add_to_cart: float = 3.0


class StrategyLimits(CamelBaseModel):
    trending: int = 10
    user_favorites: int = 5
    explore: int = 5


class BanditConfig(CamelBaseModel):
    epsilon: float = 0.2
    personal_threshold: int = 10


class FavouriteWeights(CamelBaseModel):
    frequency: float = 0.7
    quantity: float = 0.3


class SegmentConfig(CamelBaseModel):
    trending_now_days: int = 14
    customer_favourites_days: int = 60
    explore_days: Optional[int] = None
    exclude_user_purchases_days: Optional[int] = None
    wholesaler_favourites_days: Optional[int] = None
    business_favourites_days: Optional[int] = None
    explore_available: bool = False


class SegmentsConfig(CamelBaseModel):
    guest: SegmentConfig = Field(default_factory=SegmentConfig)
    retail: SegmentConfig = Field(default_factory=SegmentConfig)
    wholesaler: SegmentConfig = Field(default_factory=SegmentConfig)

    def for_segment(self, segment: str) -> SegmentConfig:
        if segment == "guest":
            return self.guest
        if segment == "retail":
            return self.retail
        if segment == "wholesaler":
            return self.wholesaler
        return SegmentConfig()


class SectionWiseWeights(CamelBaseModel):
    customer_favourites: EngagementWeights = Field(default_factory=EngagementWeights)
    trending_now: EngagementWeights = Field(default_factory=EngagementWeights)
    explore: EngagementWeights = Field(default_factory=EngagementWeights)
    wholesaler_customer_favourites: EngagementWeights = Field(default_factory=EngagementWeights)
    wholesaler_trending_now: EngagementWeights = Field(default_factory=EngagementWeights)
    wholesaler_explore: EngagementWeights = Field(default_factory=EngagementWeights)
    wholesaler_favourites: EngagementWeights = Field(default_factory=EngagementWeights)
    quick_picks: EngagementWeights = Field(default_factory=EngagementWeights)
    business_favourites: EngagementWeights = Field(default_factory=EngagementWeights)

    def for_slot(self, slot: str, default: EngagementWeights) -> EngagementWeights:
        if slot == "customer_favourites":
            return self.customer_favourites
        if slot == "trending_now":
            return self.trending_now
        if slot == "explore":
            return self.explore
        if slot == "wholesaler_customer_favourites":
            return self.wholesaler_customer_favourites
        if slot == "wholesaler_trending_now":
            return self.wholesaler_trending_now
        if slot == "wholesaler_explore":
            return self.wholesaler_explore
        if slot == "wholesaler_favourites":
            return self.wholesaler_favourites
        if slot == "quick_picks":
            return self.quick_picks
        if slot == "business_favourites":
            return self.business_favourites
        return default


class RecommendationConfig(CamelBaseModel):
    engagement_days: int = 30
    engagement_weights: EngagementWeights = Field(default_factory=EngagementWeights)
    strategy_limits: StrategyLimits = Field(default_factory=StrategyLimits)
    total_limit: int = 20
    bandit: BanditConfig = Field(default_factory=BanditConfig)
    customer_favourites_weights: FavouriteWeights = Field(default_factory=FavouriteWeights)
    business_favourites_weights: FavouriteWeights = Field(default_factory=FavouriteWeights)
    segments: SegmentsConfig = Field(default_factory=SegmentsConfig)
    section_wise_weights: SectionWiseWeights = Field(default_factory=SectionWiseWeights)


class FavouritesCacheResult(CamelBaseModel):
    product_ids: List[str] = Field(default_factory=list)
    updated_at: str


class FavouritesRankedResult(CamelBaseModel):
    ranked_ids: List[Tuple[str, float]] = Field(default_factory=list)
    states: List[str] = Field(default_factory=list)
    cities: List[str] = Field(default_factory=list)


class BundleRecommendationItem(CamelBaseModel):
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    mrp: float = 0.0
    price: float = 0.0
    display_image: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    sales_count: int = 0
    created_at: Optional[datetime] = None
    is_active: bool = True
    is_bundle: bool = True
    sellers: List[Any] = Field(default_factory=list)
