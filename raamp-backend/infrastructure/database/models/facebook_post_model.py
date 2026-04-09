"""
Facebook Post Models
Database models for Facebook posts and scheduled posts
"""
from beanie import Document, Indexed
from pydantic import Field
from datetime import datetime
from typing import Optional


class FacebookPostModel(Document):
    """Model for Facebook posts"""
    user_id: Indexed(str) = Field(..., description="User ID who created the post")
    page_id: str = Field(..., description="Facebook Page ID")
    page_name: Optional[str] = Field(None, description="Facebook Page name")
    media_type: str = Field(..., description="Type of media: PHOTO, VIDEO, TEXT")
    media_url: Optional[str] = Field(None, description="Media URL")
    message: Optional[str] = Field(None, description="Post message/caption")
    title: Optional[str] = Field(None, description="Video title")
    facebook_post_id: Optional[str] = Field(None, description="Facebook post ID")
    status: str = Field(..., description="Post status: PENDING, PROCESSING, PUBLISHED, FAILED")
    error: Optional[str] = Field(None, description="Error message if posting failed")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Trend attribution (optional)
    trend_signal_id: Optional[str] = Field(None, description="Associated TrendSignal id for attribution")
    
    class Settings:
        name = "facebook_posts"
        indexes = [
            [("user_id", 1)],
            [("page_id", 1)],
            [("status", 1)],
            [("created_at", -1)]
        ]


class ScheduledFacebookPostModel(Document):
    """Model for scheduled Facebook posts"""
    user_id: Indexed(str) = Field(..., description="User ID who created the post")
    page_id: str = Field(..., description="Facebook Page ID")
    page_name: Optional[str] = Field(None, description="Facebook Page name")
    media_type: str = Field(..., description="Type of media: PHOTO, VIDEO, TEXT")
    media_url: Optional[str] = Field(None, description="Media URL")
    message: Optional[str] = Field(None, description="Post message/caption")
    title: Optional[str] = Field(None, description="Video title")
    scheduled_time: datetime = Field(..., description="When to publish the post")
    status: str = Field(default="SCHEDULED", description="Post status: SCHEDULED, PROCESSING, PUBLISHED, FAILED, CANCELLED")
    facebook_post_id: Optional[str] = Field(None, description="Facebook post ID after publishing")
    error: Optional[str] = Field(None, description="Error message if posting failed")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    published_at: Optional[datetime] = Field(None, description="When the post was published")

    # Trend attribution (optional)
    trend_signal_id: Optional[str] = Field(None, description="Associated TrendSignal id for attribution")
    
    class Settings:
        name = "scheduled_facebook_posts"
        indexes = [
            [("user_id", 1)],
            [("page_id", 1)],
            [("status", 1)],
            [("scheduled_time", 1)],
            [("created_at", -1)]
        ]
