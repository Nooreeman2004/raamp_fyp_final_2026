"""
Domain entities for Instagram posting feature.
These represent core business objects independent of infrastructure.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class PostMode(str, Enum):
    """Enum representing the mode of Instagram posting"""
    POST_NOW = "post_now"
    SCHEDULE_POST = "schedule_post"
    POST_STORY = "post_story"


class PostStatus(str, Enum):
    """Enum representing the status of an Instagram post"""
    PENDING = "pending"
    PROCESSING = "processing"
    PUBLISHED = "published"
    SCHEDULED = "scheduled"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MediaType(str, Enum):
    """Enum representing Instagram media types"""
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    CAROUSEL_ALBUM = "CAROUSEL_ALBUM"
    STORIES = "STORIES"


class InstagramPost(BaseModel):
    """
    Domain entity representing an Instagram post.
    This is the core business object that encapsulates post data.
    """
    id: Optional[str] = None  # MongoDB document ID
    user_id: str
    ig_business_id: str
    media_url: str
    caption: Optional[str] = None
    media_type: MediaType = MediaType.IMAGE
    status: PostStatus = PostStatus.PENDING
    instagram_media_id: Optional[str] = None
    instagram_post_id: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    published_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class ScheduledPost(BaseModel):
    """
    Domain entity representing a scheduled Instagram post.
    Separates scheduling concerns from immediate posting.
    """
    id: Optional[str] = None  # MongoDB document ID
    user_id: str
    ig_business_id: str
    media_url: str
    caption: Optional[str] = None
    media_type: MediaType = MediaType.IMAGE
    scheduled_time: datetime
    status: PostStatus = PostStatus.SCHEDULED
    instagram_post_id: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    executed_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class StoryPost(BaseModel):
    """
    Domain entity representing an Instagram story post.
    Stories have special requirements (24h expiry, no scheduling by Meta).
    """
    id: Optional[str] = None  # MongoDB document ID
    user_id: str
    ig_business_id: str
    media_url: str
    media_type: MediaType = MediaType.STORIES
    status: PostStatus = PostStatus.PENDING
    instagram_story_id: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    published_at: Optional[datetime] = None

    class Config:
        use_enum_values = True
