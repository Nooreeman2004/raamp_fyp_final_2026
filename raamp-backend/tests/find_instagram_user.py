"""
Find users who have Instagram connected
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.database.models.user_model import UserModel
from infrastructure.database.models.social_media_account_model import SocialMediaAccountModel
from config import settings

async def find_instagram_users():
    """Find all users with Instagram connected"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client["raamp_db"]
    
    # Initialize Beanie
    await init_beanie(
        database=db,
        document_models=[UserModel, SocialMediaAccountModel]
    )
    
    print("🔍 Searching for users with Instagram connected...\n")
    
    # Find all social media connections with Instagram business ID
    instagram_connections = await SocialMediaAccountModel.find(
        SocialMediaAccountModel.ig_business_id != None
    ).to_list()
    
    if not instagram_connections:
        print("❌ No Instagram connections found in database")
        
        # Check if there are any users at all
        all_users = await UserModel.find().limit(5).to_list()
        if all_users:
            print(f"\n📋 Found {len(all_users)} users in database (showing first 5):")
            for user in all_users:
                print(f"  📧 {user.email} (username: {user.username})")
        return
    
    print(f"✅ Found {len(instagram_connections)} Instagram connection(s)\n")
    
    # Get user details for each connection
    for i, connection in enumerate(instagram_connections, 1):
        user = await UserModel.get(connection.user_id)
        if user:
            print(f"User #{i}:")
            print(f"  📧 Email: {user.email}")
            print(f"  👤 Username: {user.username}")
            print(f"  🆔 User ID: {str(user.id)}")
            print(f"  📄 Page Name: {connection.page_name}")
            print(f"  🔑 Page ID: {connection.page_id}")
            print(f"  📱 IG Business ID: {connection.ig_business_id}")
            print(f"  ✅ Connected: {connection.created_at}")
            print(f"  🔐 Has Page Token: {'Yes' if connection.page_access_token else 'No'}")
            print()
    
    # Close connection
    client.close()

if __name__ == "__main__":
    asyncio.run(find_instagram_users())
