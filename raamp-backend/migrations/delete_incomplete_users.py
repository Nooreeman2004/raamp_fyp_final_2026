"""
Delete users with incomplete onboarding (no business data)
WARNING: This is a destructive operation. Users will be permanently deleted.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from infrastructure.database.models.user_model import UserModel
from infrastructure.database.models.business_model import BusinessModel
import os
from dotenv import load_dotenv

load_dotenv()

async def delete_incomplete_users():
    """Delete users who have no business data (incomplete onboarding)"""
    
    # Connect to MongoDB
    mongo_uri = os.getenv("MONGODB_URL", os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    client = AsyncIOMotorClient(mongo_uri)
    db = client["raamp_db"]
    
    # Initialize Beanie
    await init_beanie(database=db, document_models=[UserModel, BusinessModel])
    
    print("🔍 Finding users with incomplete onboarding...")
    print("=" * 80)
    
    # Get all users
    users = await UserModel.find_all().to_list()
    users_to_delete = []
    users_to_keep = []
    
    for user in users:
        # Check if user has business data
        business = await BusinessModel.find_one({"user_id": str(user.id)})
        
        if not business or not business.country:
            users_to_delete.append(user)
        else:
            users_to_keep.append(user)
    
    print(f"\n📊 ANALYSIS:")
    print(f"   - Total users: {len(users)}")
    print(f"   - Users with complete data: {len(users_to_keep)}")
    print(f"   - Users with incomplete data: {len(users_to_delete)}")
    
    if not users_to_delete:
        print("\n✅ No incomplete users found. Nothing to delete.")
        client.close()
        return
    
    print(f"\n⚠️  THE FOLLOWING {len(users_to_delete)} USERS WILL BE DELETED:")
    print("=" * 80)
    for user in users_to_delete:
        print(f"   - {user.email}")
    
    print("\n" + "=" * 80)
    response = input(f"\n⚠️  Are you SURE you want to DELETE {len(users_to_delete)} users? (yes/no): ")
    
    if response.lower() != "yes":
        print("\n❌ Deletion cancelled. No users were deleted.")
        client.close()
        return
    
    print("\n🗑️  Deleting users...")
    deleted_count = 0
    
    for user in users_to_delete:
        try:
            await user.delete()
            print(f"✅ Deleted: {user.email}")
            deleted_count += 1
        except Exception as e:
            print(f"❌ Failed to delete {user.email}: {str(e)}")
    
    print("\n" + "=" * 80)
    print(f"✅ Deletion complete!")
    print(f"   - Deleted: {deleted_count} users")
    print(f"   - Remaining: {len(users_to_keep)} users")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(delete_incomplete_users())
