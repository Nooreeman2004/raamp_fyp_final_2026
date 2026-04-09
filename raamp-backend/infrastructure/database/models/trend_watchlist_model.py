
# Infrastructure Layer - Trend Watchlist MongoDB Document
from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional

class TrendWatchlistModel(Document):
    """MongoDB document for user's trend watchlist"""
    user_email: str = Field(..., description="Email of the user who owns this watchlist item")
    keyword: str = Field(..., description="The trend keyword being tracked")
    niche: str = Field(..., description="Business niche for context")
    location: str = Field(..., description="Geographic location being tracked")
    
    # Snapshot of scores when added or last updated
    last_velocity: float = Field(default=0.0)
    last_saturation: float = Field(default=0.0)
    last_arbitrage_score: float = Field(default=0.0)
    last_profit_score: float = Field(default=0.0)
    
    # Alert settings
    alert_on_spike: bool = Field(default=True, description="Whether to notify on velocity spikes")
    velocity_threshold: float = Field(default=5.0, description="σ threshold to trigger an alert")

    alert_on_profit_score: bool = Field(default=True, description="Notify when profit/opportunity score crosses threshold")
    profit_score_threshold: float = Field(default=75.0, description="Profit score threshold (0-100) to trigger alert")

    alert_on_saturation_drop: bool = Field(default=False, description="Notify when saturation drops meaningfully (less competition)")
    saturation_drop_threshold: float = Field(default=10.0, description="Drop amount (points) vs last_saturation to trigger alert")
    
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "trend_watchlist"
        indexes = [
            "user_email",
            [("user_email", 1), ("keyword", 1)],  # Unique-ish per user
            "keyword"
        ]
