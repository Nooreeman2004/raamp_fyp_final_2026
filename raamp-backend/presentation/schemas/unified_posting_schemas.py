"""
Unified Posting Schemas.
Schemas for multi-platform social media posting.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

class PlatformEnum(str, Enum):
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    BOTH = "both"

class PostModeEnum(str, Enum):
    POST_NOW = "post_now"
    SCHEDULE_POST = "schedule_post"
    POST_STORY = "post_story"

class UnifiedPostRequest(BaseModel):
    platform: PlatformEnum = Field(..., description="Target platform: instagram, facebook, or both")
    mode: PostModeEnum = Field(..., description="Post mode: post_now, schedule_post, post_story")
    media_url: str = Field(..., description="Public URL of the media")
    caption: Optional[str] = Field(None, description="Caption/Message for the post")
    scheduled_time: Optional[str] = Field(None, description="ISO datetime for scheduling")
    
    # Optional overrides
    facebook_page_id: Optional[str] = Field(None, description="Specific FB Page ID if known")
    
    @field_validator("scheduled_time")
    @classmethod
    def validate_scheduled_time(cls, v, info):
        mode = info.data.get("mode")
        if mode == PostModeEnum.SCHEDULE_POST:
            if not v:
                raise ValueError("scheduled_time is required for schedule_post mode")
        return v

class PlatformResult(BaseModel):
    platform: str
    status: str
    post_id: Optional[str] = None
    external_id: Optional[str] = None
    error: Optional[str] = None

class UnifiedPostResponse(BaseModel):
    success: bool
    results: List[PlatformResult]
    message: str
