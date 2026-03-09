"""
Caption Log Model for MongoDB - stores all AI-generated captions
"""
from beanie import Document
from pydantic import Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


class AssetTypeEnum(str, Enum):
    """Types of content assets"""
    POST = "post"
    STORY = "story"
    REEL = "reel"
    CAROUSEL = "carousel"
    AD_COPY = "ad_copy"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    HASHTAG = "hashtag"


class CaptionLogModel(Document):
    """Caption log document stored in MongoDB"""
    
    # Core Identification
    caption_id: str = Field(..., description="Unique caption identifier (UUID)")
    user_id: str = Field(..., description="Reference to the user who owns this caption")
    
    # Campaign Context
    campaign_id: Optional[str] = Field(None, description="Campaign identifier if part of a campaign")
    campaign_idea: Optional[str] = Field(None, description="Original campaign idea from user")
    
    # Caption Details
    asset_type: AssetTypeEnum = Field(..., description="Type of content (post, story, reel, etc.)")
    caption_text: str = Field(..., description="The generated caption text")
    hashtags: list[str] = Field(default_factory=list, description="Associated hashtags")
    tone: str = Field(..., description="Tone/variant of this caption (e.g., 'Vibrant & Direct')")
    
    # Generation Metadata
    generation_prompt: Optional[str] = Field(None, description="AI prompt used to generate this caption")
    model_used: Optional[str] = Field(None, description="AI model used (e.g., 'gpt-4o-mini')")
    variant_number: Optional[int] = Field(None, description="Variant number (1, 2, or 3)")
    predicted_performance: Optional[str] = Field(None, description="AI prediction: Best, Good, Experimental")
    
    # Brand Context
    brand_tone_used: Optional[str] = Field(None, description="Brand tone of voice at generation time")
    target_audience: Optional[str] = Field(None, description="Target audience for this caption")
    
    # Usage Tracking
    times_used: int = Field(default=0, description="Number of times this caption was used in posts")
    last_used_at: Optional[datetime] = Field(None, description="Last time caption was used")
    
    # Performance Tracking (for future A/B testing integration)
    actual_performance: Optional[str] = Field(None, description="Actual performance data")
    engagement_rate: Optional[float] = Field(None, description="Engagement rate if tracked")
    
    # Organization
    tags: list[str] = Field(default_factory=list, description="User-defined tags for organization")
    is_favorite: bool = Field(default=False, description="Whether user marked as favorite")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(protected_namespaces=())
    
    class Settings:
        name = "caption_logs"
        indexes = [
            "caption_id",
            "user_id",
            "asset_type",
            "created_at",
            [("user_id", 1), ("created_at", -1)],  # Compound index for user timeline
            [("user_id", 1), ("asset_type", 1)],  # Filter by user and asset type
            [("user_id", 1), ("campaign_id", 1)],  # Filter by user and campaign
        ]
