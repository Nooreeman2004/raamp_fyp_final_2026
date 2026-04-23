"""
Debug fetch_status values more carefully
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
    from infrastructure.database.models.instagram_post_model import InstagramPostModel

    await connect_to_mongo()
    await init_db()
    try:
        # Get all posts
        all_posts = await InstagramPostModel.find_all().limit(20).to_list()
        
        print("=== Sample posts with fetch_status values ===\n")
        for p in all_posts:
            status = getattr(p.roi_metrics, "fetch_status", "NO_ATTR")
            print(f"Post {p.id}")
            print(f"  status: {p.status}")
            print(f"  instagram_post_id: {p.instagram_post_id}")
            print(f"  published_at: {p.published_at}")
            print(f"  roi.fetch_status: {repr(status)}")
            print(f"  roi.reach: {p.roi_metrics.reach}")
            print()

        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
