# Infrastructure Layer - Trend Signal MongoDB Document
from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional, Dict, List, Any


class TrendSignalModel(Document):
    """MongoDB document for trend_signals collection"""
    user_email: str = Field(..., description="Email of the user who requested the trend data")
    
    # User input parameters
    niche: str = Field(..., description="Business niche (fashion, food, tech, crypto, etc.)")
    category: str = Field(..., description="Sub-category or specific area within the niche")
    location: str = Field(..., description="Geographic location (city, country, region)")
    radius: Optional[str] = Field(None, description="Optional radius for geo-specific searches")
    
    # Google Trends data
    keywords: List[str] = Field(default_factory=list, description="Keywords fetched based on niche/category")
    search_interest: Dict = Field(default_factory=dict, description="Time-series search interest data")
    geo_data: Dict = Field(default_factory=dict, description="Geographic distribution of interest")
    related_queries: Dict = Field(default_factory=dict, description="Related queries from Google Trends")
    rising_queries: Dict = Field(default_factory=dict, description="Rising queries from Google Trends")
    
    # Provider metadata (observability)
    provider: Optional[str] = Field(None, description="Provider used to fetch time-series data (serpapi|pytrends)")
    fallback_from: Optional[str] = Field(None, description="If provider fallback occurred, indicates the initial provider")
    geo_relaxed: bool = Field(default=False, description="Whether geo was relaxed to global due to provider recovery")
    
    # Computed metrics
    arbitrage_score: Optional[float] = Field(None, description="Computed arbitrage score (Velocity / Saturation)")
    saturation_score: Optional[float] = Field(None, description="Computed market saturation score (0-100)")
    social_score: Optional[float] = Field(None, description="Computed social trend score (0-100)")
    hashtags: List[str] = Field(default_factory=list, description="Derived hashtags from related queries")
    platform_bias: Dict[str, float] = Field(default_factory=dict, description="Platform affinity scores (google, instagram, facebook)")
    is_real_social: bool = Field(default=False, description="Whether real social metrics were used")
    is_real_saturation: bool = Field(default=False, description="Whether real saturation scraping was used")

    # Event signals (future: EventSignalService) — kept here for forward compatibility
    event_score: Optional[float] = Field(None, description="Local events catalyst score (0-100)")
    event_items: List[Dict[str, Any]] = Field(default_factory=list, description="Top event items contributing to event_score")
    is_real_events: bool = Field(default=False, description="Whether real event sources were used")
    
    # Lifecycle & Prediction fields (ENHANCEMENT)
    lifecycle_stage: Optional[str] = Field(None, description="Emerging, Breakout, Mainstream, Saturated, Declining")
    predicted_growth_pct: Optional[float] = Field(None, description="7-day predicted growth percentage")
    breakout_probability: Optional[float] = Field(None, description="Probability of breakout (0-100)")
    profit_score: Optional[float] = Field(None, description="Monetization potential score (0-100)")
    forecast_series: Optional[List[float]] = Field(None, description="7-day forecast values")
    timeframe: Optional[str] = Field("30d", description="Timeframe used for analysis (24h, 7d, 30d, 90d)")
    
    # Metadata
    fetch_status: str = Field(default="pending", description="Status: pending, processing, completed, failed")
    progress_step: str = Field(default="Starting...", description="Current step in the detection pipeline")
    error_message: Optional[str] = Field(None, description="Error message if fetch failed")
    fetched_at: Optional[datetime] = Field(None, description="Timestamp when data was successfully fetched")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    class Settings:
        name = "trend_signals"  # Collection name
        indexes = [
            "user_email",  # Index for user-specific queries
            "niche",  # Index for niche-based queries
            "location",  # Index for location-based queries
            "created_at",  # Index for time-based queries
            [("user_email", 1), ("created_at", -1)],  # Compound index for user's latest trends
        ]
