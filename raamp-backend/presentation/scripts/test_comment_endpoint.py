"""Test comment moderation endpoint directly"""
import asyncio
from infrastructure.database.database import connect_to_mongo, init_db
from presentation.routers.comment_analysis_router import get_moderation_comments

async def test_endpoint():
    """Test the endpoint function directly"""
    await connect_to_mongo()
    await init_db()
    
    print("Testing get_moderation_comments endpoint...")
    try:
        # Mock the current_user dependency (it's just for auth, not used in the function)
        result = await get_moderation_comments(
            _current_user="test@test.com",
            sentiment=None,
            limit=100
        )
        print("✅ Endpoint returned successfully!")
        print(f"Response: {result}")
    except Exception as e:
        print(f"❌ Endpoint failed with error:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_endpoint())
