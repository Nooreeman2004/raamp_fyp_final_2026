# Infrastructure Layer - Content Suggestion Cache MongoDB Model
from beanie import Document
from pydantic import Field
from datetime import datetime, timedelta
from typing import Dict, List


class ContentSuggestionCacheModel(Document):
    """
    Model for caching AI-generated content suggestions.
    Reduces duplicate LLM API calls for the same keyword.
    """
    keyword: str = Field(..., description="The trending keyword")
    niche: str = Field(..., description="Business niche")
    lifecycle_stage: str = Field(..., description="Lifecycle stage when generated")
    
    # Cached suggestions
    video_ideas: List[str] = Field(..., description="3 video concepts")
    hooks: List[str] = Field(..., description="3 attention-grabbing hooks")
    hashtags: List[str] = Field(..., description="10 optimized hashtags")
    campaign_angle: str = Field(..., description="Campaign strategy")
    influencer_strategy: str = Field(..., description="Influencer partnership approach")
    
    # Cache metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(hours=24),
        description="Cache TTL: 24 hours"
    )
    
    class Settings:
        name = "content_suggestion_cache"
        indexes = [
            "keyword",
            "expires_at",
            ("keyword", "niche"),
        ]
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return datetime.utcnow() > self.expires_at
