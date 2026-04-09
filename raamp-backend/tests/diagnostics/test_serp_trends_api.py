"""
Diagnostics: SerpAPI Google Trends engine
----------------------------------------
Verifies that SerpAPI's Google Trends engine responds for a simple query.

This is intentionally lightweight: it confirms credentials + basic connectivity.
The production pipeline still normalizes/validates the shape and can fall back to pytrends.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict

import httpx
from dotenv import load_dotenv

from _diag_utils import DiagResult, safe_main


def run() -> DiagResult:
    load_dotenv()

    api_key = os.getenv("SERPAPI_API_KEY", "").strip()
    if not api_key:
        return DiagResult(
            name="SerpAPI_Trends",
            status="FAIL",
            reason="Missing SERPAPI_API_KEY in environment",
            details={"timestamp_utc": datetime.utcnow().isoformat() + "Z"},
        )

    q = os.getenv("DIAG_SERPAPI_TRENDS_QUERY", "fashion trends").strip() or "fashion trends"
    geo = os.getenv("DIAG_SERPAPI_TRENDS_GEO", "PK").strip() or "PK"
    date = os.getenv("DIAG_SERPAPI_TRENDS_DATE", "today 1-m").strip() or "today 1-m"

    params = {
        "engine": "google_trends",
        "q": q,
        "api_key": api_key,
        "geo": geo,
        "date": date,
    }

    details: Dict[str, Any] = {
        "query": q,
        "geo": geo,
        "date": date,
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.get("https://serpapi.com/search.json", params=params)
        details["http_status"] = r.status_code

        if r.status_code in (401, 403):
            return DiagResult(name="SerpAPI_Trends", status="FAIL", reason="Unauthorized (invalid API key)", details=details)
        if r.status_code == 429:
            return DiagResult(name="SerpAPI_Trends", status="FAIL", reason="Rate limited / quota exceeded (429)", details=details)
        if r.status_code >= 500:
            return DiagResult(name="SerpAPI_Trends", status="FAIL", reason="SerpAPI server error", details=details)

        payload = r.json()
        details["payload_keys"] = sorted(list(payload.keys())) if isinstance(payload, dict) else "non_dict"
        if isinstance(payload, dict) and payload.get("error"):
            return DiagResult(name="SerpAPI_Trends", status="FAIL", reason=f"API error: {payload.get('error')}", details=details)

        return DiagResult(name="SerpAPI_Trends", status="PASS", reason="Returned payload", details=details)

    except Exception as e:
        if os.getenv("DIAG_DEBUG", "").lower() in ("1", "true", "yes"):
            details["error"] = str(e)
        return DiagResult(name="SerpAPI_Trends", status="FAIL", reason="Request failed", details=details)


if __name__ == "__main__":
    raise SystemExit(safe_main(run, "SerpAPI_Trends"))

