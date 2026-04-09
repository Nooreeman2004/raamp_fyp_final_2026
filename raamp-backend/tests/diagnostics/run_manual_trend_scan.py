"""
Manual Trend Scan Runner (diagnostic)
------------------------------------
Runs a full trend scan for a given user email without using HTTP.

Why:
- Allows verifying keyword seeding (no 'all'), PyTrends 429/backoff, and live_feed_source logs.

Usage:
  python tests/diagnostics/run_manual_trend_scan.py abdullah@gmail.com [30d|90d|7d|24h] [keyword1] [keyword2] ...

Notes:
- This will CREATE a TrendSignal and detection records, just like a real scan.
"""

from __future__ import annotations

import sys
import asyncio
import logging


async def main() -> int:
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    # Ensure backend root on sys.path when running as a script
    import os
    here = os.path.abspath(os.path.dirname(__file__))
    backend_root = os.path.abspath(os.path.join(here, "..", ".."))
    if backend_root not in sys.path:
        sys.path.insert(0, backend_root)

    email = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    if not email:
        print("ERROR: Provide user email. Example: python tests/diagnostics/run_manual_trend_scan.py user@example.com")
        return 2
    timeframe = (sys.argv[2] if len(sys.argv) > 2 else "90d").strip() or "90d"
    explicit_keywords = [k.strip() for k in sys.argv[3:] if isinstance(k, str) and k.strip()]

    from infrastructure.database.database import connect_to_mongo, init_db, close_mongo_connection
    from infrastructure.database.models.user_model import UserModel
    from infrastructure.database.models.trend_signal_model import TrendSignalModel
    from application.services.trend_detection_service import TrendDetectionService

    await connect_to_mongo()
    await init_db()

    try:
        user = await UserModel.find_one({"email": email})
        if not user:
            print(f"ERROR: User not found: {email}")
            return 1

        svc = TrendDetectionService()
        sig = await svc.initialize_detection_signal(user, None, "all")

        if explicit_keywords:
            # Override seeded keywords for volatility testing without UI/DB edits.
            # Keep category aligned to the first keyword to avoid confusing logs/UX.
            try:
                persisted_sig = await TrendSignalModel.get(sig.id)
                if persisted_sig:
                    persisted_sig.keywords = explicit_keywords[:10]
                    persisted_sig.category = explicit_keywords[0]
                    await persisted_sig.save()
                    sig = persisted_sig
            except Exception as e:
                print(f"WARN: Failed to override keywords on signal: {e}")

        print(f"trend_id={sig.id}")
        print(f"seed_keywords={getattr(sig, 'keywords', None)}")

        await svc.execute_detection_pipeline(str(sig.id), timeframe)

        # Re-load persisted signal to confirm actual keywords and status.
        persisted = await TrendSignalModel.get(sig.id)
        if persisted:
            print(f"fetch_status={getattr(persisted, 'fetch_status', None)}")
            print(f"error_message={getattr(persisted, 'error_message', None)}")
            print(f"persisted_keywords={(getattr(persisted, 'keywords', None) or [])[:5]}")
        else:
            print("fetch_status=UNKNOWN (signal not found)")
        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

