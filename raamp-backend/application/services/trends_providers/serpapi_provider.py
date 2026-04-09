from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from config import config
from application.services.trends_providers.base import TrendsFetchResult, ITrendsProvider
from application.services.trends_providers.schemas import TrendsProviderNormalizedPayload, TrendsSearchInterest


logger = logging.getLogger(__name__)


class SerpApiTrendsProvider(ITrendsProvider):
    """
    SerpAPI-backed Google Trends provider.

    SerpAPI exposes multiple engines via https://serpapi.com/search.json.
    For trends, SerpAPI provides a dedicated engine (commonly referred to as `google_trends`).

    This provider normalizes SerpAPI responses into the same shape used by
    `GoogleTrendsService.fetch_trends_data` so downstream pipeline code remains unchanged.

    Notes:
    - If the response shape is unexpected, we fail with `retryable=False` so the selector can
      decide whether to fall back to pytrends (usually only on transient errors).
    - We keep parsing deliberately defensive because SerpAPI payloads can differ by engine/version.
    """

    name = "serpapi"

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: str = "https://serpapi.com/search.json",
        engine: str = "google_trends",
        timeout_s: float = 15.0,
    ) -> None:
        self.api_key = (api_key if api_key is not None else config.SERPAPI_API_KEY).strip()
        self.base_url = base_url
        self.engine = engine
        self.timeout_s = timeout_s

    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def fetch_trends_data(
        self,
        *,
        keywords: List[str],
        location: str,
        timeframe: str,
    ) -> TrendsFetchResult:
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

        if not self.is_configured():
            return TrendsFetchResult(
                provider=self.name,
                fallback_from=None,
                success=False,
                keywords=keywords,
                search_interest={},
                geo_data={},
                related_queries={},
                rising_queries={},
                error="serpapi_not_configured",
                retryable=True,
            )

        # SerpAPI typically expects:
        # - engine=google_trends
        # - q=<query>
        # - geo=<country_code>
        # - date=<timeframe> (varies by engine; we pass through our google-formatted timeframe)
        #
        # Since SerpAPI trends engine conventions can differ, we keep parsing flexible and
        # fall back to pytrends if SerpAPI returns transient failures.
        #
        # Also: some queries return "no results" on SerpAPI even when Google Trends has data
        # for related/broader terms. To avoid failing the whole pipeline, try each keyword
        # from most-specific -> broader until we get a usable payload.
        #
        # Point-density fix: SerpAPI may return weekly granularity for `today 1-m` (≈4 points),
        # which falls below our detector's min_data_points (5). Fetch 3 months instead to
        # ensure enough history for EWMA/Z-score, then the detector filters spikes back down
        # to the originally requested window.
        request_timeframe = "today 3-m" if timeframe == "today 1-m" else timeframe

        def _pick_keywords_for_recovery(all_keywords: List[str]) -> List[str]:
            cleaned = [str(k).strip() for k in (all_keywords or []) if str(k).strip()]
            if not cleaned:
                return []
            # Best-effort: in our pipeline the first keyword is often the user-entered category/broad term.
            # For recovery, try the "top 1-2" niche-map/specialty keywords first (skip the first element).
            preferred = cleaned[1:3]
            return preferred if preferred else cleaned[:2]

        last_err: Optional[str] = None

        async def _attempt(
            *,
            candidate_keywords: List[str],
            geo: str,
            date_param: str,
            geo_relaxed_flag: bool,
        ) -> Optional[TrendsFetchResult]:
            nonlocal last_err
            for q in [k for k in candidate_keywords if str(k).strip()]:
                params: Dict[str, Any] = {
                    "engine": self.engine,
                    "api_key": self.api_key,
                    "q": q,
                }

                # Best-effort geo/timeframe mapping. If the engine ignores unknown params, that's OK.
                if geo:
                    params["geo"] = geo
                if date_param:
                    params["date"] = date_param

                try:
                    async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                        resp = await client.get(self.base_url, params=params)
                except Exception as exc:
                    last_err = f"serpapi_network_error: {exc}"
                    logger.warning("SerpAPI trends request failed (network) for q=%s: %s", q, str(exc))
                    return TrendsFetchResult(
                        provider=self.name,
                        fallback_from=None,
                        success=False,
                        keywords=keywords,
                        search_interest={},
                        geo_data={},
                        related_queries={},
                        rising_queries={},
                        geo_relaxed=geo_relaxed_flag,
                        error=last_err,
                        retryable=True,
                    )

                status = resp.status_code
                if status in (401, 403):
                    return TrendsFetchResult(
                        provider=self.name,
                        fallback_from=None,
                        success=False,
                        keywords=keywords,
                        search_interest={},
                        geo_data={},
                        related_queries={},
                        rising_queries={},
                        geo_relaxed=geo_relaxed_flag,
                        error="serpapi_unauthorized",
                        retryable=False,
                    )
                if status == 429:
                    return TrendsFetchResult(
                        provider=self.name,
                        fallback_from=None,
                        success=False,
                        keywords=keywords,
                        search_interest={},
                        geo_data={},
                        related_queries={},
                        rising_queries={},
                        geo_relaxed=geo_relaxed_flag,
                        error="serpapi_rate_limited",
                        retryable=True,
                    )
                if status >= 500:
                    return TrendsFetchResult(
                        provider=self.name,
                        fallback_from=None,
                        success=False,
                        keywords=keywords,
                        search_interest={},
                        geo_data={},
                        related_queries={},
                        rising_queries={},
                        geo_relaxed=geo_relaxed_flag,
                        error=f"serpapi_server_error_{status}",
                        retryable=True,
                    )

                try:
                    payload = resp.json()
                except Exception as exc:
                    last_err = f"serpapi_malformed_json: {exc}"
                    return TrendsFetchResult(
                        provider=self.name,
                        fallback_from=None,
                        success=False,
                        keywords=keywords,
                        search_interest={},
                        geo_data={},
                        related_queries={},
                        rising_queries={},
                        geo_relaxed=geo_relaxed_flag,
                        error=last_err,
                        retryable=True,
                    )

                # SerpAPI may include explicit error field.
                if isinstance(payload, dict) and payload.get("error"):
                    msg = str(payload.get("error"))
                    m = msg.lower()
                    if "hasn't returned any results" in m or "no results" in m:
                        last_err = f"serpapi_error: {msg}"
                        logger.warning("SerpAPI returned no results for q=%s (will try next keyword)", q)
                        continue
                    retryable = ("quota" in m) or ("limit" in m) or ("rate" in m)
                    return TrendsFetchResult(
                        provider=self.name,
                        fallback_from=None,
                        success=False,
                        keywords=keywords,
                        search_interest={},
                        geo_data={},
                        related_queries={},
                        rising_queries={},
                        geo_relaxed=geo_relaxed_flag,
                        error=f"serpapi_error: {msg}",
                        retryable=retryable,
                    )

                # --- Normalization ---
                search_interest: Dict[str, Any] = {"dates": [], "data": {}}
                geo_data: Dict[str, Any] = {}
                related_queries: Dict[str, Any] = {}
                rising_queries: Dict[str, Any] = {}

                timeline = (
                    payload.get("interest_over_time")
                    or payload.get("timeline_data")
                    or payload.get("timeline")
                    or []
                )
                if isinstance(timeline, list) and timeline:
                    dates: List[str] = []
                    series: List[int] = []
                    for row in timeline:
                        if not isinstance(row, dict):
                            continue
                        d = row.get("date") or row.get("formatted_time") or row.get("time") or row.get("timestamp")
                        v = row.get("value") or row.get("values") or row.get("interest")
                        if isinstance(v, list) and v:
                            v = v[0]
                        if d is not None and v is not None:
                            dates.append(str(d))
                            try:
                                series.append(int(v))
                            except Exception:
                                series.append(0)
                    if dates:
                        search_interest = {"dates": dates, "data": {q: series}}
                        logger.info(
                            "SerpAPI timeline extracted: query=%s geo=%s requested_date=%s sent_date=%s points=%d geo_relaxed=%s",
                            q,
                            geo,
                            timeframe,
                            date_param,
                            len(series),
                            geo_relaxed_flag,
                        )
                    else:
                        last_err = "serpapi_timeline_normalized_empty"
                        logger.warning("SerpAPI returned timeline but extracted 0 points for q=%s (try next keyword)", q)
                        continue
                else:
                    last_err = "serpapi_no_timeline_data"
                    logger.warning("SerpAPI returned 200 but no timeline data for q=%s (try next keyword)", q)
                    continue

                regions = payload.get("interest_by_region") or payload.get("geo_map_data") or payload.get("regions") or []
                if isinstance(regions, list) and regions:
                    for r in regions:
                        if not isinstance(r, dict):
                            continue
                        name = r.get("geoName") or r.get("location") or r.get("region") or r.get("name")
                        val = r.get("value") or r.get("values") or r.get("interest")
                        if isinstance(val, list) and val:
                            val = val[0]
                        if name is not None:
                            geo_data[str(name)] = {"value": val}

                rq = payload.get("related_queries") or payload.get("related_topics") or {}
                if isinstance(rq, dict):
                    # Canonical: keyword -> list[{query, value}]
                    items = []
                    # Common SerpAPI shape: { "top": [{query,value},...], "rising": [...] }
                    if isinstance(rq.get("top"), list):
                        for it in rq.get("top")[:25]:
                            if isinstance(it, dict) and isinstance(it.get("query"), str):
                                items.append({"query": str(it.get("query")), "value": float(it.get("value") or 0.0)})
                            elif isinstance(it, str):
                                items.append({"query": it, "value": 0.0})
                    # Fallback: any list-like fields with dicts
                    if not items:
                        for v in rq.values():
                            if isinstance(v, list):
                                for it in v[:25]:
                                    if isinstance(it, dict) and isinstance(it.get("query"), str):
                                        items.append({"query": str(it.get("query")), "value": float(it.get("value") or 0.0)})
                                    elif isinstance(it, str):
                                        items.append({"query": it, "value": 0.0})
                    related_queries[q] = items

                rising = payload.get("rising_queries") or payload.get("rising") or {}
                if isinstance(rising, dict):
                    items = []
                    if isinstance(rising.get("rising"), list):
                        for it in rising.get("rising")[:25]:
                            if isinstance(it, dict) and isinstance(it.get("query"), str):
                                items.append({"query": str(it.get("query")), "value": float(it.get("value") or 0.0)})
                            elif isinstance(it, str):
                                items.append({"query": it, "value": 0.0})
                    if not items and isinstance(rising.get("top"), list):
                        for it in rising.get("top")[:25]:
                            if isinstance(it, dict) and isinstance(it.get("query"), str):
                                items.append({"query": str(it.get("query")), "value": float(it.get("value") or 0.0)})
                            elif isinstance(it, str):
                                items.append({"query": it, "value": 0.0})
                    if not items:
                        for v in rising.values():
                            if isinstance(v, list):
                                for it in v[:25]:
                                    if isinstance(it, dict) and isinstance(it.get("query"), str):
                                        items.append({"query": str(it.get("query")), "value": float(it.get("value") or 0.0)})
                                    elif isinstance(it, str):
                                        items.append({"query": it, "value": 0.0})
                    rising_queries[q] = items

                has_timeline = (
                    isinstance(search_interest.get("dates"), list)
                    and len(search_interest.get("dates") or []) > 0
                    and isinstance(search_interest.get("data"), dict)
                    and len(search_interest.get("data") or {}) > 0
                )
                if not has_timeline:
                    last_err = last_err or "serpapi_no_usable_timeline"
                    logger.warning("SerpAPI produced no usable timeline for q=%s (try next keyword)", q)
                    continue

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
                    geo_relaxed=geo_relaxed_flag,
                    error=None,
                    retryable=False,
                )

            return None

        # Attempt A: original keyword list, original geo, adjusted timeframe.
        res = await _attempt(
            candidate_keywords=[k for k in (keywords or []) if str(k).strip()],
            geo=location or "",
            date_param=request_timeframe or "",
            geo_relaxed_flag=False,
        )
        if isinstance(res, TrendsFetchResult):
            return res

        # Attempt B: keyword order recovery (top 1-2 niche-map/specialties).
        recovered_keywords = _pick_keywords_for_recovery(keywords)
        if recovered_keywords:
            logger.info("SerpAPI recovery: keyword order recovery (candidates=%s)", recovered_keywords)
            res = await _attempt(
                candidate_keywords=recovered_keywords,
                geo=location or "",
                date_param=request_timeframe or "",
                geo_relaxed_flag=False,
            )
            if isinstance(res, TrendsFetchResult):
                return res

        # Attempt C: timeframe extension (12 months).
        logger.info("SerpAPI recovery: timeframe extension to 12 months (prev=%s)", request_timeframe)
        res = await _attempt(
            candidate_keywords=recovered_keywords or [k for k in (keywords or []) if str(k).strip()],
            geo=location or "",
            date_param="today 12-m",
            geo_relaxed_flag=False,
        )
        if isinstance(res, TrendsFetchResult):
            return res

        # Attempt D: geo relaxation (global).
        logger.info("SerpAPI recovery: geo relaxation to global (prev_geo=%s)", location)
        res = await _attempt(
            candidate_keywords=recovered_keywords or [k for k in (keywords or []) if str(k).strip()],
            geo="",
            date_param="today 12-m",
            geo_relaxed_flag=True,
        )
        if isinstance(res, TrendsFetchResult):
            return res

        # Empty timeline after the recovery ladder often means SerpAPI has no usable timeline
        # for these keywords/geo/timeframe even though Google Trends (pytrends) may still
        # return data. Treat this as retryable so the selector can fall back to PyTrends.
        logger.warning(
            "SerpAPI recovery exhausted: empty/no timeline (requested_date=%s sent_date=%s keywords=%s location=%s)",
            timeframe,
            request_timeframe,
            keywords,
            location,
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
            geo_relaxed=False,
            error=last_err or "serpapi_empty_timeline",
            retryable=True,
        )

