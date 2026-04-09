# Domain Entities for Performance & Attribution
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

class CampaignStatusLevel(str, Enum):
    GREEN = "green"    # ROI >= Threshold High
    YELLOW = "yellow"  # ROI >= Threshold Low
    RED = "red"        # ROI < Threshold Low

class PerformanceMetrics(BaseModel):
    revenue: float = 0.0
    leads: int = 0
    cpc: float = 0.0
    ctr: float = 0.0
    roi: float = 0.0
    active_campaigns: int = 0

class ConversionEvent(BaseModel):
    id: Optional[str] = None
    campaign_id: str
    business_id: str
    revenue: float
    latitude: float
    longitude: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    platform: str # e.g., "instagram", "facebook"

class CampaignHealth(BaseModel):
    campaign_id: str
    name: str
    roi: float
    status: CampaignStatusLevel
    spend: float
    revenue: float
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DashboardAnalyticsSummary(BaseModel):
    metrics: PerformanceMetrics
    recent_pings: List[ConversionEvent] = []
    campaign_health: List[CampaignHealth] = []
