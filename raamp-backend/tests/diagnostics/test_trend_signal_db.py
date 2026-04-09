"""
Diagnostics: TrendSignal DB health
---------------------------------
Checks what the backend has actually persisted for TrendSignalModel.

Why this matters:
- If there are zero completed TrendSignal records, the UI cannot show real trends.
- This detects silent failures where scans never complete (stuck pending/failed).

Notes:
- This script is READ-ONLY. It does not modify any DB records.
"""

from __future__ import annotations

import os
import asyncio
from datetime import datetime
from typing import Dict, Any, List

from dotenv import load_dotenv

from _diag_utils import DiagResult, safe_main


async def _run_async() -> DiagResult:
    load_dotenv()

    from infrastructure.database.database import connect_to_mongo, init_db, close_mongo_connection
    from infrastructure.database.models.trend_signal_model import TrendSignalModel

    details: Dict[str, Any] = {"timestamp_utc": datetime.utcnow().isoformat() + "Z"}

    try:
        # Silence noisy/unicode console prints from DB bootstrap (Windows cp1252).
        import io
        from contextlib import redirect_stdout, redirect_stderr

        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            await connect_to_mongo()
            await init_db()

        completed = await TrendSignalModel.find(TrendSignalModel.fetch_status == "completed").count()
        failed = await TrendSignalModel.find(TrendSignalModel.fetch_status == "failed").count()
        pending = await TrendSignalModel.find(TrendSignalModel.fetch_status == "pending").count()

        details["completed_count"] = int(completed)
        details["failed_count"] = int(failed)
        details["pending_count"] = int(pending)

        last5: List[Dict[str, Any]] = []
        rows = await TrendSignalModel.find(TrendSignalModel.fetch_status == "completed").sort("-created_at").limit(5).to_list()
        for r in rows:
            last5.append(
                {
                    "id": str(r.id),
                    "keywords": (r.keywords or [])[:3],
                    "location": r.location,
                    "niche": r.niche,
                    "arbitrage_score": r.arbitrage_score,
                    "social_score": r.social_score,
                    "saturation_score": r.saturation_score,
                    "created_at": r.created_at.isoformat() if getattr(r, "created_at", None) else None,
                    "is_simulated": False,  # TrendSignalModel is persisted from real fetch; synthetic is now removed from live feed.
                }
            )
        details["last_5_completed"] = last5

        if completed <= 0:
            return DiagResult(
                name="TrendSignal DB",
                status="FAIL",
                reason="Zero completed TrendSignal records",
                details={**details, "warning": "ALL TRENDS DATA IS CURRENTLY UNAVAILABLE (no completed scans)"},
            )

        return DiagResult(
            name="TrendSignal DB",
            status="PASS",
            reason="Found completed TrendSignal records",
            details=details,
        )

    except Exception as e:
        if os.getenv("DIAG_DEBUG", "").lower() in ("1", "true", "yes"):
            details["error"] = str(e)
        return DiagResult(name="TrendSignal DB", status="FAIL", reason="DB query failed", details=details)
    finally:
        try:
            await close_mongo_connection()
        except Exception:
            pass


def run() -> DiagResult:
    return asyncio.run(_run_async())


if __name__ == "__main__":
    raise SystemExit(safe_main(run, "TrendSignal DB"))

