"""
Check whether real ROI metrics exist in MongoDB (needed for "real labels").
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
        def fmt(name: str, total: int, success: int, success_nonzero: int) -> None:
            print(f"\n=== {name} ===")
            print("total:", total)
            print("roi_success:", success)
            print("roi_success_engagement_gt0:", success_nonzero)

        async def status_counts(model, label: str):
            pending = await model.find(model.roi_metrics.fetch_status == "pending").count()
            failed = await model.find(model.roi_metrics.fetch_status == "failed").count()
            other = await model.find(
                model.roi_metrics.fetch_status != "pending",
                model.roi_metrics.fetch_status != "failed",
                model.roi_metrics.fetch_status != "success",
            ).count()
            print("roi_pending:", pending)
            print("roi_failed:", failed)
            if other:
                print("roi_other:", other)

        posts_total = await InstagramPostModel.find_all().count()
        posts_success = await InstagramPostModel.find(
            InstagramPostModel.roi_metrics.fetch_status == "success"
        ).count()
        posts_success_nonzero = await InstagramPostModel.find(
            InstagramPostModel.roi_metrics.fetch_status == "success",
            InstagramPostModel.roi_metrics.engagement_rate > 0,
        ).count()
        fmt("instagram_posts", posts_total, posts_success, posts_success_nonzero)
        await status_counts(InstagramPostModel, "instagram_posts")
        sample_posts = await InstagramPostModel.find_all().limit(5).to_list()
        print("sample fetch_status values (posts):", [getattr(p.roi_metrics, "fetch_status", None) for p in sample_posts])

        sched_total = await ScheduledInstagramPostModel.find_all().count()
        sched_success = await ScheduledInstagramPostModel.find(
            ScheduledInstagramPostModel.roi_metrics.fetch_status == "success"
        ).count()
        sched_success_nonzero = await ScheduledInstagramPostModel.find(
            ScheduledInstagramPostModel.roi_metrics.fetch_status == "success",
            ScheduledInstagramPostModel.roi_metrics.engagement_rate > 0,
        ).count()
        fmt("scheduled_instagram_posts", sched_total, sched_success, sched_success_nonzero)
        await status_counts(ScheduledInstagramPostModel, "scheduled_instagram_posts")
        sample_sched = await ScheduledInstagramPostModel.find_all().limit(5).to_list()
        print("sample fetch_status values (scheduled):", [getattr(p.roi_metrics, "fetch_status", None) for p in sample_sched])

        stories_total = await InstagramStoryModel.find_all().count()
        stories_success = await InstagramStoryModel.find(
            InstagramStoryModel.roi_metrics.fetch_status == "success"
        ).count()
        stories_success_nonzero = await InstagramStoryModel.find(
            InstagramStoryModel.roi_metrics.fetch_status == "success",
            InstagramStoryModel.roi_metrics.engagement_rate > 0,
        ).count()
        fmt("instagram_stories", stories_total, stories_success, stories_success_nonzero)
        await status_counts(InstagramStoryModel, "instagram_stories")
        sample_stories = await InstagramStoryModel.find_all().limit(5).to_list()
        print("sample fetch_status values (stories):", [getattr(p.roi_metrics, "fetch_status", None) for p in sample_stories])

        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

