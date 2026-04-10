"""
Try refreshing ROI for multiple posts for a user until we get a success.

Usage:
  python tests/refresh_roi_for_user_batch.py abdullah@gmail.com 10
"""

import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta

_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND_ROOT = os.path.dirname(_HERE)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)


async def main() -> int:
    user = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    if not user:
        print("Provide user email, e.g. abdullah@gmail.com")
        return 2

    from infrastructure.database.database import connect_to_mongo, init_db, close_mongo_connection
    from infrastructure.database.models.instagram_post_model import InstagramPostModel
    from application.services.instagram_roi_service import refresh_post_roi

    await connect_to_mongo()
    await init_db()
    try:
        posts = await InstagramPostModel.find(
            InstagramPostModel.user_id == user,
            InstagramPostModel.instagram_post_id != None,  # noqa: E711
        ).sort(InstagramPostModel.created_at).limit(limit).to_list()  # oldest first

        print(f"\nFound {len(posts)} posts (oldest first) to refresh for {user}")
        success = 0
        pending = 0
        failed = 0

        for p in posts:
            metrics = await refresh_post_roi(str(p.id))
            st = getattr(metrics, "fetch_status", None) if metrics else None
            if st == "success":
                success += 1
            elif st == "pending":
                pending += 1
            else:
                failed += 1
            print(
                "- post_id:", str(p.id),
                "| ig_post_id:", p.instagram_post_id,
                "| ig_media_id:", getattr(p, "instagram_media_id", None),
                "| published_at:", getattr(p, "published_at", None),
                "| status:", st,
                "| er%:", getattr(metrics, "engagement_rate", None) if metrics else None,
            )

        print("\nSummary:", {"success": success, "pending": pending, "failed": failed})
        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

