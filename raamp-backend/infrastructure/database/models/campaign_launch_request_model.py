"""
Campaign Launch Request Model
=============================
Approval-gated campaign launch requests triggered from Trend Arbitrage.

Goals:
- Persist a user-initiated "request to launch" that requires explicit approval.
- On approval, orchestrate existing posting flows (do not rewrite posting logic).
- Persist results (post IDs, errors) for auditability and UI display.
"""

from __future__ import annotations

from beanie import Document, Indexed
from pydantic import Field
from datetime import datetime
from typing import Optional, Dict, Any


class CampaignLaunchStatus:
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class CampaignLaunchRequestModel(Document):
    """MongoDB document for campaign launch approvals."""

    user_email: Indexed(str) = Field(..., description="User who owns this request")

    # Trend attribution
    trend_keyword: Optional[str] = Field(None, description="Keyword associated with this launch")
    trend_signal_id: Optional[str] = Field(None, description="TrendSignal id associated with this launch")

    # Posting intent (mirrors unified posting semantics)
    platform: str = Field(..., description="instagram | facebook | both")
    mode: str = Field(..., description="post_now | schedule_post | post_story")
    media_url: str = Field(..., description="Public media URL")
    caption: Optional[str] = Field(None, description="Caption/message")
    scheduled_time: Optional[str] = Field(None, description="ISO datetime if scheduling")
    facebook_page_id: Optional[str] = Field(None, description="Optional FB page id override")

    status: str = Field(default=CampaignLaunchStatus.PENDING, description="Approval workflow status")
    status_reason: Optional[str] = Field(None, description="Reason for rejection/failure")

    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Results from posting orchestration
    result: Dict[str, Any] = Field(default_factory=dict, description="Execution result payload")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "campaign_launch_requests"
        indexes = [
            "user_email",
            "status",
            "created_at",
            [("user_email", 1), ("created_at", -1)],
            [("user_email", 1), ("status", 1)],
        ]

