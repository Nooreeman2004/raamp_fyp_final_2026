"""
Migration: Fix onboarding_location for existing users
Sets user.onboarding_location from business.country for users who have business data but no onboarding_location
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from infrastructure.database.models.user_model import UserModel
from infrastructure.database.models.business_model import BusinessModel
import os
from dotenv import load_dotenv

load_dotenv()

async def fix_onboarding_locations():
    """Set onboarding_location for users who have business country but no onboarding_location"""
    
    # Connect to MongoDB
    mongo_uri = os.getenv("MONGODB_URL", os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    client = AsyncIOMotorClient(mongo_uri)
    db = client["raamp_db"]
    
    # Initialize Beanie
    await init_beanie(database=db, document_models=[UserModel, BusinessModel])
    
    print("🔍 Finding users with business location but no onboarding_location...")
    
    # Get all users
    users = await UserModel.find_all().to_list()
    fixed_count = 0
    skipped_count = 0
    
    for user in users:
        # Skip if user already has onboarding_location
        if user.onboarding_location:
            print(f"✅ {user.email}: Already has onboarding_location={user.onboarding_location}")
            skipped_count += 1
            continue
        
        # Check if user has business with country (search by user ObjectId, not email)
        business = await BusinessModel.find_one({"user_id": str(user.id)})
        if business and business.country:
            # Set onboarding_location from business.country
            user.onboarding_location = business.country
            await user.save()
            print(f"✅ {user.email}: Set onboarding_location={business.country} from business.country")
            fixed_count += 1
        else:
            print(f"⚠️  {user.email}: No business country found - user needs to complete onboarding")
    
    print(f"\n✅ Migration complete!")
    print(f"   - Fixed: {fixed_count} users")
    print(f"   - Skipped: {skipped_count} users (already had location)")
    print(f"   - Total processed: {len(users)} users")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_onboarding_locations())
