"""Smoke test: GeoIntentService.recommend_zones at Lahore demo coords. Run: python tests/smoke_recommend_zones.py"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv()


async def main():
    from infrastructure.database.database import connect_to_mongo, init_db, close_mongo_connection
    from application.services.geo_intent_service import GeoIntentService

    await connect_to_mongo()
    await init_db()

    svc = GeoIntentService()
    zones = await svc.recommend_zones(
        business_id="smoke_lahore",
        keywords=["retail", "clothing", "store"],
        latitude=31.518,
        longitude=74.349,
        radius=5000,
        is_indoor=True,
        user_id="abdullah@gmail.com",
    )
    print(f"Top {len(zones)} zones:")
    for z in zones:
        print(
            f"  {z['label']}: score={z['score']} urgency={z['urgency']} "
            f"lat={z['latitude']:.5f} lng={z['longitude']:.5f}"
        )

    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
