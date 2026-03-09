"""
List all existing users in the database
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from infrastructure.database.models.user_model import UserModel
from infrastructure.database.models.business_model import BusinessModel
import os
from dotenv import load_dotenv

load_dotenv()

async def list_users():
    """List all users with their details"""
    
    # Connect to MongoDB
    mongo_uri = os.getenv("MONGODB_URL", os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    client = AsyncIOMotorClient(mongo_uri)
    db = client["raamp_db"]
    
    # Initialize Beanie
    await init_beanie(database=db, document_models=[UserModel, BusinessModel])
    
    print("📋 EXISTING USERS")
    print("=" * 100)
    
    # Get all users
    users = await UserModel.find_all().to_list()
    
    if not users:
        print("No users found in database.")
        client.close()
        return
    
    print(f"\nTotal Users: {len(users)}\n")
    
    for i, user in enumerate(users, 1):
        # Get business data
        business = await BusinessModel.find_one({"user_id": str(user.id)})
        
        # Determine completion status
        has_business = "✅" if business and business.country else "❌"
        has_location = "✅" if user.onboarding_location else "❌"
        profile_status = "✅" if user.profile_completed else "❌"
        
        print(f"{i}. {user.email}")
        print(f"   ID: {user.id}")
        print(f"   Name: {user.first_name or 'N/A'} {user.last_name or 'N/A'}")
        print(f"   Profile Completed: {profile_status}")
        print(f"   Business Data: {has_business}")
        print(f"   Onboarding Location: {has_location} ({user.onboarding_location or 'Not Set'})")
        
        if business:
            print(f"   Business: {business.business_name or 'N/A'} ({business.country or 'No Country'})")
            if business.latitude and business.longitude:
                print(f"   Coordinates: {business.latitude}, {business.longitude}")
        
        print(f"   Connections: FB:{user.facebook_connected}, IG:{user.instagram_connected}, GM:{user.google_maps_connected}")
        print(f"   Created: {user.created_at.strftime('%Y-%m-%d %H:%M')}")
        print()
    
    print("=" * 100)
    
    # Summary
    complete_users = []
    incomplete_users = []
    
    for user in users:
        business = await BusinessModel.find_one({"user_id": str(user.id)})
        if business and business.country:
            complete_users.append(user.email)
        else:
            incomplete_users.append(user.email)
    
    print(f"\n📊 SUMMARY:")
    print(f"   Complete Users ({len(complete_users)}): {', '.join(complete_users) if complete_users else 'None'}")
    print(f"   Incomplete Users ({len(incomplete_users)}): {len(incomplete_users)} users")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(list_users())
