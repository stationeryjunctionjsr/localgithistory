from pydantic import BaseModel, Field
from typing import Dict, Optional

class EngagementWeights(BaseModel):
    product_view: float = 1.0
    add_to_cart: float = 3.0

class StrategyLimits(BaseModel):
    trending: int = 10
    user_favorites: int = 5
    explore: int = 5

class BanditConfig(BaseModel):
    epsilon: float = 0.2
    personal_threshold: int = 10

class FavouriteWeights(BaseModel):
    frequency: float = 0.7
    quantity: float = 0.3

class SegmentConfig(BaseModel):
    trending_now_days: int = 14
    customer_favourites_days: int = 60
    explore_days: Optional[int] = None
    exclude_user_purchases_days: Optional[int] = None
    wholesaler_favourites_days: Optional[int] = None
    business_favourites_days: Optional[int] = None
    explore_available: bool = False

class RecommendationConfig(BaseModel):
    engagement_days: int = 30
    engagement_weights: EngagementWeights = Field(default_factory=EngagementWeights)
    strategy_limits: StrategyLimits = Field(default_factory=StrategyLimits)
    total_limit: int = 20
    bandit: BanditConfig = Field(default_factory=BanditConfig)
    customer_favourites_weights: FavouriteWeights = Field(default_factory=FavouriteWeights)
    business_favourites_weights: FavouriteWeights = Field(default_factory=FavouriteWeights)
    segments: Dict[str, SegmentConfig] = Field(default_factory=dict)
    section_wise_weights: Dict[str, EngagementWeights] = Field(default_factory=dict)
