"""
Initialize unique indexes on users and businesses collections
This ensures no duplicate emails, usernames, or user_ids
"""
import asyncio
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from pathlib import Path

# Import models
from infrastructure.database.models.user_model import UserModel
from infrastructure.database.models.business_model import BusinessModel

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

async def init_indexes():
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
        await init_beanie(database=db, document_models=[UserModel, BusinessModel])
        print("✅ Connected to MongoDB Atlas")
        
        # Create unique indexes on users collection
        print("\n📋 Creating unique indexes on 'users' collection...")
        users_collection = db.users
        
        # Drop existing indexes if they exist (except _id)
        existing_indexes = await users_collection.index_information()
        for index_name in existing_indexes:
            if index_name != "_id_":
                print(f"   Dropping existing index: {index_name}")
                await users_collection.drop_index(index_name)
        
        # Create unique index on email
        await users_collection.create_index("email", unique=True, name="email_unique")
        print("   ✅ Created unique index on 'email'")
        
        # Create unique index on username
        await users_collection.create_index("username", unique=True, name="username_unique")
        print("   ✅ Created unique index on 'username'")
        
        # Create unique indexes on businesses collection
        print("\n📋 Creating unique indexes on 'businesses' collection...")
        businesses_collection = db.businesses
        
        # Drop existing indexes if they exist (except _id)
        existing_indexes = await businesses_collection.index_information()
        for index_name in existing_indexes:
            if index_name != "_id_":
                print(f"   Dropping existing index: {index_name}")
                await businesses_collection.drop_index(index_name)
        
        # Create unique index on user_id
        await businesses_collection.create_index("user_id", unique=True, name="user_id_unique")
        print("   ✅ Created unique index on 'user_id'")
        
        # Create regular index on google_place_id
        await businesses_collection.create_index("google_place_id", name="google_place_id_idx")
        print("   ✅ Created index on 'google_place_id'")
        
        print("\n✅ All unique indexes created successfully!")
        print("\n📊 Summary:")
        print("   - users.email: UNIQUE")
        print("   - users.username: UNIQUE")
        print("   - businesses.user_id: UNIQUE")
        print("   - businesses.google_place_id: INDEXED")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(init_indexes())
