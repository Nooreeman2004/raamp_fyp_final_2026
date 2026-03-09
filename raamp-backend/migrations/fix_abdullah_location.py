"""
Quick fix for abdullah@gmail.com - Set onboarding_location from existing business country
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from infrastructure.database.models.user_model import UserModel
from infrastructure.database.models.business_model import BusinessModel
import os
from dotenv import load_dotenv

load_dotenv()

async def fix_abdullah():
    """Fix abdullah@gmail.com specifically"""
    
    # Connect to MongoDB
    mongo_uri = os.getenv("MONGODB_URL", os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    client = AsyncIOMotorClient(mongo_uri)
    db = client["raamp_db"]
    
    # Initialize Beanie
    await init_beanie(database=db, document_models=[UserModel, BusinessModel])
    
    email = "abdullah@gmail.com"
    
    print(f"🔍 Looking for user: {email}...")
    user = await UserModel.find_one(UserModel.email == email)
    
    if not user:
        print(f"❌ User not found: {email}")
        client.close()
        return
    
    print(f"✅ User found: {email}")
    print(f"   - User ID: {str(user.id)}")
    print(f"   - Current onboarding_location: {user.onboarding_location}")
    
    # Get business by user's ObjectId (not email!)
    business = await BusinessModel.find_one({"user_id": str(user.id)})
    
    if not business:
        print(f"❌ No business found for {email}")
        client.close()
        return
    
    print(f"✅ Business found:")
    print(f"   - Country: {business.country}")
    print(f"   - Latitude: {business.latitude}")
    print(f"   - Longitude: {business.longitude}")
    
    if business.country:
        user.onboarding_location = business.country
        await user.save()
        print(f"\n✅ SUCCESS! Set onboarding_location={business.country} for {email}")
    else:
        print(f"\n⚠️  Business has no country set - cannot fix automatically")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_abdullah())
