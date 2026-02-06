"""
Request and response schemas for Instagram posting API.
Defines contracts between presentation layer and clients.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime, timezone
from enum import Enum


class PostModeEnum(str, Enum):
    """API-level enum for posting modes"""
    POST_NOW = "post_now"
    SCHEDULE_POST = "schedule_post"
    POST_STORY = "post_story"


class InstagramPostRequest(BaseModel):
    """
    Request schema for Instagram posting endpoint.
    Unified schema supporting all posting modes.
    """
    mode: PostModeEnum = Field(
        ...,
        description="Posting mode: post_now, schedule_post, or post_story"
    )
    media_url: str = Field(
        ...,
        description="Publicly accessible URL of the media to post"
    )
    caption: Optional[str] = Field(
        None,
        max_length=2200,
        description="Post caption (max 2200 chars, not used for stories)"
    )
    scheduled_time: Optional[str] = Field(
        None,
        description="ISO 8601 datetime for scheduled posts"
    )
    
    @validator("media_url")
    def validate_media_url(cls, v):
        """Ensure media URL is from Cloudinary or localhost (development only)"""
        if not v or not v.strip():
            raise ValueError("media_url is required and cannot be empty")
        
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            raise ValueError(f"media_url must be a valid HTTP/HTTPS URL. Received: {v[:100]}")
        
        v_lower = v.lower()
        
        # Only allow Cloudinary URLs (production)
        if 'cloudinary.com' in v_lower:
            return v
        
        # Allow localhost URLs (development/testing)
        if 'localhost' in v_lower or '127.0.0.1' in v:
            return v
        
        # Reject all other external URLs
        raise ValueError(
            f"media_url must be a Cloudinary URL or localhost URL. "
            f"External URLs are not supported. Please upload media through the Asset Library. "
            f"Received URL: {v[:100]}"
        )
    
    @validator("scheduled_time")
    def validate_scheduled_time(cls, v, values):
        """Validate scheduled_time when mode is schedule_post"""
        mode = values.get("mode")
        if mode == PostModeEnum.SCHEDULE_POST:
            if not v:
                raise ValueError("scheduled_time is required for schedule_post mode")
            try:
                scheduled_dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
                if scheduled_dt <= datetime.now(timezone.utc):
                    raise ValueError("scheduled_time must be in the future")
            except ValueError as e:
                raise ValueError(f"Invalid scheduled_time format: {e}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "mode": "post_now",
                "media_url": "https://example.com/image.jpg",
                "caption": "Check out our new product! #brand",
                "scheduled_time": None
            }
        }


class InstagramPostResponse(BaseModel):
    """
    Response schema for Instagram posting endpoint.
    Provides consistent response structure across all modes.
    """
    status: str = Field(
        ...,
        description="Status: published, scheduled, or failed"
    )
    post_id: Optional[str] = Field(
        None,
        description="Internal post ID for tracking"
    )
    instagram_post_id: Optional[str] = Field(
        None,
        description="Instagram post/story ID (only for published posts)"
    )
    scheduled_time: Optional[str] = Field(
        None,
        description="Scheduled execution time (only for scheduled posts)"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if status is failed"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "published",
                "post_id": "1706976543.123",
                "instagram_post_id": "17890123456789012",
                "scheduled_time": None,
                "error": None
            }
        }


class ScheduledPostListResponse(BaseModel):
    """Response schema for listing scheduled posts"""
    posts: list = Field(
        default_factory=list,
        description="List of scheduled posts"
    )
    total: int = Field(
        0,
        description="Total number of scheduled posts"
    )


class ScheduledPostItem(BaseModel):
    """Individual scheduled post item"""
    post_id: str
    media_url: str
    caption: Optional[str]
    scheduled_time: str
    status: str
    created_at: str


class CancelScheduledPostRequest(BaseModel):
    """Request schema for cancelling scheduled post"""
    post_id: str = Field(
        ...,
        description="ID of scheduled post to cancel"
    )


class CancelScheduledPostResponse(BaseModel):
    """Response schema for cancelling scheduled post"""
    success: bool
    message: str


class PostHistoryResponse(BaseModel):
    """Response schema for post history"""
    posts: list = Field(
        default_factory=list,
        description="List of posts"
    )
    total: int = Field(
        0,
        description="Total number of posts"
    )


class PostHistoryItem(BaseModel):
    """Individual post history item"""
    post_id: str
    internal_id: Optional[str] = None
    platform: str = "instagram"
    media_url: str
    caption: Optional[str]
    status: str
    instagram_post_id: Optional[str]
    created_at: str
    published_at: Optional[str]
    error_message: Optional[str]
