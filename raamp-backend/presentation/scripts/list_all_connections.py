#!/usr/bin/env python3
"""
List all Instagram/Facebook connections to find orphaned accounts.
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from infrastructure.database.models.instagram_connection_model import InstagramConnectionModel
from infrastructure.database.models.facebook_connection_model import FacebookConnectionModel
from config import settings


async def list_all_connections():
    """Show all social media connections across all users."""
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client["raamp_db"]
    await init_beanie(
        database=db,
        document_models=[
            InstagramConnectionModel,
            FacebookConnectionModel,
        ],
    )

    print("\n📱 All Instagram Connections:\n")
    ig_conns = await InstagramConnectionModel.find_all().to_list()
    if ig_conns:
        for conn in ig_conns:
            print(f"   User ID: {conn.user_id}")
            print(f"   Username: {conn.username}")
            print(f"   IG Business ID: {conn.ig_business_id}")
            print(f"   Token Valid: {conn.token_valid}")
            print(f"   Created: {conn.created_at}")
            print()
    else:
        print("   None found\n")

    print("📘 All Facebook Connections:\n")
    fb_conns = await FacebookConnectionModel.find_all().to_list()
    if fb_conns:
        for conn in fb_conns:
            print(f"   User ID: {conn.user_id}")
            print(f"   Pages: {[p.get('name') for p in conn.fb_pages]}")
            print(f"   Token Valid: {conn.token_valid}")
            print(f"   Created: {conn.created_at}")
            print()
    else:
        print("   None found\n")


if __name__ == "__main__":
    asyncio.run(list_all_connections())
