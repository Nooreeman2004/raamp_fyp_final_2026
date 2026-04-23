"""
Batch refresh ROI for all posts with instagram_post_id
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
        # Get real media IDs from Instagram
        conn = await InstagramConnectionModel.find_one(
            InstagramConnectionModel.user_id == "abdullah@gmail.com"
        )
        
        if not conn:
            print("No connection found")
            return 0
        
        token = EncryptionService().decrypt(conn.page_access_token)
        business_id = conn.ig_business_id
        
        # Get actual media IDs from Instagram API
        url = f"https://graph.facebook.com/v22.0/{business_id}/media"
        params = {"fields": "id", "access_token": token, "limit": 100}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, params=params)
            ig_media_ids = {m["id"] for m in r.json().get("data", [])}
        
        print(f"Real media on Instagram: {len(ig_media_ids)}")
        
        # Get all posts with instagram_post_id
        all_posts = await InstagramPostModel.find(
            InstagramPostModel.ig_business_id == business_id,
            NE(InstagramPostModel.instagram_post_id, None)
        ).to_list()
        
        print(f"Posts in DB with instagram_post_id: {len(all_posts)}\n")
        
        # Batch refresh only the real media
        success = 0
        failed = 0
        
        for post in all_posts:
            # Skip fake media IDs
            if post.instagram_post_id not in ig_media_ids:
                continue
            
            try:
                metrics = await refresh_post_roi(str(post.id))
                if metrics and metrics.fetch_status == "success":
                    success += 1
                    reach = metrics.reach
                    print(f"✓ {post.instagram_post_id}: reach={reach}")
                else:
                    failed += 1
                    status = metrics.fetch_status if metrics else "None"
                    print(f"✗ {post.instagram_post_id}: status={status}")
            except Exception as e:
                failed += 1
                print(f"✗ {post.instagram_post_id}: {str(e)[:60]}")
        
        print(f"\n=== Batch Refresh Complete ===")
        print(f"Success: {success}")
        print(f"Failed: {failed}")
        
        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
