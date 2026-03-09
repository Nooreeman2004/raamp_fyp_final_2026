
# Presentation Layer - Arbitrage Schemas
from pydantic import BaseModel, Field
from typing import List, Optional

class UserProfileSchema(BaseModel):
    """Simplified user profile for context"""
    niche: str
    location: str
    business_type: Optional[str] = "SMB"
    target_audience: Optional[str] = "General"

class TrendSignalInputSchema(BaseModel):
    """Structured trend signal data for Layer 2 input"""
    keyword: str
    velocity_label: str # e.g. "High", "Low" (non-technical)
    saturation_label: str # e.g. "Emerging", "Saturated"
    arbitrage_potential: str # e.g. "Gold Mine", "Low"
    platform_fit: List[str] # Sorted list of best platforms
    hashtags: List[str]

class CampaignRecommendationResponse(BaseModel):
    """Schema for a single campaign recommendation"""
    trend_name: str
    campaign_idea: str
    recommended_platform: str
    reasoning: str
    expected_marketing_goal: str
    suggested_hooks: List[str]
    estimated_effort: str
    priority: int

class ArbitrageRecommendationResponse(BaseModel):
    """Collection of campaign recommendations"""
    recommendations: List[CampaignRecommendationResponse]
    context: str # Brief summary of why these were chosen
