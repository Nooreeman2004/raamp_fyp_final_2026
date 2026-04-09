from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime

class KPIMetric(BaseModel):
    label: str
    value: float
    prefix: Optional[str] = None
    suffix: Optional[str] = None
    change: str
    trend: str 
    icon_type: str 

class ConversionEvent(BaseModel):
    id: str
    campaign_id: str
    business_id: str
    revenue: float
    latitude: float
    longitude: float
    platform: str
    timestamp: datetime

class CampaignHealth(BaseModel):
    campaign_id: str
    name: str
    roi: float
    status: str
    spend: float
    revenue: float
    last_updated: datetime

class StrategicInsight(BaseModel):
    id: str
    type: str  
    title: str
    message: str
    impact: str 
    color: str 

class HeatmapRegion(BaseModel):
    id: str
    name: str # e.g., "Clifton Block 4"
    score: int # 0-100
    urgency: str # Low, Medium, High, Critical
    trend: str # "Rising", "Stable", "Dropping"

class ScheduledPostItem(BaseModel):
    id: str
    platform: str # "Instagram", "Facebook"
    media_url: str
    caption: Optional[str]
    time: datetime # scheduled time
    status: str # "scheduled", "pending"

class CreativeVelocityPoint(BaseModel):
    type: str # "AI Generated" or "User Upload"
    value: int # Count

class PostingCadenceDay(BaseModel):
    day: str # "Mon", "Tue"...
    posts: int # total posts on that day

class DashboardSummaryResponse(BaseModel):
    kpis: List[KPIMetric]
    recent_pings: List[ConversionEvent]
    campaign_health: List[CampaignHealth]
    strategic_insights: List[StrategicInsight]
    
    # NEW COMPONENTS
    top_regions: List[HeatmapRegion]
    deployment_timeline: List[ScheduledPostItem]
    posting_cadence: List[PostingCadenceDay]
    
    last_updated: datetime = datetime.now()

class ConversionLogRequest(BaseModel):
    campaign_id: str
    business_id: str
    revenue: float
    latitude: float
    longitude: float
    platform: str
