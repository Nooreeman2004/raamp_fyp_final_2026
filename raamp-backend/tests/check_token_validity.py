"""
Check if the Instagram access token is still valid and has required permissions
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
    from config import settings

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
        
        print(f"User: {user_id}")
        print(f"Business ID: {conn.ig_business_id}")
        print(f"Token valid flag: {conn.token_valid}")
        print(f"Token expires at: {conn.expires_at}")
        print(f"Last refreshed: {conn.last_refreshed_at}\n")
        
        token = EncryptionService().decrypt(conn.page_access_token)
        
        # Test token validity with a simple ME endpoint
        print("=== Checking token validity ===\n")
        
        url = "https://graph.facebook.com/v22.0/me"
        params = {"access_token": token}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, params=params)
            print(f"GET /me: {r.status_code}")
            data = r.json()
            if r.status_code == 200:
                print(f"ID: {data.get('id')}")
                print(f"Name: {data.get('name')}")
            else:
                error = data.get("error", {})
                print(f"Error: {error.get('message', 'Unknown')}")
                print(f"Code: {error.get('code', 'N/A')}")
        
        print("\n=== Checking Instagram Business Account ===\n")
        
        if conn.ig_business_id:
            url = f"https://graph.facebook.com/v22.0/{conn.ig_business_id}"
            params = {"fields": "id,name,username,profile_picture_url", "access_token": token}
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(url, params=params)
                print(f"GET /business_id: {r.status_code}")
                data = r.json()
                if r.status_code == 200:
                    print(f"Name: {data.get('name')}")
                    print(f"Username: {data.get('username')}")
                else:
                    error = data.get("error", {})
                    print(f"Error: {error.get('message', 'Unknown')}")
        
        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
