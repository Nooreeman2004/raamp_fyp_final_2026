"""
Diagnostics: Google News RSS
---------------------------
Verifies that Google News RSS is reachable and returns parseable items.

Why this matters:
- EventSignalService depends on RSS headlines to compute event catalysts.
- If RSS is blocked, event scores should be unavailable (fail-closed), not fabricated.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import List, Dict, Any

from dotenv import load_dotenv

from _diag_utils import DiagResult, safe_main


def run() -> DiagResult:
    load_dotenv()

    kws_env = os.getenv("DIAG_RSS_KEYWORDS", "").strip()
    keywords: List[str] = [k.strip() for k in kws_env.split(",") if k.strip()] if kws_env else [
        "cold brew",
        "artisan coffee",
        "eid outfit ideas",
    ]
    keywords = keywords[:3]
    location = os.getenv("DIAG_RSS_LOCATION", "Pakistan")
    niche = os.getenv("DIAG_RSS_NICHE", "marketing")

    details: Dict[str, Any] = {
        "keywords": keywords,
        "location": location,
        "niche": niche,
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
    }

    try:
        from integrations.events.google_news_client import GoogleNewsClient

        client = GoogleNewsClient(timeout_s=5.0)
        # GoogleNewsClient.fetch_items is async; run it with asyncio.
        import asyncio

        async def _go():
            return await client.fetch_items(
                keywords=keywords,
                location=location,
                category=niche,
                max_per_keyword=10,
            )

        items = asyncio.run(_go())

        details["items_count"] = len(items or [])
        if not items:
            return DiagResult(
                name="Google News RSS",
                status="FAIL",
                reason="No RSS items returned (empty feed or blocked)",
                details=details,
            )

        # Print a tiny sample
        sample = []
        for it in items[:3]:
            sample.append(
                {
                    "title": getattr(it, "title", None),
                    "source": getattr(it, "source", None),
                    "published_at": getattr(it, "published_at", None),
                    "url": getattr(it, "url", None),
                }
            )
        details["sample_items"] = sample

        return DiagResult(
            name="Google News RSS",
            status="PASS",
            reason="RSS returned parseable items",
            details=details,
        )

    except Exception as e:
        if os.getenv("DIAG_DEBUG", "").lower() in ("1", "true", "yes"):
            details["error"] = str(e)
        return DiagResult(
            name="Google News RSS",
            status="FAIL",
            reason="Request/parse failed",
            details=details,
        )


if __name__ == "__main__":
    raise SystemExit(safe_main(run, "Google News RSS"))

