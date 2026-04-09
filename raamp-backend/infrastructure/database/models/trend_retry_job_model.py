"""
Trend Retry Job Model
====================
Persistent retry queue entries for trend processing jobs.

Purpose:
- Avoid returning synthetic data on transient provider failures (e.g. Google Trends 429).
- Persist retry intent across process restarts (unlike in-memory scheduling).
"""

from __future__ import annotations

from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional


class TrendRetryJobStatus:
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TrendRetryJobModel(Document):
    """MongoDB document for trend retry jobs."""

    trend_id: str = Field(..., description="TrendSignal id to retry")
    user_email: str = Field(..., description="User email for ownership/auditing")

    attempt: int = Field(default=0, description="0-based attempt counter")
    max_attempts: int = Field(default=3, description="Maximum retry attempts")

    run_at: datetime = Field(..., description="When this retry is eligible to run (UTC)")
    status: str = Field(default=TrendRetryJobStatus.PENDING, description="Retry job status")

    last_error: Optional[str] = Field(None, description="Last error message")
    last_run_at: Optional[datetime] = Field(None, description="Last execution timestamp (UTC)")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "trend_retry_jobs"
        indexes = [
            "trend_id",
            "user_email",
            "status",
            "run_at",
            [("status", 1), ("run_at", 1)],
        ]

