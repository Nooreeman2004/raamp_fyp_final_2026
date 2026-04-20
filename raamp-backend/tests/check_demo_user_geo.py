"""Print demo user abdullah@gmail.com business lat/lng for geo-intent. Run: python tests/check_demo_user_geo.py"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv()


async def main():
    from infrastructure.database.database import connect_to_mongo, init_db, close_mongo_connection
    from infrastructure.database.models.user_model import UserModel
    from infrastructure.repositories.business_repository import BusinessRepository

    await connect_to_mongo()
    await init_db()

    email = "abdullah@gmail.com"
    user = await UserModel.find_one(UserModel.email == email)
    if not user:
        print(f"User not found: {email}")
        await close_mongo_connection()
        sys.exit(1)

    biz = await BusinessRepository().get_by_user_id(str(user.id))
    if not biz:
        print(f"No business for {email}")
        await close_mongo_connection()
        sys.exit(1)

    print(f"User: {email}")
    print(f"  business_name: {getattr(biz, 'business_name', None)}")
    print(f"  latitude: {biz.latitude}")
    print(f"  longitude: {biz.longitude}")
    print(f"  google_place_id: {getattr(biz, 'google_place_id', None)}")
    print(f"  country: {getattr(biz, 'country', None)}")

    if biz.latitude is None or biz.longitude is None:
        print("\nWARNING: Missing coordinates — Geo-Intent will fall back to demo defaults until setup is saved.")
        sys.exit(2)
    print("\nOK: Restaurant location is set for geo scans.")
    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
