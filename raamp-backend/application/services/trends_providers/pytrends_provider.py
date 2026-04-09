from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from datetime import datetime
from functools import partial
from typing import Any, Dict, List, Optional

from pytrends.request import TrendReq

from application.services.trends_providers.base import TrendsFetchResult, ITrendsProvider
from application.services.trends_providers.schemas import TrendsProviderNormalizedPayload, TrendsSearchInterest


logger = logging.getLogger(__name__)


class PytrendsProvider(ITrendsProvider):
    """
    PyTrends-backed provider.

    This preserves the existing retry/backoff behavior (including 60s base backoff on 429)
    that was previously embedded in `GoogleTrendsService.fetch_trends_data`.
    """

    name = "pytrends"

    def __init__(self) -> None:
        self.pytrends: Optional[TrendReq] = None
        self.last_request_time = datetime.min
        self.min_request_interval = 2.0

    def _get_pytrends(self) -> TrendReq:
        if self.pytrends is None:
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry

            session = requests.Session()
            retry_strategy = Retry(
                total=5,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS"],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("https://", adapter)
            session.mount("http://", adapter)

            self.pytrends = TrendReq(
                hl="en-US",
                tz=360,
                timeout=(10, 25),
                requests_args={"verify": True},
            )
            self.pytrends.requests = session

        return self.pytrends

    async def _rate_limit_delay(self) -> None:
        time_since_last = (datetime.now() - self.last_request_time).total_seconds()
        if time_since_last < self.min_request_interval:
            delay = self.min_request_interval - time_since_last
            logger.info("Rate limiting: waiting %.2fs before next request", delay)
            await asyncio.sleep(delay)
        self.last_request_time = datetime.now()

    async def fetch_trends_data(
        self,
        *,
        keywords: List[str],
        location: str,
        timeframe: str,
    ) -> TrendsFetchResult:
        await self._rate_limit_delay()

        max_retries = 3
        rate_limit_base_delay_s = 60.0

        for attempt in range(max_retries):
            try:
                loop = asyncio.get_event_loop()
                pytrends = self._get_pytrends()

                if not keywords:
                    return TrendsFetchResult(
                        provider=self.name,
                        fallback_from=None,
                        success=False,
                        keywords=[],
                        search_interest={},
                        geo_data={},
                        related_queries={},
                        rising_queries={},
                        error="No keywords provided for analysis",
                        retryable=False,
                    )

                await loop.run_in_executor(
                    None,
                    partial(
                        pytrends.build_payload,
                        keywords,
                        cat=0,
                        timeframe=timeframe,
                        geo=location if location.upper() != "GLOBAL" else "",
                        gprop="",
                    ),
                )

                interest_over_time_df = await loop.run_in_executor(None, pytrends.interest_over_time)
                interest_by_region_df = await loop.run_in_executor(
                    None,
                    partial(
                        pytrends.interest_by_region,
                        resolution="COUNTRY",
                        inc_low_vol=True,
                        inc_geo_code=False,
                    ),
                )
                related_queries_dict = await loop.run_in_executor(None, pytrends.related_queries)

                search_interest: Dict[str, Any] = {}
                if interest_over_time_df is not None and not interest_over_time_df.empty:
                    if "isPartial" in interest_over_time_df.columns:
                        interest_over_time_df = interest_over_time_df.drop("isPartial", axis=1)
                    search_interest = {
                        "dates": interest_over_time_df.index.strftime("%Y-%m-%d").tolist(),
                        "data": interest_over_time_df.to_dict(orient="list"),
                    }

                geo_data: Dict[str, Any] = {}
                if interest_by_region_df is not None and not interest_by_region_df.empty:
                    geo_data = interest_by_region_df.to_dict(orient="index")

                related_queries: Dict[str, Any] = {}
                rising_queries: Dict[str, Any] = {}
                if related_queries_dict:
                    for keyword, queries in related_queries_dict.items():
                        if queries.get("top") is not None and not queries["top"].empty:
                            # Canonical: list[{query, value}]
                            related_queries[keyword] = [
                                {"query": str(r.get("query")), "value": float(r.get("value") or 0.0)}
                                for r in queries["top"].to_dict(orient="records")
                                if isinstance(r, dict) and isinstance(r.get("query"), str)
                            ]
                        if queries.get("rising") is not None and not queries["rising"].empty:
                            rising_queries[keyword] = [
                                {"query": str(r.get("query")), "value": float(r.get("value") or 0.0)}
                                for r in queries["rising"].to_dict(orient="records")
                                if isinstance(r, dict) and isinstance(r.get("query"), str)
                            ]

                normalized = TrendsProviderNormalizedPayload(
                    search_interest=TrendsSearchInterest(
                        dates=[str(d) for d in (search_interest.get("dates") or [])],
                        data={
                            str(k): [float(x) for x in (v or [])]
                            for k, v in (search_interest.get("data") or {}).items()
                            if isinstance(v, list)
                        },
                    ),
                    geo_data=geo_data or {},
                    related_queries=related_queries or {},
                    rising_queries=rising_queries or {},
                ).model_dump()

                return TrendsFetchResult(
                    provider=self.name,
                    fallback_from=None,
                    success=True,
                    keywords=keywords,
                    search_interest=normalized["search_interest"],
                    geo_data=normalized["geo_data"],
                    related_queries=normalized["related_queries"],
                    rising_queries=normalized["rising_queries"],
                    error=None,
                    retryable=False,
                )

            except Exception as e:
                error_msg = str(e)
                if ("429" in error_msg or "Too Many Requests" in error_msg) and attempt < max_retries - 1:
                    wait_time = rate_limit_base_delay_s * (2**attempt)
                    logger.warning(
                        "Google Trends rate limited (429). Backoff: %.0fs (Attempt %d/%d).",
                        wait_time,
                        attempt + 1,
                        max_retries,
                    )
                    await asyncio.sleep(wait_time)
                    self.pytrends = None
                elif "429" in error_msg or "Too Many Requests" in error_msg:
                    logger.error("Max retries exceeded due to rate limiting (429). Marking as failed (no fallback).")
                    return TrendsFetchResult(
                        provider=self.name,
                        fallback_from=None,
                        success=False,
                        keywords=keywords,
                        search_interest={},
                        geo_data={},
                        related_queries={},
                        rising_queries={},
                        error="rate_limited",
                        retryable=True,
                    )
                else:
                    logger.error("Critical error in Google Trends pipeline: %s", error_msg)
                    return TrendsFetchResult(
                        provider=self.name,
                        fallback_from=None,
                        success=False,
                        keywords=keywords,
                        search_interest={},
                        geo_data={},
                        related_queries={},
                        rising_queries={},
                        error=error_msg,
                        retryable=False,
                    )

        return TrendsFetchResult(
            provider=self.name,
            fallback_from=None,
            success=False,
            keywords=keywords,
            search_interest={},
            geo_data={},
            related_queries={},
            rising_queries={},
            error="Max retries exceeded for Google Trends",
            retryable=True,
        )

