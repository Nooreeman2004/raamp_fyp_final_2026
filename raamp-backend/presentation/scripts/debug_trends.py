import asyncio
import os
from infrastructure.database.models.trend_detection_model import TrendDetectionModel
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

async def check():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    await init_beanie(database=client.raamp, document_models=[TrendDetectionModel])
    
    count = await TrendDetectionModel.find_all().count()
    print(f"TOTAL_TRENDS: {count}")
    
    trends = await TrendDetectionModel.find_all().limit(5).to_list()
    for t in trends:
        print(f"TREND: {t.keyword} | USER: {t.user_id} | NICHE: {t.niche} | EXPIRES: {t.expires_at}")

if __name__ == "__main__":
    asyncio.run(check())
