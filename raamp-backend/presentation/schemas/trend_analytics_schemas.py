from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class DataQuality(BaseModel):
    """
    Standard data quality / provenance metadata included on all analytics responses.
    """

    is_real: bool = Field(..., description="True if derived from real persisted data (not guessed/synthetic)")
    source: str = Field(..., description="Short identifier describing the provenance/source path")
    notes: Optional[str] = Field(default=None, description="Human-readable notes for debugging/UI empty states")
    flags: Dict[str, Any] = Field(default_factory=dict, description="Optional structured flags (is_real_social, etc.)")


class LiveTrendItem(BaseModel):
    id: str
    keyword: str
    niche: str
    location: str
    score: Optional[float] = None
    z_score_spike: Optional[float] = None
    impact: Optional[str] = None
    detected_at: Any
    current_value: Optional[float] = None
    is_spike: bool = True
    sentiment: Optional[str] = None
    arbitrage_score: Optional[float] = None
    profitability: Optional[float] = None
    confidence: Optional[float] = None
    time_diff: Optional[str] = None
    social_score: Optional[float] = None
    saturation_score: Optional[float] = None
    is_real_social: bool = False
    is_real_saturation: bool = False
    is_real_events: bool = False
    lifecycle_stage: Optional[str] = None
    predicted_growth_pct: Optional[float] = None
    breakout_probability: Optional[float] = None
    profit_score: Optional[float] = None
    timeframe: Optional[str] = None
    trend_signal_id: Optional[str] = None
    fetch_status: Optional[str] = None
    error_message: Optional[str] = None
    recommendations: Optional[Dict[str, Any]] = None


class LiveTrendsResponse(BaseModel):
    trends: List[LiveTrendItem] = Field(default_factory=list)
    count: int = 0
    data_quality: DataQuality


class HeatmapRegionItem(BaseModel):
    keyword: str
    city: str
    intensity: float
    x: float
    y: float
    delta: Optional[str] = None
    velocity: Optional[str] = None


class HeatmapResponse(BaseModel):
    regions: List[HeatmapRegionItem] = Field(default_factory=list)
    count: int = 0
    is_real_geo: bool = False
    data_quality: DataQuality


class SpikeTimelineItem(BaseModel):
    date: str
    count: int
    avg_z: float


class SpikeTimelineResponse(BaseModel):
    timeline: List[SpikeTimelineItem] = Field(default_factory=list)
    count: int = 0
    last_successful_scan_at: Optional[str] = None
    data_quality: DataQuality


class BubbleChartItem(BaseModel):
    keyword: str
    velocity: float
    saturation: float
    arbitrage_score: float
    quadrant: str
    impact: str
    lifecycle_stage: str
    breakout_probability: float
    profit_score: float
    timeframe: str
    is_real_social: bool = False
    is_real_saturation: bool = False
    is_real_events: bool = False


class BubbleChartResponse(BaseModel):
    opportunities: List[BubbleChartItem] = Field(default_factory=list)
    count: int = 0
    data_quality: DataQuality


class PlatformReachResponse(BaseModel):
    google: int = 0
    instagram: int = 0
    facebook: int = 0
    total_reach: str = "0%"
    is_real: bool = False
    source: Optional[str] = None
    trend_signal_id: Optional[str] = None
    data_quality: DataQuality


class TrendingNowRelevantItem(BaseModel):
    term: str
    score: float = 0.0
    matched_terms: List[str] = Field(default_factory=list, description="Matched specialty/niche tokens")


class TrendingNowResponse(BaseModel):
    """
    Regional trending-now feed + a business-relevant shortlist.

    - `terms`: raw trending terms for the requested geo
    - `relevant`: subset ranked by relevance to the user's business niche/specialties
    """

    geo: Optional[str] = None
    terms: List[str] = Field(default_factory=list)
    relevant: List[TrendingNowRelevantItem] = Field(default_factory=list)
    count: int = 0
    data_quality: DataQuality


class IndustryTrendsResponse(BaseModel):
    """
    "Industry trends" from Google Trends related/rising queries.

    This is intentionally NOT the same as SerpAPI Trending Now (regional newsy feed).
    It is derived from related/rising queries for niche/specialty seed keywords.
    """

    scope: str = Field(default="GLOBAL", description="GLOBAL or a geo code like PK")
    niche: str
    seed_keywords: List[str] = Field(default_factory=list)
    terms: List[str] = Field(default_factory=list)
    count: int = 0
    data_quality: DataQuality

