"""
Try to access one of the actual media that exists on Instagram to see what data we can get
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
        # Get a connection
        conn = await InstagramConnectionModel.find_one(
            InstagramConnectionModel.user_id == "abdullah@gmail.com",
            InstagramConnectionModel.page_access_token != None,  # noqa: E711
        )
        
        if not conn:
            print("No connection found")
            return 0
        
        token = EncryptionService().decrypt(conn.page_access_token)
        business_id = conn.ig_business_id
        
        # List media endpoint
        url = f"https://graph.facebook.com/v22.0/{business_id}/media"
        params = {
            "fields": "id,media_type,created_time,caption",
            "access_token": token,
            "limit": 1
        }
        
        print("=== Getting one real media item ===\n")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, params=params)
            data = r.json()
            
            if r.status_code != 200:
                print(f"Error: {data}")
                return 1
            
            media_list = data.get("data", [])
            if not media_list:
                print("No media found")
                return 0
            
            actual_media_id = media_list[0]["id"]
            print(f"Actual media ID from Instagram: {actual_media_id}")
            print(f"Media type: {media_list[0].get('media_type')}\n")
            
            # Now try to get insights for this actual media
            print("=== Testing insights for actual media ===\n")
            
            insights_url = f"https://graph.facebook.com/v22.0/{actual_media_id}/insights"
            insights_params = {
                "metric": "reach,impressions",
                "access_token": token
            }
            
            r_insights = await client.get(insights_url, params=insights_params)
            print(f"Insights status: {r_insights.status_code}")
            
            insights_data = r_insights.json()
            if r_insights.status_code == 200:
                print(f"Insights data: {insights_data}")
            else:
                error = insights_data.get("error", {})
                print(f"Error: {error.get('message', 'Unknown')}")
        
        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
