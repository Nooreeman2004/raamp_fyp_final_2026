"""
Event Signal Service
===================
Generates an "event catalyst" score using Google News RSS headlines.

Design goals:
- Bounded work (top 2-3 keywords)
- Fast (RSS only)
- Safe: never raises; returns empty signal on failure
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from integrations.events.google_news_client import GoogleNewsClient, GoogleNewsItem

logger = logging.getLogger(__name__)


class EventSignalService:
    # simple source quality allowlist (very lightweight; can expand)
    _HIGH_QUALITY_SOURCES = {
        "reuters",
        "associated press",
        "ap news",
        "bbc",
        "the guardian",
        "al jazeera",
        "bloomberg",
        "financial times",
        "the new york times",
        "the washington post",
        "cnn",
    }

    def __init__(self):
        self.client = GoogleNewsClient(timeout_s=5.0)

    @staticmethod
    def _recency_factor(published_at: Optional[str]) -> float:
        """
        published within 24h -> 1.0, within 7d -> 0.3..1.0, older/unknown -> 0.0..0.2
        """
        if not published_at:
            return 0.2
        try:
            # published_at could be RFC822 string; we only reliably score ISO values from client when parsed.
            dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age_h = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
            if age_h <= 24:
                return 1.0
            if age_h <= 24 * 7:
                return max(0.3, 1.0 - ((age_h - 24) / (24 * 6)) * 0.7)
            return 0.0
        except Exception:
            return 0.2

    @classmethod
    def _source_quality(cls, source: str) -> float:
        s = (source or "").strip().lower()
        if not s:
            return 0.4
        if any(hq in s for hq in cls._HIGH_QUALITY_SOURCES):
            return 1.0
        return 0.6

    @staticmethod
    def _overlap_boost(keyword: str, title: str) -> float:
        kw = (keyword or "").strip().lower()
        t = (title or "").strip().lower()
        if not kw or not t:
            return 0.0
        return 1.0 if kw in t else 0.2

    @staticmethod
    def _specialty_boost(specialties: List[str], title: str) -> float:
        """
        Boost when business specialties appear in the headline.
        Returns 0.0..1.0.
        """
        if not specialties:
            return 0.0
        t = (title or "").strip().lower()
        if not t:
            return 0.0
        hits = 0
        for s in specialties[:5]:
            ss = (s or "").strip().lower()
            if ss and ss in t:
                hits += 1
        if hits <= 0:
            return 0.0
        return min(1.0, 0.3 + (hits * 0.2))

    async def get_event_signal(
        self,
        *,
        keywords: List[str],
        location: str,
        niche: str,
        specialties: Optional[List[str]] = None,
        max_keywords: int = 3,
    ) -> Dict[str, Any]:
        """
        Returns:
          { event_score: float(0..100), event_items: list[dict], is_real_events: bool }
        Never raises.
        """
        try:
            # Bound keywords: take first N unique non-empty
            seen = set()
            top: List[str] = []
            for k in (keywords or []):
                kk = (k or "").strip()
                if not kk:
                    continue
                lk = kk.lower()
                if lk in seen:
                    continue
                seen.add(lk)
                top.append(kk)
                if len(top) >= max_keywords:
                    break

            if not top:
                return {"event_score": 0.0, "event_items": [], "is_real_events": False}

            items: List[GoogleNewsItem] = await self.client.fetch_items(
                keywords=top,
                location=location or "",
                category=niche or "",
                max_per_keyword=10,
            )

            scored: List[Dict[str, Any]] = []
            for it in items:
                rec = self._recency_factor(it.published_at)
                srcq = self._source_quality(it.source)
                # use best overlap across the selected top keywords
                ov = max(self._overlap_boost(k, it.title) for k in top)
                sp = self._specialty_boost(list(specialties or []), it.title)
                score = (rec * 0.40) + (ov * 0.30) + (srcq * 0.20) + (sp * 0.10)
                scored.append(
                    {
                        "title": it.title,
                        "source": it.source,
                        "published_at": it.published_at,
                        "url": it.url,
                        "relevance_score": it.relevance_score,
                        "signal_score": round(score, 3),
                    }
                )

            scored.sort(key=lambda x: x["signal_score"], reverse=True)
            top_events = scored[:5]

            # Aggregate: scale average signal score to 0..100
            if not top_events:
                return {"event_score": 0.0, "event_items": [], "is_real_events": True}

            avg = sum(e["signal_score"] for e in top_events) / len(top_events)
            event_score = round(min(100.0, max(0.0, avg * 100.0)), 2)

            return {
                "event_score": event_score,
                "event_items": top_events,
                "is_real_events": True,
            }
        except Exception as e:
            logger.warning("EventSignalService failed (non-fatal): %s", str(e))
            return {"event_score": 0.0, "event_items": [], "is_real_events": False}

