# Domain Layer - Trend Signal Entity
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, List


@dataclass
class TrendSignal:
    """Trend Signal domain entity - represents Google Trends data"""
    id: Optional[str]  # MongoDB ObjectId
    user_email: str  # User who requested the trend data
    
    # User input parameters
    niche: str  # e.g., "fashion", "food", "tech", "crypto"
    category: str  # Sub-niche or category
    location: str  # City, country, or region
    radius: Optional[str] = None  # Optional radius for geo-specific searches
    
    # Google Trends data
    keywords: List[str] = None  # Keywords fetched based on niche/category
    search_interest: Dict = None  # Time-series search interest data
    geo_data: Dict = None  # Geographic distribution of interest
    related_queries: Dict = None  # Related queries from Google Trends
    rising_queries: Dict = None  # Rising queries from Google Trends

    # Provider metadata (observability)
    provider: Optional[str] = None
    fallback_from: Optional[str] = None
    geo_relaxed: bool = False
    
    # Computed metrics
    arbitrage_score: Optional[float] = None
    saturation_score: Optional[float] = None
    social_score: Optional[float] = None
    hashtags: List[str] = None
    platform_bias: Dict[str, float] = None
    is_real_social: bool = False
    is_real_saturation: bool = False
    
    # Lifecycle & Prediction fields (ENHANCEMENT)
    lifecycle_stage: Optional[str] = None
    predicted_growth_pct: Optional[float] = None
    breakout_probability: Optional[float] = None
    profit_score: Optional[float] = None
    forecast_series: Optional[List[float]] = None
    timeframe: Optional[str] = "30d"
    
    # Metadata
    fetch_status: str = "pending"  # pending, processing, completed, failed
    progress_step: str = "Initializing..."  # Current step in the detection pipeline
    error_message: Optional[str] = None
    fetched_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.keywords is None:
            self.keywords = []
        if self.search_interest is None:
            self.search_interest = {}
        if self.geo_data is None:
            self.geo_data = {}
        if self.related_queries is None:
            self.related_queries = {}
        if self.rising_queries is None:
            self.rising_queries = {}
        if self.hashtags is None:
            self.hashtags = []
        if self.platform_bias is None:
            self.platform_bias = {}
