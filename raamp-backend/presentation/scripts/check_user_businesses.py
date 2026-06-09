"""
Check business documents for a specific user using Beanie
"""
import asyncio
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from pathlib import Path

# Import your models
from infrastructure.database.models.business_model import BusinessModel

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

async def check_user_businesses():
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
        
        # Initialize Beanie with BusinessModel
        await init_beanie(database=db, document_models=[BusinessModel])
        print("✅ Connected to MongoDB Atlas and initialized Beanie")
        
        # Get all business documents
        all_businesses = await BusinessModel.find_all().to_list()
        print(f"\n📊 Total business documents in database: {len(all_businesses)}")
        print("=" * 100)
        
        # Group by user_id
        user_businesses = {}
        for business in all_businesses:
            user_id = business.user_id
            if user_id not in user_businesses:
                user_businesses[user_id] = []
            user_businesses[user_id].append(business)
        
        # Check each user
        for user_id, businesses in user_businesses.items():
            print(f"\n👤 User: {user_id}")
            print(f"   Found {len(businesses)} business document(s)")
            
            if len(businesses) > 1:
                print(f"   ⚠️  WARNING: DUPLICATE DOCUMENTS DETECTED!")
            
            for i, b in enumerate(businesses, 1):
                print(f"\n   Document {i}:")
                print(f"      ID: {b.id}")
                print(f"      business_name: {b.business_name or 'None'}")
                print(f"      tagline: {b.tagline or 'None'}")
                print(f"      restaurant_theme: {b.restaurant_theme or 'None'}")
                print(f"      brand_logo_url: {b.brand_logo_url or 'None'}")
                print(f"      brand_colors: {b.brand_colors or []}")
                print(f"      tone_of_voice: {(b.tone_of_voice[:50] + '...') if b.tone_of_voice else 'None'}")
                print(f"      created_at: {b.created_at}")
                print(f"      updated_at: {b.updated_at if hasattr(b, 'updated_at') else 'N/A'}")
        
        print("\n" + "=" * 100)
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_user_businesses())
