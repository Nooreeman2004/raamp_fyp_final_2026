"""
Schemas for Facebook posting endpoints
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime, timezone
from typing import Optional, List
from enum import Enum


class PostModeEnum(str, Enum):
    """Posting mode options"""
    POST_NOW = "POST_NOW"
    SCHEDULE_POST = "SCHEDULE_POST"


class MediaTypeEnum(str, Enum):
    """Media type for Facebook posts"""
    PHOTO = "PHOTO"
    VIDEO = "VIDEO"
    TEXT = "TEXT"


class FacebookPostRequest(BaseModel):
    """Request schema for Facebook posting"""
    mode: PostModeEnum = Field(..., description="Posting mode: POST_NOW or SCHEDULE_POST")
    page_id: str = Field(..., description="Facebook Page ID to post to")
    media_type: MediaTypeEnum = Field(..., description="Type of media: PHOTO, VIDEO, or TEXT")
    media_url: Optional[str] = Field(None, description="Media URL (required for PHOTO/VIDEO)")
    message: Optional[str] = Field(None, description="Post message/caption", max_length=63206)
    title: Optional[str] = Field(None, description="Title for video posts")
    scheduled_time: Optional[datetime] = Field(None, description="Scheduled posting time (required for SCHEDULE_POST)")
    
    @field_validator('media_url')
    @classmethod
    def validate_media_url(cls, v, info):
        """Validate media URL format and requirement"""
        media_type = info.data.get('media_type')
        
        if media_type in [MediaTypeEnum.PHOTO, MediaTypeEnum.VIDEO]:
            if not v:
                raise ValueError(f"media_url is required for {media_type} posts")
            if not v.startswith(('http://', 'https://')):
                raise ValueError(f"media_url must be a valid HTTP(S) URL. Received: {v[:100]}")
            
            # Allow Firebase Storage URLs without extension check
            if 'firebasestorage.googleapis.com' in v.lower():
                return v
            
            # Allow localhost URLs (development/fallback)
            if 'localhost' in v.lower() or '127.0.0.1' in v:
                return v
            
            # Validate that URL points to an actual image/video file, not a webpage
            v_lower = v.lower()
            if media_type == MediaTypeEnum.PHOTO:
                valid_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
                if not any(v_lower.endswith(ext) or f'{ext}?' in v_lower for ext in valid_extensions):
                    raise ValueError(
                        f"media_url must be a direct link to an image file (e.g., https://example.com/photo.jpg) "
                        f"or a Firebase Storage URL. Webpage URLs are not supported. Received: {v[:100]}"
                    )
            elif media_type == MediaTypeEnum.VIDEO:
                valid_extensions = ('.mp4', '.mov', '.avi', '.mkv', '.webm')
                if not any(v_lower.endswith(ext) or f'{ext}?' in v_lower for ext in valid_extensions):
                    raise ValueError(
                        f"media_url must be a direct link to a video file (e.g., https://example.com/video.mp4) "
                        f"or a Firebase Storage URL. Webpage URLs are not supported. Received: {v[:100]}"
                    )
        
        return v
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v, info):
        """Validate message requirement"""
        media_type = info.data.get('media_type')
        
        if media_type == MediaTypeEnum.TEXT and not v:
            raise ValueError("message is required for TEXT posts")
        
        return v
    
    @field_validator('scheduled_time')
    @classmethod
    def validate_scheduled_time(cls, v, info):
        """Validate scheduled time is in the future and required for SCHEDULE_POST"""
        mode = info.data.get('mode')
        
        if mode == PostModeEnum.SCHEDULE_POST:
            if not v:
                raise ValueError("scheduled_time is required for SCHEDULE_POST mode")
            if v <= datetime.now(timezone.utc):
                raise ValueError("scheduled_time must be in the future")
        
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "mode": "POST_NOW",
                "page_id": "1234567890",
                "media_type": "PHOTO",
                "media_url": "https://example.com/image.jpg",
                "message": "Check out our latest update!",
                "scheduled_time": None
            }
        }
    }


class FacebookPostResponse(BaseModel):
    """Response schema for Facebook posting"""
    status: str = Field(..., description="Post status: PUBLISHED, PENDING, SCHEDULED, FAILED")
    post_id: Optional[str] = Field(None, description="Internal post ID")
    facebook_post_id: Optional[str] = Field(None, description="Facebook post ID")
    scheduled_time: Optional[datetime] = Field(None, description="Scheduled posting time")
    error: Optional[str] = Field(None, description="Error message if posting failed")
    page_id: str = Field(..., description="Facebook Page ID")
    page_name: Optional[str] = Field(None, description="Facebook Page name")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "PUBLISHED",
                "post_id": "abc123",
                "facebook_post_id": "1234567890_9876543210",
                "scheduled_time": None,
                "error": None,
                "page_id": "1234567890",
                "page_name": "My Business Page"
            }
        }
    }


class ScheduledPostsResponse(BaseModel):
    """Response schema for listing scheduled posts"""
    scheduled_posts: List[dict] = Field(..., description="List of scheduled posts")
    total: int = Field(..., description="Total number of scheduled posts")


class CancelScheduledPostRequest(BaseModel):
    """Request schema for canceling scheduled post"""
    post_id: str = Field(..., description="Internal post ID to cancel")


class CancelScheduledPostResponse(BaseModel):
    """Response schema for canceling scheduled post"""
    success: bool = Field(..., description="Whether cancellation was successful")
    message: str = Field(..., description="Success or error message")
