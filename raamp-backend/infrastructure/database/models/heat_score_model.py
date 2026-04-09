# Infrastructure Layer - Heat Score MongoDB Document
from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class HeatScoreModel(Document):
    """MongoDB document for heat_scores collection — stores per-request heat computations"""

    business_id: str = Field(..., description="Reference to the business")
    location: Dict[str, Any] = Field(
        default_factory=dict,
        description="GeoJSON Point: {type: 'Point', coordinates: [lng, lat]}"
    )
    score: int = Field(..., description="Final computed heat score 0–100")
    urgency: str = Field(..., description="Low | Medium | High | Critical")
    zone: str = Field(default="geo_intent", description="Zone label for heatmap grouping")
    signals: Dict[str, float] = Field(
        default_factory=dict,
        description="Normalized signal breakdown: {trends, places, weather}"
    )
    radius: int = Field(default=1000, description="Search radius in meters")
    is_critical: bool = Field(default=False)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "heat_scores"
        indexes = [
            "business_id",
            "timestamp",
            [("location", "2dsphere")],          # Geospatial index
            [("business_id", 1), ("timestamp", -1)],
        ]
