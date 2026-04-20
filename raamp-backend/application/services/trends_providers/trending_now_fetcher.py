from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from config import config
from infrastructure.database.models.trend_cache_model import TrendCacheModel

logger = logging.getLogger(__name__)

_DEBUG_TRENDING = ("1", "true", "True", "yes", "YES")


class TrendingNowFetcher:
    """
    SerpAPI discovery helper.

    Uses SerpAPI engine=google_trends_trending_now to fetch currently trending terms
    for a geo. Category filtering may not be supported by SerpAPI; we treat it as best-effort.
    """

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: str = "https://serpapi.com/search.json",
        engine: str = "google_trends_trending_now",
        timeout_s: float = 15.0,
        ttl_s: int = 600,
        default_limit: int = 8,
    ) -> None:
        self.api_key = (api_key if api_key is not None else config.SERPAPI_API_KEY).strip()
        self.base_url = base_url
        self.engine = engine
        self.timeout_s = timeout_s
        self.ttl_s = ttl_s
        self.default_limit = default_limit

    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def fetch_terms(
        self,
        *,
        geo: str,
        category: str = "",
        limit: Optional[int] = None,
        use_cache: bool = True,
    ) -> List[str]:
        if not self.is_configured():
            logger.info("TrendingNowFetcher not configured (missing SERPAPI_API_KEY).")
            return []

        geo_norm = (geo or "").strip().upper()
        if not geo_norm:
            geo_norm = ""

        cat_norm = (category or "").strip()
        if cat_norm.lower() == "all":
            cat_norm = ""

        n = int(limit or self.default_limit)
        n = max(1, min(n, 20))

        cache_key = f"geo={geo_norm}|cat={cat_norm.lower()}|n={n}"
        if use_cache:
            try:
                now = datetime.utcnow()
                doc = await TrendCacheModel.find_one(
                    {
                        "namespace": "trending_now",
                        "key": cache_key,
                        "expires_at": {"$gt": now},
                    }
                )
                if doc and isinstance(doc.value, dict):
                    terms = doc.value.get("terms")
                    if isinstance(terms, list) and terms:
                        return [str(t) for t in terms if str(t).strip()]
            except Exception as e:
                logger.warning("Trending-now DB cache read failed (non-fatal): %s", str(e))

        params: Dict[str, Any] = {
            "engine": self.engine,
            "api_key": self.api_key,
        }
        if geo_norm:
            params["geo"] = geo_norm
        # Best-effort: some SerpAPI engines support category; if ignored, response still works.
        if cat_norm:
            params["category"] = cat_norm

        try:
            async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                resp = await client.get(self.base_url, params=params)
        except Exception as exc:
            logger.warning("Trending-now fetch failed (network): %s", str(exc))
            return []

        # Parse payload even on non-200 for diagnostics (no URL/key logged).
        payload: Any = None
        try:
            payload = resp.json()
        except Exception as exc:
            logger.warning("Trending-now payload malformed JSON: %s", str(exc))
            payload = None

        # Temporary diagnostics (gated): log payload keys + a single sample entry.
        # Enable with RAAMP_DEBUG_TRENDING=1
        try:
            import os

            if os.getenv("RAAMP_DEBUG_TRENDING", "").strip() in _DEBUG_TRENDING and isinstance(payload, dict):
                logger.debug("trending_now raw keys: %s", list(payload.keys()))
                # Prefer sampling the actual list we parse from.
                sample_src = payload.get("trending_searches") or payload.get("daily_trends") or payload.get("trends")
                sample = None
                if isinstance(sample_src, list):
                    sample = sample_src[:1]
                elif isinstance(sample_src, dict):
                    # Avoid dumping deep structures; show keys only
                    sample = {"keys": list(sample_src.keys())}
                else:
                    sample = sample_src
                logger.debug("trending_now first entry sample: %s", sample)
        except Exception:
            pass

        if resp.status_code in (401, 403):
            logger.warning("Trending-now fetch unauthorized (status=%s).", resp.status_code)
            return []
        if resp.status_code == 429:
            logger.warning("Trending-now fetch rate limited (429).")
            return []
        if resp.status_code >= 500:
            logger.warning("Trending-now fetch server error (status=%s).", resp.status_code)
            return []

        if payload is None:
            return []

        terms = self._extract_terms(payload, limit=n)
        if terms and use_cache:
            try:
                now = datetime.utcnow()
                expires_at = now + timedelta(seconds=int(self.ttl_s))
                await TrendCacheModel.find_one(
                    {"namespace": "trending_now", "key": cache_key}
                ).upsert(
                    {"$set": {
                        "value": {"terms": list(terms)},
                        "meta": {"ttl_s": int(self.ttl_s), "geo": geo_norm, "category": cat_norm, "limit": n},
                        "expires_at": expires_at,
                        "created_at": now,
                    }},
                    on_insert=TrendCacheModel(
                        namespace="trending_now",
                        key=cache_key,
                        value={"terms": list(terms)},
                        meta={"ttl_s": int(self.ttl_s), "geo": geo_norm, "category": cat_norm, "limit": n},
                        expires_at=expires_at,
                        created_at=now,
                    ),
                )
            except Exception as e:
                logger.warning("Trending-now DB cache write failed (non-fatal): %s", str(e))
        logger.info("Trending-now discovery: geo=%s category=%s terms=%d", geo_norm or "GLOBAL", cat_norm or "∅", len(terms))
        return terms

    def _extract_terms(self, payload: Any, *, limit: int) -> List[str]:
        """
        Best-effort normalization for SerpAPI trending-now shapes.
        We accept a variety of keys to reduce brittleness.
        """
        if not isinstance(payload, dict):
            return []

        # Plan / engine errors
        if isinstance(payload.get("error"), str):
            logger.warning("Trending-now engine error: %s", payload.get("error"))
            return []

        # Common-ish candidates across SerpAPI formats
        candidates: Any = (
            payload.get("trending_searches")
            or payload.get("daily_trends")
            or payload.get("trending_now")
            or payload.get("trends")
            or payload.get("searches")
            or []
        )

        terms: List[str] = []
        seen = set()

        def _add(term: str) -> None:
            t = (term or "").strip()
            if not t:
                return
            k = t.lower()
            if k in seen:
                return
            seen.add(k)
            terms.append(t)

        def _extract_from_item(item: Any) -> None:
            if item is None or len(terms) >= limit:
                return
            if isinstance(item, str):
                _add(item)
                return
            if not isinstance(item, dict):
                return

            # Common direct fields
            for key in ("query", "title", "name", "search_term", "term"):
                if key in item and isinstance(item.get(key), str):
                    _add(str(item.get(key)))
                    return

            # Nested shape: {"searches": [{"query": "..."}]}
            nested = item.get("searches") or item.get("items") or item.get("trends")
            if isinstance(nested, list):
                for nitem in nested:
                    _extract_from_item(nitem)
                    if len(terms) >= limit:
                        return

            # Some formats store the actual phrase under a dict like {"title": {"query": "..."}}
            for key in ("title", "trend", "search"):
                v = item.get(key)
                if isinstance(v, dict):
                    _extract_from_item(v)
                    return

        # candidates can be list, dict, or something else.
        if isinstance(candidates, list):
            for item in candidates:
                _extract_from_item(item)
                if len(terms) >= limit:
                    break
        elif isinstance(candidates, dict):
            # Sometimes the list lives under a nested key
            nested_list = (
                candidates.get("searches")
                or candidates.get("trending_searches")
                or candidates.get("trends")
                or candidates.get("items")
                or []
            )
            if isinstance(nested_list, list):
                for item in nested_list:
                    _extract_from_item(item)
                    if len(terms) >= limit:
                        break

        return terms[:limit]

