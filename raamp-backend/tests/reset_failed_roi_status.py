"""
Reset failed ROI statuses back to pending so they can be retried with better error handling
"""

import asyncio
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND_ROOT = os.path.dirname(_HERE)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)


async def main() -> int:
    from infrastructure.database.database import connect_to_mongo, init_db, close_mongo_connection
    from infrastructure.database.models.instagram_post_model import (
        InstagramPostModel,
        ScheduledInstagramPostModel,
        InstagramStoryModel,
    )

    await connect_to_mongo()
    await init_db()
    try:
        # Reset failed statuses back to pending for all content types
        # This allows them to be retried with the new error handling
        
        # Reset posts
        posts_updated = await InstagramPostModel.find(
            InstagramPostModel.roi_metrics.fetch_status == "failed"
        ).update({"$set": {"roi_metrics.fetch_status": "pending"}})
        print(f"Updated {posts_updated.modified_count} posts with fetch_status=failed -> pending")
        
        # Reset scheduled posts
        sched_updated = await ScheduledInstagramPostModel.find(
            ScheduledInstagramPostModel.roi_metrics.fetch_status == "failed"
        ).update({"$set": {"roi_metrics.fetch_status": "pending"}})
        print(f"Updated {sched_updated.modified_count} scheduled posts with fetch_status=failed -> pending")
        
        # Reset stories
        stories_updated = await InstagramStoryModel.find(
            InstagramStoryModel.roi_metrics.fetch_status == "failed"
        ).update({"$set": {"roi_metrics.fetch_status": "pending"}})
        print(f"Updated {stories_updated.modified_count} stories with fetch_status=failed -> pending")
        
        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
