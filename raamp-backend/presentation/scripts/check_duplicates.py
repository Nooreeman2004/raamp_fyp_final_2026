"""
Quick script to check for duplicate business documents in MongoDB
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables from the correct .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

async def check_duplicates():
    # Connect to MongoDB
    mongo_uri = os.getenv("MONGODB_URI") or os.getenv("MONGODB_URL")
    
    if not mongo_uri:
        print("❌ ERROR: MONGODB_URI or MONGODB_URL not found in .env file")
        print(f"   Looking for .env at: {env_path}")
        print(f"   .env exists: {env_path.exists()}")
        return
    
    print(f"🔗 Connecting to MongoDB Atlas...")
    print(f"   URI: {mongo_uri[:50]}...")
    
    try:
        client = AsyncIOMotorClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # Test connection
        await client.admin.command('ping')
        print("✅ Connected to MongoDB Atlas")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return
    
    db = client.raamp_db
    
    # Get all business documents
    businesses = await db.businesses.find({}).to_list(length=None)
    
    print(f"\n📊 Total business documents: {len(businesses)}")
    print("=" * 80)
    
    # Group by user_id
    user_businesses = {}
    for business in businesses:
        user_id = business.get('user_id')
        if user_id not in user_businesses:
            user_businesses[user_id] = []
        user_businesses[user_id].append(business)
    
    # Find duplicates
    duplicates_found = False
    for user_id, docs in user_businesses.items():
        if len(docs) > 1:
            duplicates_found = True
            print(f"\n⚠️  User {user_id} has {len(docs)} business documents:")
            for i, doc in enumerate(docs, 1):
                print(f"\n   Document {i} (ID: {doc.get('_id')}):")
                print(f"      business_name: {doc.get('business_name', 'None')}")
                print(f"      tagline: {doc.get('tagline', 'None')}")
                print(f"      restaurant_theme: {doc.get('restaurant_theme', 'None')}")
                print(f"      brand_logo_url: {doc.get('brand_logo_url', 'None')}")
                print(f"      brand_colors: {doc.get('brand_colors', [])}")
                print(f"      tone_of_voice: {doc.get('tone_of_voice', 'None')[:50] if doc.get('tone_of_voice') else 'None'}...")
                print(f"      created_at: {doc.get('created_at', 'None')}")
                print(f"      updated_at: {doc.get('updated_at', 'None')}")
    
    if not duplicates_found:
        print("\n✅ No duplicate business documents found")
        print("\nShowing all business documents:")
        for user_id, docs in user_businesses.items():
            doc = docs[0]
            print(f"\n   User: {user_id}")
            print(f"      business_name: {doc.get('business_name', 'None')}")
            print(f"      tagline: {doc.get('tagline', 'None')}")
            print(f"      restaurant_theme: {doc.get('restaurant_theme', 'None')}")
            print(f"      brand_logo_url: {doc.get('brand_logo_url', 'None')}")
            print(f"      brand_colors: {doc.get('brand_colors', [])}")
    
    print("\n" + "=" * 80)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_duplicates())
