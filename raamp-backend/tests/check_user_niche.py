import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def check_user_niche():
    uri = os.getenv("MONGODB_URL", os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    client = AsyncIOMotorClient(uri)
    db = client["raamp_db"]
    
    # 1. Check all domains
    domains = await db["business_domains"].find().to_list(100)
    print("Available Business Domains:")
    for d in domains:
        print(f"ID: {d['_id']}, Name: {d['business']}")
        
    # 2. Check user
    user = await db["users"].find_one({"email": "abdullah@gmail.com"})
    if user:
        print(f"\nUser: {user['email']}")
        print(f"Business Domain ID: {user.get('business_domain')}")
        
    client.close()

if __name__ == "__main__":
    asyncio.run(check_user_niche())
