"""
List all media available on the Instagram Business Account
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
        # Get a user with posts
        post = await InstagramPostModel.find(
            NE(InstagramPostModel.instagram_post_id, None)
        ).limit(1).to_list()
        
        if not post:
            print("No published posts found")
            return 0
        
        user_id = post[0].user_id
        
        # Get connection
        conn = await InstagramConnectionModel.find_one(
            InstagramConnectionModel.user_id == user_id,
            InstagramConnectionModel.page_access_token != None,  # noqa: E711
        )
        
        if not conn:
            print(f"No connection for user {user_id}")
            return 0
        
        token = EncryptionService().decrypt(conn.page_access_token)
        business_id = conn.ig_business_id
        
        print(f"Fetching media for business account: {business_id}\n")
        
        # List media endpoint
        url = f"https://graph.facebook.com/v22.0/{business_id}/media"
        params = {
            "fields": "id,media_type,media_product_type,created_time,caption",
            "access_token": token,
            "limit": 50
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, params=params)
            print(f"Status: {r.status_code}\n")
            
            data = r.json()
            if r.status_code == 200:
                media_list = data.get("data", [])
                print(f"Found {len(media_list)} media items:\n")
                
                for item in media_list[:5]:  # Show first 5
                    print(f"ID: {item.get('id')}")
                    print(f"  Type: {item.get('media_type')}")
                    print(f"  Product Type: {item.get('media_product_type')}")
                    print(f"  Created: {item.get('created_time')}")
                    print()
                
                # Check if any of our stored IDs exist in this list
                print("\n=== Checking if stored IDs exist ===\n")
                stored_ids = await InstagramPostModel.find(
                    InstagramPostModel.user_id == user_id,
                    NE(InstagramPostModel.instagram_post_id, None)
                ).limit(5).to_list()
                
                found_ids = {m['id'] for m in media_list}
                
                for stored_post in stored_ids:
                    if stored_post.instagram_post_id in found_ids:
                        print(f"✓ Found: {stored_post.instagram_post_id}")
                    else:
                        print(f"✗ Not found: {stored_post.instagram_post_id}")
            else:
                error = data.get("error", {})
                print(f"Error: {error.get('message', 'Unknown')}")
                print(f"Code: {error.get('code', 'N/A')}")
        
        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
