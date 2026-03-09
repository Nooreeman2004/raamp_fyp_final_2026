# Infrastructure Layer - Trend Detection MongoDB Model
from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional, Dict, List


class TrendDetectionModel(Document):
    """
    Model for storing detected trend spikes persistently.
    Used for analytics dashboards like Trend Arbitrage.
    """
    user_id: str = Field(..., description="Reference to the user (email)")
    keyword: str = Field(..., description="The trending keyword")
    niche: str = Field(..., description="Business niche")
    location: str = Field(..., description="Geographic location (country code)")
    
    z_score: float = Field(..., description="Statistical significance of the spike")
    current_value: float = Field(..., description="Current interest value (0-100)")
    expected_value: float = Field(..., description="Expected baseline value (EWMA)")
    
    # Analysis fields
    impact_level: str = Field(default="MEDIUM", description="LOW, MEDIUM, or HIGH based on z-score")
    sentiment_score: float = Field(default=0.0, description="Sentiment analysis result (-1 to 1)")
    market_gap: float = Field(default=0.0, description="Calculated market gap/opportunity score")
    
    # Lifecycle & Prediction fields (ENHANCEMENT)
    lifecycle_stage: Optional[str] = Field(None, description="Emerging, Breakout, Mainstream, Saturated, Declining")
    predicted_growth_pct: Optional[float] = Field(None, description="7-day predicted growth percentage")
    breakout_probability: Optional[float] = Field(None, description="Probability of breakout (0-100)")
    profit_score: Optional[float] = Field(None, description="Monetization potential score (0-100)")
    forecast_series: Optional[List[float]] = Field(None, description="7-day forecast values")
    timeframe: Optional[str] = Field("30d", description="Timeframe used for analysis (24h, 7d, 30d, 90d)")
    
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "trend_detections"
        indexes = [
            "user_id",
            "detected_at",
            "keyword",
            ("user_id", "detected_at"),
            ("user_id", "keyword")
        ]
