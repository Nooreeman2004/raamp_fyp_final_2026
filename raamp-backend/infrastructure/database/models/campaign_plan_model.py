from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Literal, Optional

from beanie import Document, Indexed
from pydantic import Field


CampaignPlanStatus = Literal["generated", "edited", "archived"]
GenerationStatus = Literal["queued", "running", "completed", "failed"]


class CampaignPlanModel(Document):
    """
    Brand-driven campaign planning container.

    A Campaign Plan is a strategic brief + generated plan metadata.
    The calendar items live in CampaignPlannedPostModel.
    """

    user_email: Indexed(str) = Field(..., description="Owner user (email)")
    business_id: Indexed(str) = Field(..., description="Associated business id (BusinessModel.id)")

    input_brief: Dict[str, Any] = Field(default_factory=dict, description="User-provided campaign brief answers")
    generated: Dict[str, Any] = Field(default_factory=dict, description="AI-generated campaign plan summary")

    start_date: datetime = Field(..., description="Campaign start (timezone-aware)")
    end_date: datetime = Field(..., description="Campaign end (timezone-aware)")
    timezone: str = Field(default="UTC", description="IANA timezone, e.g. Asia/Karachi")
    posting_frequency: str = Field(default="3_per_week", description="e.g. 3_per_week, daily, custom")

    generation_status: GenerationStatus = Field(default="queued")
    generation_error: Optional[str] = Field(default=None, description="Last generation failure reason")

    status: CampaignPlanStatus = Field(default="generated")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "campaign_plans"
        indexes = [
            "user_email",
            "business_id",
            "status",
            "generation_status",
            [("user_email", 1), ("created_at", -1)],
            [("user_email", 1), ("status", 1)],
        ]

