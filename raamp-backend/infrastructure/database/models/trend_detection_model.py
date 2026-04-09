# Infrastructure Layer - Trend Detection MongoDB Model
from beanie import Document
from pydantic import Field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum


class TrendDetectionStatus(str, Enum):
    """
    Lifecycle status for a detected spike.
    NOTE: This is separate from CampaignLaunchRequest status; it is a lightweight
    state machine for what happened to this detected opportunity.
    """

    NEW = "new"
    NOTIFIED = "notified"
    APPROVED = "approved"
    REJECTED = "rejected"
    CAMPAIGN_LAUNCHED = "campaign_launched"
    EXPIRED = "expired"


class TrendDetectionModel(Document):
    """
    Model for storing detected trend spikes persistently.
    Used for analytics dashboards like Trend Arbitrage.
    """
    user_id: str = Field(..., description="Reference to the user (email)")
    keyword: str = Field(..., description="The trending keyword")
    niche: str = Field(..., description="Business niche")
    location: str = Field(..., description="Geographic location (country code)")
    trend_signal_id: Optional[str] = Field(None, description="Parent TrendSignal id for this detection (if known)")
    
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
    is_recent: bool = Field(default=False, description="True if spike occurred in the last 3 points of the series")

    # Provenance / data quality flags copied from parent TrendSignal
    is_real_social: bool = Field(default=False, description="Whether real Instagram/social metrics were used in the parent scan")
    is_real_saturation: bool = Field(default=False, description="Whether real saturation sources were used in the parent scan")
    is_real_events: bool = Field(default=False, description="Whether real event sources were used in the parent scan")

    # Opportunity lifecycle
    status: TrendDetectionStatus = Field(default=TrendDetectionStatus.NEW, description="Lifecycle status for this detection")
    expires_at: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(hours=72),
        description="When this detection expires (used to keep dashboards clean)",
    )
    niche_match_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="0..1 confidence that this spike matches the user's niche/specialties",
    )

    # AI recommendations payload (kept flexible; does NOT change downstream required fields)
    recommendations: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Actionable recommendations JSON for rendering in trend cards",
    )
    
    # Enrichment fields (for displaying sub-trends)
    rising_queries: Optional[List[str]] = Field(
        default=None,
        description="Top 5 specific sub-queries found during discovery scavenging"
    )
    
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "trend_detections"
        indexes = [
            "user_id",
            "detected_at",
            "expires_at",
            "status",
            "keyword",
            ("user_id", "detected_at"),
            ("user_id", "keyword"),
            ("user_id", "status"),
            ("user_id", "expires_at"),
            ("user_id", "trend_signal_id"),
        ]
