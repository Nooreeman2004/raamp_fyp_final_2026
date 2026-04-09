"""
Diagnostics: Google Trends (PyTrends)
------------------------------------
Verifies that PyTrends can connect and returns non-empty, non-error data.

Why this matters:
- If PyTrends is rate-limited (429) or blocked, the entire trend pipeline becomes stale.
- We fail closed in production; this test identifies whether the upstream source is healthy.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import List, Dict, Any

from dotenv import load_dotenv
from pytrends.request import TrendReq

from _diag_utils import DiagResult, safe_main


def _classify_error(msg: str) -> str:
    m = (msg or "").lower()
    if "429" in m or "too many requests" in m or "rate" in m and "limit" in m:
        return "rate_limited_429"
    if "timeout" in m:
        return "timeout"
    if "connection" in m or "dns" in m or "name or service not known" in m:
        return "connection_error"
    return "unknown_error"


def run() -> DiagResult:
    load_dotenv()

    # Keep keywords short + common to avoid "no data" false negatives.
    # You can override via env var for your business/niche.
    kws_env = os.getenv("DIAG_PYTRENDS_KEYWORDS", "").strip()
    keywords: List[str] = [k.strip() for k in kws_env.split(",") if k.strip()] if kws_env else [
        "cold brew",
        "artisan coffee",
        "eid outfit ideas",
    ]
    keywords = keywords[:3]

    geo = os.getenv("GOOGLE_TRENDS_GEO", os.getenv("DIAG_PYTRENDS_GEO", "PK")).strip() or "PK"
    timeframe = os.getenv("DIAG_PYTRENDS_TIMEFRAME", "today 1-m")

    details: Dict[str, Any] = {
        "keywords": keywords,
        "geo": geo,
        "timeframe": timeframe,
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
    }

    try:
        pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25), requests_args={"verify": True})
        pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo, gprop="")
        df = pytrends.interest_over_time()

        row_count = int(getattr(df, "shape", (0, 0))[0]) if df is not None else 0
        col_count = int(getattr(df, "shape", (0, 0))[1]) if df is not None else 0
        details["interest_over_time_rows"] = row_count
        details["interest_over_time_cols"] = col_count

        if df is None or row_count <= 0 or col_count <= 0:
            return DiagResult(
                name="Google Trends",
                status="FAIL",
                reason="Empty response (no rows returned)",
                details=details,
            )

        # Raw sample (small) – safe to print
        try:
            details["sample_head"] = df.head(3).to_dict()  # type: ignore[attr-defined]
        except Exception:
            details["sample_head"] = "unavailable"

        return DiagResult(
            name="Google Trends",
            status="PASS",
            reason="PyTrends returned non-empty interest_over_time data",
            details=details,
        )

    except Exception as e:
        kind = _classify_error(str(e))
        details["error_kind"] = kind
        # Do not leak full upstream error unless debug enabled.
        if os.getenv("DIAG_DEBUG", "").lower() in ("1", "true", "yes"):
            details["error"] = str(e)

        return DiagResult(
            name="Google Trends",
            status="FAIL",
            reason=f"Request failed ({kind})",
            details=details,
        )


if __name__ == "__main__":
    raise SystemExit(safe_main(run, "Google Trends"))

