"""
Compare posts with and without instagram_post_id
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
    from beanie.operators import NE

    await connect_to_mongo()
    await init_db()
    try:
        # Get a post WITH instagram_post_id
        with_id = await InstagramPostModel.find(
            NE(InstagramPostModel.instagram_post_id, None)
        ).limit(1).to_list()
        
        if with_id:
            p = with_id[0]
            print("=== Post WITH instagram_post_id ===")
            print(f"Post {p.id}")
            print(f"  status: {p.status}")
            print(f"  instagram_post_id: {p.instagram_post_id}")
            print(f"  published_at: {p.published_at}")
            print(f"  roi.fetch_status: {p.roi_metrics.fetch_status}")
            print(f"  roi.reach: {p.roi_metrics.reach}")
        else:
            print("No posts with instagram_post_id found!")
        
        # Get a post WITHOUT instagram_post_id
        print("\n=== Post WITHOUT instagram_post_id (for comparison) ===")
        without_id = await InstagramPostModel.find(
            InstagramPostModel.instagram_post_id == None  # noqa: E711
        ).limit(1).to_list()
        
        if without_id:
            p = without_id[0]
            print(f"Post {p.id}")
            print(f"  status: {p.status}")
            print(f"  instagram_post_id: {p.instagram_post_id}")
            print(f"  published_at: {p.published_at}")
            print(f"  roi.fetch_status: {p.roi_metrics.fetch_status}")
            print(f"  roi.reach: {p.roi_metrics.reach}")

        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
