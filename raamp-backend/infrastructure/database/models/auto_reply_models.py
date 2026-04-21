"""
Auto Reply Models (FB + IG)
==========================
Persistence for Meta comment events, auto-reply decisions, drafts, and sent replies.
"""

from __future__ import annotations

from beanie import Document
from datetime import datetime
from pydantic import Field
from typing import Any, Dict, List, Optional


class CommentEventStatus:
    RECEIVED = "received"
    PROCESSED = "processed"
    REPLIED = "replied"
    SKIPPED = "skipped"
    FAILED = "failed"


class PolicyAction:
    AUTO_REPLY = "auto_reply"
    NEEDS_REVIEW = "needs_review"
    SKIP = "skip"


class AutoReplyDraftStatus:
    ACTIVE = "active"
    EXPIRED = "expired"
    SENT = "sent"
    SKIPPED = "skipped"


class CommentEventModel(Document):
    """
    Raw comment event received from Meta (FB/IG) webhooks.
    One record per unique event (deduped).
    """

    user_id: Optional[str] = Field(
        default=None,
        description="Owning user (email). Populated after enrichment/lookup, may be null at ingest time.",
    )
    platform: str = Field(..., description="facebook | instagram")

    page_id: Optional[str] = Field(None, description="Facebook Page id (if platform=facebook)")
    ig_business_id: Optional[str] = Field(None, description="Instagram Business id (if platform=instagram)")

    post_id: Optional[str] = Field(None, description="Facebook post id (if applicable)")
    media_id: Optional[str] = Field(None, description="Instagram media id (if applicable)")

    comment_id: str = Field(..., description="Meta comment id")
    from_id: Optional[str] = Field(None, description="Actor id that created the comment")
    text: str = Field(..., description="Comment text")
    created_time: Optional[datetime] = Field(None, description="Comment created time (UTC) if provided")

    raw_payload: Dict[str, Any] = Field(default_factory=dict, description="Original webhook payload (subset or full)")

    dedupe_key: str = Field(..., description="Dedupe key for Meta retries (computed at ingest)")
    status: str = Field(default=CommentEventStatus.RECEIVED, description="Processing state")
    error: Optional[str] = Field(None, description="Last error message (truncated)")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "comment_events"
        indexes = [
            "user_id",
            "platform",
            "comment_id",
            "dedupe_key",
            "status",
            "created_at",
            [("platform", 1), ("comment_id", 1)],
            [("dedupe_key", 1)],
        ]


class AutoReplyDecisionModel(Document):
    """
    Decision record for a comment event.
    Stores intent classification output + policy action + minimal context snapshot.
    """

    comment_event_id: str = Field(..., description="Reference to CommentEventModel.id (stringified)")
    user_id: str = Field(..., description="Owning user (email)")
    platform: str = Field(..., description="facebook | instagram")
    comment_id: str = Field(..., description="Meta comment id (denormalized for queries)")

    intent_label: Optional[str] = Field(None, description="Intent label (pricing/hours/location/...)")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Classifier confidence 0..1")
    risk_level: Optional[str] = Field(None, description="risk label/level (low/medium/high or policy-specific)")

    policy_action: str = Field(..., description="auto_reply | needs_review | skip")
    reason: Optional[str] = Field(None, description="Human-readable reason (truncated)")

    context_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="Snapshot of context used (e.g., parent caption/permalink, thread excerpt)",
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "auto_reply_decisions"
        indexes = [
            "user_id",
            "platform",
            "comment_id",
            "comment_event_id",
            "policy_action",
            "created_at",
            [("user_id", 1), ("created_at", -1)],
            [("platform", 1), ("comment_id", 1)],
        ]


class AutoReplyDraftModel(Document):
    """
    Draft reply suggestions (review path).
    """

    comment_event_id: str = Field(..., description="Reference to CommentEventModel.id (stringified)")
    decision_id: Optional[str] = Field(None, description="Reference to AutoReplyDecisionModel.id (stringified)")

    user_id: str = Field(..., description="Owning user (email)")
    platform: str = Field(..., description="facebook | instagram")
    comment_id: str = Field(..., description="Meta comment id")

    suggested_reply: str = Field(..., description="Primary suggested reply")
    alternatives: List[str] = Field(default_factory=list, description="Optional alternative suggestions")

    requires_user_action: bool = Field(default=True, description="True for review-required drafts")
    expires_at: datetime = Field(..., description="Draft expiry time (UTC)")

    status: str = Field(default=AutoReplyDraftStatus.ACTIVE, description="active | expired | sent | skipped")
    resolved_at: Optional[datetime] = Field(None, description="When draft was resolved (sent/skipped/expired)")

    approval_nonce: str = Field(
        ...,
        description="Server-generated idempotency token required for Approve & Send.",
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "auto_reply_drafts"
        indexes = [
            "user_id",
            "platform",
            "comment_id",
            "comment_event_id",
            "decision_id",
            "status",
            "expires_at",
            [("status", 1), ("expires_at", 1)],
            [("platform", 1), ("comment_id", 1)],
        ]


class AutoReplySentModel(Document):
    """
    Successfully posted replies (auto path or user-approved).
    """

    comment_event_id: str = Field(..., description="Reference to CommentEventModel.id (stringified)")
    draft_id: Optional[str] = Field(None, description="Reference to AutoReplyDraftModel.id (stringified), if any")
    decision_id: Optional[str] = Field(None, description="Reference to AutoReplyDecisionModel.id (stringified), if any")

    user_id: str = Field(..., description="Owning user (email)")
    platform: str = Field(..., description="facebook | instagram")
    comment_id: str = Field(..., description="Meta comment id")

    reply_id: Optional[str] = Field(None, description="Graph API reply id (if provided)")
    reply_text: str = Field(..., description="Reply body actually sent")
    normalized_reply_hash: str = Field(..., description="SHA-256 of normalized reply text")

    sent_at: datetime = Field(default_factory=datetime.utcnow)
    graph_response: Dict[str, Any] = Field(default_factory=dict, description="Safe subset of Graph API response")
    idempotency_key: str = Field(..., description="platform + comment_id + normalized_reply_hash")

    class Settings:
        name = "auto_reply_sent"
        indexes = [
            "user_id",
            "platform",
            "comment_id",
            "idempotency_key",
            "sent_at",
            [("platform", 1), ("comment_id", 1), ("normalized_reply_hash", 1)],
            [("idempotency_key", 1)],
        ]

