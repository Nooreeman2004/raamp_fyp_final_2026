import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def check_db():
    uri = os.getenv("MONGODB_URL", os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    print(f"Connecting to: {uri}")
    client = AsyncIOMotorClient(uri)
    db = client["raamp_db"]
    
    det_count = await db["trend_detections"].count_documents({})
    sig_count = await db["trend_signals"].count_documents({})
    
    print(f"Total Trend Detections: {det_count}")
    print(f"Total Trend Signals: {sig_count}")
    
    if det_count > 0:
        latest = await db["trend_detections"].find().sort("detected_at", -1).limit(1).to_list(1)
        print(f"Latest detection at: {latest[0]['detected_at']}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_db())
