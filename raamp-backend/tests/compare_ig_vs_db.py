"""
Check what media we have in DB vs what's on Instagram
"""

import asyncio
import os
import sys

import httpx

_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND_ROOT = os.path.dirname(_HERE)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)


async def main() -> int:
    from infrastructure.database.database import connect_to_mongo, init_db, close_mongo_connection
    from infrastructure.database.models.instagram_connection_model import InstagramConnectionModel
    from infrastructure.database.models.instagram_post_model import InstagramPostModel
    from application.services.encryption_service import EncryptionService
    from beanie.operators import NE

    await connect_to_mongo()
    await init_db()
    try:
        # Get media from Instagram
        conn = await InstagramConnectionModel.find_one(
            InstagramConnectionModel.user_id == "abdullah@gmail.com"
        )
        
        token = EncryptionService().decrypt(conn.page_access_token)
        business_id = conn.ig_business_id
        
        url = f"https://graph.facebook.com/v22.0/{business_id}/media"
        params = {
            "fields": "id",
            "access_token": token,
            "limit": 100
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, params=params)
            ig_media_ids = {m["id"] for m in r.json().get("data", [])}
        
        print(f"Media on Instagram: {len(ig_media_ids)}")
        
        # Get media from DB
        db_posts = await InstagramPostModel.find(
            InstagramPostModel.ig_business_id == business_id
        ).to_list()
        
        db_media_ids = {p.instagram_post_id for p in db_posts if p.instagram_post_id}
        print(f"Media in DB: {len(db_media_ids)}")
        
        # Check overlap
        overlap = ig_media_ids & db_media_ids
        print(f"Media in both: {len(overlap)}")
        
        ig_only = ig_media_ids - db_media_ids
        print(f"Media only on Instagram: {len(ig_only)}")
        
        db_only = db_media_ids - ig_media_ids
        print(f"Media only in DB: {len(db_only)}")
        
        if ig_only:
            print(f"\nSample IG-only IDs: {list(ig_only)[:3]}")
        
        if db_only:
            print(f"Sample DB-only IDs: {list(db_only)[:3]}")
        
        # Check if DB records have reach data
        print("\n=== DB posts with reach data ===")
        with_reach = [p for p in db_posts if p.roi_metrics.reach > 0]
        print(f"Posts with reach > 0: {len(with_reach)}")
        
        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
