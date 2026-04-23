"""
Check the total reach summary like the KPI dashboard would see
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
        business_id = "17841478865387098"
        
        # This mimics what the KPI endpoint does
        posts = await InstagramPostModel.find(
            InstagramPostModel.ig_business_id == business_id
        ).to_list()
        scheduled = await ScheduledInstagramPostModel.find(
            ScheduledInstagramPostModel.ig_business_id == business_id
        ).to_list()
        stories = await InstagramStoryModel.find(
            InstagramStoryModel.ig_business_id == business_id
        ).to_list()
        
        all_content = posts + scheduled + stories
        
        print(f"Total content items: {len(all_content)}")
        print(f"  Posts: {len(posts)}")
        print(f"  Scheduled: {len(scheduled)}")
        print(f"  Stories: {len(stories)}\n")
        
        # Calculate like the KPI router does
        total_reach = sum(p.roi_metrics.reach for p in all_content)
        total_impressions = sum(p.roi_metrics.impressions for p in all_content)
        
        success_posts = [p for p in all_content if p.roi_metrics.fetch_status == "success"]
        total_engagement_rate = sum(p.roi_metrics.engagement_rate for p in success_posts)
        
        avg_er = 0.0
        if success_posts:
            avg_er = total_engagement_rate / len(success_posts)
        
        print("=== KPI Summary ===\n")
        print(f"Total Reach: {total_reach}")
        print(f"Total Impressions: {total_impressions}")
        print(f"Avg Engagement Rate: {avg_er:.2f}%")
        print(f"Posts with success: {len(success_posts)}")
        
        if total_reach > 0:
            print(f"\n✓ SUCCESS: Total Reach is now NON-ZERO!")
        else:
            print(f"\n✗ Still zero")
        
        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
