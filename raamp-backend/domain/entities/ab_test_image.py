"""
A/B Test Image Domain Entity
=============================
Represents analyzed images for A/B testing optimization.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from domain.utils.scoring_logic import get_relevance_level, RelevanceLevel


class ContentType(str, Enum):
    """Types of restaurant content for classification"""
    FOOD = "food"
    POSTER = "poster"
    INTERIOR = "interior"
    MENU = "menu"
    PEOPLE = "people"
    OTHER = "other"


class ImageAnalysisScore(BaseModel):
    """Detailed scoring breakdown for a single image"""
    restaurant_relevance: float = Field(ge=0, le=10, description="How relevant to restaurant marketing (0-10)")
    viral_potential: float = Field(ge=0, le=10, description="Estimated viral/engagement potential (0-10)")
    aesthetic_quality: float = Field(ge=0, le=10, description="Visual quality and appeal (0-10)")
    composite_score: float = Field(ge=0, le=10, description="Weighted final score (0-10)")


class ImageAnalysisResult(BaseModel):
    """Complete analysis result for a restaurant marketing image"""
    image_id: str = Field(description="Unique identifier for the analyzed image")
    filename: str = Field(description="Original filename")
    file_hash: Optional[str] = Field(None, description="MD5 hash for caching")
    
    # Classification
    content_type: ContentType = Field(description="Type of content detected")
    
    # Scores
    scores: ImageAnalysisScore = Field(description="Scoring breakdown")
    
    # Insights
    why_good: str = Field(description="2-3 bullet points of strengths")
    why_bad: str = Field(description="2-3 bullet points of weaknesses")
    recommendation: str = Field(description="Use/Don't use recommendation")
    
    # Classifications (populated by scoring_logic)
    relevance_level: Optional[str] = Field(None, description="relevant, weak, or not_relevant")
    score_grade: Optional[str] = Field(None, description="excellent, good, or poor")
    
    # Metadata
    user_id: str = Field(description="User who uploaded the image")
    image_url: Optional[str] = Field(None, description="URL to the uploaded image")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # A/B Test grouping
    ab_test_batch_id: Optional[str] = Field(None, description="Batch ID if part of an A/B test set")
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_id": "abc123",
                "filename": "burger_special.jpg",
                "file_hash": "d41d8cd98f00b204e9800998ecf8427e",
                "content_type": "food",
                "scores": {
                    "restaurant_relevance": 9.5,
                    "viral_potential": 8.0,
                    "aesthetic_quality": 8.5,
                    "composite_score": 8.7
                },
                "why_good": "• Excellent food presentation\n• Appetizing colors\n• Professional lighting",
                "why_bad": "• Background slightly cluttered\n• Could use better plating",
                "recommendation": "Use - strong restaurant content with good viral potential",
                "user_id": "user@example.com",
                "image_url": "https://storage.example.com/abc123.jpg",
                "ab_test_batch_id": "batch_001"
            }
        }


class ScheduleRecommendation(BaseModel):
    """Optimal posting time recommendation based on platform and niche"""
    day_of_week: str = Field(description="Best day (e.g., 'Tuesday')")
    time_range: str = Field(description="Best time window (e.g., '6-8 PM')")
    timezone: str = Field(default="local", description="Timezone context")
    confidence: str = Field(description="Based on platform studies")
    source: str = Field(description="Research source reference")


class ABTestSchedule(BaseModel):
    """Scheduled A/B test with posting times"""
    schedule_id: str = Field(description="Unique schedule identifier")
    batch_id: str = Field(description="Reference to ABTestBatch")
    user_id: str = Field(description="User who created the schedule")
    campaign_id: Optional[str] = Field(None, description="Campaign this test belongs to")
    
    # Variants to test
    variant_a_image_id: str = Field(description="First image to test")
    variant_b_image_id: str = Field(description="Second image to test")
    
    # Schedule
    platform: str = Field(description="instagram, facebook, tiktok")
    post_time: datetime = Field(description="When to publish Variant A")
    variant_a_post_time: datetime = Field(description="When to publish Variant A")
    variant_b_post_time: datetime = Field(description="When to publish Variant B")
    caption: Optional[str] = Field(None, description="Post caption/copy (backward compatibility)")
    caption_a: Optional[str] = Field(None, description="Variant A caption")
    caption_b: Optional[str] = Field(None, description="Variant B caption")
    
    # Status
    status: str = Field(default="scheduled", description="scheduled, live, completed, cancelled")
    test_duration_hours: int = Field(default=48, description="How long to run the test")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = Field(None, description="When posts went live")


class EngagementMetrics(BaseModel):
    """Real engagement metrics from social platforms"""
    likes: int = Field(default=0)
    comments: int = Field(default=0)
    shares: int = Field(default=0)
    saves: int = Field(default=0)
    reach: int = Field(default=0)
    ctr: float = Field(default=0.0, description="Click-through rate as percentage")
    
    # Calculated
    composite_score: float = Field(default=0.0, description="Weighted engagement score")
    
    def calculate_composite(self) -> float:
        """
        Calculate composite engagement score.
        Weighted: (likes×1) + (comments×3) + (shares×5) + (saves×4) + (reach×0.1) + (CTR×10)
        """
        score = (
            (self.likes * 1) +
            (self.comments * 3) +
            (self.shares * 5) +
            (self.saves * 4) +
            (self.reach * 0.1) +
            (self.ctr * 10)
        )
        self.composite_score = score
        return score


class ABTestResult(BaseModel):
    """Results of a completed A/B test"""
    result_id: str = Field(description="Unique result identifier")
    schedule_id: str = Field(description="Reference to schedule")
    user_id: str = Field(description="User who ran the test")
    
    # Variant A results
    variant_a_image_id: str
    variant_a_metrics: EngagementMetrics
    
    # Variant B results
    variant_b_image_id: str
    variant_b_metrics: EngagementMetrics
    
    # Winner analysis
    winner_image_id: str = Field(description="ID of winning variant")
    delta_percentage: float = Field(description="Performance gap: (winner - loser) / loser * 100")
    confidence_level: str = Field(description="clear_winner (>30%), moderate (10-30%), too_close (<10%)")
    
    # Metadata
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    test_duration_actual: Optional[int] = Field(None, description="Actual test duration in hours")


class AdBriefRecommendation(BaseModel):
    """Generated ad brief for the winning variant"""
    brief_id: str = Field(description="Unique brief identifier")
    result_id: str = Field(description="Reference to test result")
    winning_image_id: str = Field(description="Image to use in ad")
    
    # Targeting (from geo-intent module)
    target_geo: str = Field(description="City/region from geo-intent")
    audience_segment: str = Field(description="18-34, mobile users, etc.")
    
    # Budget & Schedule
    suggested_budget_daily: float = Field(description="USD per day")
    suggested_duration_days: int = Field(description="3, 5, or 7 days")
    total_spend: float = Field(description="Total budget")
    
    # Projections
    estimated_reach: str = Field(description="e.g., '21k-42k'")
    estimated_clicks: str = Field(description="e.g., '670-1,340'")
    estimated_ctr: float = Field(description="Baseline CTR from organic test")
    estimated_cost_per_click: str = Field(description="e.g., '$0.16-$0.31'")
    
    # Creative guidance
    creative_hook: str = Field(description="What worked in the organic test")
    cta_recommendation: str = Field(description="Suggested call-to-action")
    what_not_to_change: str = Field(description="Elements that drove success")
    
    # Platform
    platform: str = Field(default="instagram_tiktok", description="Instagram + TikTok")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ABTestBatch(BaseModel):
    """A collection of images being compared for A/B testing"""
    batch_id: str = Field(description="Unique batch identifier")
    user_id: str = Field(description="User who created the batch")
    images: List[ImageAnalysisResult] = Field(description="Images in this batch")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Recommendations
    recommended_pair: Optional[tuple[str, str]] = Field(None, description="Top 2 image IDs for A/B test")
    score_gap: Optional[float] = Field(None, description="Score difference between top 2 images")
    
    # Test execution
    schedule_id: Optional[str] = Field(None, description="If scheduled, reference to schedule")
    result_id: Optional[str] = Field(None, description="If completed, reference to result")
    ad_brief_id: Optional[str] = Field(None, description="If brief generated, reference to brief")
    
    def calculate_recommendations(self) -> None:
        """Calculate which images should be A/B tested"""
        if len(self.images) < 2:
            return
        
        # Filter to only relevant restaurant content
        relevant = [img for img in self.images if get_relevance_level(img.scores.restaurant_relevance) == RelevanceLevel.RELEVANT]
        
        if len(relevant) >= 2:
            # Sort by composite score
            sorted_images = sorted(relevant, key=lambda x: x.scores.composite_score, reverse=True)
            top_two = sorted_images[:2]
            
            self.recommended_pair = (top_two[0].image_id, top_two[1].image_id)
            self.score_gap = abs(top_two[0].scores.composite_score - top_two[1].scores.composite_score)
    
    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch_001",
                "user_id": "user@example.com",
                "images": [],
                "recommended_pair": ["img1", "img2"],
                "score_gap": 0.3
            }
        }
