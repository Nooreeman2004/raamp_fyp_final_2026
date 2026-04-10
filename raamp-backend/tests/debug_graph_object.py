"""
Debug what a stored instagram_post_id actually refers to by querying Graph API.

This prints only safe metadata (no tokens).
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
    user = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    if not user:
        print("Usage: python tests/debug_graph_object.py abdullah@gmail.com")
        return 2

    from infrastructure.database.database import connect_to_mongo, init_db, close_mongo_connection
    from infrastructure.database.models.instagram_connection_model import InstagramConnectionModel
    from infrastructure.database.models.instagram_post_model import InstagramPostModel
    from application.services.encryption_service import EncryptionService

    await connect_to_mongo()
    await init_db()
    try:
        post = await InstagramPostModel.find(
            InstagramPostModel.user_id == user,
            InstagramPostModel.instagram_post_id != None,  # noqa: E711
        ).sort(InstagramPostModel.created_at).first_or_none()
        if not post or not post.instagram_post_id:
            print("No post with instagram_post_id found for user:", user)
            return 0

        conn = await InstagramConnectionModel.find_one(
            InstagramConnectionModel.user_id == user,
            InstagramConnectionModel.page_access_token != None,  # noqa: E711
            InstagramConnectionModel.token_valid == True,  # noqa: E712
        )
        if not conn:
            print("No usable connection (page_access_token) for user:", user)
            return 1

        token = EncryptionService().decrypt(conn.page_access_token)
        obj_id = post.instagram_post_id

        url = f"https://graph.facebook.com/v22.0/{obj_id}"
        params = {"fields": "id,caption,media_type,permalink,username,created_time", "access_token": token}
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(url, params=params)
            print("status_code:", r.status_code)
            data = r.json()
            # Print only keys + a couple safe fields
            if isinstance(data, dict):
                print("response_keys:", sorted(list(data.keys()))[:30])
                print("id:", data.get("id"))
                print("media_type:", data.get("media_type"))
                print("created_time:", data.get("created_time"))
                print("has_caption:", bool(data.get("caption")))
                if data.get("error"):
                    print("error:", data["error"].get("message"), "code:", data["error"].get("code"))
            else:
                print("response:", data)
        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

