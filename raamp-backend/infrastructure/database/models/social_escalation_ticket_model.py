"""
Social Escalation Ticket Model (Beanie Document)
===============================================
Tracks escalations derived from social comments (Meta webhooks) that require business-admin action.

This is intentionally separate from the RAAMP Complaints module (which is for users complaining about RAAMP).
"""

from __future__ import annotations

from beanie import Document
from datetime import datetime
from pydantic import Field
from typing import Any, Dict, Optional
from pymongo import IndexModel


class SocialEscalationStatus:
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class SocialEscalationPriority:
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"


class SocialEscalationTicketModel(Document):
    """
    One ticket per (platform, comment_id) via unique external_ref.
    """

    # Scoping
    business_id: str = Field(..., description="Business ObjectId (stringified)")
    social_account_id: str = Field(..., description="Owning social account/page id (page_id or ig_business_id)")
    owner_user_id: Optional[str] = Field(
        default=None,
        description="Owning user email (denormalized convenience; not required for correctness)",
    )

    # Dedupe + linkage
    external_ref: str = Field(..., description="Unique ref: meta_comment:{platform}:{comment_id}")
    comment_event_id: str = Field(..., description="CommentEventModel.id (stringified)")
    draft_id: Optional[str] = Field(default=None, description="AutoReplyDraftModel.id (stringified)")

    platform: str = Field(..., description="facebook|instagram")
    comment_id: str = Field(..., description="Meta comment id")

    # Classification
    intent: Optional[str] = Field(default=None, description="complaint|refund|chargeback|scam|angry|...")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    priority: str = Field(default=SocialEscalationPriority.MEDIUM, description="critical|high|medium")

    # Lifecycle + SLA
    status: str = Field(default=SocialEscalationStatus.OPEN, description="open|acknowledged|resolved")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    first_viewed_at: Optional[datetime] = Field(default=None, description="Set on first admin view (passive)")
    acknowledged_at: Optional[datetime] = Field(default=None, description="Set on explicit acknowledge (active)")
    resolved_at: Optional[datetime] = Field(default=None, description="Set on resolve")

    sla_seconds: int = Field(default=0, description="SLA duration in seconds")
    sla_due_at: Optional[datetime] = Field(default=None, description="When SLA is due (UTC)")

    admin_notification_sent_at: Optional[datetime] = Field(
        default=None,
        description="When the initial admin notification was successfully sent (for retry control)",
    )

    # Optional payload snapshot for UI/debug (avoid sensitive data)
    context: Dict[str, Any] = Field(default_factory=dict, description="Small context snapshot for admin UI")

    class Settings:
        name = "social_escalation_tickets"
        indexes = [
            # Dedupe
            # Must match DB: unique external_ref_1
            IndexModel([("external_ref", 1)], unique=True, name="external_ref_1"),
            # Queue queries
            [("business_id", 1), ("status", 1), ("sla_due_at", 1)],
            [("social_account_id", 1), ("status", 1)],
            [("owner_user_id", 1), ("status", 1)],
            "platform",
            "comment_id",
            "created_at",
        ]

