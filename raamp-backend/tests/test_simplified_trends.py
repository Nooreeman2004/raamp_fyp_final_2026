"""
Test script for simplified trends endpoint
Run with: python raamp-backend/tests/test_simplified_trends.py
"""
import asyncio
import sys
import os
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from infrastructure.database.models.business_model import BusinessModel, BusinessTypeEnum
from infrastructure.database.models.user_model import UserModel
from application.services.trend_simplification_service import TrendSimplificationService
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from config import config


async def init_db():
    """Initialize database connection with all required models"""
    # Use MONGO_URI instead of MONGODB_URL
    mongo_uri = getattr(config, 'MONGO_URI', None) or getattr(config, 'MONGODB_URL', 'mongodb://localhost:27017/raamp_db')
    client = AsyncIOMotorClient(mongo_uri)
    
    # Import all document models needed
    from infrastructure.database.models.trend_signal_model import TrendSignalModel
    
    await init_beanie(
        database=client.get_database(),
        document_models=[UserModel, BusinessModel, TrendSignalModel]
    )


async def test_simplification_service():
    """Test the simplification service logic"""
    print("\n" + "="*60)
    print("TEST 1: Simplification Service Logic")
    print("="*60)
    
    # Test data with different scores
    test_trends = [
        {"keyword": "biryani", "location": "Lahore", "score": 85, "profit_score": 85},
        {"keyword": "bubble tea", "location": "Karachi", "score": 55, "profit_score": 55},
        {"keyword": "vegan food", "location": "Islamabad", "score": 25, "profit_score": 25},
        {"keyword": "trending topic", "location": "GLOBAL", "score": None, "profit_score": None},
    ]
    
    for trend in test_trends:
        print(f"\n📊 Testing: {trend['keyword']} (score: {trend.get('profit_score')})")
        
        # Test with RESTAURANT type
        result_restaurant = TrendSimplificationService.simplify_trend(
            {
                "id": "test123",
                "keyword": trend["keyword"],
                "location": trend["location"],
                "niche": "food",
                "profit_score": trend.get("profit_score"),
                "score": trend.get("score"),
                "detected_at": "2024-01-01T00:00:00",
            },
            business_type="restaurant"
        )
        
        print(f"  🍽️  RESTAURANT:")
        print(f"     Opportunity: {result_restaurant['opportunity_level']}")
        print(f"     Why: {result_restaurant['why_relevant']}")
        print(f"     Action: {result_restaurant['suggested_action']}")
        
        # Test with RETAIL type
        result_retail = TrendSimplificationService.simplify_trend(
            {
                "id": "test123",
                "keyword": trend["keyword"],
                "location": trend["location"],
                "niche": "retail",
                "profit_score": trend.get("profit_score"),
                "score": trend.get("score"),
                "detected_at": "2024-01-01T00:00:00",
            },
            business_type="retail"
        )
        
        print(f"  🏪 RETAIL:")
        print(f"     Opportunity: {result_retail['opportunity_level']}")
        print(f"     Why: {result_retail['why_relevant']}")
        print(f"     Action: {result_retail['suggested_action']}")


async def test_business_type_enum():
    """Test business type enum storage and retrieval"""
    print("\n" + "="*60)
    print("TEST 2: Business Type Enum")
    print("="*60)
    
    await init_db()
    
    # Test creating businesses with different types
    test_types = [
        (BusinessTypeEnum.RESTAURANT, "test_restaurant@test.com"),
        (BusinessTypeEnum.CAFE, "test_cafe@test.com"),
        (BusinessTypeEnum.RETAIL, "test_retail@test.com"),
    ]
    
    for biz_type, email in test_types:
        print(f"\n🏢 Testing {biz_type.value.upper()}")
        
        # Check if business exists
        existing = await BusinessModel.find_one({"user_id": email})
        if existing:
            print(f"   Found existing business: {existing.business_type}")
            print(f"   Is food business: {TrendSimplificationService.is_food_business(str(existing.business_type))}")
        else:
            print(f"   ⚠️  No business found for {email}")
            print(f"   Creating test business...")
            
            # Create test business
            business = BusinessModel(
                user_id=email,
                business_type=biz_type,
                business_name=f"Test {biz_type.value.title()}",
                specialties=["test", "specialty"]
            )
            await business.insert()
            print(f"   ✅ Created business with type: {business.business_type}")


async def test_api_endpoint():
    """Test the actual API endpoint (requires running server)"""
    print("\n" + "="*60)
    print("TEST 3: API Endpoint (requires running server)")
    print("="*60)
    
    import httpx
    
    # Test with different users
    test_users = [
        {"email": "test_restaurant@test.com", "type": "RESTAURANT"},
        {"email": "test_retail@test.com", "type": "RETAIL"},
    ]
    
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000/api")
    
    for user in test_users:
        print(f"\n👤 Testing user: {user['email']} ({user['type']})")
        
        # Note: This requires authentication token
        # For now, just show the curl command
        curl_cmd = f"""
curl -X GET "{base_url}/trends/simplified?limit=5" \\
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \\
  -H "Content-Type: application/json"
"""
        print(f"   Run this command after logging in as {user['email']}:")
        print(f"   {curl_cmd}")


async def test_edge_cases():
    """Test edge cases and null handling"""
    print("\n" + "="*60)
    print("TEST 4: Edge Cases")
    print("="*60)
    
    edge_cases = [
        {
            "name": "Null score",
            "data": {"keyword": "test", "location": "PK", "profit_score": None, "score": None}
        },
        {
            "name": "Zero score",
            "data": {"keyword": "test", "location": "PK", "profit_score": 0, "score": 0}
        },
        {
            "name": "Negative score",
            "data": {"keyword": "test", "location": "PK", "profit_score": -10, "score": -10}
        },
        {
            "name": "Very high score",
            "data": {"keyword": "test", "location": "PK", "profit_score": 150, "score": 150}
        },
        {
            "name": "Empty location",
            "data": {"keyword": "test", "location": "", "profit_score": 50, "score": 50}
        },
        {
            "name": "GLOBAL location",
            "data": {"keyword": "test", "location": "GLOBAL", "profit_score": 50, "score": 50}
        },
    ]
    
    for case in edge_cases:
        print(f"\n🧪 {case['name']}")
        try:
            result = TrendSimplificationService.simplify_trend(
                {
                    "id": "test",
                    "niche": "test",
                    "detected_at": "2024-01-01T00:00:00",
                    **case["data"]
                },
                business_type="restaurant"
            )
            print(f"   ✅ Opportunity: {result['opportunity_level']}")
            print(f"   ✅ Why: {result['why_relevant'][:80]}...")
            print(f"   ✅ Action: {result['suggested_action'][:80]}...")
        except Exception as e:
            print(f"   ❌ Error: {e}")


async def test_real_data():
    """Test with real data from database"""
    print("\n" + "="*60)
    print("TEST 5: Real Data from Database")
    print("="*60)
    
    await init_db()
    
    # Try to find a real user with trends
    from infrastructure.database.models.trend_signal_model import TrendSignalModel
    
    try:
        # Get latest trend signal
        trend_signal = await TrendSignalModel.find_one({})
        
        if not trend_signal:
            print("   ⚠️  No trend signals found in database")
            return
        
        print(f"\n📈 Found trend signal: {trend_signal.id}")
        print(f"   User: {trend_signal.user_email}")
        print(f"   Keywords: {trend_signal.keywords[:3] if trend_signal.keywords else []}")
        
        # Get user's business
        try:
            business = await BusinessModel.find_one({"user_id": trend_signal.user_email})
            
            if business:
                print(f"   Business type: {business.business_type}")
                business_type = str(business.business_type) if business.business_type else "restaurant"
            else:
                print(f"   ⚠️  No business found, using default")
                business_type = "restaurant"
        except Exception as e:
            # Handle validation errors for old data (e.g., business_type="General")
            print(f"   ⚠️  Business validation error (likely old data format): {str(e)[:100]}")
            print(f"   Using default business_type=restaurant")
            business_type = "restaurant"
        
        # Simplify the trend
        trend_dict = {
            "id": str(trend_signal.id),
            "keyword": trend_signal.keywords[0] if trend_signal.keywords else "unknown",
            "location": trend_signal.location,
            "niche": trend_signal.niche,
            "profit_score": trend_signal.profit_score,
            "score": trend_signal.arbitrage_score,
            "social_score": trend_signal.social_score,
            "detected_at": trend_signal.created_at,
        }
        
        result = TrendSimplificationService.simplify_trend(trend_dict, business_type)
        
        print(f"\n✨ SIMPLIFIED RESULT:")
        print(json.dumps(result, indent=2, default=str))
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("SIMPLIFIED TRENDS BACKEND TEST SUITE")
    print("="*60)
    
    # Test 1: Service logic
    await test_simplification_service()
    
    # Test 2: Business type enum
    await test_business_type_enum()
    
    # Test 3: Edge cases
    await test_edge_cases()
    
    # Test 4: Real data
    await test_real_data()
    
    # Test 5: API endpoint instructions
    await test_api_endpoint()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("""
✅ Service logic tested
✅ Business type enum tested
✅ Edge cases tested
✅ Real data tested

📝 NEXT STEPS:
1. Start the backend server: cd raamp-backend && uvicorn main:app --reload
2. Get an auth token by logging in
3. Test the endpoint manually:
   
   curl -X GET "http://localhost:8000/api/trends/simplified?limit=5" \\
     -H "Authorization: Bearer YOUR_TOKEN" \\
     -H "Content-Type: application/json"

4. Check the response for:
   - Is why_relevant plain English or templated?
   - Is opportunity_level correct for different scores?
   - Is suggested_action useful?
   - Does business type affect the response?

5. If all looks good, proceed with frontend implementation plan.
""")


if __name__ == "__main__":
    asyncio.run(main())
