"""
Debug script to check user's business data and map locations.
"""
import asyncio
import sys
import os

# Add backend to path
_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND_ROOT = os.path.dirname(_HERE)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)


async def main():
    from infrastructure.database.database import connect_to_mongo, init_db, close_mongo_connection
    from infrastructure.database.models.user_model import UserModel
    from infrastructure.repositories.business_repository import BusinessRepository
    from infrastructure.database.models.performance_analytics_model import ConversionEventModel
    
    await connect_to_mongo()
    await init_db()
    
    try:
        email = sys.argv[1] if len(sys.argv) > 1 else "abdullah@gmail.com"
        print(f"\n=== Checking business data for {email} ===\n")
        
        # 1. Get user
        user = await UserModel.find_one(UserModel.email == email)
        if not user:
            print(f"❌ User not found: {email}")
            return
        
        print(f"✓ User found: {user.first_name} {user.last_name}")
        print(f"  ID: {user.id}")
        
        # 2. Get business
        business_repo = BusinessRepository()
        business = await business_repo.get_by_user_id(str(user.id))
        
        if not business:
            print("❌ No business found for user")
            return
        
        print(f"\n=== BUSINESS DATA ===")
        print(f"Business Name: {business.business_name}")
        print(f"Business Type: {business.business_type}")
        print(f"Address: {business.business_address}")
        print(f"City: {business.city}")
        print(f"Country: {business.country}")
        print(f"Latitude: {business.latitude}")
        print(f"Longitude: {business.longitude}")
        print(f"Place ID: {business.google_place_id}")
        print(f"Business ID: {business.id}")
        
        # 3. Check conversion events
        print(f"\n=== CONVERSION EVENTS ===")
        conversions = await ConversionEventModel.find(
            ConversionEventModel.business_id == str(business.id)
        ).sort(-ConversionEventModel.timestamp).limit(10).to_list()
        
        print(f"Found {len(conversions)} conversion events for this business")
        for i, conv in enumerate(conversions, 1):
            print(f"\n{i}. Conversion {conv.id}")
            print(f"   Revenue: ${conv.revenue}")
            print(f"   Location: ({conv.latitude}, {conv.longitude})")
            print(f"   Platform: {conv.platform}")
            print(f"   Timestamp: {conv.timestamp}")
        
        # 4. Show what should appear on map
        print(f"\n=== MAP DISPLAY ===")
        print(f"HQ Marker should show:")
        print(f"  Name: {business.business_name or 'Headquarters'}")
        print(f"  Address: {business.business_address}")
        print(f"  Location: ({business.latitude}, {business.longitude})")
        
        if conversions:
            print(f"\nConversion pings should show:")
            for conv in conversions[:3]:
                print(f"  - 'Conversion: ${conv.revenue}' at ({conv.latitude}, {conv.longitude})")
        
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
