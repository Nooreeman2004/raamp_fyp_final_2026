from typing import Optional, List
from datetime import datetime, timezone
from beanie import Document, Indexed
from pydantic import Field

class ConversionEventModel(Document):
    """
    MongoDB model for a conversion event (sale, lead, etc.)
    Attributed to a specific AI campaign.
    """
    campaign_id: str = Indexed()
    business_id: str = Indexed()
    revenue: float
    latitude: float
    longitude: float
    platform: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "conversion_events"

class CampaignPerformanceModel(Document):
    """
    Cached or persisted performance metrics for a campaign.
    """
    campaign_id: str = Indexed(unique=True)
    name: str
    spend: float = 0.0
    revenue: float = 0.0
    clicks: int = 0
    conversions: int = 0
    roi: float = 0.0
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "campaign_performance"
