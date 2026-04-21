"""
Auto Reply Settings Model
Collection: auto_reply_settings
"""

from beanie import Document
from pydantic import Field
from datetime import datetime


class AutoReplyMode:
    REVIEW_ONLY = "review_only"
    HYBRID_AUTO = "hybrid_auto"


class AutoReplySettingsModel(Document):
    """Per-user per-platform auto-reply settings."""

    user_id: str = Field(..., description="Reference to the user (email)")

    facebook_auto_replies_enabled: bool = Field(default=True, description="Enable Facebook auto replies")
    instagram_auto_replies_enabled: bool = Field(default=True, description="Enable Instagram auto replies")

    facebook_mode: str = Field(default=AutoReplyMode.REVIEW_ONLY, description="review_only | hybrid_auto")
    instagram_mode: str = Field(default=AutoReplyMode.REVIEW_ONLY, description="review_only | hybrid_auto")

    # Context enrichment quota controls
    thread_context_depth: int = Field(
        default=0,
        ge=0,
        le=3,
        description="How many recent thread comments/replies to include (0/1/3).",
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "auto_reply_settings"
        indexes = [
            "user_id",
        ]

