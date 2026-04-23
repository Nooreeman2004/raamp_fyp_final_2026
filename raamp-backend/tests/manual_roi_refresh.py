"""
Manually refresh ROI for a post with instagram_post_id to see the actual error
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
    from infrastructure.database.models.instagram_connection_model import InstagramConnectionModel
    from application.services.instagram_roi_service import refresh_post_roi
    from application.services.encryption_service import EncryptionService
    from beanie.operators import NE
    import httpx

    await connect_to_mongo()
    await init_db()
    try:
        # Get actual media IDs from Instagram
        conn = await InstagramConnectionModel.find_one(
            InstagramConnectionModel.user_id == "abdullah@gmail.com"
        )
        
        token = EncryptionService().decrypt(conn.page_access_token)
        business_id = conn.ig_business_id
        
        # Get real media IDs from Instagram API
        url = f"https://graph.facebook.com/v22.0/{business_id}/media"
        params = {"fields": "id", "access_token": token, "limit": 1}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, params=params)
            ig_media_ids = {m["id"] for m in r.json().get("data", [])}
        
        # Find a post in DB that's actually on Instagram
        all_posts = await InstagramPostModel.find(
            InstagramPostModel.ig_business_id == business_id,
            NE(InstagramPostModel.instagram_post_id, None)
        ).to_list()
        
        real_post = None
        for p in all_posts:
            if p.instagram_post_id in ig_media_ids:
                real_post = p
                break
        
        if not real_post:
            print("No real posts found (not in both DB and Instagram)")
            return 0
            
        post = real_post
        print(f"Found post: {post.id}")
        print(f"  instagram_post_id: {post.instagram_post_id}")
        print(f"  current fetch_status: {post.roi_metrics.fetch_status}")
        print(f"  current reach: {post.roi_metrics.reach}\n")
        
        print("Attempting to refresh ROI metrics...")
        try:
            metrics = await refresh_post_roi(str(post.id))
            print(f"\nRefresh completed!")
            print(f"  fetch_status: {metrics.fetch_status if metrics else 'None'}")
            print(f"  reach: {metrics.reach if metrics else 'None'}")
        except Exception as e:
            print(f"\nError during refresh: {type(e).__name__}: {e}")

        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
