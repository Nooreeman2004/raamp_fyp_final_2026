#!/usr/bin/env python3
"""
Check connection status after reconnecting.
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from infrastructure.database.models.instagram_connection_model import InstagramConnectionModel
from infrastructure.database.models.facebook_connection_model import FacebookConnectionModel
from infrastructure.database.models.user_model import UserModel
from config import settings


async def check_connections(user_email: str):
    """Quick check for active social media connections."""
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client["raamp_db"]
    await init_beanie(
        database=db,
        document_models=[
            InstagramConnectionModel,
            FacebookConnectionModel,
            UserModel,
        ],
    )

    user = await UserModel.find_one(UserModel.email == user_email)
    if not user:
        print(f"❌ User not found: {user_email}")
        return

    print(f"\n✅ Checking connections for: {user.email}\n")

    ig_conn = await InstagramConnectionModel.find_one(InstagramConnectionModel.user_id == str(user.id))
    if ig_conn:
        print(f"✅ Instagram CONNECTED")
        print(f"   Business ID: {ig_conn.ig_business_id}")
        print(f"   Username: {ig_conn.username}")
        print(f"   Token Valid: {ig_conn.token_valid}")
    else:
        print("❌ Instagram NOT connected")
    print()

    fb_conn = await FacebookConnectionModel.find_one(FacebookConnectionModel.user_id == str(user.id))
    if fb_conn:
        print(f"✅ Facebook CONNECTED")
        if fb_conn.fb_pages:
            for page in fb_conn.fb_pages:
                print(f"   Page: {page.get('name')} (ID: {page.get('id')})")
        print(f"   Token Valid: {fb_conn.token_valid}")
    else:
        print("❌ Facebook NOT connected")
    print()

    if (ig_conn and ig_conn.token_valid) or (fb_conn and fb_conn.token_valid):
        print("✅ Ready for auto-replies!")
        print("\n💡 Comment on your post and check /dashboard/auto-replies")
    else:
        print("⚠️  Connect a social account to enable auto-replies")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_connections.py <user_email>")
        sys.exit(1)

    email = sys.argv[1].strip().lower()
    asyncio.run(check_connections(email))
