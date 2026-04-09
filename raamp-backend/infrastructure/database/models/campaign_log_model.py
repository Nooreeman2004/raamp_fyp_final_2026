# Infrastructure Layer - Campaign Log MongoDB Document
from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class CampaignLogModel(Document):
    """MongoDB document for campaign_logs collection — stores geo-intent campaign runs"""

    business_id: str = Field(..., description="Reference to the business")
    keywords: List[str] = Field(default_factory=list, description="Keywords used in analysis")
    location: Dict[str, Any] = Field(
        default_factory=dict,
        description="GeoJSON Point: {type: 'Point', coordinates: [lng, lat]}"
    )
    radius: int = Field(default=1000, description="Search radius in meters")
    signals: Dict[str, float] = Field(
        default_factory=dict,
        description="Raw signal values: {trends_score, places_score, weather_score}"
    )
    final_score: int = Field(..., description="Final heat score 0–100")
    urgency: str = Field(..., description="Low | Medium | High | Critical")
    is_indoor: bool = Field(default=False, description="Indoor business flag")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "campaign_logs"
        indexes = [
            "business_id",
            "timestamp",
            [("business_id", 1), ("timestamp", -1)],
        ]
