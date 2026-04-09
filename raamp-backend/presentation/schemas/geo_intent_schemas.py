# Presentation Layer - Geo-Intent Marketing Engine Schemas
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------

class HeatScoreRequest(BaseModel):
    """Request payload for computing a geo-intent heat score"""

    business_id: str = Field(..., description="Unique identifier for the business")
    keywords: List[str] = Field(
        ...,
        min_length=1,
        description="Keywords that describe the business or campaign"
    )
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Location latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Location longitude")
    radius: int = Field(
        default=1000,
        ge=500,
        le=50000,
        description="Search radius in meters (500–50000)"
    )
    is_indoor: bool = Field(
        default=False,
        description="True if business is indoors (affects weather signal weighting)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "business_id": "biz_01HZXYZ",
                "keywords": ["coffee", "cafe", "espresso"],
                "latitude": 33.7215,
                "longitude": 73.0433,
                "radius": 1000,
                "is_indoor": True,
            }
        }
    }

    @field_validator("keywords")
    @classmethod
    def keywords_not_empty(cls, v: List[str]) -> List[str]:
        stripped = [k.strip() for k in v if k.strip()]
        if not stripped:
            raise ValueError("keywords must contain at least one non-empty string")
        return stripped[:5]   # cap at 5 keywords


# ---------------------------------------------------------------------------
# Signal / Score Schemas
# ---------------------------------------------------------------------------

class SignalBreakdown(BaseModel):
    """Normalised signal values (0.0 – 1.0)"""
    trends_score: float = Field(..., ge=0.0, le=1.0)
    places_score: float = Field(..., ge=0.0, le=1.0)
    weather_score: float = Field(..., ge=0.0, le=1.0)

    model_config = {"from_attributes": True}


class HeatScoreResponse(BaseModel):
    """Response for POST /heat-score"""
    score: int = Field(..., ge=0, le=100, description="Final heat score 0–100")
    urgency: str = Field(..., description="Low | Medium | High | Critical")
    is_critical: bool = Field(..., description="True when score >= 90")
    signals: SignalBreakdown
    signals_status: Dict[str, str] = Field(..., description="Status of each signal ('ok' or 'failed')")
    reasoning: Optional[str] = Field(None, description="Actionable insight explaining the score")
    persona_split: List[Dict[str, Any]] = Field(default_factory=list)
    radar_feed: List[Dict[str, Any]] = Field(default_factory=list)
    latitude: Optional[float] = Field(None, description="Location latitude")
    longitude: Optional[float] = Field(None, description="Location longitude")
    radius_km: Optional[float] = Field(None, description="Search radius in KM")
    timestamp: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "score": 74,
                "urgency": "High",
                "is_critical": False,
                "signals": {
                    "trends_score": 0.68,
                    "places_score": 0.82,
                    "weather_score": 0.61,
                },
                "signals_status": {
                    "trends": "ok",
                    "places": "ok",
                    "weather": "ok",
                },
                "timestamp": "2026-03-29T14:00:00Z",
            }
        },
    }


# ---------------------------------------------------------------------------
# Heatmap / GeoJSON Schemas
# ---------------------------------------------------------------------------

class GeoJSONGeometry(BaseModel):
    type: str = "Point"
    coordinates: List[float]   # [longitude, latitude]

    model_config = {"from_attributes": True}


class GeoJSONProperties(BaseModel):
    score: int
    urgency: str
    zone: str
    timestamp: str

    model_config = {"from_attributes": True}


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: GeoJSONGeometry
    properties: GeoJSONProperties

    model_config = {"from_attributes": True}


class HeatmapResponse(BaseModel):
    """GeoJSON FeatureCollection for heatmap visualisation"""
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# History / Campaign Log Schemas
# ---------------------------------------------------------------------------

class CampaignLogEntry(BaseModel):
    """Single campaign log entry"""
    business_id: str
    keywords: List[str]
    radius: int
    final_score: int
    urgency: str
    is_indoor: bool
    signals: Dict[str, float]
    timestamp: datetime

    model_config = {"from_attributes": True}


class CampaignHistoryResponse(BaseModel):
    """Response for GET /history/{business_id}"""
    business_id: str
    total: int
    logs: List[CampaignLogEntry]

    model_config = {"from_attributes": True}
