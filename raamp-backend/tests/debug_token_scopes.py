"""
Debug Graph API token scopes using /debug_token.

Requires FACEBOOK_APP_ID and FACEBOOK_APP_SECRET in environment (.env loaded by database connect).
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
        print("Usage: python tests/debug_token_scopes.py abdullah@gmail.com")
        return 2

    app_id = os.getenv("FACEBOOK_APP_ID") or os.getenv("INSTAGRAM_APP_ID")
    app_secret = os.getenv("FACEBOOK_APP_SECRET") or os.getenv("INSTAGRAM_APP_SECRET")
    if not app_id or not app_secret:
        print("Missing FACEBOOK_APP_ID/FACEBOOK_APP_SECRET in environment.")
        return 1

    from infrastructure.database.database import connect_to_mongo, init_db, close_mongo_connection
    from infrastructure.database.models.instagram_connection_model import InstagramConnectionModel
    from application.services.encryption_service import EncryptionService

    await connect_to_mongo()
    await init_db()
    try:
        conn = await InstagramConnectionModel.find_one(InstagramConnectionModel.user_id == user)
        if not conn:
            print("No Instagram connection for user:", user)
            return 0

        enc = conn.user_access_token or conn.page_access_token
        if not enc:
            print("Connection has no stored access token.")
            return 1

        token = EncryptionService().decrypt(enc)
        app_token = f"{app_id}|{app_secret}"

        url = "https://graph.facebook.com/debug_token"
        params = {"input_token": token, "access_token": app_token}
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(url, params=params)
            print("status_code:", r.status_code)
            data = r.json()
            if isinstance(data, dict) and data.get("data"):
                d = data["data"]
                print("is_valid:", d.get("is_valid"))
                print("user_id:", d.get("user_id"))
                print("app_id:", d.get("app_id"))
                print("type:", d.get("type"))
                scopes = d.get("scopes") or []
                print("scopes:", scopes)
            else:
                print("response:", data)
        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

