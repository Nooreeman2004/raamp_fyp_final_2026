
# Unit Test for Arbitrage Intelligence Service
import pytest
import asyncio
from unittest.mock import MagicMock, patch
from application.services.arbitrage_intelligence_service import ArbitrageIntelligenceService
from presentation.schemas.arbitrage_schemas import UserProfileSchema, TrendSignalInputSchema

@pytest.mark.asyncio
async def test_generate_fallback():
    """Test the fallback logic when LLM fails"""
    service = ArbitrageIntelligenceService()
    
    user_profile = UserProfileSchema(
        niche="Fashion",
        location="Pakistan",
        target_audience="Gen Z"
    )
    
    trends = [
        TrendSignalInputSchema(
            keyword="Oversized hoodies",
            velocity_label="High",
            saturation_label="Emerging",
            arbitrage_potential="Gold Mine",
            platform_fit=["Instagram", "TikTok"],
            hashtags=["#hoodies", "#streetwear"]
        )
    ]
    
    result = service._generate_fallback(trends, user_profile)
    
    assert "recommendations" in result
    assert len(result["recommendations"]) == 1
    assert result["recommendations"][0]["trend_name"] == "Oversized hoodies"
    assert "Gold Mine" in result["context"] or "hoodies" in result["context"]

@pytest.mark.asyncio
async def test_llm_parsing_success():
    """Test successful LLM response parsing"""
    service = ArbitrageIntelligenceService()
    
    mock_json = {
        "recommendations": [
            {
                "trend_name": "Oversized hoodies",
                "campaign_idea": "Cozy Vibes Campaign",
                "recommended_platform": "Instagram",
                "reasoning": "High demand, low supply.",
                "expected_marketing_goal": "Sales",
                "suggested_hooks": ["Stay cozy!"],
                "estimated_effort": "Low",
                "priority": 9
            }
        ],
        "context": "Focus on winter wear."
    }
    
    with patch.object(service.llm_client, 'generate_structured_json', return_value=asyncio.Future()) as mock_call:
        mock_call.return_value = mock_json
        
        user_profile = UserProfileSchema(niche="Fashion", location="PK")
        trends = [TrendSignalInputSchema(
            keyword="hoodies", velocity_label="High", saturation_label="Low", 
            arbitrage_potential="High", platform_fit=["IG"], hashtags=[]
        )]
        
        result = await service.generate_recommendations(trends, user_profile)
        
        assert result == mock_json
        assert result["recommendations"][0]["trend_name"] == "Oversized hoodies"

if __name__ == "__main__":
    asyncio.run(test_generate_fallback())
    print("Fallback test passed!")
