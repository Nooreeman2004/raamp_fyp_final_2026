"""
Google News RSS Client
=====================
Fetches lightweight "event signal" headlines from Google News RSS.

Constraints (production readiness):
- Strict 5s timeout
- No retries
- Bounded max items per keyword
- TTL cache to avoid repeated RSS pulls
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import quote_plus

import httpx
import feedparser
from cachetools import TTLCache
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# Shared cache across users: (keyword, location, gl) -> list[items]
_rss_cache: TTLCache = TTLCache(maxsize=2048, ttl=30 * 60)  # 30 minutes


@dataclass
class GoogleNewsItem:
    title: str
    source: str
    published_at: Optional[str]
    url: str
    relevance_score: float


class GoogleNewsClient:
    def __init__(self, *, timeout_s: float = 5.0):
        self.timeout_s = timeout_s

    @staticmethod
    def _geo_code(location: Optional[str]) -> str:
        """
        Google News RSS expects gl/ceid. Keep it simple: 2-letter country code.
        """
        loc = (location or "").strip().upper()
        if len(loc) == 2 and loc.isalpha():
            return loc
        return "PK"

    def _build_rss_url(self, *, keyword: str, location: str, gl: str) -> str:
        # Query string: keyword + location term (not geo scoping; that's gl/ceid)
        q = f"{keyword} {location}".strip()
        return (
            "https://news.google.com/rss/search"
            f"?q={quote_plus(q)}&hl=en&gl={gl}&ceid={gl}:en"
        )

    @staticmethod
    def _dedupe(items: List[GoogleNewsItem]) -> List[GoogleNewsItem]:
        """
        Deduplicate by title similarity (simple, bounded).
        """
        out: List[GoogleNewsItem] = []
        for it in items:
            t = (it.title or "").strip().lower()
            if not t:
                continue
            is_dup = False
            for ex in out:
                ratio = SequenceMatcher(None, t, (ex.title or "").strip().lower()).ratio()
                if ratio >= 0.90:
                    is_dup = True
                    break
            if not is_dup:
                out.append(it)
        return out

    @staticmethod
    def _parse_published(entry: dict) -> Optional[datetime]:
        # feedparser provides published_parsed as time.struct_time sometimes
        parsed = entry.get("published_parsed")
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc)
            except Exception:
                return None
        pub = entry.get("published") or entry.get("updated")
        if isinstance(pub, str) and pub:
            # best-effort: keep as string only if parsing fails
            return None
        return None

    @staticmethod
    def _relevance_score(*, keyword: str, title: str, published_dt: Optional[datetime]) -> float:
        """
        Local relevance score: keyword overlap + recency.
        Score range roughly 0..1.
        """
        kw = (keyword or "").strip().lower()
        text = (title or "").strip().lower()
        overlap = 1.0 if kw and kw in text else 0.3

        rec = 0.2
        if published_dt:
            age_h = (datetime.now(timezone.utc) - published_dt).total_seconds() / 3600
            if age_h <= 24:
                rec = 1.0
            elif age_h <= 24 * 7:
                rec = max(0.3, 1.0 - ((age_h - 24) / (24 * 6)) * 0.7)  # decays to ~0.3
            else:
                rec = 0.0

        return round(min(1.0, max(0.0, (overlap * 0.6) + (rec * 0.4))), 3)

    async def fetch_items(
        self,
        *,
        keywords: List[str],
        location: str,
        category: str = "",
        max_per_keyword: int = 10,
    ) -> List[GoogleNewsItem]:
        """
        Returns deduped list of items across keywords.
        """
        gl = self._geo_code(location)
        items: List[GoogleNewsItem] = []

        async with httpx.AsyncClient(timeout=self.timeout_s, follow_redirects=True) as client:
            for kw in keywords:
                kw_norm = (kw or "").strip()
                if not kw_norm:
                    continue

                cache_key = (kw_norm.lower(), (location or "").strip().lower(), gl)
                cached = _rss_cache.get(cache_key)
                if cached is not None:
                    items.extend(cached)
                    continue

                url = self._build_rss_url(keyword=kw_norm, location=location or "", gl=gl)
                try:
                    r = await client.get(url)
                    r.raise_for_status()
                    feed = feedparser.parse(r.text)
                except Exception as e:
                    logger.info("GoogleNews RSS fetch failed for kw=%s gl=%s: %s", kw_norm, gl, str(e))
                    _rss_cache[cache_key] = []
                    continue

                raw_entries = list(feed.entries or [])[:max_per_keyword]
                per_kw_items: List[GoogleNewsItem] = []
                for ent in raw_entries:
                    title = (ent.get("title") or "").strip()
                    link = (ent.get("link") or "").strip()
                    source = ""
                    if isinstance(ent.get("source"), dict):
                        source = (ent["source"].get("title") or "").strip()
                    if not source:
                        # feedparser sometimes provides "author"
                        source = (ent.get("author") or "").strip()
                    published_dt = self._parse_published(ent)
                    published_at = None
                    if published_dt:
                        published_at = published_dt.isoformat()
                    elif isinstance(ent.get("published"), str):
                        published_at = ent.get("published")

                    score = self._relevance_score(keyword=kw_norm, title=title, published_dt=published_dt)
                    if not title or not link:
                        continue
                    per_kw_items.append(
                        GoogleNewsItem(
                            title=title,
                            source=source or "Unknown",
                            published_at=published_at,
                            url=link,
                            relevance_score=score,
                        )
                    )

                per_kw_items = self._dedupe(per_kw_items)
                _rss_cache[cache_key] = per_kw_items
                items.extend(per_kw_items)

        items = self._dedupe(items)
        items.sort(key=lambda x: x.relevance_score, reverse=True)
        return items

