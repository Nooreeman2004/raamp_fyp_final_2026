from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol


@dataclass(frozen=True)
class TrendsFetchResult:
    provider: str
    success: bool
    keywords: List[str]
    search_interest: Dict[str, Any]
    geo_data: Dict[str, Any]
    related_queries: Dict[str, Any]
    rising_queries: Dict[str, Any]
    geo_relaxed: bool = False
    fallback_from: Optional[str] = None
    error: Optional[str] = None
    retryable: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "fallback_from": self.fallback_from,
            "success": self.success,
            "keywords": self.keywords,
            "search_interest": self.search_interest,
            "geo_data": self.geo_data,
            "related_queries": self.related_queries,
            "rising_queries": self.rising_queries,
            "geo_relaxed": self.geo_relaxed,
            "error": self.error,
            "retryable": self.retryable,
        }


class ITrendsProvider(Protocol):
    name: str

    async def fetch_trends_data(
        self,
        *,
        keywords: List[str],
        location: str,
        timeframe: str,
    ) -> TrendsFetchResult: ...

