from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Literal, Optional

from beanie import Document, Indexed
from pydantic import Field


DraftKind = Literal["carousel", "reel", "story"]


class CampaignDraftModel(Document):
    """
    Persisted content drafts generated from trends (Create Pack).
    These are intentionally lightweight and can be opened in CreativeStudio.
    """

    user_id: Indexed(str) = Field(..., description="User email")
    kind: DraftKind = Field(..., description="Draft type: carousel/reel/story")

    trend_keyword: Optional[str] = Field(None)
    niche: Optional[str] = Field(None)
    location: Optional[str] = Field(None)

    title: str = Field(..., description="Draft title shown in UI lists")
    content: Dict[str, Any] = Field(default_factory=dict, description="Generated payload (caption/hashtags/prompt/etc.)")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "campaign_drafts"
        indexes = [
            "user_id",
            "kind",
            "created_at",
            ("user_id", "created_at"),
        ]

