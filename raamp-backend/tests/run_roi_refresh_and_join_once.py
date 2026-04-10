"""
Force ROI refresh once, then run ROI→caption join once, then report:
  - count of instagram_posts with roi_metrics.fetch_status == 'success'
  - count of caption_logs labels updated in last 24h

This is the quickest "make labels real" attempt without waiting for APScheduler.
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
    from application.services.instagram_roi_service import scheduled_roi_refresh
    from application.services.caption_roi_join_service import backfill_caption_log_engagement_rates
    from infrastructure.database.models.instagram_post_model import InstagramPostModel
    from infrastructure.database.models.caption_log_model import CaptionLogModel

    await connect_to_mongo()
    await init_db()

    try:
        print("\n=== forcing scheduled_roi_refresh() once ===")
        await scheduled_roi_refresh()

        success_posts = await InstagramPostModel.find(
            InstagramPostModel.roi_metrics.fetch_status == "success"
        ).count()
        print("instagram_posts roi_success:", success_posts)

        print("\n=== forcing ROI→caption join once ===")
        summary = await backfill_caption_log_engagement_rates(lookback_days=365, limit_per_collection=500)
        print("join summary:", summary)

        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        cutoff_naive = cutoff.replace(tzinfo=None)
        real_count = await CaptionLogModel.find(
            CaptionLogModel.engagement_rate != None,  # noqa: E711
            CaptionLogModel.updated_at > cutoff_naive,
        ).count()
        print("\ncaption_logs updated last 24h:", real_count)

        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

