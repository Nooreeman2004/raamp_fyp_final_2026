from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from domain.entities.performance import (
    PerformanceMetrics,
    ConversionEvent,
    CampaignHealth,
    DashboardAnalyticsSummary
)

class PerformanceSummaryResponse(BaseModel):
    """API response model for the dashboard analytics summary."""
    metrics: PerformanceMetrics
    recent_pings: List[Any] # Simplified for now, can be more specific
    campaign_health: List[CampaignHealth]
    last_updated: datetime

class ConversionEventCreate(BaseModel):
    """Request model for manual/system conversion event tracking (for demo purposes)."""
    campaign_id: str
    business_id: str
    revenue: float
    latitude: float
    longitude: float
    platform: str
