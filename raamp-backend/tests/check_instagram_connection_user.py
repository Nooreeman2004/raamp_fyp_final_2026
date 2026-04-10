"""
Inspect Instagram connection + posts for a given user.

Usage:
  python tests/check_instagram_connection_user.py abdullah@gmail.com
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
    from infrastructure.database.models.instagram_connection_model import InstagramConnectionModel
    from infrastructure.database.models.instagram_post_model import InstagramPostModel

    await connect_to_mongo()
    await init_db()
    try:
        conn = await InstagramConnectionModel.find_one(InstagramConnectionModel.user_id == user)
        print("\n=== instagram_connections ===")
        if not conn:
            print("No connection found for user_id:", user)
        else:
            print("user_id:", conn.user_id)
            print("ig_business_id:", conn.ig_business_id)
            print("ig_business_id type:", type(conn.ig_business_id).__name__)
            print("token_valid:", conn.token_valid)
            print("expires_at:", conn.expires_at)
            print("has page_access_token:", bool(conn.page_access_token))
            print("has user_access_token:", bool(conn.user_access_token))
            print("linked_fb_page_id:", conn.linked_fb_page_id)
            print("updated_at:", conn.updated_at)

        posts = await InstagramPostModel.find(InstagramPostModel.user_id == user).sort(-InstagramPostModel.created_at).limit(5).to_list()
        print("\n=== instagram_posts (latest 5 for user) ===")
        if not posts:
            print("No posts found for user_id:", user)
        for p in posts:
            print(
                "- post_id:", str(p.id),
                "| ig_business_id:", p.ig_business_id,
                "| ig_business_id type:", type(p.ig_business_id).__name__,
                "| instagram_post_id:", p.instagram_post_id,
                "| fetch_status:", getattr(p.roi_metrics, "fetch_status", None),
                "| engagement_rate:", getattr(p.roi_metrics, "engagement_rate", None),
            )

        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

