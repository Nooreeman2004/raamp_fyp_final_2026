"""
Campaign Launch Schemas
======================
Request/response models for approval-gated campaign launches.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List


class CampaignLaunchCreateRequest(BaseModel):
    platform: str = Field(..., description="instagram | facebook | both")
    mode: str = Field(..., description="post_now | schedule_post | post_story")
    media_url: str = Field(..., description="Public media URL")
    caption: Optional[str] = Field(None, description="Caption/message")
    scheduled_time: Optional[str] = Field(None, description="ISO datetime if scheduling")
    facebook_page_id: Optional[str] = Field(None, description="Optional FB page id override")

    trend_keyword: Optional[str] = Field(None, description="Associated trend keyword")
    trend_signal_id: Optional[str] = Field(None, description="Associated TrendSignal id")

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        vv = (v or "").strip().lower()
        if vv not in ("instagram", "facebook", "both"):
            raise ValueError("platform must be one of: instagram, facebook, both")
        return vv

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        vv = (v or "").strip().lower()
        if vv not in ("post_now", "schedule_post", "post_story"):
            raise ValueError("mode must be one of: post_now, schedule_post, post_story")
        return vv

    @field_validator("scheduled_time")
    @classmethod
    def validate_scheduled_time(cls, v: Optional[str], info):
        mode = (info.data.get("mode") or "").strip().lower()
        if mode == "schedule_post" and not v:
            raise ValueError("scheduled_time is required for schedule_post mode")
        return v


class CampaignLaunchCreateResponse(BaseModel):
    success: bool = True
    request_id: str
    status: str
    message: str


class CampaignLaunchApproveResponse(BaseModel):
    success: bool
    request_id: str
    status: str
    result: Dict[str, Any] = Field(default_factory=dict)


class CampaignLaunchRejectRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=200, description="Optional reason for rejection")


class CampaignLaunchItem(BaseModel):
    id: str
    status: str
    platform: str
    mode: str
    media_url: str
    caption: Optional[str] = None
    scheduled_time: Optional[str] = None
    trend_keyword: Optional[str] = None
    trend_signal_id: Optional[str] = None
    fetch_status: Optional[str] = None
    error_message: Optional[str] = None
    is_simulated: Optional[bool] = None
    created_at: str
    updated_at: str
    result: Dict[str, Any] = Field(default_factory=dict)


class CampaignLaunchListResponse(BaseModel):
    requests: List[CampaignLaunchItem]
    total: int

