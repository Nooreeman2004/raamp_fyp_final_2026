# Infrastructure Layer - Trend Cache MongoDB Model (TTL-based)
from __future__ import annotations

from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Any, Optional

from pymongo import IndexModel


class TrendCacheModel(Document):
    """
    Generic TTL cache for trend-related upstream calls.

    Why DB-backed:
    - Survives process restarts
    - Shared across multi-worker deployments
    - Reduces duplicate external API calls / quota waste

    TTL:
    - Entries auto-expire via MongoDB TTL index on `expires_at`
    """

    namespace: str = Field(..., description="Cache namespace (e.g., google_trends, trending_now)")
    key: str = Field(..., description="Cache key (namespace-scoped)")

    value: Any = Field(..., description="Cached payload (JSON-serializable)")
    meta: Optional[dict[str, Any]] = Field(default=None, description="Optional metadata (provider, etc.)")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(..., description="UTC expiry timestamp (TTL index)")

    class Settings:
        name = "trend_cache"
        indexes = [
            IndexModel([("namespace", 1), ("key", 1)], unique=True),
            IndexModel([("expires_at", 1)], expireAfterSeconds=0),
            IndexModel([("namespace", 1), ("expires_at", 1)]),
        ]

