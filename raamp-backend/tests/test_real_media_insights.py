"""
Test fetching insights for one of the real media IDs that's in both DB and Instagram
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
        # Get a post that's in BOTH DB and Instagram
        all_posts = await InstagramPostModel.find(
            InstagramPostModel.ig_business_id == "17841478865387098",
            NE(InstagramPostModel.instagram_post_id, None)
        ).to_list()
        
        # Get actual media from Instagram
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
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(url, params=params)
            ig_media_ids = {m["id"] for m in r.json().get("data", [])}
        
        # Find a post that's in both
        real_post = None
        for p in all_posts:
            if p.instagram_post_id in ig_media_ids:
                real_post = p
                break
        
        if not real_post:
            print("No posts found in both DB and Instagram")
            return 0
        
        print(f"Testing with real media ID: {real_post.instagram_post_id}")
        print(f"Current reach: {real_post.roi_metrics.reach}")
        print(f"Current status: {real_post.roi_metrics.fetch_status}\n")
        
        # Try to fetch insights with the new metric list
        media_id = real_post.instagram_post_id
        metrics = "reach,impressions,likes,comments,shares,saved,total_interactions"
        
        insights_url = f"https://graph.facebook.com/v22.0/{media_id}/insights"
        insights_params = {
            "metric": metrics,
            "access_token": token
        }
        
        print(f"Fetching insights from: {insights_url}\n")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(insights_url, params=insights_params)
            print(f"Status: {r.status_code}")
            
            data = r.json()
            if r.status_code == 200:
                print("Success! Metrics:")
                for metric in data.get("data", []):
                    name = metric.get("name")
                    value = metric.get("values", [{}])[0].get("value", "N/A")
                    print(f"  {name}: {value}")
            else:
                error = data.get("error", {})
                print(f"Error: {error.get('message')}")
                print(f"Code: {error.get('code')}")
        
        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
