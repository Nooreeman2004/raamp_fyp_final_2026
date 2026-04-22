from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


ObjectiveEnum = Literal["awareness", "engagement", "foot_traffic", "sales", "leads"]
FrequencyEnum = Literal["daily", "3_per_week", "5_per_week", "custom"]
PostTypeEnum = Literal["reel", "carousel", "story", "static"]
PlannedPostStatusEnum = Literal[
    "planned",
    "draft_created",
    "approval_requested",
    "approved",
    "scheduled",
    "published",
    "failed",
]


class CampaignPlannerCreateRequest(BaseModel):
    idea: str = Field(..., min_length=10, description="High-level campaign idea")
    objective: ObjectiveEnum = Field(default="engagement")
    budget_min: Optional[int] = Field(default=None, ge=0)
    budget_max: Optional[int] = Field(default=None, ge=0)
    start_date: datetime
    end_date: datetime
    timezone: str = Field(default="UTC", description="IANA timezone, e.g. Asia/Karachi")
    posting_frequency: FrequencyEnum = Field(default="3_per_week")
    platforms: List[str] = Field(default_factory=lambda: ["instagram"], description="instagram|facebook|both")
    target_audience: Optional[str] = None
    offer_or_cta: Optional[str] = None
    constraints: Optional[str] = Field(default=None, description="Do/don't, compliance notes, etc.")

    @field_validator("platforms")
    @classmethod
    def validate_platforms(cls, v: List[str]) -> List[str]:
        vv = [(x or "").strip().lower() for x in (v or []) if (x or "").strip()]
        allowed = {"instagram", "facebook", "both"}
        out = [x for x in vv if x in allowed]
        return out or ["instagram"]

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, end_date: datetime, info):
        start_date = info.data.get("start_date")
        if start_date and end_date < start_date:
            raise ValueError("end_date must be after start_date")
        return end_date


class CampaignPlannerCreateResponse(BaseModel):
    plan_id: str
    generation_status: str


class CampaignPlanListItem(BaseModel):
    id: str
    name: str
    objective: Optional[str] = None
    start_date: str
    end_date: str
    timezone: str
    generation_status: str
    created_at: str


class CampaignPlanListResponse(BaseModel):
    plans: List[CampaignPlanListItem]
    total: int


class PlannedPostItem(BaseModel):
    id: str
    campaign_plan_id: str
    scheduled_time: str
    timezone: str
    title: str
    post_type: PostTypeEnum
    status: PlannedPostStatusEnum
    prompts: Dict[str, Any] = Field(default_factory=dict)
    cta: Optional[str] = None
    hashtags: List[str] = Field(default_factory=list)
    why_it_fits_brand: Optional[str] = None
    draft_id: Optional[str] = None
    launch_request_id: Optional[str] = None
    last_error: Optional[str] = None
    last_error_at: Optional[str] = None


class CampaignPlanDetailResponse(BaseModel):
    id: str
    input_brief: Dict[str, Any]
    generated: Dict[str, Any]
    start_date: str
    end_date: str
    timezone: str
    posting_frequency: str
    generation_status: str
    generation_error: Optional[str] = None
    status: str
    created_at: str
    updated_at: str
    posts: List[PlannedPostItem] = Field(default_factory=list)


class CalendarQueryResponse(BaseModel):
    items: List[PlannedPostItem]


class PlannedPostPatchRequest(BaseModel):
    scheduled_time: Optional[datetime] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=120)
    status: Optional[PlannedPostStatusEnum] = None


class ApprovalRequestQuery(BaseModel):
    mode: str = Field(default="schedule_post", description="post_now|schedule_post|post_story")
    platform: str = Field(default="instagram", description="instagram|facebook|both")
    media_url: str = Field(..., description="Public HTTPS media URL")

