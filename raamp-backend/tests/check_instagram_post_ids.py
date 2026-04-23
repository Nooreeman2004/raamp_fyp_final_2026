"""
Check if posts have instagram_post_id set (needed for ROI refresh).
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
    from beanie.operators import NE

    await connect_to_mongo()
    await init_db()
    try:
        # Check posts with instagram_post_id
        posts_with_id = await InstagramPostModel.find(
            NE(InstagramPostModel.instagram_post_id, None)
        ).count()
        posts_without_id = await InstagramPostModel.find(
            InstagramPostModel.instagram_post_id == None  # noqa: E711
        ).count()
        
        # Check stories with instagram_story_id
        stories_with_id = await InstagramStoryModel.find(
            NE(InstagramStoryModel.instagram_story_id, None)
        ).count()
        stories_without_id = await InstagramStoryModel.find(
            InstagramStoryModel.instagram_story_id == None  # noqa: E711
        ).count()
        
        # Check scheduled posts
        sched_with_id = await ScheduledInstagramPostModel.find(
            NE(ScheduledInstagramPostModel.instagram_post_id, None)
        ).count()
        sched_without_id = await ScheduledInstagramPostModel.find(
            ScheduledInstagramPostModel.instagram_post_id == None  # noqa: E711
        ).count()

        print("\n=== Posts ===")
        print(f"with instagram_post_id: {posts_with_id}")
        print(f"without instagram_post_id: {posts_without_id}")
        
        print("\n=== Stories ===")
        print(f"with instagram_story_id: {stories_with_id}")
        print(f"without instagram_story_id: {stories_without_id}")
        
        print("\n=== Scheduled Posts ===")
        print(f"with instagram_post_id: {sched_with_id}")
        print(f"without instagram_post_id: {sched_without_id}")
        
        # Sample some posts that are published but pending ROI
        print("\n=== Sample pending posts (published, no ROI) ===")
        pending = await InstagramPostModel.find(
            InstagramPostModel.roi_metrics.fetch_status == "pending"
        ).limit(3).to_list()
        
        for p in pending:
            print(f"Post {p.id}:")
            print(f"  status: {p.status}")
            print(f"  instagram_post_id: {p.instagram_post_id}")
            print(f"  published_at: {p.published_at}")
            print(f"  roi fetch_status: {p.roi_metrics.fetch_status}")

        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
