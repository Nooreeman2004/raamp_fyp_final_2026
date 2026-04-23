"""
Verify that the media IDs actually exist on Instagram
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
        # Get a user with both posts and connections
        post = await InstagramPostModel.find(
            NE(InstagramPostModel.instagram_post_id, None)
        ).limit(1).to_list()
        
        if not post:
            print("No published posts found")
            return 0
        
        post = post[0]
        user_id = post.user_id
        
        # Get connection for this user
        conn = await InstagramConnectionModel.find_one(
            InstagramConnectionModel.user_id == user_id,
            InstagramConnectionModel.page_access_token != None,  # noqa: E711
        )
        
        if not conn:
            print(f"No connection for user {user_id}")
            return 0
        
        token = EncryptionService().decrypt(conn.page_access_token)
        media_id = post.instagram_post_id
        business_id = post.ig_business_id
        
        print(f"Post: {post.id}")
        print(f"Media ID: {media_id}")
        print(f"Business ID: {business_id}")
        print(f"Published at: {post.published_at}\n")
        
        # Try different endpoint formats
        endpoints_to_try = [
            (f"{media_id}", "Plain media ID"),
            (f"{business_id}_{media_id}", "Formatted (business_media)"),
            (f"{business_id}/media/{media_id}", "Business account path"),
        ]
        
        print("=== Testing endpoint accessibility ===\n")
        
        for endpoint, description in endpoints_to_try:
            url = f"https://graph.facebook.com/v22.0/{endpoint}"
            params = {"access_token": token}
            
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    r = await client.get(url, params=params)
                    
                    status = r.status_code
                    if status == 200:
                        print(f"✓ {description}: SUCCESS (200)")
                        data = r.json()
                        print(f"  Fields available: {list(data.keys())[:10]}")
                    else:
                        data = r.json()
                        error = data.get("error", {})
                        error_msg = error.get("message", "")
                        print(f"✗ {description}: {status}")
                        print(f"  Error: {error_msg[:100]}")
                    print()
            except Exception as e:
                print(f"✗ {description}: Exception - {e}\n")
        
        # Try insights endpoint directly
        print("=== Testing insights endpoint ===\n")
        insights_endpoints = [
            (f"{media_id}/insights", "Plain media ID"),
            (f"{business_id}_{media_id}/insights", "Formatted media ID"),
        ]
        
        for endpoint, description in insights_endpoints:
            url = f"https://graph.facebook.com/v22.0/{endpoint}"
            params = {
                "metric": "reach,impressions",
                "access_token": token
            }
            
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    r = await client.get(url, params=params)
                    
                    status = r.status_code
                    if status == 200:
                        print(f"✓ {description}: SUCCESS (200)")
                        data = r.json()
                        print(f"  Data: {data}")
                    else:
                        data = r.json()
                        error = data.get("error", {})
                        error_msg = error.get("message", "")
                        error_code = error.get("code", "")
                        print(f"✗ {description}: {status}")
                        print(f"  Code: {error_code}, Message: {error_msg[:100]}")
                    print()
            except Exception as e:
                print(f"✗ {description}: Exception - {e}\n")
        
        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
