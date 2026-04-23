"""
infrastructure/database/models/comment_analysis_model.py
======================================================
Persistence for Comment Spam and Sentiment Analysis results.
"""

from __future__ import annotations
from beanie import Document
from datetime import datetime
from pydantic import Field
from typing import Optional


class CommentAnalysisModel(Document):
    """
    Stores analysis results for a specific Instagram/Facebook comment.
    Used to cache results and avoid re-running ML models on every view.
    """
    
    comment_id: str = Field(..., description="External platform comment ID (IG/FB)")
    post_id: str = Field(..., description="External platform post/media ID")
    text: str = Field(..., description="The content of the comment at the time of analysis")
    
    is_spam: bool = Field(default=False)
    spam_confidence: float = Field(default=0.0)
    
    sentiment: str = Field(default="NEUTRAL", description="POSITIVE | NEUTRAL | NEGATIVE")
    sentiment_score: float = Field(default=0.0)
    
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "comment_analysis"
        indexes = [
            "comment_id",
            "post_id",
            [("post_id", 1), ("analyzed_at", -1)],
        ]
