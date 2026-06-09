"""
Cleanup script to:
1. Delete all users except abdullah@gmail.com and 698338fad7c3f5ec620c599b
2. Copy brand settings from 698338fad7c3f5ec620c599b to abdullah@gmail.com
3. Delete the 698338fad7c3f5ec620c599b user
"""
import asyncio
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from pathlib import Path

# Import models
from infrastructure.database.models.business_model import BusinessModel
from infrastructure.database.models.user_model import UserModel

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

async def cleanup_and_merge():
    # Get MongoDB connection
    mongo_uri = os.getenv("MONGODB_URI") or os.getenv("MONGODB_URL")
    
    if not mongo_uri:
        print("❌ ERROR: MONGODB_URI or MONGODB_URL not found in .env file")
        return
    
    print(f"🔗 Connecting to MongoDB Atlas...")
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongo_uri)
        db = client.raamp_db
        
        # Initialize Beanie
        await init_beanie(database=db, document_models=[BusinessModel, UserModel])
        print("✅ Connected to MongoDB Atlas")
        
        # Step 1: Find the two users we want to keep
        abdullah_email_user = await BusinessModel.find_one(BusinessModel.user_id == "abdullah@gmail.com")
        butlers_user = await BusinessModel.find_one(BusinessModel.user_id == "698338fad7c3f5ec620c599b")
        
        if not butlers_user:
            print("❌ Could not find user 698338fad7c3f5ec620c599b")
            return
        
        print(f"\n📋 Found butlers user with brand settings:")
        print(f"   business_name: {butlers_user.business_name}")
        print(f"   tagline: {butlers_user.tagline}")
        print(f"   restaurant_theme: {butlers_user.restaurant_theme}")
        print(f"   brand_logo_url: {butlers_user.brand_logo_url}")
        print(f"   brand_colors: {butlers_user.brand_colors}")
        
        # Step 2: Copy brand settings to abdullah@gmail.com
        if abdullah_email_user:
            print(f"\n📝 Updating abdullah@gmail.com with brand settings...")
            abdullah_email_user.business_name = butlers_user.business_name
            abdullah_email_user.tagline = butlers_user.tagline
            abdullah_email_user.restaurant_theme = butlers_user.restaurant_theme
            abdullah_email_user.brand_logo_url = butlers_user.brand_logo_url
            abdullah_email_user.brand_colors = butlers_user.brand_colors
            abdullah_email_user.palette_source = butlers_user.palette_source
            abdullah_email_user.primary_color = butlers_user.primary_color
            abdullah_email_user.secondary_color = butlers_user.secondary_color
            abdullah_email_user.tone_of_voice = butlers_user.tone_of_voice
            abdullah_email_user.tone_profile = butlers_user.tone_profile
            await abdullah_email_user.save()
            print("✅ Brand settings copied to abdullah@gmail.com")
        else:
            print("❌ Could not find abdullah@gmail.com business document")
            return
        
        # Step 3: Get all business documents
        all_businesses = await BusinessModel.find_all().to_list()
        print(f"\n📊 Total business documents: {len(all_businesses)}")
        
        # Step 4: Delete all except abdullah@gmail.com
        keep_users = ["abdullah@gmail.com"]
        deleted_count = 0
        
        for business in all_businesses:
            if business.user_id not in keep_users:
                print(f"🗑️  Deleting user: {business.user_id}")
                await business.delete()
                deleted_count += 1
        
        print(f"\n✅ Deleted {deleted_count} business documents")
        print(f"✅ Kept 1 user: abdullah@gmail.com")
        
        # Step 5: Verify
        remaining = await BusinessModel.find_all().to_list()
        print(f"\n📊 Remaining business documents: {len(remaining)}")
        for b in remaining:
            print(f"   User: {b.user_id}")
            print(f"      business_name: {b.business_name}")
            print(f"      tagline: {b.tagline}")
            print(f"      brand_logo_url: {b.brand_logo_url}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("⚠️  WARNING: This will delete all users except abdullah@gmail.com")
    print("   and copy brand settings from 698338fad7c3f5ec620c599b")
    response = input("\nType 'yes' to continue: ")
    
    if response.lower() == 'yes':
        asyncio.run(cleanup_and_merge())
    else:
        print("❌ Cancelled")
