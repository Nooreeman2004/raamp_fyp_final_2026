"""
Simplified trend response schemas for restaurant owners without marketing expertise.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class SimplifiedTrendResponse(BaseModel):
    """Simplified trend for non-marketing users"""
    id: str
    topic: str = Field(..., description="The trending keyword/topic")
    opportunity_level: str = Field(..., description="high | medium | low")
    why_relevant: str = Field(..., description="Simple explanation in restaurant terms")
    suggested_action: str = Field(..., description="One clear action to take")
    ready_to_use: bool = Field(default=True, description="Always true for simplified view")
    
    # Optional context
    location: Optional[str] = None
    niche: Optional[str] = None
    detected_at: Optional[datetime] = None


class SimplifiedTrendsListResponse(BaseModel):
    """List of simplified trends"""
    trends: List[SimplifiedTrendResponse]
    total: int
    location: str
    last_updated: datetime
