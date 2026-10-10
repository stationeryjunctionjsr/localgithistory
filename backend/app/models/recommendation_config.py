from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
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


class RecommendationConfig(CamelBaseModel):
    engagement_days: int = 30
    engagement_weights: EngagementWeights = Field(default_factory=EngagementWeights)
    strategy_limits: StrategyLimits = Field(default_factory=StrategyLimits)
    total_limit: int = 20
    bandit: BanditConfig = Field(default_factory=BanditConfig)
    customer_favourites_weights: FavouriteWeights = Field(default_factory=FavouriteWeights)
    business_favourites_weights: FavouriteWeights = Field(default_factory=FavouriteWeights)
    segments: Dict[str, SegmentConfig] = Field(default_factory=dict)
    section_wise_weights: Dict[str, EngagementWeights] = Field(default_factory=dict)


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
