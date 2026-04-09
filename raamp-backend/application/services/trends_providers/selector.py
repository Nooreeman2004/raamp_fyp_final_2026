from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from config import config
from application.services.trends_providers.base import TrendsFetchResult
from application.services.trends_providers.pytrends_provider import PytrendsProvider
from application.services.trends_providers.serpapi_provider import SerpApiTrendsProvider
from application.services.trends_providers.schemas import (
    TrendsProviderNormalizedPayload,
    TrendsRelatedQueries,
    TrendsRisingQueries,
)
from infrastructure.utils.obs import emit_event


logger = logging.getLogger(__name__)


def _provider_order(mode: str, serpapi_configured: bool) -> Tuple[str, ...]:
    m = (mode or "auto").strip().lower()
    if m == "serpapi":
        return ("serpapi", "pytrends")
    if m == "pytrends":
        return ("pytrends",)
    # auto
    return ("serpapi", "pytrends") if serpapi_configured else ("pytrends",)


class TrendsProviderSelector:
    """
    Selects a trends provider and applies conservative fallback rules.

    Fallback occurs only when the primary fails with retryable/transient errors:
    - rate limiting / quota (429)
    - network failures
    - provider 5xx
    """

    def __init__(self) -> None:
        self.serpapi = SerpApiTrendsProvider()
        self.pytrends = PytrendsProvider()

    async def fetch_trends_data(
        self,
        *,
        keywords: List[str],
        location: str,
        timeframe: str,
        provider_mode: Optional[str] = None,
    ) -> TrendsFetchResult:
        mode = provider_mode or getattr(config, "TRENDS_PROVIDER", "auto")
        order = _provider_order(mode, self.serpapi.is_configured())

        last: Optional[TrendsFetchResult] = None
        for name in order:
            if name == "serpapi":
                res = await self.serpapi.fetch_trends_data(
                    keywords=keywords, location=location, timeframe=timeframe
                )
            else:
                res = await self.pytrends.fetch_trends_data(
                    keywords=keywords, location=location, timeframe=timeframe
                )

            if res.success:
                # Contract assertion: providers must return normalized, fully-populated shapes.
                try:
                    TrendsProviderNormalizedPayload(
                        search_interest=res.search_interest or {},
                        geo_data=res.geo_data or {},
                        related_queries=res.related_queries or {},
                        rising_queries=res.rising_queries or {},
                    )
                    # Stricter normalization for ancillary fields:
                    # - related_queries/rising_queries must be keyword->[{query,value},...]
                    TrendsRelatedQueries.model_validate(res.related_queries or {})
                    TrendsRisingQueries.model_validate(res.rising_queries or {})
                except Exception as e:
                    # Treat schema violations as non-retryable provider bugs.
                    logger.error("Provider returned non-normalized payload (provider=%s): %s", res.provider, str(e))
                    res = TrendsFetchResult(
                        provider=res.provider,
                        fallback_from=None,
                        success=False,
                        keywords=res.keywords,
                        search_interest={},
                        geo_data={},
                        related_queries={},
                        rising_queries={},
                        geo_relaxed=getattr(res, "geo_relaxed", False),
                        error="provider_schema_violation",
                        retryable=False,
                    )
                    last = res
                    break

                # Central validation (provider-agnostic): ensure time-series is usable.
                ok, reason = _validate_normalized_timeseries(res.search_interest)
                if not ok:
                    last = TrendsFetchResult(
                        provider=res.provider,
                        fallback_from=None,
                        success=False,
                        keywords=res.keywords,
                        search_interest={},
                        geo_data={},
                        related_queries={},
                        rising_queries={},
                        geo_relaxed=getattr(res, "geo_relaxed", False),
                        error=f"invalid_provider_payload:{reason}",
                        retryable=True,
                    )
                    logger.warning(
                        "Provider returned non-useful payload: provider=%s reason=%s (will fallback if possible)",
                        res.provider,
                        reason,
                    )
                    # continue loop to allow fallback provider
                    continue
                if last and last.provider != res.provider:
                    logger.info("Trends provider fallback succeeded: %s -> %s", last.provider, res.provider)
                    emit_event(
                        "trends.provider.fallback",
                        from_provider=last.provider,
                        to_provider=res.provider,
                        location=location,
                        timeframe=timeframe,
                        keywords_count=len(keywords or []),
                    )
                    res = TrendsFetchResult(
                        provider=res.provider,
                        fallback_from=last.provider,
                        success=True,
                        keywords=res.keywords,
                        search_interest=res.search_interest,
                        geo_data=res.geo_data,
                        related_queries=res.related_queries,
                        rising_queries=res.rising_queries,
                        geo_relaxed=getattr(res, "geo_relaxed", False),
                        error=res.error,
                        retryable=res.retryable,
                    )
                return res

            last = res
            logger.warning(
                "Trends provider failed: provider=%s retryable=%s error=%s",
                res.provider,
                res.retryable,
                res.error,
            )

            # Only fallback if retryable and there is another provider available.
            if not res.retryable:
                break

        return last or TrendsFetchResult(
            provider="none",
            fallback_from=None,
            success=False,
            keywords=keywords,
            search_interest={},
            geo_data={},
            related_queries={},
            rising_queries={},
            geo_relaxed=False,
            error="no_provider_attempted",
            retryable=True,
        )


def _validate_normalized_timeseries(search_interest: dict) -> tuple[bool, str]:
    """
    Validate normalized provider output:
    - dates must be non-empty list
    - data must be dict with list values, each exactly len(dates)
    - each series must not be all zeros/nulls
    """
    if not isinstance(search_interest, dict):
        return False, "search_interest_not_dict"
    dates = search_interest.get("dates")
    data = search_interest.get("data")
    if not isinstance(dates, list) or len(dates) == 0:
        return False, "empty_dates"
    if not isinstance(data, dict) or len(data) == 0:
        return False, "empty_data"
    n = len(dates)
    for k, values in data.items():
        if not isinstance(values, list) or len(values) != n:
            return False, f"length_mismatch:{k}"
        cleaned = [v for v in values if v is not None]
        if not cleaned:
            return False, f"all_null:{k}"
        try:
            if all(float(v) == 0.0 for v in cleaned):
                return False, f"all_zero:{k}"
        except Exception:
            return False, f"non_numeric:{k}"
    return True, "ok"

