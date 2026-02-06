"""
Database model for Instagram posts.
Maps domain entities to database persistence layer.
"""
from beanie import Document, Indexed
from pydantic import Field
from typing import Optional
from datetime import datetime


class InstagramPostModel(Document):
    """
    Persistent model for Instagram feed posts.
    Tracks post lifecycle from creation to publication.
    """
    user_id: str = Indexed()
    ig_business_id: str
    media_url: str
    caption: Optional[str]
    media_type: str = "IMAGE"  # IMAGE, VIDEO, CAROUSEL_ALBUM
    status: str = "pending"  # pending, processing, published, failed
    instagram_media_id: Optional[str]
    instagram_post_id: Optional[str] = Indexed()
    error_message: Optional[str]
    retry_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime]

    class Settings:
        name = "instagram_posts"
        indexes = [
            "user_id",
            "status",
            "created_at",
        ]


class ScheduledInstagramPostModel(Document):
    """
    Persistent model for scheduled Instagram posts.
    Enables deferred posting functionality.
    """
    user_id: str = Indexed()
    ig_business_id: str
    media_url: str
    caption: Optional[str]
    media_type: str = "IMAGE"
    scheduled_time: datetime = Indexed()
    status: str = "scheduled"  # scheduled, processing, published, failed, cancelled
    instagram_post_id: Optional[str]
    error_message: Optional[str]
    retry_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime]

    class Settings:
        name = "scheduled_instagram_posts"
        indexes = [
            "user_id",
            "scheduled_time",
            "status",
        ]


class InstagramStoryModel(Document):
    """
    Persistent model for Instagram stories.
    Stories have 24h lifecycle and different publishing rules.
    """
    user_id: str = Indexed()
    ig_business_id: str
    media_url: str
    media_type: str = "STORIES"
    status: str = "pending"  # pending, processing, published, failed
    instagram_story_id: Optional[str]
    error_message: Optional[str]
    retry_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime]

    class Settings:
        name = "instagram_stories"
        indexes = [
            "user_id",
            "status",
            "created_at",
        ]
