"""
Run the ROI→caption join once immediately, then verify "real labels" via:
  caption_logs where engagement_rate != null AND updated_at > now-24h

This script:
  1) connects to MongoDB + inits Beanie
  2) runs backfill_caption_log_engagement_rates()
  3) prints join summary
  4) prints count of labels updated in last 24 hours
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone


_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND_ROOT = os.path.dirname(_HERE)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)


async def main() -> int:
    from infrastructure.database.database import connect_to_mongo, init_db, close_mongo_connection
    from application.services.caption_roi_join_service import backfill_caption_log_engagement_rates
    from infrastructure.database.models.caption_log_model import CaptionLogModel

    await connect_to_mongo()
    await init_db()

    try:
        print("\n=== running caption ROI join once ===")
        # Use a wider lookback to catch older ROI records (common in FYP demos)
        summary = await backfill_caption_log_engagement_rates(
            lookback_days=365,
            limit_per_collection=500,
        )
        print("summary:", summary)

        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        cutoff_naive = cutoff.replace(tzinfo=None)

        real_count = await CaptionLogModel.find(
            CaptionLogModel.engagement_rate != None,  # noqa: E711
            CaptionLogModel.updated_at != None,       # noqa: E711
            CaptionLogModel.updated_at > cutoff_naive,
        ).count()

        print("\n=== real labels check (last 24h) ===")
        print("cutoff_utc:", cutoff.isoformat())
        print("count:", real_count)

        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

