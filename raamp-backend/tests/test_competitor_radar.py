import asyncio
import json
from unittest.mock import AsyncMock, patch

async def run_logic_test():
    print("RUNNING LOGIC TEST: Competitor Radar")
    
    # Mock data
    mock_media = [
        {
            "username": "competitor_one",
            "like_count": 100,
            "comments_count": 50,
            "permalink": "https://ig.com/p/123",
            "media_type": "VIDEO"
        },
        {
            "username": "competitor_two",
            "like_count": 200,
            "comments_count": 100,
            "permalink": "https://ig.com/p/456",
            "media_type": "IMAGE"
        }
    ]

    # Import the router function
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from presentation.routers.trend_signal_router import competitor_radar

    # Mock the Instagram Client
    with patch("presentation.routers.trend_signal_router.InstagramGraphAPIClient") as MockClient:
        instance = MockClient.return_value
        instance.search_hashtag_id = AsyncMock(return_value="tag123")
        instance.get_hashtag_recent_media_info = AsyncMock(return_value=mock_media)
        
        # Mock Cache helpers
        with patch("presentation.routers.trend_signal_router._cached_get", AsyncMock(return_value=None)):
            with patch("presentation.routers.trend_signal_router._cached_set", AsyncMock(return_value=True)):
                
                # Execute logic
                result = await competitor_radar(
                    geo="PK",
                    niche="food",
                    keyword="pizza",
                    current_user_email="test@example.com"
                )
                
                # Verify
                print("Result:", json.dumps(result, indent=2))
                
                influencers = result.get("influencers", [])
                assert len(influencers) == 2
                
                # Top one should be competitor_two (higher heat)
                # interactions = 300, heat = 60
                assert influencers[0]["handle"] == "competitor_two"
                assert influencers[0]["engagement_rate"] == 60
                assert "300+ interactions" in influencers[0]["follower_count_formatted"]
                assert influencers[0]["url"] == "https://ig.com/p/456"
                
                # Second one should be competitor_one
                # interactions = 150, heat = 30
                assert influencers[1]["handle"] == "competitor_one"
                assert influencers[1]["engagement_rate"] == 30
                
                print("✅ LOGIC TEST PASSED")

if __name__ == "__main__":
    asyncio.run(run_logic_test())
