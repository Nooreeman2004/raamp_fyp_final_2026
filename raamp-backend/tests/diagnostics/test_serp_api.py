"""
Diagnostics: SerpAPI
-------------------
Verifies that SerpAPI is configured and returns organic/ad results.

Why this matters:
- Saturation/competition should be derived from real SERP data, not fabricated.
- This test confirms the external SERP provider is working and not rate-limited.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, Any

import httpx
from dotenv import load_dotenv

from _diag_utils import DiagResult, safe_main


def _classify_serp_error(payload: Dict[str, Any]) -> str:
    # SerpAPI uses "error" or "search_metadata" status fields.
    if not isinstance(payload, dict):
        return "malformed_response"
    if payload.get("error"):
        msg = str(payload.get("error"))
        m = msg.lower()
        if "invalid" in m and "api" in m and "key" in m:
            return "invalid_api_key"
        if "quota" in m or "limit" in m:
            return "quota_exceeded"
        return "api_error"
    meta = payload.get("search_metadata") or {}
    status = str(meta.get("status") or "").lower()
    if status and status not in ("success",):
        return f"status_{status}"
    return "unknown"


def run() -> DiagResult:
    load_dotenv()

    # Prefer config.py settings if available.
    api_key = os.getenv("SERPAPI_API_KEY", "").strip()
    if not api_key:
        return DiagResult(
            name="SerpAPI",
            status="FAIL",
            reason="Missing SERPAPI_API_KEY in environment",
            details={"timestamp_utc": datetime.utcnow().isoformat() + "Z"},
        )

    q = os.getenv("DIAG_SERPAPI_QUERY", "cold brew").strip() or "cold brew"
    gl = os.getenv("DIAG_SERPAPI_GL", "pk").strip() or "pk"
    hl = os.getenv("DIAG_SERPAPI_HL", "en").strip() or "en"

    params = {
        "engine": "google",
        "q": q,
        "api_key": api_key,
        "gl": gl,
        "hl": hl,
        "num": 10,
    }

    details: Dict[str, Any] = {
        "query": q,
        "gl": gl,
        "hl": hl,
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get("https://serpapi.com/search.json", params=params)
        details["http_status"] = r.status_code

        if r.status_code in (401, 403):
            return DiagResult(name="SerpAPI", status="FAIL", reason="Unauthorized (invalid API key)", details=details)
        if r.status_code == 429:
            return DiagResult(name="SerpAPI", status="FAIL", reason="Rate limited / quota exceeded (429)", details=details)
        if r.status_code >= 500:
            return DiagResult(name="SerpAPI", status="FAIL", reason="SerpAPI server error", details=details)

        payload = r.json()

        organic = payload.get("organic_results") or []
        ads_top = payload.get("ads") or payload.get("top_ads") or []
        ads_bottom = payload.get("bottom_ads") or []
        details["organic_results"] = len(organic) if isinstance(organic, list) else 0
        details["ads_top"] = len(ads_top) if isinstance(ads_top, list) else 0
        details["ads_bottom"] = len(ads_bottom) if isinstance(ads_bottom, list) else 0

        if details["organic_results"] <= 0:
            kind = _classify_serp_error(payload)
            return DiagResult(
                name="SerpAPI",
                status="FAIL",
                reason=f"Empty organic results ({kind})",
                details=details,
            )

        return DiagResult(
            name="SerpAPI",
            status="PASS",
            reason="Returned organic results",
            details=details,
        )

    except Exception as e:
        if os.getenv("DIAG_DEBUG", "").lower() in ("1", "true", "yes"):
            details["error"] = str(e)
        return DiagResult(name="SerpAPI", status="FAIL", reason="Request failed", details=details)


if __name__ == "__main__":
    raise SystemExit(safe_main(run, "SerpAPI"))

