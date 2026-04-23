import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DB_NAME", "raamp")
    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    
    posts = await db.instagram_posts.find().to_list(10)
    for p in posts:
        print(f"Post IG ID: {p.get('instagram_post_id')}, ROI: {p.get('roi_metrics')}")
    
    stories = await db.instagram_stories.find().to_list(10)
    for p in stories:
        print(f"Story IG ID: {p.get('instagram_story_id')}, ROI: {p.get('roi_metrics')}")

asyncio.run(main())
