"""
A/B Test Image Analysis MongoDB Model
======================================
Database schema for storing image analysis results.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ImageAnalysisScoreModel(BaseModel):
    """Scoring breakdown for an analyzed image"""
    restaurant_relevance: float
    viral_potential: float
    aesthetic_quality: float
    composite_score: float


class ImageAnalysisModel(BaseModel):
    """MongoDB document for image analysis results"""
    image_id: str
    filename: str
    file_hash: Optional[str] = None
    
    # Classification
    content_type: str  # food, poster, interior, menu, people, other
    
    # Scores
    restaurant_relevance: float
    viral_potential: float
    aesthetic_quality: float
    composite_score: float
    
    # Insights
    why_good: str
    why_bad: str
    recommendation: str
    
    # Metadata
    user_id: str
    image_url: Optional[str] = None
    local_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # A/B Test grouping
    ab_test_batch_id: Optional[str] = None
    
    class Config:
        collection = "ab_test_images"


class ABTestBatchModel(BaseModel):
    """MongoDB document for A/B test batches"""
    batch_id: str
    user_id: str
    image_ids: List[str]  # References to image_id in ImageAnalysisModel
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Recommendations
    recommended_pair: Optional[List[str]] = None  # [image_id_1, image_id_2]
    score_gap: Optional[float] = None
    
    # Test execution
    schedule_id: Optional[str] = None
    result_id: Optional[str] = None
    ad_brief_id: Optional[str] = None
    
    class Config:
        collection = "ab_test_batches"


class ABTestScheduleModel(BaseModel):
    """MongoDB document for scheduled A/B tests"""
    schedule_id: str
    batch_id: str
    user_id: str
    campaign_id: Optional[str] = None
    
    # Variants
    variant_a_image_id: str
    variant_b_image_id: str
    
    # Schedule
    platform: str
    post_time: datetime
    caption: Optional[str] = None
    
    # Status
    status: str = "scheduled"
    test_duration_hours: int = 48
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None
    
    class Config:
        collection = "ab_test_schedules"


class EngagementMetricsModel(BaseModel):
    """Engagement metrics from social platforms"""
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    reach: int = 0
    ctr: float = 0.0
    composite_score: float = 0.0


class ABTestResultModel(BaseModel):
    """MongoDB document for A/B test results"""
    result_id: str
    schedule_id: str
    user_id: str
    
    # Variant A
    variant_a_image_id: str
    variant_a_metrics: EngagementMetricsModel
    
    # Variant B
    variant_b_image_id: str
    variant_b_metrics: EngagementMetricsModel
    
    # Winner
    winner_image_id: str
    delta_percentage: float
    confidence_level: str
    
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    test_duration_actual: Optional[int] = None
    
    class Config:
        collection = "ab_test_results"


class AdBriefModel(BaseModel):
    """MongoDB document for generated ad briefs"""
    brief_id: str
    result_id: str
    user_id: str
    winning_image_id: str
    
    # Targeting
    target_geo: str
    audience_segment: str
    
    # Budget
    suggested_budget_daily: float
    suggested_duration_days: int
    total_spend: float
    
    # Projections
    estimated_reach: str
    estimated_clicks: str
    estimated_ctr: float
    estimated_cost_per_click: str
    
    # Creative
    creative_hook: str
    cta_recommendation: str
    what_not_to_change: str
    
    platform: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        collection = "ab_test_ad_briefs"
