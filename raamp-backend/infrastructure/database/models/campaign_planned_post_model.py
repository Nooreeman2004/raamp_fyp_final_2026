from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from beanie import Document, Indexed
from pydantic import Field


PlannedPostStatus = Literal[
    "planned",
    "draft_created",
    "approval_requested",
    "approved",
    "scheduled",
    "published",
    "failed",
]

PostType = Literal["reel", "carousel", "story", "static"]


class CampaignPlannedPostModel(Document):
    """
    A single calendar item produced by a CampaignPlan.
    Links into Drafts + Approval-gated Launch pipeline once user acts on it.
    """

    user_email: Indexed(str) = Field(..., description="Owner user (email)")
    campaign_plan_id: Indexed(str) = Field(..., description="CampaignPlanModel.id")

    scheduled_time: datetime = Field(..., description="UTC datetime when post should be published")
    timezone: str = Field(default="UTC", description="IANA timezone used for calendar rendering")

    title: str = Field(..., min_length=1, max_length=120, description="Title shown in calendar cell")
    post_type: PostType = Field(default="static")

    prompts: Dict[str, Any] = Field(
        default_factory=dict,
        description="Prompt payloads: caption_prompt, creative_prompt, shot_list, etc.",
    )
    cta: Optional[str] = None
    hashtags: List[str] = Field(default_factory=list)
    why_it_fits_brand: Optional[str] = Field(default=None, max_length=600)

    # State machine
    status: PlannedPostStatus = Field(default="planned")
    last_error: Optional[str] = Field(default=None, max_length=500)
    last_error_at: Optional[datetime] = None

    # Linkage to existing flows
    draft_id: Optional[str] = None
    launch_request_id: Optional[str] = None
    scheduled_post_id: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "campaign_planned_posts"
        indexes = [
            "user_email",
            "campaign_plan_id",
            "status",
            "scheduled_time",
            [("user_email", 1), ("scheduled_time", 1)],
            [("campaign_plan_id", 1), ("scheduled_time", 1)],
        ]

