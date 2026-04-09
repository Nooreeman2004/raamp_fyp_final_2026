# Infrastructure Layer - Geo-Intent Campaign Brief MongoDB Document
from beanie import Document, Indexed
from pydantic import Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class CampaignBriefModel(Document):
    """
    MongoDB document for campaign_briefs collection.
    Stores the full AI-generated strategic blueprint for a geo-intent run.
    """

    user_email: str = Indexed()
    business_id: str = Indexed()
    
    # 1. Spatial Context
    location: Dict[str, Any] = Field(
        description="GeoJSON Point: {type: 'Point', coordinates: [lng, lat]}"
    )
    radius_km: float
    coordinates_display: str  # e.g. "33.7215° N, 73.0433° E"
    
    # 2. Market Intelligence Snapshot
    heat_score: float
    urgency: str
    trends_score: float
    weather_score: float
    places_score: float
    persona_split: List[Dict[str, Any]]
    
    # 3. AI Creative Strategy
    strategy_rationale: str
    captions: Dict[str, str] = Field(
        default_factory=dict,
        description="Variants: aggressive, soft, urgency, etc."
    )
    hashtags: List[str] = Field(default_factory=list)
    
    # 4. Ad Execution Parameters
    best_time_window: str
    suggested_budget: Dict[str, int]  # {"min": 300, "max": 1500}
    meta_objective: str
    meta_deep_link: str
    
    # 5. Metadata & Versioning
    ai_model: str = "gemini-1.5-flash"
    strategy_version: str = "v1"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "campaign_briefs"
        indexes = [
            "user_email",
            "business_id",
            "timestamp",
            [("business_id", 1), ("timestamp", -1)],
            [("location", "2dsphere")],
        ]
