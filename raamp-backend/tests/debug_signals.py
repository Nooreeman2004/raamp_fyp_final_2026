import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def debug_signals():
    uri = os.getenv("MONGODB_URL", os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    client = AsyncIOMotorClient(uri)
    db = client["raamp_db"]
    
    signals = await db["trend_signals"].find().to_list(100)
    print(f"Total Trend Signals: {len(signals)}")
    
    for s in signals:
        print(f"Signal ID: {s['_id']}, Niche: {s.get('niche')}, Location: {s.get('location')}")
        search_int = s.get('search_interest', {})
        print(f"  Keywords in search_interest: {list(search_int.keys())}")
        for kw, data in search_int.items():
            print(f"    - {kw} has {len(data)} data points")
            
    client.close()

if __name__ == "__main__":
    asyncio.run(debug_signals())
