from __future__ import annotations

from beanie import Document
from pydantic import Field
from pymongo import IndexModel
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional


class TrendAIAnalysisModel(Document):
    """
    AI analysis generated for a TrendSignal.

    Stored separately from `trend_detections` so it can be regenerated independently
    without mutating the detection pipeline artifacts.
    """

    # Core fields
    trend_id: str = Field(..., description="Reference to trend_signals.id")
    user_id: str = Field(..., description="User email/id")
    trend_keyword: str = Field(..., description="Top trend keyword this analysis covers")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    status: Literal["pending", "completed", "failed"] = Field(default="pending")

    # Tab 1 — Analysis
    executive_summary: Optional[str] = None
    opportunity_score: Dict[str, int] = Field(
        default_factory=dict, description="urgency/relevance/competition (0-100 each)"
    )
    opportunity_window: Optional[str] = Field(
        None, description="Plain English window status (e.g., 'Extreme Early Access')"
    )
    market_context: Optional[str] = None
    risk_level: Optional[Literal["flash", "sustained", "uncertain"]] = None
    risk_explanation: Optional[str] = None
    competitor_gap: Optional[bool] = None

    # Tab 2 — Strategy
    content_angles: List[str] = Field(default_factory=list)
    platform_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    hashtag_pack: Dict[str, List[str]] = Field(
        default_factory=dict, description="primary/secondary/niche hashtag lists"
    )
    posting_window: Optional[str] = None

    # Intelligence grid cards (same LLM call as analysis)
    campaign_ideas: List[Dict[str, Any]] = Field(default_factory=list)
    content_format_recommendation: Dict[str, Any] = Field(default_factory=dict)
    growth_hacks: List[str] = Field(default_factory=list)

    # Meta
    brand_voice_used: Dict[str, Any] = Field(default_factory=dict)
    model_version: Optional[str] = None
    error_message: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "trend_ai_analysis"
        indexes = [
            IndexModel([("trend_id", 1), ("user_id", 1)], unique=True),
            IndexModel([("user_id", 1), ("generated_at", -1)]),
            IndexModel([("trend_id", 1), ("generated_at", -1)]),
        ]

