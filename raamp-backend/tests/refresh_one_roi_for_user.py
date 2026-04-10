"""
Manually refresh ROI for the latest Instagram post for a user.

Usage:
  python tests/refresh_one_roi_for_user.py abdullah@gmail.com
"""

import asyncio
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND_ROOT = os.path.dirname(_HERE)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)


async def main() -> int:
    user = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    if not user:
        print("Provide user email, e.g. abdullah@gmail.com")
        return 2

    from infrastructure.database.database import connect_to_mongo, init_db, close_mongo_connection
    from infrastructure.database.models.instagram_post_model import InstagramPostModel
    from infrastructure.database.models.instagram_connection_model import InstagramConnectionModel
    from application.services.instagram_roi_service import refresh_post_roi

    await connect_to_mongo()
    await init_db()
    try:
        post = await InstagramPostModel.find(InstagramPostModel.user_id == user).sort(-InstagramPostModel.created_at).first_or_none()
        if not post:
            print("No Instagram posts found for user:", user)
            return 0

        print("\n=== refreshing ROI for post ===")
        print("post_id:", str(post.id))
        print("instagram_post_id:", post.instagram_post_id)
        print("ig_business_id:", post.ig_business_id)
        print("current fetch_status:", post.roi_metrics.fetch_status)

        # Sanity check: can we resolve connection via the same lookup as refresh_post_roi?
        conn = await InstagramConnectionModel.find_one(
            InstagramConnectionModel.ig_business_id == post.ig_business_id
        )
        print("\n=== connection lookup by ig_business_id ===")
        print("found:", bool(conn))
        if conn:
            print("user_id:", conn.user_id)
            print("token_valid:", conn.token_valid)
            print("has page_access_token:", bool(conn.page_access_token))

        metrics = await refresh_post_roi(str(post.id))
        print("\n=== result ===")
        if not metrics:
            print("metrics: None (refresh failed)")
            return 1

        print("fetch_status:", metrics.fetch_status)
        print("engagement_rate:", metrics.engagement_rate)
        print("reach:", metrics.reach)
        print("likes:", metrics.likes, "comments:", metrics.comments, "shares:", metrics.shares)
        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

